#!/usr/bin/env python3
'''
Tenable.io - Get IP Networks from Scan Tags

Description:
  This script retrieves all scans from Tenable.io and extracts the IP networks associated with each
  scan through their tag targets. It processes the tag filters to identify asset-related tags and
  extracts the relevant IP subnet information. The collected data is compiled into a pandas
  DataFrame and saved as a Markdown file for reporting purposes.

Auth/Secrets:
  - Use TIO_ACCESS_KEY / TIO_SECRET_KEY env vars.

Requires:
  pip install pytenable pandas tqdm

Outputs:
  - Markdown file with details of scan target networks, including scan ID, scan name, tag ID,
    property, and value (e.g., IP subnets or UUIDs), along with summary statistics.
'''
import json
import logging
import pandas as pd
from tqdm import tqdm
from tenable.io import TenableIO

# Note: The above imports assume you have pytenable installed and properly configured.

def _get_tag_filters(io_client, tag_id, cache):
    """
    Fetches and parses tag filters with caching.
    """
    if tag_id in cache:
        return cache[tag_id]

    try:
        tags = io_client.tags.details(tag_id)
        filter_dict = tags.get("filters")

        if not filter_dict or 'asset' not in filter_dict:
            logging.info("No asset filters found for tag %s. Skipping.", tag_id)
            cache[tag_id] = []
            return []

        asset_json_string = filter_dict['asset']
        asset_data = json.loads(asset_json_string)
        filter_list = asset_data.get('and', [])

        if not filter_list:
            logging.info("No 'and' filters found for tag %s. Skipping.", tag_id)
            cache[tag_id] = []
            return []

        cache[tag_id] = filter_list
        return filter_list
    except Exception as err:  # pylint: disable=broad-exception-caught
        logging.error("Error processing tag %s: %s", tag_id, err)
        cache[tag_id] = []
        return []

def _parse_filter_value(value, tag_id):
    """
    Normalizes the filter value, handling nested lists.
    """
    if isinstance(value, list) and value:
        try:
            if isinstance(value[0], list):
                return value[0][0]
            return value[0]
        except (IndexError, TypeError):
            logging.warning("Could not extract value from nested list for tag %s.", tag_id)
            return None
    return value

def extract_scan_tag_data(io_client, scans_list):
    """
    Extracts scan tag targets and their associated IP networks/filters.
    """
    all_extracted_data = []
    tag_cache = {}  # ⚡ BOLT Optimization: Cache tag details to minimize API calls.

    for scan in tqdm(scans_list, desc="Processing scans"):
        scan_id = scan['id']
        scan_name = scan.get('name', f"Scan {scan_id}")

        try:
            scan_details = io_client.scans.details(scan_id)
            settings = scan_details.get('settings') or {}
            tag_targets = settings.get('tag_targets')

            if not tag_targets:
                logging.info("No tag_targets found for scan id %s. Skipping.", scan_id)
                continue

            for tag_id in tag_targets:
                filter_list = _get_tag_filters(io_client, tag_id, tag_cache)

                for item in filter_list:
                    val = _parse_filter_value(item.get('value'), tag_id)
                    all_extracted_data.append({
                        'scan_id': scan_id,
                        'scan_name': scan_name,
                        'tag_id': tag_id,
                        'property': item.get('property'),
                        'value': val
                    })
        except Exception as err:  # pylint: disable=broad-exception-caught
            logging.error("Error processing scan %s: %s", scan_id, err)
            continue

    return pd.DataFrame(all_extracted_data)

def generate_markdown_report(df, filename):
    """
    Generates a Markdown report from the extracted data DataFrame.
    """
    with open(filename, 'w', encoding='utf-8') as f_out:
        f_out.write('# Tenable Scans & Their Subnets\n\n')
        f_out.write('## Scan Target Networks\n\n')
        f_out.write(df.to_markdown(tablefmt='github'))
        f_out.write('\n\n## Summary Statistics\n\n')
        f_out.write('### Scan ID Summary\n\n')
        f_out.write(df['scan_id'].astype(str).describe().to_markdown(tablefmt='github'))
        f_out.write('\n\n### Scan Name Summary\n\n')
        f_out.write(df['scan_name'].describe().to_markdown(tablefmt='github'))
        f_out.write('\n\n### IP Subnets Summary\n\n')
        f_out.write(df['value'].describe().to_markdown(tablefmt='github'))
        f_out.write('\n\n')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    io = TenableIO()
    scans_data = io.scans.list()

    extracted_df = extract_scan_tag_data(io, scans_data)
    if not extracted_df.empty:
        generate_markdown_report(extracted_df, 'TENABLE-SCAN-TARGETS.md')
        print("Report generated: TENABLE-SCAN-TARGETS.md")
    else:
        print("No tag data extracted. Report not generated.")
