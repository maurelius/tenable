"""tenable_io_rogue_assets.py: Checks the list of assets and finds ones that went rogue on us"""

### Import Modules
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
# Get list of assets
asset_list = io.assets.list()
# Define FQDNs we own that we don't want 
our_fqdns = ['my.fqdn1.com', 'my.fqdn2.net']
for asset in asset_list:
    host_fqdn = asset.get('fqdn')
    host_uuid = asset.get('id')
    host_ipv4 = asset.get('ipv4')
    asset_tags = io.assets.tags(uuid=host_uuid).get('tags')
    tag_values = [tag['value'] for tag in asset_tags]
    
    # Check if host_fqdn is null
    if len(host_fqdn) == 0:
        print(f"Host w/ IP Address: {host_ipv4} has no FQDN")
    else:
        # Check if any of our FQDNs are in the host's FQDN list
        if not any(fqdn in fqdn_part for fqdn in our_fqdns for fqdn_part in host_fqdn) and 'My Access Group Manage Assets' not in tag_values:
            print(f"Rogue asset found: {host_fqdn}")