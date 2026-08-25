#!/usr/bin/env python3
'''
Tenable.io - Get IP Networks from Scan Tags

Description:
  This script retrieves all scans from Tenable.io and extracts the IP networks
  associated with each scan through their tag targets.
  It processes tag filters to identify asset-related tags and extracts IP subnet
  information. The collected data is compiled into a pandas DataFrame and saved
  as a Markdown file for reporting purposes.

Auth/Secrets:
  - Use TIO_ACCESS_KEY / TIO_SECRET_KEY env vars.

Requires:
  pip install pytenable pandas

Outputs:
  - Markdown file with details of scan target networks, including scan ID, scan
    name, tag ID, property, and value (e.g., IP subnets or UUIDs), along with
    summary statistics for each field.
'''
import json
import logging
import pandas as pd
from tenable.io import TenableIO


def _get_tag_filters(io_client, tag_id, tag_cache, stats):
    """
    Retrieves and caches tag filter details to avoid redundant API calls.

    ⚡ BOLT Optimization: Caches tag details per tag_id. Across multiple scans
    sharing identical target tags, this reduces API calls from O(N * M) to
    O(Unique Tags).
    """
    if tag_id in tag_cache:
        stats['hits'] += 1
        return tag_cache[tag_id]

    stats['misses'] += 1
    try:
        tags = io_client.tags.details(tag_id)
        filter_dict = tags.get("filters")

        if not filter_dict or 'asset' not in filter_dict:
            logging.info("No asset filters found for tag %s. Skipping.", tag_id)
            tag_cache[tag_id] = None
            return None

        asset_data = json.loads(filter_dict['asset'])
        filter_list = asset_data.get('and', [])

        if not filter_list:
            logging.info("No 'and' filters found for tag %s. Skipping.", tag_id)
            tag_cache[tag_id] = None
            return None

        tag_cache[tag_id] = filter_list
        return filter_list
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("Error processing tag %s: %s", tag_id, e)
        tag_cache[tag_id] = None
        return None


def _extract_item_value(value, tag_id):
    """Safely flattens nested list structures to extract the tag value."""
    if isinstance(value, list) and value:
        try:
            if isinstance(value[0], list):
                return value[0][0]
            return value[0]
        except (IndexError, TypeError):
            logging.warning("Could not extract value from nested list for tag %s.", tag_id)
            return None
    return value


def _process_single_scan(io_client, scan, tag_cache, stats):
    """Processes target tags for a single scan and returns extracted items."""
    scan_id = scan['id']
    scan_name = scan['name']
    items = []

    try:
        scan_details = io_client.scans.details(scan_id)
        settings = scan_details.get('settings') or {}
        tag_targets = settings.get('tag_targets')

        if not tag_targets:
            logging.info("No tag_targets found for scan id %s. Skipping.", scan_id)
            return items

        for t in tag_targets:
            filter_list = _get_tag_filters(io_client, t, tag_cache, stats)
            if not filter_list:
                continue

            for item in filter_list:
                items.append({
                    'scan_id': scan_id,
                    'scan_name': scan_name,
                    'tag_id': t,
                    'property': item.get('property'),
                    'value': _extract_item_value(item.get('value'), t)
                })

    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("Error processing scan %s: %s", scan_id, e)

    return items


def process_scan_ip_networks(io_client):
    """
    Retrieves all scans and processes their target tags to extract IP networks.
    """
    scans = io_client.scans.list()
    all_extracted_data = []

    tag_cache = {}
    stats = {'hits': 0, 'misses': 0}

    for scan in scans:
        extracted = _process_single_scan(io_client, scan, tag_cache, stats)
        all_extracted_data.extend(extracted)

    logging.info("Tag Lookup Cache Stats - Hits: %d, Misses: %d", stats['hits'], stats['misses'])
    return pd.DataFrame(all_extracted_data)


def save_markdown_report(df, filename='TENABLE-SCAN-TARGETS.md'):
    """Saves extracted scan target network data to a markdown report file."""
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
    io = TenableIO()
    df_results = process_scan_ip_networks(io)
    if not df_results.empty:
        save_markdown_report(df_results)
