#!/usr/bin/env python3
"""
Tenable.io - Get IP Networks from Scan Tags

Description:
  This script retrieves all scans from Tenable.io and extracts the IP
  networks associated with each scan through their tag targets.
  It processes tag filters to identify asset-related tags and extracts
  the relevant IP subnet/UUID information.

Auth/Secrets:
  - Uses TENABLE_ACCESS_KEY / TENABLE_SECRET_KEY env vars via tenable_config.

Requires:
  pip install pytenable pandas

Outputs:
  - TENABLE-SCAN-TARGETS.md with scan target network details and summary stats.
"""

import json
import logging
import pandas as pd
from tenable_config import get_tenable_io_client


def _get_tag_filters(io_client, tag_id, tag_cache, stats):
    """
    Retrieve tag filters with dictionary caching to prevent redundant API calls.

    ⚡ BOLT Optimization: Scans frequently share identical tag targets.
    Caching tag details reduces API requests from O(Total Tag References)
    to O(Unique Tags).
    """
    if tag_id in tag_cache:
        stats['hits'] += 1
        return tag_cache[tag_id]

    stats['misses'] += 1
    try:
        tags = io_client.tags.details(tag_id)
        filter_dict = tags.get("filters")
        tag_cache[tag_id] = filter_dict
        return filter_dict
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("Error fetching tag details for %s: %s", tag_id, e)
        return None


def _extract_item_value(item):
    """Safely extract a flat filter value from an item dictionary."""
    value = item.get('value')
    if isinstance(value, list) and value:
        try:
            if isinstance(value[0], list):
                return value[0][0]
            return value[0]
        except (IndexError, TypeError):
            return None
    return value


def _parse_tag_asset_items(scan_meta, tag_id, filter_dict):
    """Parse asset filter items from a tag filter dictionary."""
    if not filter_dict or 'asset' not in filter_dict:
        logging.info("No asset filters found for tag %s. Skipping.", tag_id)
        return []

    asset_json_string = filter_dict['asset']
    if not asset_json_string:
        return []

    asset_data = json.loads(asset_json_string)
    filter_list = asset_data.get('and', [])

    if not filter_list:
        logging.info("No 'and' filters found for tag %s. Skipping.", tag_id)
        return []

    scan_id, scan_name = scan_meta
    extracted_items = []
    for item in filter_list:
        extracted_items.append({
            'scan_id': scan_id,
            'scan_name': scan_name,
            'tag_id': tag_id,
            'property': item.get('property'),
            'value': _extract_item_value(item)
        })
    return extracted_items


def _process_single_scan(io_client, scan, tag_cache, cache_stats):
    """Process a single scan and return its extracted tag network items."""
    scan_id = scan.get('id')
    scan_name = scan.get('name')
    extracted = []

    try:
        scan_details = io_client.scans.details(scan_id)
        settings = scan_details.get('settings') if scan_details else None
        tag_targets = settings.get('tag_targets') if settings else None

        if not tag_targets:
            logging.info("No tag_targets found for scan id %s. Skipping.", scan_id)
            return extracted

        scan_meta = (scan_id, scan_name)
        for t in tag_targets:
            filter_dict = _get_tag_filters(io_client, t, tag_cache, cache_stats)
            extracted.extend(_parse_tag_asset_items(scan_meta, t, filter_dict))

    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("Error processing scan %s: %s", scan_id, e)

    return extracted


def fetch_scan_ip_networks(io_client):
    """
    Retrieves all scans and extracts target IP network items from tag targets.
    """
    all_extracted_data = []
    tag_cache = {}
    cache_stats = {'hits': 0, 'misses': 0}

    scans = io_client.scans.list()

    for scan in scans:
        all_extracted_data.extend(
            _process_single_scan(io_client, scan, tag_cache, cache_stats)
        )

    logging.info(
        "Tag details lookup complete. Cache Hits: %d, Cache Misses: %d",
        cache_stats['hits'],
        cache_stats['misses']
    )
    return all_extracted_data


def generate_report(data, output_file='TENABLE-SCAN-TARGETS.md'):
    """Generate Markdown report and summary statistics from extracted data."""
    df = pd.DataFrame(data)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('# Tenable Scans & Their Subnets\n\n')
        f.write('## Scan Target Networks\n\n')
        f.write(df.to_markdown(tablefmt='github'))
        f.write('\n\n')
        f.write('## Summary Statistics\n\n')
        f.write('### Scan ID Summary\n\n')
        f.write(df['scan_id'].astype(str).describe().to_markdown(tablefmt='github'))
        f.write('\n\n')
        f.write('### Scan Name Summary\n\n')
        f.write(df['scan_name'].describe().to_markdown(tablefmt='github'))
        f.write('\n\n')
        f.write('### IP Subnets Summary\n\n')
        f.write(df['value'].describe().to_markdown(tablefmt='github'))
        f.write('\n\n')


def main():
    """Main execution function."""
    logging.basicConfig(level=logging.INFO)
    io_client = get_tenable_io_client()
    data = fetch_scan_ip_networks(io_client)
    generate_report(data)


if __name__ == '__main__':
    main()
