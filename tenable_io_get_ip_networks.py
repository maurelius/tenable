#!/usr/bin/env python3
'''
Tenable.io - Get IP Networks from Scan Tags

Description:
  This script retrieves all scans from Tenable.io and extracts the IP networks
  associated with each scan through their tag targets.
  It processes the tag filters to identify asset-related tags and extracts
  the relevant IP subnet information.
  The collected data is compiled into a pandas DataFrame and saved as a
  Markdown file for reporting purposes, including summary statistics for each field.

Auth/Secrets:
  - Use TIO_ACCESS_KEY / TIO_SECRET_KEY env vars.

Requires:
  pip install pytenable pandas

Outputs:
  - Markdown file with details of scan target networks, including scan ID, scan name,
    tag ID, property, and value (e.g., IP subnets or UUIDs), along with summary statistics.
'''
import json
import logging
import pandas as pd
from tenable.io import TenableIO
from tenable_config import get_tenable_io_client


def _init_client():
    """Initialize Tenable.io client using tenable_config or direct TenableIO fallback."""
    try:
        return get_tenable_io_client()
    except (ValueError, KeyError, AttributeError):
        return TenableIO()


def _get_tag_filters(io_client, tag_id, tag_cache, cache_stats):
    """
    Retrieves and parses asset filter list for a tag with dictionary caching.

    Args:
        io_client: TenableIO client instance.
        tag_id: UUID string of the tag.
        tag_cache: Dictionary cache mapping tag_id to filter list.
        cache_stats: Dictionary tracking hits and misses.

    Returns:
        list: Filter list from asset tag data, or None if not found/invalid.
    """
    if tag_id in tag_cache:
        cache_stats['hits'] += 1
        return tag_cache[tag_id]

    cache_stats['misses'] += 1
    try:
        tags = io_client.tags.details(tag_id)
        filter_dict = tags.get("filters") if isinstance(tags, dict) else None

        if not filter_dict or 'asset' not in filter_dict:
            logging.info("No asset filters found for tag %s. Skipping.", tag_id)
            tag_cache[tag_id] = None
            return None

        asset_json_string = filter_dict['asset']
        asset_data = json.loads(asset_json_string)
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


def _extract_item_value(item):
    """Safely flattens and extracts property value from a filter item dictionary."""
    value = item.get('value')
    if isinstance(value, list) and value:
        try:
            return value[0][0] if isinstance(value[0], list) else value[0]
        except (IndexError, TypeError):
            return None
    return value


def _process_scan_tag(io_client, scan_info, tag_id, tag_cache, cache_stats):
    """Processes tag filters for a given scan and tag ID, returning list of extracted items."""
    filter_list = _get_tag_filters(io_client, tag_id, tag_cache, cache_stats)
    if not filter_list:
        return []

    scan_id, scan_name = scan_info
    items = []
    for item in filter_list:
        items.append({
            'scan_id': scan_id,
            'scan_name': scan_name,
            'tag_id': tag_id,
            'property': item.get('property'),
            'value': _extract_item_value(item)
        })
    return items


def extract_scan_ip_networks(io_client=None):
    """
    Extracts IP network information from all scans via their tag targets.

    Args:
        io_client: Optional TenableIO client instance.

    Returns:
        tuple: (pandas DataFrame, cache stats dictionary)
    """
    if io_client is None:
        io_client = _init_client()

    scans = io_client.scans.list()
    all_extracted_data = []
    tag_cache = {}
    cache_stats = {'hits': 0, 'misses': 0}

    for scan in scans:
        scan_id = scan.get('id')
        scan_name = scan.get('name')

        try:
            scan_details = io_client.scans.details(scan_id)
            settings = scan_details.get('settings') if isinstance(scan_details, dict) else None
            tag_targets = settings.get('tag_targets') if settings else None

            if not tag_targets:
                logging.info("No tag_targets found for scan id %s. Skipping.", scan_id)
                continue

            for t in tag_targets:
                items = _process_scan_tag(
                    io_client, (scan_id, scan_name), t, tag_cache, cache_stats
                )
                all_extracted_data.extend(items)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logging.error("Error processing scan %s: %s", scan_id, e)
            continue

    logging.info(
        "Tag cache stats - Hits: %d, Misses: %d", cache_stats['hits'], cache_stats['misses']
    )
    df = pd.DataFrame(all_extracted_data)
    return df, cache_stats


def generate_report(df, output_filepath='TENABLE-SCAN-TARGETS.md'):
    """Generates a markdown report from the scan targets DataFrame."""
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write('# Tenable Scans & Their Subnets\n\n')
        f.write('## Scan Target Networks\n\n')
        f.write(df.to_markdown(tablefmt='github'))
        f.write('\n\n')
        f.write('## Summary Statistics\n\n')
        f.write('### Scan ID Summary\n\n')
        if 'scan_id' in df.columns and not df.empty:
            f.write(df['scan_id'].astype(str).describe().to_markdown(tablefmt='github'))
        f.write('\n\n')
        f.write('### Scan Name Summary\n\n')
        if 'scan_name' in df.columns and not df.empty:
            f.write(df['scan_name'].describe().to_markdown(tablefmt='github'))
        f.write('\n\n')
        f.write('### IP Subnets Summary\n\n')
        if 'value' in df.columns and not df.empty:
            f.write(df['value'].describe().to_markdown(tablefmt='github'))
        f.write('\n\n')


def main():
    """Main execution entry point."""
    df, _ = extract_scan_ip_networks()
    generate_report(df)


if __name__ == '__main__':
    main()
