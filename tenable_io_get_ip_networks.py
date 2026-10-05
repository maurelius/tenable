#!/usr/bin/env python3
'''
Tenable.io - Get IP Networks from Scan Tags

Description:
  This script retrieves all scans from Tenable.io and extracts the IP networks
  associated with each scan through their tag targets.
  It processes the tag filters to identify asset-related tags and extracts the
  relevant IP subnet information.
  The collected data is compiled into a pandas DataFrame and saved as a Markdown file
  for reporting purposes, including summary statistics for each field.

Auth/Secrets:
  - Use TIO_ACCESS_KEY / TIO_SECRET_KEY env vars.

Requires:
  pip install pytenable pandas

Outputs:
  - Markdown file with details of scan target networks, including scan ID, scan name,
    tag ID, property, and value (e.g., IP subnets or UUIDs), along with summary
    statistics for each field.
'''
import json
import logging
import pandas as pd
from tenable.io import TenableIO


def _get_tag_filters(io_client, tag_id, tag_cache, stats):
    """
    Retrieves and caches parsed asset filter dictionaries for a given tag ID.
    ⚡ BOLT Optimization: Caches tag details lookups to prevent redundant network requests.
    """
    if tag_id in tag_cache:
        stats['hits'] += 1
        return tag_cache[tag_id]

    stats['misses'] += 1
    tags = io_client.tags.details(tag_id)
    filter_dict = tags.get("filters") if tags else None

    if not filter_dict or 'asset' not in filter_dict:
        tag_cache[tag_id] = None
        return None

    asset_json_string = filter_dict['asset']
    try:
        asset_data = json.loads(asset_json_string)
        filter_list = asset_data.get('and', [])
    except (json.JSONDecodeError, TypeError):
        filter_list = []

    tag_cache[tag_id] = filter_list
    return filter_list


def _extract_item_value(value, tag_id):
    """Safely extracts flat value from potential nested list structure."""
    if isinstance(value, list) and value:
        try:
            return value[0][0] if isinstance(value[0], list) else value[0]
        except (IndexError, TypeError):
            logging.warning("Could not extract value from nested list for tag %s.", tag_id)
            return None
    return value


def _process_single_tag(t, io_client, tag_cache, stats, scan_info):
    """Processes a single tag target and returns extracted items."""
    scan_id, scan_name = scan_info
    extracted = []
    filter_list = _get_tag_filters(io_client, t, tag_cache, stats)

    if not filter_list:
        logging.info("No asset filters found for tag %s. Skipping.", t)
        return extracted

    for item in filter_list:
        val = _extract_item_value(item.get('value'), t)
        extracted.append({
            'scan_id': scan_id,
            'scan_name': scan_name,
            'tag_id': t,
            'property': item.get('property'),
            'value': val
        })
    return extracted


def process_scan_tag_networks(io_client):
    """
    Main processing function to extract IP networks from scan tag targets.
    Returns extracted data list and cache resolution stats.
    """
    scans = io_client.scans.list()
    all_extracted_data = []

    tag_cache = {}
    stats = {'hits': 0, 'misses': 0}

    for scan in scans:
        scan_id = scan['id']
        scan_name = scan['name']

        try:
            scan_details = io_client.scans.details(scan_id)
            settings = scan_details.get('settings') if scan_details else None
            tag_targets = settings.get('tag_targets') if settings else None

            if not tag_targets:
                logging.info("No tag_targets found for scan id %s. Skipping.", scan_id)
                continue

            for t in tag_targets:
                try:
                    items = _process_single_tag(
                        t, io_client, tag_cache, stats, (scan_id, scan_name)
                    )
                    all_extracted_data.extend(items)
                except Exception as e:  # pylint: disable=broad-except
                    logging.error("Error processing tag %s for scan %s: %s", t, scan_id, e)

        except Exception as e:  # pylint: disable=broad-except
            logging.error("Error processing scan %s: %s", scan_id, e)

    return all_extracted_data, stats


def main():
    """Main entry point for script execution."""
    io_client = TenableIO()
    all_extracted_data, stats = process_scan_tag_networks(io_client)

    logging.info(
        "Tag resolution stats: Cache Hits: %s, Cache Misses: %s",
        stats['hits'],
        stats['misses']
    )
    print(f"\nTag resolution stats: Cache Hits: {stats['hits']}, Cache Misses: {stats['misses']}")

    df = pd.DataFrame(all_extracted_data)

    with open('TENABLE-SCAN-TARGETS.md', 'w', encoding='utf-8') as f:
        f.write('# Tenable Scans & Their Subnets\n\n')
        f.write('## Scan Target Networks\n\n')
        f.write(df.to_markdown(tablefmt='github'))
        f.write('\n\n')
        f.write('## Summary Statistics\n\n')
        f.write('### Scan ID Summary\n\n')
        if not df.empty and 'scan_id' in df:
            f.write(df['scan_id'].astype(str).describe().to_markdown(tablefmt='github'))
        f.write('\n\n')
        f.write('### Scan Name Summary\n\n')
        if not df.empty and 'scan_name' in df:
            f.write(df['scan_name'].describe().to_markdown(tablefmt='github'))
        f.write('\n\n')
        f.write('### IP Subnets Summary\n\n')
        if not df.empty and 'value' in df:
            f.write(df['value'].describe().to_markdown(tablefmt='github'))
        f.write('\n\n')


if __name__ == '__main__':
    main()
