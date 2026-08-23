#!/usr/bin/env python3
"""
Tenable.io - Collect scans' tag value filters and include scan metadata.
Also emits a Graphviz DOT file to visualize Scanner/Group -> Scan -> Tag Value relationships.

Outputs:
  1) JSON (tenable_io_tag_filters_and_values.json) rows with:
      - scan_id, scan_name, scanner_name, tag_value_uuid, value, filters
  2) Graphviz DOT (tenable_io_architecture.dot):
      - clusters per scanner/group
      - scan nodes within each cluster
      - tag value nodes connected under each scan
      - optional subnet/CIDR hints derived from tag filters

Auth/Secrets:
  - Use TIO_ACCESS_KEY / TIO_SECRET_KEY env vars.

Requires:
  pip install pytenable tqdm graphviz restfly

Render examples:
  dot  -Tpng tenable_io_architecture.dot -o tenable_io_architecture.png
  dot  -Tsvg tenable_io_architecture.dot -o tenable_io_architecture.svg
"""

import json
import logging
import re
import time
import html
import hashlib
from restfly.errors import NotFoundError
from tenable.io import TenableIO
from tqdm import tqdm

# Correct UUID pattern (Tenable returns lowercase hex by default)
UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.I
)

# ---------------------------
# Helpers / Utilities
# ---------------------------

def get_scan_details(scan_id, tio_client=None):
    """Wrapper to get scan details with retry on 404 errors."""
    client = tio_client or TenableIO()
    max_retries = 3
    delay_seconds = 2
    for attempt in range(max_retries):
        try:
            return client.scans.details(scan_id=scan_id)
        except NotFoundError:
            if attempt < max_retries - 1:
                logging.warning(
                    "Scan ID %s not found. Retrying in %d seconds...",
                    scan_id, delay_seconds
                )
                time.sleep(delay_seconds)
            else:
                logging.error(
                    "Scan ID %s not found after %d attempts.",
                    scan_id, max_retries
                )
                raise
    return None


def _normalize_uuid_like(x):
    """
    Accept uuid-like things:
      - 'uuid' (str)
      - ['uuid'] or [['uuid']] -> unwrap first element repeatedly
      - dicts like {'uuid': ...}, {'tag_value_uuid': ...}, {'id': ...}
    Returns a uuid string or None if it cannot be normalized/validated.
    """
    v = x
    while isinstance(v, (list, tuple)) and len(v) > 0:
        v = v[0]
    if isinstance(v, dict):
        for k in ('tag_value_uuid', 'uuid', 'id', 'value_uuid'):
            if k in v and isinstance(v[k], str):
                v = v[k]
                break
    if not isinstance(v, str):
        return None
    v = v.strip()
    return v if UUID_RE.match(v) else None


def normalize_tag_value_uuid(raw):
    """
    Accepts a UUID string, a list/tuple possibly nested,
    or a dict with a likely uuid field, and returns a clean UUID string.
    Raises ValueError if it can't produce a valid UUID.
    """
    v = raw
    while isinstance(v, (list, tuple)) and len(v) > 0:
        v = v[0]
    if isinstance(v, dict):
        for k in ('tag_value_uuid', 'uuid', 'id', 'value_uuid'):
            if k in v and isinstance(v[k], str):
                v = v[k]
                break
    if not isinstance(v, str):
        raise ValueError(
            f"Unrecognized tag identifier shape: {type(v).__name__}"
        )
    v = v.strip()
    if not UUID_RE.match(v):
        raise ValueError(
            f"tag_value_uuid has value of {raw!r}. Does not match UUID pattern"
        )
    return v


def parse_asset_filters(filters, tag_id):
    """Return a list of AND filters from filters['asset']."""
    if not filters or 'asset' not in filters:
        logging.info("No asset filters found for tag %s. Skipping.", tag_id)
        return None
    asset = filters['asset']
    if isinstance(asset, str):
        try:
            asset_data = json.loads(asset)
        except json.JSONDecodeError as e:
            logging.warning(
                "Invalid JSON in filters['asset'] for tag %s: %s", tag_id, e
            )
            return None
    elif isinstance(asset, dict):
        asset_data = asset
    else:
        logging.warning(
            "Unexpected type for filters['asset'] in tag %s: %s",
            tag_id, type(asset).__name__
        )
        return None

    filter_list = asset_data.get('and', [])
    if not filter_list:
        logging.info("No 'and' filters found for tag %s. Skipping.", tag_id)
        return None
    return filter_list


# ---------------------------
# Phase 1: Build tag-target map WITH scan metadata
# ---------------------------

def _extract_scan_targets(scan, client):
    """Extracts scan details and normalized tag targets for a single scan."""
    scan_id = scan.get('id')
    try:
        scan_details = get_scan_details(scan_id, tio_client=client)
    except NotFoundError:
        return None, "not_found", 0

    if not isinstance(scan_details, dict):
        logging.error(
            "Scan %s: details payload is None or not a dict; skipping.",
            scan_id
        )
        return None, "invalid_payload", 0

    scan_name = scan_details.get('name') or scan.get('name') or f"Scan {scan_id}"
    settings = scan_details.get('settings') or {}

    scanner_name = (
        settings.get('scanner_name') or
        settings.get('scanner') or
        settings.get('scanner_id') or
        scan_details.get('scanner_id') or
        "Unknown Scanner/Group"
    )

    raw_targets = settings.get('tag_targets', [])
    if not raw_targets:
        return None, "empty", 0

    normalized = []
    dropped_invalid = 0
    for x in raw_targets:
        u = _normalize_uuid_like(x)
        if u:
            normalized.append(u)
        else:
            dropped_invalid += 1
            logging.debug("Scan %s: dropping malformed tag target %r", scan_id, x)

    if not normalized:
        return None, "all_invalid", dropped_invalid

    meta = {
        "scan_id": scan_id,
        "uuids": normalized,
        "scan_name": str(scan_name),
        "scanner_name": str(scanner_name)
    }
    return meta, "ok", dropped_invalid


def get_tag_targets(scans_list=None, tio_client=None):
    """
    Returns a dict keyed by scan_id with metadata needed later:
      {
        <scan_id>: {
          "uuids": [<tag_value_uuid>, ...],
          "scan_name": "<name>",
          "scanner_name": "<scanner id or name>"
        },
        ...
      }
    """
    client = tio_client or TenableIO()
    scans_to_process = (
        scans_list if scans_list is not None else client.scans.list()
    )

    kept = {}
    dropped_empty = 0
    dropped_all_invalid = 0
    dropped_items_invalid = 0

    print("Getting tag UUIDs for scan count: ", len(scans_to_process), "\n")
    for scan in tqdm(
        scans_to_process,
        desc="Processing scans",
        bar_format=(
            "{l_bar}{bar} {n_fmt}/{total_fmt} "
            "[Elapsed: {elapsed} - Remaining: {remaining}, {rate_fmt}]"
        ),
        ncols=100
    ):
        meta, status, dropped_cnt = _extract_scan_targets(scan, client)
        dropped_items_invalid += dropped_cnt

        if status == "empty":
            dropped_empty += 1
        elif status == "all_invalid":
            dropped_all_invalid += 1
        elif status == "ok" and meta:
            kept[meta["scan_id"]] = {
                "scan_id": meta["scan_id"],
                "uuids": meta["uuids"],
                "scan_name": meta["scan_name"],
                "scanner_name": meta["scanner_name"]
            }

    logging.info(
        "Tag targets summary — kept scans: %d | dropped(empty): %d | "
        "dropped(all invalid): %d | dropped(invalid items): %d",
        len(kept), dropped_empty, dropped_all_invalid, dropped_items_invalid
    )
    return kept


# ---------------------------
# Phase 2: Resolve tag values & filters and emit rows carrying scan metadata
# ---------------------------

def _resolve_tag_details_with_cache(tio_client, t, tag_cache, stats):
    """
    Resolves tag details for a given UUID, using and updating the cache.
    """
    if t in tag_cache:
        stats["hits"] += 1
        return tag_cache[t]

    stats["misses"] += 1
    tags = tio_client.tags.details(t)
    tag_value = tags.get("value")
    if not tag_value:
        logging.info("No 'value' found for tag value UUID %s. Skipping.", t)
        tag_cache[t] = None
        return None

    filters = tags.get("filters")
    filter_list = parse_asset_filters(filters, t)
    if not filter_list:
        tag_cache[t] = None
        return None

    tag_cache[t] = {
        "value": tag_value,
        "filters": filter_list
    }
    return tag_cache[t]


def _process_scan_tag_target(tio_client, meta, raw_t, tag_cache, stats):
    """Processes a single raw tag target for a scan and returns a result dict or None."""
    t = normalize_tag_value_uuid(raw_t)
    cached = _resolve_tag_details_with_cache(tio_client, t, tag_cache, stats)
    if cached is None:
        return None

    scan_id = meta.get("scan_id", "unknown")
    return {
        "scan_id": scan_id,
        "scan_name": meta.get("scan_name") or f"Scan {scan_id}",
        "scanner_name": meta.get("scanner_name") or "Unknown Scanner/Group",
        "tag_value_uuid": t,
        "value": cached["value"],
        "filters": cached["filters"]
    }


def collect_tag_filters_and_value(tio_client, tag_targets):
    """
    Iterate tag_targets and collect parsed asset filters AND the tag 'value'
    for each tag value UUID.
    """
    results = []
    # ⚡ BOLT Optimization: Cache tag details to reduce API calls O(Total)->O(Unique)
    tag_cache = {}
    stats = {"hits": 0, "misses": 0}

    for scan_id, meta in tag_targets.items():
        if not isinstance(meta, dict):
            logging.error(
                "Scan %s: unexpected tag_targets meta type %s; skipping.",
                scan_id, type(meta).__name__
            )
            continue

        meta_ctx = dict(meta)
        meta_ctx["scan_id"] = scan_id

        for raw_t in meta_ctx.get("uuids") or []:
            try:
                row = _process_scan_tag_target(
                    tio_client, meta_ctx, raw_t, tag_cache, stats
                )
                if row:
                    results.append(row)

            except ValueError as ve:
                logging.error("Error processing tag %r: %s", raw_t, ve)
            except NotFoundError as nf:
                logging.error("Error processing tag %s: %s", raw_t, nf)
            except Exception as e:  # pylint: disable=broad-except
                logging.error(
                    "Unexpected error processing tag %r: %s", raw_t, e
                )

    logging.info(
        "Tag resolution stats: Cache Hits: %d, Cache Misses: %d",
        stats["hits"], stats["misses"]
    )
    return results


# ---------------------------
# Phase 3: Graphviz DOT generation
# ---------------------------

def _sanitize_id(s: str) -> str:
    """Make a deterministic Graphviz-safe ID from an arbitrary string."""
    base = re.sub(r'[^A-Za-z0-9_]', '_', s or "node")
    if re.match(r'^\d', base):
        base = "_" + base
    digest = hashlib.md5(s.encode('utf-8')).hexdigest()[:8]
    return f"{base}_{digest}"


def _filters_to_subnet_hints(filters) -> list:
    """Extract any CIDR-like values from filter entries for rendering hints."""
    cidrs = []
    cidr_re = re.compile(r'^\s*\d{1,3}(?:\.\d{1,3}){3}/\d{1,2}\s*$')

    def add_cidr(x):
        if isinstance(x, str) and cidr_re.match(x):
            cidrs.append(x.strip())

    for f_entry in filters or []:
        for key in ('value', 'values'):
            if key in f_entry:
                val = f_entry[key]
                if isinstance(val, list):
                    for item in val:
                        add_cidr(item)
                else:
                    add_cidr(val)

    seen = set()
    uniq = []
    for c in cidrs:
        if c not in seen:
            uniq.append(c)
            seen.add(c)
    return uniq


def _build_tag_node_lines(scan_node_id, tag_rows):
    """Builds DOT lines for tag nodes under a scan."""
    lines = []
    for r in tag_rows:
        tag_uuid = r.get("tag_value_uuid")
        tag_value = r.get("value") or tag_uuid
        subnets = _filters_to_subnet_hints(r.get("filters"))

        lines_lbl = [html.escape(str(tag_value))]
        if subnets:
            preview = ", ".join(subnets[:4]) + ("…" if len(subnets) > 4 else "")
            lines_lbl.append(html.escape(f"Subnets: {preview}"))
        tag_label = "\\n".join(lines_lbl)

        tag_node_id = _sanitize_id(f"tag::{tag_uuid}::{tag_value}")
        tooltip = html.escape(f"Tag UUID: {tag_uuid}")
        lines.append(
            f'    "{tag_node_id}" [label="{tag_label}", shape=note, '
            f'fillcolor="#FFF7E6", tooltip="{tooltip}"];'
        )
        lines.append(f'    "{scan_node_id}" -> "{tag_node_id}";')
    return lines


def _build_cluster_dot(scanner_name, scans_map):
    """Builds DOT syntax lines for a single scanner cluster."""
    lines = []
    cluster_id = _sanitize_id(f"cluster_{scanner_name}")
    scanner_lbl = html.escape(scanner_name)
    lines.append(f'  subgraph cluster_{cluster_id} {{')
    lines.append('    style="rounded"; color="#C7D3E3";')
    lines.append(f'    label=<<b>Scanner/Group:</b> {scanner_lbl}>;')

    for scan_name, tag_rows in sorted(scans_map.items(), key=lambda kv: kv[0].lower()):
        scan_node_id = _sanitize_id(f"scan::{scanner_name}::{scan_name}")
        scan_lbl = html.escape(scan_name)
        lines.append(f'    "{scan_node_id}" [label="{scan_lbl}", fillcolor="#E8F0FE"];')
        lines.extend(_build_tag_node_lines(scan_node_id, tag_rows))

    lines.append('  }')
    return lines


def write_graphviz_dot(rows, dot_path="tenable_io_architecture.dot"):
    """
    rows: list of dicts from tag_filters_and_values
    Writes a DOT file with clusters per scanner_name.
    """
    by_scanner = {}
    for r in rows:
        scanner = r.get("scanner_name") or "Unknown Scanner/Group"
        scan = r.get("scan_name") or f"Scan {r.get('scan_id')}"
        by_scanner.setdefault(scanner, {}).setdefault(scan, []).append(r)

    lines = [
        'digraph TenableScannerArchitecture {',
        '  rankdir=LR;',
        '  graph [fontname="Segoe UI", fontsize=10, labelloc=top];',
        '  node  [fontname="Segoe UI", fontsize=9, shape=box, '
        'style="rounded,filled", fillcolor="#F3F6FB"];',
        '  edge  [fontname="Segoe UI", fontsize=8, color="#6A7D9B"];'
    ]

    for scanner_name, scans_map in sorted(by_scanner.items(), key=lambda kv: kv[0].lower()):
        cluster_lines = _build_cluster_dot(scanner_name, scans_map)
        lines.extend(cluster_lines)

    lines.append('}')

    with open(dot_path, 'w', encoding='utf-8') as out_f:
        out_f.write("\n".join(lines))

    print(f"Graphviz DOT written to {dot_path}")


if __name__ == '__main__':
    io_client = TenableIO()
    resolved_tag_targets = get_tag_targets(tio_client=io_client)
    tag_filters_and_values = collect_tag_filters_and_value(
        io_client, resolved_tag_targets
    )

    # Output (JSON + DOT)
    OUTPUT_FILE = "tenable_io_tag_filters_and_values.json"
    with open(OUTPUT_FILE, "w", encoding="utf-8") as json_out:
        json.dump(tag_filters_and_values, json_out, indent=4)

    print(f"Tag filters and values written to {OUTPUT_FILE}")

    # Emit Graphviz DOT
    write_graphviz_dot(tag_filters_and_values, dot_path="tenable_io_architecture.dot")
