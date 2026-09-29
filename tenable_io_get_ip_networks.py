#!/usr/bin/env python3
"""
Tenable.io - Get IP Networks from Scan Tags

Description:
  This script retrieves all scans from Tenable.io and extracts the IP networks
  associated with each scan through their tag targets.
  It processes the tag filters to identify asset-related tags and extracts
  the relevant IP subnet information.
  The collected data is compiled into a pandas DataFrame and saved as a Markdown file.

Auth/Secrets:
  - Use TIO_ACCESS_KEY / TIO_SECRET_KEY env vars.

Requires:
  pip install pytenable pandas

Outputs:
  - Markdown file with details of scan target networks and summary statistics.
"""

import json
import logging
import pandas as pd
from tenable.io import TenableIO

# ⚡ BOLT Optimization: Added tag details caching to eliminate duplicate API requests


def _get_tag_filters(io, tag_id, cache, stats):
    """Retrieve and cache asset filter list for a given tag ID."""
    if tag_id in cache:
        stats['hits'] += 1
        return cache[tag_id]

    stats['misses'] += 1
    filter_list = []
    try:
        tags = io.tags.details(tag_id)
        filter_dict = tags.get("filters") if tags else None

        if not filter_dict or 'asset' not in filter_dict:
            logging.info("No asset filters found for tag %s. Skipping.", tag_id)
        else:
            asset_json_string = filter_dict['asset']
            asset_data = json.loads(asset_json_string)
            filter_list = asset_data.get('and', [])
            if not filter_list:
                logging.info("No 'and' filters found for tag %s. Skipping.", tag_id)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        logging.error("Error parsing tag %s: %s", tag_id, exc)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logging.error("Error fetching tag %s details: %s", tag_id, exc)

    cache[tag_id] = filter_list
    return filter_list


def _extract_filter_value(value):
    """Extract flat value from nested filter list structure."""
    if isinstance(value, list) and value:
        try:
            if isinstance(value[0], list):
                return value[0][0]
            return value[0]
        except (IndexError, TypeError):
            logging.warning("Could not extract value from nested list.")
            return None
    return value


def _process_scan_tag_targets(io, scan_info, cache, stats):
    """Process tag targets for a single scan and return extracted data records."""
    scan_id = scan_info['id']
    scan_name = scan_info['name']
    extracted_records = []

    try:
        scan_details = io.scans.details(scan_id)
        settings = scan_details.get('settings') if scan_details else None
        tag_targets = settings.get('tag_targets') if settings else None

        if not tag_targets:
            logging.info("No tag_targets found for scan id %s. Skipping.", scan_id)
            return extracted_records

        for tag_id in tag_targets:
            filter_list = _get_tag_filters(io, tag_id, cache, stats)
            for item in filter_list:
                val = _extract_filter_value(item.get('value'))
                extracted_records.append({
                    'scan_id': scan_id,
                    'scan_name': scan_name,
                    'tag_id': tag_id,
                    'property': item.get('property'),
                    'value': val
                })
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logging.error("Error processing scan %s: %s", scan_id, exc)

    return extracted_records


def extract_all_scan_networks(io):
    """Retrieve all scans and extract target network information using tag caching."""
    scans = io.scans.list()
    all_extracted_data = []
    tag_cache = {}
    cache_stats = {'hits': 0, 'misses': 0}

    for scan in scans:
        records = _process_scan_tag_targets(io, scan, tag_cache, cache_stats)
        all_extracted_data.extend(records)

    logging.info(
        "Tag detail lookups completed. Cache hits: %d, Cache misses: %d",
        cache_stats['hits'],
        cache_stats['misses']
    )
    return pd.DataFrame(all_extracted_data)


def write_markdown_report(df, filename='TENABLE-SCAN-TARGETS.md'):
    """Write scan network target DataFrame and statistics to a Markdown report."""
    with open(filename, 'w', encoding='utf-8') as file_out:
        file_out.write('# Tenable Scans & Their Subnets\n\n')
        file_out.write('## Scan Target Networks\n\n')
        file_out.write(df.to_markdown(tablefmt='github'))
        file_out.write('\n\n')
        file_out.write('## Summary Statistics\n\n')
        file_out.write('### Scan ID Summary\n\n')
        if 'scan_id' in df and not df.empty:
            file_out.write(df['scan_id'].astype(str).describe().to_markdown(tablefmt='github'))
        file_out.write('\n\n')
        file_out.write('### Scan Name Summary\n\n')
        if 'scan_name' in df and not df.empty:
            file_out.write(df['scan_name'].describe().to_markdown(tablefmt='github'))
        file_out.write('\n\n')
        file_out.write('### IP Subnets Summary\n\n')
        if 'value' in df and not df.empty:
            file_out.write(df['value'].describe().to_markdown(tablefmt='github'))
        file_out.write('\n\n')


def main():
    """Main execution entrypoint."""
    logging.basicConfig(level=logging.INFO)
    io_client = TenableIO()
    df_results = extract_all_scan_networks(io_client)
    write_markdown_report(df_results)


if __name__ == '__main__':
    main()
