#!/usr/bin/env python3
'''
Tenable.io - Get Scans from Tag Targets

Description:
    This script retrieves all scans from Tenable.io and extracts tag target information
    from the `tag_targets` field in scan settings. It normalizes and validates tag value
    UUIDs, fetches detailed tag information including filters, and resolves asset filter
    data to identify which assets are targeted by each scan's tags.
    
    The script handles edge cases including missing/empty tag_targets, malformed UUIDs,
    nested list/dict structures, and API call failures with retries. It collects metadata
    for each tag including scan details, tag values, and parsed asset filter constraints,
    outputting results as JSON for further analysis or integration.

Auth/Secrets:
    - Use TIO_ACCESS_KEY / TIO_SECRET_KEY env vars.

Requires:
    pip install pytenable tqdm 
    
Outputs:
    - JSON file with details of scan tag targets, including scan ID, scan name, scanner name, tag value UUID, display value, and parsed asset filters.
'''
from tenable.io import TenableIO
import json
import os
import logging
import re
from restfly.errors import NotFoundError
from tqdm import tqdm
import time

# Note: The above imports assume you have pytenable installed and properly configured with your Tenable.io credentials.

# Bootstrap Tenable.io client
io = TenableIO()
scans = io.scans.list()

# Helpers / Utilities
def get_scan_details(scan_id):
    """Wrapper to get scan details with retry on 404 errors."""
    max_retries = 3
    delay_seconds = 2
    for attempt in range(max_retries):
        try:
            return io.scans.details(scan_id=scan_id)
        except NotFoundError:
            if attempt < max_retries - 1:
                logging.warning(f"Scan ID {scan_id} not found. Retrying in {delay_seconds} seconds...")
                time.sleep(delay_seconds)
            else:
                logging.error(f"Scan ID {scan_id} not found after {max_retries} attempts.")
                raise

# Correct UUID pattern (Tenable returns lowercase hex by default)
UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')

def _normalize_uuid_like(x):
    """
    Accept uuid-like things:
      - 'uuid' (str)
      - ['uuid'] or [['uuid']] -> unwrap first element repeatedly
      - dicts like {'uuid': ...}, {'tag_value_uuid': ...}, {'id': ...}, {'value_uuid': ...}
    Returns a uuid string or None if it cannot be normalized/validated.
    """
    v = x
    # unwrap nested lists/tuples like [["uuid"]] -> "uuid"
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
    Accepts a UUID string, a list/tuple possibly nested (e.g., [['uuid']]),
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
        raise ValueError(f"Unrecognized tag identifier shape: {type(v).__name__}")
    v = v.strip()
    if not UUID_RE.match(v):
        raise ValueError(f"tag_value_uuid has value of {raw!r}. Does not match UUID pattern")
    return v

def parse_asset_filters(filters, tag_id):
    """Return a list of AND filters from filters['asset'], handling JSON string or dict."""
    if not filters or 'asset' not in filters:
        logging.info(f"No asset filters found for tag {tag_id}. Skipping.")
        return None
    asset = filters['asset']
    if isinstance(asset, str):
        try:
            asset_data = json.loads(asset)
        except json.JSONDecodeError as e:
            logging.warning(f"Invalid JSON in filters['asset'] for tag {tag_id}: {e}")
            return None
    elif isinstance(asset, dict):
        asset_data = asset
    else:
        logging.warning(f"Unexpected type for filters['asset'] in tag {tag_id}: {type(asset).__name__}")
        return None

    filter_list = asset_data.get('and', [])
    if not filter_list:
        logging.info(f"No 'and' filters found for tag {tag_id}. Skipping.")
        return None
    return filter_list


# Build tag-target map WITH scan metadata
def get_tag_targets():
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
    kept = {}
    dropped_empty = 0
    dropped_all_invalid = 0
    dropped_items_invalid = 0

    print("Getting tag UUIDs for scan count: ", len(scans), "\n")
    for scan in tqdm(
        scans,
        desc="Processing scans",
        bar_format="{l_bar}{bar} {n_fmt}/{total_fmt} [Elapsed: {elapsed} - Remaining: {remaining}, {rate_fmt}]",
        ncols=100
    ):
        scan_id = scan.get('id')

        # Fetch details with retry wrapper
        try:
            scan_details = get_scan_details(scan_id)
        except NotFoundError:
            # Already logged in wrapper; skip this scan
            continue

        # Guard against None or unexpected responses
        if not isinstance(scan_details, dict):
            logging.error(f"Scan {scan_id}: details payload is None or not a dict; skipping.")
            continue

        # SAFE accessors from here on
        scan_name = scan_details.get('name') or scan.get('name') or f"Scan {scan_id}"
        settings = scan_details.get('settings') or {}

        # Prefer friendly scanner name when present; fall back to ids/unknown
        scanner_name = (
            settings.get('scanner_name') or
            settings.get('scanner') or          # sometimes the name lives here
            settings.get('scanner_id') or       # numeric id
            scan_details.get('scanner_id') or   # legacy field (present in your file)
            "Unknown Scanner/Group"
        )

        raw_targets = settings.get('tag_targets', [])

        if not raw_targets:
            dropped_empty += 1
            continue

        normalized = []
        for x in raw_targets:
            u = _normalize_uuid_like(x)
            if u:
                normalized.append(u)
            else:
                dropped_items_invalid += 1
                logging.debug(f"Scan {scan_id}: dropping malformed tag target {x!r}")

        if not normalized:
            dropped_all_invalid += 1
            continue

        kept[scan_id] = {
            "uuids": normalized,
            "scan_name": str(scan_name),
            "scanner_name": str(scanner_name)
        }

    logging.info(
        "Tag targets summary — kept scans: %d | dropped(empty): %d | dropped(all invalid): %d | dropped(invalid items): %d",
        len(kept), dropped_empty, dropped_all_invalid, dropped_items_invalid
    )
    return kept

tag_targets = get_tag_targets()

# Resolve tag values & filters and emit rows carrying scan metadata
def collect_tag_filters_and_value(io, tag_targets):
    """
    Iterate tag_targets and collect parsed asset filters AND the tag 'value' (singular)
    for each tag value UUID.

    Returns a flat list of dicts, each row carrying scan metadata:
      [
        {
          "scan_id": "<id>",
          "scan_name": "<name>",
          "scanner_name": "<scanner or group>",
          "tag_value_uuid": "<uuid>",
          "value": "<Value>",     # Display value of the tag VALUE
          "filters": [ ... ]      # AND-list from /tags/values/<uuid> -> filters.asset.and
        },
        ...
      ]
    """
    results = []
    # Correct 2-value unpack from dict.items()
    for scan_id, meta in tag_targets.items():
        if not isinstance(meta, dict):
            logging.error(f"Scan {scan_id}: unexpected tag_targets meta type {type(meta).__name__}; skipping.")
            continue

        uuids = meta.get("uuids") or []
        scan_name = meta.get("scan_name") or f"Scan {scan_id}"
        scanner_name = meta.get("scanner_name") or "Unknown Scanner/Group"

        for raw_t in uuids:
            try:
                t = normalize_tag_value_uuid(raw_t)
                # Tenable.io API call: tag value details (contains 'value' and 'filters')
                tags = io.tags.details(t)
                tag_value = tags.get("value")
                if not tag_value:
                    logging.info(f"No 'value' found for tag value UUID {t}. Skipping.")
                    continue

                filters = tags.get("filters")
                filter_list = parse_asset_filters(filters, t)
                if not filter_list:
                    # parse_asset_filters already logged why
                    continue

                results.append({
                    "scan_id": scan_id,
                    "scan_name": scan_name,
                    "scanner_uuid": scanner_name,
                    "tag_value_uuid": t,
                    "value": tag_value,
                    "filters": filter_list
                })

            except ValueError as ve:
                # Covers nested list shapes and regex mismatches
                logging.error(f"Error processing tag {raw_t!r}: {ve}")
                continue
            except NotFoundError as nf:
                # Tag value UUID not found (deleted/permissions)
                logging.error(f"Error processing tag {raw_t}: {nf}")
                continue
            except Exception as e:
                logging.error(f"Unexpected error processing tag {raw_t!r}: {e}")
                continue
    return results

tag_filters_and_values = collect_tag_filters_and_value(io, tag_targets)

# Output
output_file = "tenable_io_tag_filters_and_values.json"
with open(output_file, "w") as f:
    json.dump(tag_filters_and_values, f, indent=4)

print(f"Tag filters and values written to {output_file}")