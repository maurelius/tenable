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
from tenable.io import TenableIO
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.WARNING)

def _get_tag_filters(io_client, tag_id, tag_cache):
    """Retrieves and parses filters for a given tag, with caching."""
    if tag_id in tag_cache:
        return tag_cache[tag_id], True

    try:
        tags = io_client.tags.details(tag_id)
        filter_dict = tags.get("filters")

        if not filter_dict or 'asset' not in filter_dict:
            logging.info("No asset filters found for tag %s. Skipping.", tag_id)
            tag_cache[tag_id] = None
            return None, False

        asset_json_string = filter_dict['asset']
        asset_data = json.loads(asset_json_string)
        filter_list = asset_data.get('and', [])

        if not filter_list:
            logging.info("No 'and' filters found for tag %s. Skipping.", tag_id)
            tag_cache[tag_id] = None
            return None, False

        tag_cache[tag_id] = filter_list
        return filter_list, False
    except Exception as e: # pylint: disable=broad-exception-caught
        logging.error("Error processing tag %s: %s", tag_id, e)
        tag_cache[tag_id] = None
        return None, False

def _extract_value(value):
    """Helper to extract a flat value from potentially nested lists."""
    if isinstance(value, list) and value:
        try:
            if isinstance(value[0], list):
                return value[0][0]
            return value[0]
        except (IndexError, TypeError):
            return None
    return value

def _process_scan(io_client, scan, tag_cache, stats):
    """Processes a single scan and returns extracted data rows."""
    scan_id = scan['id']
    scan_name = scan['name']
    extracted_data = []

    try:
        scan_details = io_client.scans.details(scan_id)
        settings = scan_details.get('settings')
        tag_targets = settings.get('tag_targets') if settings else None

        if not tag_targets:
            return []

        for t_id in tag_targets:
            filter_list, is_hit = _get_tag_filters(io_client, t_id, tag_cache)
            if is_hit:
                stats['hits'] += 1
            else:
                stats['misses'] += 1

            if not filter_list:
                continue

            for item in filter_list:
                extracted_data.append({
                    'scan_id': scan_id,
                    'scan_name': scan_name,
                    'tag_id': t_id,
                    'property': item.get('property'),
                    'value': _extract_value(item.get('value'))
                })
    except Exception as e: # pylint: disable=broad-exception-caught
        logging.error("Error processing scan %s: %s", scan_id, e)

    return extracted_data

def _generate_report(df, output_file):
    """Generates a Markdown report from the extracted data DataFrame."""
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
    """Main execution logic for extracting IP networks from scan tags."""
    io = TenableIO()
    scans = io.scans.list()

    all_extracted_data = []
    tag_cache = {}
    stats = {'hits': 0, 'misses': 0}

    print(f"Processing {len(scans)} scans to extract tag targets...")

    for scan in tqdm(scans, desc="Processing scans"):
        all_extracted_data.extend(_process_scan(io, scan, tag_cache, stats))

    if not all_extracted_data:
        print("No data extracted. Skipping report generation.")
        return

    df = pd.DataFrame(all_extracted_data)
    output_file = 'TENABLE-SCAN-TARGETS.md'
    _generate_report(df, output_file)

    print(f"Report written to {output_file}")
    print(f"Tag Cache Performance: Hits={stats['hits']}, Misses={stats['misses']}")

if __name__ == "__main__":
    main()
