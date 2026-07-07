"""tenable_io_rogue_assets.py: Checks the list of assets and finds ones that went rogue on us"""

### Import Modules
import logging
from tenable_config import get_tenable_io_client

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Bootstrap API connection
io = get_tenable_io_client()
# ⚡ BOLT Optimization: Use bulk asset export instead of sequential list + tag lookups.
# io.exports.assets() retrieves all assets and their associated tags in a single bulk operation,
# reducing API overhead from O(N) to O(1) export job.
asset_list = io.exports.assets()

# Define FQDNs we own that we don't want 
our_fqdns = ['my.fqdn1.com', 'my.fqdn2.net']

for asset in asset_list:
    host_fqdn = asset.get('fqdn', [])
    host_uuid = asset.get('id')
    host_ipv4 = asset.get('ipv4')

    # In the bulk export, tags are already included in the asset object.
    asset_tags = asset.get('tags', [])
    tag_values = [tag['value'] for tag in asset_tags]
    
    # Check if host_fqdn is null or empty
    if not host_fqdn:
        print(f"Host w/ IP Address: {host_ipv4} has no FQDN")
    else:
        # Check if any of our FQDNs are in the host's FQDN list
        is_managed = 'My Access Group Manage Assets' in tag_values
        matches_our_domains = any(
            fqdn in fqdn_part for fqdn in our_fqdns for fqdn_part in host_fqdns
        )
        if not matches_our_domains and not is_managed:
            print(f"Rogue asset found: {host_fqdns}")
