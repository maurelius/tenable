"""tenable_io_get_tag_details.py - Get all tag values for tags in a defined category"""

### Import Modules
import re
import pandas as pd
import logging
from tenable.io import TenableIO

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Define keys to auth to API
accessKey = '1234'
secretKey = '1234'
# Bootstrap API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)
category = input('Enter the tag category to look up: ')

# Grab the UUIDs of every tag in category, don't process tag multiple times
uuids = set()

for d in io.tags.list():
    if d['category_name'] == category and d['uuid'] not in uuids:
        uuids.add(d['uuid'])

# Create an empty list to store the IP address subnets
subnet_list = []

# Define a regular expression pattern to match IP address subnets
subnet_pattern = r'\d+\.\d+\.\d+\.\d+/\d+'

# Loop through the matching UUIDs
for uuid in uuids:
    # Retrieve the details for the UUID
    details = io.tags.details(uuid)
    
    # Extract the 'filters' dictionary from the details
    filters = details.get('filters', {})
    
    # Extract the 'asset' field from the filters dictionary as a string
    asset_filter_str = filters.get('asset', '')
    
    # Use regular expressions to find IP address subnets in the 'asset' field
    subnets = re.findall(subnet_pattern, asset_filter_str)
    
    # Append the found subnets to the list
    subnet_list.extend(subnets)
    subnet_list = list(set(subnet_list))
df = pd.DataFrame(subnet_list).drop_duplicates().rename(columns={0: 'Subnet'})
# Print the list of IP address subnets
with open('TENABLE-SUBNETS.md', 'w') as f:
    f.write(f'# Tenable Subnets for Tag Category: {category}\n\n')
    f.write(df.to_markdown(tablefmt='github'))
    f.write('\n')