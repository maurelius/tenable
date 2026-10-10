#!/usr/bin/env python3
'''
Tenable.io - Get IP Networks from Scan Tags

Description:
  This script retrieves all scans from Tenable.io and extracts the IP networks associated with
  each scan through their tag targets.
  It processes the tag filters to identify asset-related tags and extracts relevant IP subnets.
  Tag details are cached in memory to avoid duplicate API calls across scans.
  The collected data is compiled into a pandas DataFrame and saved as a Markdown file for
  reporting purposes, including summary statistics for each field.

Auth/Secrets:
  - Uses TENABLE_ACCESS_KEY / TENABLE_SECRET_KEY env vars via get_tenable_io_client().

Requires:
  pip install pytenable pandas

Outputs:
  - Markdown file (TENABLE-SCAN-TARGETS.md) with scan target network details and statistics.
'''
import json
import logging
import pandas as pd
from tenable_config import get_tenable_io_client


def _get_tag_details(client, tag_id, cache, cache_stats):
    """
    Fetches tag details using client.tags.details, caching results in memory.
    """
    if tag_id in cache:
        cache_stats['hits'] += 1
        return cache[tag_id]

    cache_stats['misses'] += 1
    details = client.tags.details(tag_id)
    cache[tag_id] = details
    return details


def _extract_value_from_item(item, tag_id):
    """
    Safely flattens nested lists or extracts single values from filter items.
    """
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


def _process_tag_target(client, scan_info, tag_id, cache, cache_stats):
    """
    Processes a single tag target and extracts filter property/value pairs.
    """
    extracted_items = []
    try:
        tags = _get_tag_details(client, tag_id, cache, cache_stats)
        filter_dict = tags.get("filters") if tags else None

        if not filter_dict or 'asset' not in filter_dict:
            logging.info("No asset filters found for tag %s. Skipping.", tag_id)
            return extracted_items

        asset_json_string = filter_dict['asset']
        asset_data = json.loads(asset_json_string)
        filter_list = asset_data.get('and', [])

        if not filter_list:
            logging.info("No 'and' filters found for tag %s. Skipping.", tag_id)
            return extracted_items

        scan_id, scan_name = scan_info
        for item in filter_list:
            extracted_items.append({
                'scan_id': scan_id,
                'scan_name': scan_name,
                'tag_id': tag_id,
                'property': item.get('property'),
                'value': _extract_value_from_item(item, tag_id)
            })
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logging.error("Error processing tag %s for scan %s: %s", tag_id, scan_info[0], exc)

    return extracted_items


def extract_ip_networks(client):
    """
    Main extraction function iterating over scans and tag targets with caching.
    """
    all_extracted_data = []
    tag_cache = {}
    cache_stats = {'hits': 0, 'misses': 0}

    scans = client.scans.list()

    for scan in scans:
        scan_id = scan['id']
        scan_name = scan['name']

        try:
            scan_details = client.scans.details(scan_id)
            settings = scan_details.get('settings') if scan_details else None
            tag_targets = settings.get('tag_targets') if settings else None

            if not tag_targets:
                logging.info("No tag_targets found for scan id %s. Skipping.", scan_id)
                continue

            for tag_id in tag_targets:
                items = _process_tag_target(client, (scan_id, scan_name), tag_id,
                                            tag_cache, cache_stats)
                all_extracted_data.extend(items)

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logging.error("Error processing scan %s: %s", scan_id, exc)
            continue

    logging.info("Tag Details Caching Stats - Hits: %d, Misses: %d",
                 cache_stats['hits'], cache_stats['misses'])
    return all_extracted_data


def generate_report(data, filename='TENABLE-SCAN-TARGETS.md'):
    """
    Generates a Markdown report with summary statistics from extracted IP network data.
    """
    dataframe = pd.DataFrame(data)

    if dataframe.empty:
        dataframe = pd.DataFrame(columns=['scan_id', 'scan_name', 'tag_id', 'property', 'value'])

    with open(filename, 'w', encoding='utf-8') as file_handle:
        file_handle.write('# Tenable Scans & Their Subnets\n\n')
        file_handle.write('## Scan Target Networks\n\n')
        file_handle.write(dataframe.to_markdown(tablefmt='github'))
        file_handle.write('\n\n## Summary Statistics\n\n')

        if not dataframe.empty:
            file_handle.write('### Scan ID Summary\n\n')
            file_handle.write(dataframe['scan_id'].astype(str).describe().to_markdown(
                tablefmt='github'))
            file_handle.write('\n\n### Scan Name Summary\n\n')
            file_handle.write(dataframe['scan_name'].describe().to_markdown(tablefmt='github'))
            file_handle.write('\n\n### IP Subnets Summary\n\n')
            file_handle.write(dataframe['value'].describe().to_markdown(tablefmt='github'))
            file_handle.write('\n\n')


def main():
    """
    Entry point for script execution.
    """
    logging.basicConfig(level=logging.INFO)
    client = get_tenable_io_client()
    extracted_data = extract_ip_networks(client)
    generate_report(extracted_data)


if __name__ == '__main__':
    main()
