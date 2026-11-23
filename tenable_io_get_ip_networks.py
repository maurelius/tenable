#!/usr/bin/env python3
"""
Tenable.io - Get IP Networks from Scan Tags

Description:
  This script retrieves all scans from Tenable.io and extracts the IP networks associated with
  each scan through their tag targets. It processes tag filters to identify asset-related tags
  and extracts relevant IP subnet/UUID details using an in-memory cache for tag lookups to eliminate
  redundant network requests.
"""
import json
import logging
import pandas as pd
from tenable_config import get_tenable_io_client


def _get_tag_filters(tio_client, tag_uuid, tag_cache, stats):
    """
    Retrieves and parses asset filter items for a tag UUID, utilizing a dictionary cache.
    Tracks hits and misses in the provided stats dictionary.
    """
    if tag_uuid in tag_cache:
        stats["hits"] += 1
        return tag_cache[tag_uuid]

    stats["misses"] += 1
    try:
        tag_details = tio_client.tags.details(tag_uuid)
        filter_dict = tag_details.get("filters") if tag_details else None

        if not filter_dict or "asset" not in filter_dict:
            logging.info("No asset filters found for tag %s. Skipping.", tag_uuid)
            tag_cache[tag_uuid] = []
            return []

        asset_json_string = filter_dict["asset"]
        asset_data = json.loads(asset_json_string)
        filter_list = asset_data.get("and", [])

        if not filter_list:
            logging.info("No 'and' filters found for tag %s. Skipping.", tag_uuid)
            tag_cache[tag_uuid] = []
            return []

        tag_cache[tag_uuid] = filter_list
        return filter_list

    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("Error processing tag %s: %s", tag_uuid, e)
        tag_cache[tag_uuid] = []
        return []


def _extract_item_value(item_value, tag_uuid):
    """
    Safely extracts a flat scalar value from an item value, which may be a nested list or scalar.
    """
    if isinstance(item_value, list) and item_value:
        try:
            if isinstance(item_value[0], list):
                return item_value[0][0]
            return item_value[0]
        except (IndexError, TypeError):
            logging.warning("Could not extract value from nested list for tag %s.", tag_uuid)
            return None
    return item_value


def _process_single_scan(tio_client, scan, tag_cache, stats):
    """
    Processes a single scan record and returns a list of extracted network target dictionaries.
    """
    scan_id = scan["id"]
    scan_name = scan["name"]
    extracted = []

    try:
        scan_details = tio_client.scans.details(scan_id)
        settings = scan_details.get("settings") if scan_details else None
        tag_targets = settings.get("tag_targets") if settings else None

        if not tag_targets:
            logging.info("No tag_targets found for scan id %s. Skipping.", scan_id)
            return extracted

        for t_uuid in tag_targets:
            filter_list = _get_tag_filters(tio_client, t_uuid, tag_cache, stats)

            for item in filter_list:
                flat_val = _extract_item_value(item.get("value"), t_uuid)
                extracted.append({
                    "scan_id": scan_id,
                    "scan_name": scan_name,
                    "tag_id": t_uuid,
                    "property": item.get("property"),
                    "value": flat_val,
                })

    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("Error processing scan %s: %s", scan_id, e)

    return extracted


def collect_scan_target_networks(tio_client):
    """
    Iterates through all scans and extracts network target details from scan tag targets,
    leveraging _get_tag_filters with caching.
    """
    scans = tio_client.scans.list()
    all_extracted_data = []
    tag_cache = {}
    stats = {"hits": 0, "misses": 0}

    for scan in scans:
        extracted = _process_single_scan(tio_client, scan, tag_cache, stats)
        all_extracted_data.extend(extracted)

    logging.info("Tag cache stats - Hits: %d, Misses: %d", stats["hits"], stats["misses"])
    return all_extracted_data


def generate_markdown_report(data, filename="TENABLE-SCAN-TARGETS.md"):
    """
    Generates a GitHub-flavored Markdown report from collected scan target network data.
    """
    df = pd.DataFrame(data)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Tenable Scans & Their Subnets\n\n")
        f.write("## Scan Target Networks\n\n")
        f.write(df.to_markdown(tablefmt="github"))
        f.write("\n\n")
        f.write("## Summary Statistics\n\n")
        f.write("### Scan ID Summary\n\n")
        f.write(df["scan_id"].astype(str).describe().to_markdown(tablefmt="github"))
        f.write("\n\n")
        f.write("### Scan Name Summary\n\n")
        f.write(df["scan_name"].describe().to_markdown(tablefmt="github"))
        f.write("\n\n")
        f.write("### IP Subnets Summary\n\n")
        f.write(df["value"].describe().to_markdown(tablefmt="github"))
        f.write("\n\n")


def main():
    """
    Main entry point for retrieving scan targets and writing the report.
    """
    logging.basicConfig(level=logging.INFO)
    io = get_tenable_io_client()
    data = collect_scan_target_networks(io)
    generate_markdown_report(data)


if __name__ == "__main__":
    main()
