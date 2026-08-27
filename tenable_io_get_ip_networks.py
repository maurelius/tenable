#!/usr/bin/env python3
'''
Tenable.io - Get IP Networks from Scan Tags

Description:
  This script retrieves all scans from Tenable.io and extracts the IP networks associated
  with each scan through their tag targets. It processes the tag filters to identify asset-related
  tags and extracts the relevant IP subnet information.
  The collected data is compiled into a pandas DataFrame and saved as a Markdown file for reporting
  purposes, including summary statistics for each field.

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

def _get_tag_filters(tio_client, tag_id, tag_cache, cache_stats):
    """
    Retrieves and parses asset filter items for a given tag ID using cache.

    ⚡ BOLT Optimization: Caching tag details lookup reduces network overhead
    from O(N * M) to O(Unique Tags) across all scans sharing tag targets.
    """
    if tag_id in tag_cache:
        cache_stats['hits'] += 1
        return tag_cache[tag_id]

    cache_stats['misses'] += 1
    try:
        tags = tio_client.tags.details(tag_id)
        filter_dict = tags.get("filters") if tags else None
        if not filter_dict or 'asset' not in filter_dict:
            logging.info("No asset filters found for tag %s. Skipping.", tag_id)
            tag_cache[tag_id] = []
            return []

        asset_json_string = filter_dict['asset']
        asset_data = json.loads(asset_json_string)
        filter_list = asset_data.get('and', [])

        if not filter_list:
            logging.info("No 'and' filters found for tag %s. Skipping.", tag_id)
            tag_cache[tag_id] = []
            return []

        tag_cache[tag_id] = filter_list
        return filter_list
    except (TypeError, ValueError, KeyError, AttributeError, json.JSONDecodeError) as e:
        logging.error("Error fetching tag details for tag %s: %s", tag_id, e)
        tag_cache[tag_id] = []
        return []

def _parse_extracted_value(item, tag_id):
    """Safely flattens nested list values for tag items."""
    value = item.get('value')
    if isinstance(value, list) and value:
        try:
            if isinstance(value[0], list):
                return value[0][0]
            return value[0]
        except (IndexError, TypeError):
            logging.warning("Could not extract value from nested list for tag %s.", tag_id)
            return None
    return value

def _process_single_scan(tio_client, scan, tag_cache, cache_stats):
    """Processes a single scan to extract tag target filter items."""
    scan_id = scan['id']
    scan_name = scan['name']
    extracted_items = []

    try:
        scan_details = tio_client.scans.details(scan_id)
        settings = scan_details.get('settings') if scan_details else None
        tag_targets = settings.get('tag_targets') if settings else None

        if not tag_targets:
            logging.info("No tag_targets found for scan id %s. Skipping.", scan_id)
            return extracted_items

        for t in tag_targets:
            filter_list = _get_tag_filters(tio_client, t, tag_cache, cache_stats)
            for item in filter_list:
                extracted_items.append({
                    'scan_id': scan_id,
                    'scan_name': scan_name,
                    'tag_id': t,
                    'property': item.get('property'),
                    'value': _parse_extracted_value(item, t)
                })
    except (TypeError, ValueError, KeyError, AttributeError) as e:
        logging.error("Error processing scan %s: %s", scan_id, e)

    return extracted_items

def extract_ip_networks_from_scans(tio_client):
    """Extracts target IP network details across scans with caching enabled."""
    scans = tio_client.scans.list()
    all_extracted_data = []

    tag_cache = {}
    cache_stats = {'hits': 0, 'misses': 0}

    for scan in scans:
        scan_items = _process_single_scan(tio_client, scan, tag_cache, cache_stats)
        all_extracted_data.extend(scan_items)

    logging.info(
        "Tag details lookup complete. Cache Hits: %d, Cache Misses: %d",
        cache_stats['hits'],
        cache_stats['misses']
    )
    return pd.DataFrame(all_extracted_data)

def generate_report(df, filename='TENABLE-SCAN-TARGETS.md'):
    """Generates a markdown summary report from the extracted scan networks DataFrame."""
    with open(filename, 'w', encoding='utf-8') as f:
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

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    io_client = TenableIO()
    extracted_df = extract_ip_networks_from_scans(io_client)
    if not extracted_df.empty:
        generate_report(extracted_df)
