#!/usr/bin/env python3
'''
Tenable.io - Get IP Networks from Scan Tags

Description:
  This script retrieves all scans from Tenable.io and extracts the IP networks associated with
  each scan through their tag targets. It processes the tag filters to identify asset-related
  tags and extracts the relevant IP subnet information.
  The collected data is compiled into a pandas DataFrame and saved as a Markdown file for
  reporting purposes, including summary statistics for each field.

Auth/Secrets:
  - Use TIO_ACCESS_KEY / TIO_SECRET_KEY env vars.

Requires:
  pip install pytenable pandas

Outputs:
  - Markdown file with details of scan target networks, including scan ID, scan name, tag ID,
    property, and value (e.g., IP subnets or UUIDs), along with summary statistics for each field.
'''
import json
import logging
import pandas as pd
from tenable.io import TenableIO

# Note: The above imports assume you have pytenable installed and properly configured.

# ⚡ BOLT: Cache tag details and track performance
TAG_CACHE = {}
CACHE_HITS = 0
CACHE_MISSES = 0

def _get_tag_filters(tio_client, tag_id):
    """
    Retrieve and parse asset filters for a given tag ID with caching.
    """
    global CACHE_HITS, CACHE_MISSES  # pylint: disable=global-statement
    if tag_id in TAG_CACHE:
        CACHE_HITS += 1
        return TAG_CACHE[tag_id]

    CACHE_MISSES += 1
    try:
        tags = tio_client.tags.details(tag_id)
        filter_dict = tags.get("filters")
        if not filter_dict or 'asset' not in filter_dict:
            logging.info("No asset filters found for tag %s. Skipping.", tag_id)
            TAG_CACHE[tag_id] = None
            return None

        asset_json_string = filter_dict['asset']
        asset_data = json.loads(asset_json_string)
        filters = asset_data.get('and', [])
        TAG_CACHE[tag_id] = filters
        return filters
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("Error processing tag %s: %s", tag_id, e)
        TAG_CACHE[tag_id] = None
        return None

def _extract_item_value(value, tag_id):
    """Safely extracts value from potentially nested list or raw value."""
    if isinstance(value, list) and value:
        try:
            if isinstance(value[0], list):
                return value[0][0]
            return value[0]
        except (IndexError, TypeError):
            logging.warning(
                "Could not extract value from nested list for tag %s.", tag_id
            )
            return None
    return value

def _process_scan_tags(tio_client, scan, all_extracted_data):
    """Processes tags for a single scan and appends to all_extracted_data."""
    scan_id = scan['id']
    scan_name = scan['name']
    try:
        scan_details = tio_client.scans.details(scan_id)
        settings = scan_details.get('settings', {})
        tag_targets = settings.get('tag_targets', [])

        if not tag_targets:
            logging.info("No tag_targets found for scan id %s. Skipping.", scan_id)
            return

        for tag_id in tag_targets:
            _process_tag_item(tio_client, scan_id, scan_name, tag_id, all_extracted_data)

    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("Error processing scan %s: %s", scan_id, e)

def _process_tag_item(tio_client, scan_id, scan_name, tag_id, all_extracted_data):
    """Processes a single tag and its items."""
    try:
        # ⚡ BOLT: Use the cached helper function to reduce API calls
        filter_list = _get_tag_filters(tio_client, tag_id)
        if not filter_list:
            return

        for item in filter_list:
            extracted_item = {
                'scan_id': scan_id,
                'scan_name': scan_name,
                'tag_id': tag_id,
                'property': item.get('property'),
                'value': _extract_item_value(item.get('value'), tag_id)
            }
            all_extracted_data.append(extracted_item)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("Error processing tag %s for scan %s: %s", tag_id, scan_id, e)

def main():
    """Main execution logic."""
    # Use standard TenableIO() to maintain compatibility with TIO_ACCESS_KEY/TIO_SECRET_KEY
    io = TenableIO()
    scans = io.scans.list()

    all_extracted_data = []
    for scan in scans:
        _process_scan_tags(io, scan, all_extracted_data)

    logging.info("Tag resolution stats - Hits: %s, Misses: %s", CACHE_HITS, CACHE_MISSES)

    df = pd.DataFrame(all_extracted_data)
    if df.empty:
        logging.warning("No data extracted. Skipping file generation.")
        return

    with open('TENABLE-SCAN-TARGETS.md', 'w', encoding='utf-8') as f:
        f.write('# Tenable Scans & Their Subnets\n\n')
        f.write('## Scan Target Networks\n\n')
        f.write(df.to_markdown(tablefmt='github'))
        f.write('\n\n## Summary Statistics\n\n')
        f.write('### Scan ID Summary\n\n')
        f.write(df['scan_id'].astype(str).describe().to_markdown(tablefmt='github'))
        f.write('\n\n### Scan Name Summary\n\n')
        f.write(df['scan_name'].describe().to_markdown(tablefmt='github'))
        f.write('\n\n### IP Subnets Summary\n\n')
        f.write(df['value'].describe().to_markdown(tablefmt='github'))
        f.write('\n')

if __name__ == '__main__':
    main()
