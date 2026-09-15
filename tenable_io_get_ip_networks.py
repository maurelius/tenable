#!/usr/bin/env python3
'''
Tenable.io - Get IP Networks from Scan Tags

Description:
  This script retrieves all scans from Tenable.io and extracts the IP networks
  associated with each scan through their tag targets. It processes the tag
  filters to identify asset-related tags and extracts the relevant IP subnet
  information. The collected data is compiled into a pandas DataFrame and saved
  as a Markdown file for reporting purposes.

Auth/Secrets:
  - Use TENABLE_ACCESS_KEY / TENABLE_SECRET_KEY env vars.

Requires:
  pip install pytenable pandas tabulate

Outputs:
  - Markdown file with details of scan target networks, including scan ID,
    scan name, tag ID, property, and value (e.g., IP subnets or UUIDs),
    along with summary statistics for each field.
'''
import json
import logging
import pandas as pd
from tenable_config import get_tenable_io_client

# Set up logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

def _get_tag_filters(tio, tag_uuid, tag_cache, stats):
    """
    Retrieves and parses asset filters for a given tag UUID, using a cache.
    """
    if tag_uuid in tag_cache:
        stats['hits'] += 1
        return tag_cache[tag_uuid]

    stats['misses'] += 1
    try:
        tags = tio.tags.details(tag_uuid)
        filter_dict = tags.get("filters")

        if not filter_dict or 'asset' not in filter_dict:
            LOGGER.info("No asset filters found for tag %s. Skipping.", tag_uuid)
            tag_cache[tag_uuid] = None
            return None

        asset_json_string = filter_dict['asset']
        asset_data = json.loads(asset_json_string)
        filter_list = asset_data.get('and', [])

        if not filter_list:
            LOGGER.info("No 'and' filters found for tag %s. Skipping.", tag_uuid)
            tag_cache[tag_uuid] = None
            return None

        tag_cache[tag_uuid] = filter_list
        return filter_list

    except Exception as exc:  # pylint: disable=broad-exception-caught
        LOGGER.error("Error processing tag %s: %s", tag_uuid, exc)
        tag_cache[tag_uuid] = None
        return None

def _extract_scan_items(scan, tio, tag_cache, stats):
    """
    Extracts individual filter items from a scan's tag targets.
    """
    scan_id = scan['id']
    scan_name = scan['name']
    extracted_items = []

    try:
        scan_details = tio.scans.details(scan_id)
        settings = scan_details.get('settings')
        tag_targets = settings.get('tag_targets') if settings else None

        if not tag_targets:
            LOGGER.info("No tag_targets found for scan id %s. Skipping.", scan_id)
            return []

        for tag_uuid in tag_targets:
            filter_list = _get_tag_filters(tio, tag_uuid, tag_cache, stats)
            if not filter_list:
                continue

            for item in filter_list:
                val = item.get('value')
                if isinstance(val, list) and val:
                    try:
                        val = val[0][0] if isinstance(val[0], list) else val[0]
                    except (IndexError, TypeError):
                        LOGGER.warning("Could not extract value for tag %s.", tag_uuid)
                        val = None

                extracted_items.append({
                    'scan_id': scan_id,
                    'scan_name': scan_name,
                    'tag_id': tag_uuid,
                    'property': item.get('property'),
                    'value': val
                })
    except Exception as exc:  # pylint: disable=broad-exception-caught
        LOGGER.error("Error processing scan %s: %s", scan_id, exc)

    return extracted_items

def _generate_report(extracted_data):
    """
    Generates a Markdown report from the extracted scan data.
    """
    if not extracted_data:
        LOGGER.warning("No data extracted. Skipping report generation.")
        return

    df = pd.DataFrame(extracted_data)

    with open('TENABLE-SCAN-TARGETS.md', 'w', encoding='utf-8') as report_file:
        report_file.write('# Tenable Scans & Their Subnets\n\n')
        report_file.write('## Scan Target Networks\n\n')
        report_file.write(df.to_markdown(tablefmt='github'))
        report_file.write('\n\n## Summary Statistics\n\n')
        report_file.write('### Scan ID Summary\n\n')
        report_file.write(df['scan_id'].astype(str).describe().to_markdown(tablefmt='github'))
        report_file.write('\n\n### Scan Name Summary\n\n')
        report_file.write(df['scan_name'].describe().to_markdown(tablefmt='github'))
        report_file.write('\n\n### IP Subnets Summary\n\n')
        report_file.write(df['value'].describe().to_markdown(tablefmt='github'))
        report_file.write('\n')

def main():
    """Main execution function."""
    tio = get_tenable_io_client()
    scans = tio.scans.list()

    all_extracted_data = []
    tag_cache = {}
    stats = {'hits': 0, 'misses': 0}

    for scan in scans:
        all_extracted_data.extend(_extract_scan_items(scan, tio, tag_cache, stats))

    LOGGER.info("Tag resolution stats - Hits: %s, Misses: %s", stats['hits'], stats['misses'])
    _generate_report(all_extracted_data)

if __name__ == "__main__":
    main()
