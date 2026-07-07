"""tenable_io_get_tag_details.py - Get all tag values for tags in a defined category"""

### Import Modules
import re
import logging
import pandas as pd
from tenable_config import get_tenable_io_client

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Bootstrap API connection
io = get_tenable_io_client()
category = input('Enter the tag category to look up: ')

# Grab the UUIDs of every tag in category, don't process tag multiple times
uuids = set()

for d in io.tags.list():
    if d['category_name'] == category and d['uuid'] not in uuids:
        uuids.add(d['uuid'])

# Create an empty set to store the IP address subnets
# ⚡ BOLT Optimization: Using a set for O(1) deduplication and O(N) total complexity
subnets_found = set()

# Define a regular expression pattern to match IP address subnets
SUBNET_PATTERN = r'\d+\.\d+\.\d+\.\d+/\d+'

# Loop through the matching UUIDs
for uuid in uuids:
    # Retrieve the details for the UUID
    details = io.tags.details(uuid)

    # Extract the 'filters' dictionary from the details
    filters = details.get('filters', {})

    # Extract the 'asset' field from the filters dictionary as a string
    asset_filter_str = filters.get('asset', '')

    # Use regular expressions to find IP address subnets in the 'asset' field
    subnets = re.findall(SUBNET_PATTERN, asset_filter_str)

    # Add the found subnets to the set
    subnets_found.update(subnets)

# Sort the subnets for a cleaner report
subnet_list = sorted(list(subnets_found))
DF_SUBNETS = pd.DataFrame(subnet_list).rename(columns={0: 'Subnet'})
# Print the list of IP address subnets
with open('TENABLE-SUBNETS.md', 'w', encoding='utf-8') as f:
    f.write(f'# Tenable Subnets for Tag Category: {category}\n\n')
    f.write(DF_SUBNETS.to_markdown(tablefmt='github'))
    f.write('\n')
