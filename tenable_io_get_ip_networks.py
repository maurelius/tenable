#!/usr/bin/env python3
'''
Tenable.io - Get IP Networks from Scan Tags

Description:
  This script retrieves all scans from Tenable.io and extracts the IP networks associated with each scan through their tag targets.
  It processes the tag filters to identify asset-related tags and extracts the relevant IP subnet information.
  The collected data is compiled into a pandas DataFrame and saved as a Markdown file for reporting purposes, including summary statistics for each field.
  
Auth/Secrets:
  - Use TIO_ACCESS_KEY / TIO_SECRET_KEY env vars.
  
Requires:
  pip install pytenable pandas
  
Outputs:
  - Markdown file with details of scan target networks, including scan ID, scan name, tag ID, property, and value (e.g., IP subnets or UUIDs),
    along with summary statistics for each field.
'''
from tenable.io import TenableIO
import json
import os
import logging
import pandas as pd
from uuid import UUID

# Note: The above imports assume you have pytenable installed and properly configured with your Tenable.io credentials.

io = TenableIO()
scans = io.scans.list()
# --- Create a dictionary for efficient lookup of scan names ---
scan_name_map = {s['id']: s['name'] for s in scans}

# --- Processing Logic (Fixed) ---
# Initialize an empty list to store the data for the DataFrame
all_extracted_data = []

# Loop through the list of scans, using the full scan dictionary
for scan in scans:
    scan_id = scan['id']
    scan_name = scan['name']
    
    try:
        scan_details = io.scans.details(scan_id)
        settings = scan_details.get('settings')
        tag_targets = settings.get('tag_targets') if settings else None
        
        if not tag_targets:
            logging.info(f"No tag_targets found for scan id {scan_id}. Skipping.")
            continue
        
        for t in tag_targets:
            try:
                tags = io.tags.details(t)
                filter_dict = tags.get("filters")
                
                if not filter_dict or 'asset' not in filter_dict:
                    logging.info(f"No asset filters found for tag {t}. Skipping.")
                    continue
                
                asset_json_string = filter_dict['asset']
                asset_data = json.loads(asset_json_string)
                
                # Check for an 'and' list, use a default empty list if not present
                filter_list = asset_data.get('and', [])
                
                if not filter_list:
                    logging.info(f"No 'and' filters found for tag {t}. Skipping.")
                    continue

                for item in filter_list:
                    extracted_item = {
                        'scan_id': scan_id,
                        'scan_name': scan_name,  # Add the scan name here
                        'tag_id': t,
                        'property': item.get('property'),
                        'value': None # Initialize value as None
                    }
                    
                    value = item.get('value')
                    
                    if isinstance(value, list) and value:
                        # Handle the nested list case, like [["..."]]
                        # Safely access the value even if it's deeply nested
                        try:
                            # Flatten the list to get the single UUID or IP
                            # This handles cases like [["uuid"]] or ["ip"]
                            if isinstance(value[0], list):
                                flat_value = value[0][0]
                            else:
                                flat_value = value[0]
                            
                            extracted_item['value'] = flat_value
                        except (IndexError, TypeError):
                            # In case of a malformed list, set value to None
                            logging.warning(f"Could not extract value from nested list for tag {t}.")
                            extracted_item['value'] = None
                    else:
                        extracted_item['value'] = value

                    all_extracted_data.append(extracted_item)

            except Exception as e:
                logging.error(f"Error processing tag {t} for scan {scan_id}: {e}")
                continue

    except Exception as e:
        logging.error(f"Error processing scan {scan_id}: {e}")
        continue

# Create the DataFrame from the collected list of dictionaries
df = pd.DataFrame(all_extracted_data)

with open('TENABLE-SCAN-TARGETS.md', 'w') as f:
    f.write(f'# Tenable Scans & Their Subnets\n\n')
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