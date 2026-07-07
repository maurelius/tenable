"""tenable_io_rogue_assets.py: Checks the list of assets and finds ones that went rogue on us"""

### Import Modules
import logging
from tenable_config import get_tenable_io_client

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Bootstrap API connection
io = get_tenable_io_client()
# ⚡ BOLT Optimization: Use io.exports.assets() instead of io.assets.list().
# This reduces network overhead from O(N) to O(1) as tags are included in the export payload.
asset_list = io.exports.assets()
# Define FQDNs we own that we don't want
our_fqdns = ['my.fqdn1.com', 'my.fqdn2.net']

for asset in asset_list:
    # Export API returns plural forms for fqdns and ipv4s
    host_fqdns = asset.get('fqdns', [])
    host_ipv4s = asset.get('ipv4s', [])
    # Tags are included in the export record
    asset_tags = asset.get('tags', [])
    tag_values = [tag['value'] for tag in asset_tags]

    # Check if host_fqdns is empty
    if not host_fqdns:
        # Just use the first IP if available for the print statement
        host_ipv4 = host_ipv4s[0] if host_ipv4s else "Unknown"
        print(f"Host w/ IP Address: {host_ipv4} has no FQDN")
    else:
        # Check if any of our FQDNs are in the host's FQDN list
        is_managed = 'My Access Group Manage Assets' in tag_values
        matches_our_domains = any(
            fqdn in fqdn_part for fqdn in our_fqdns for fqdn_part in host_fqdns
        )
        if not matches_our_domains and not is_managed:
            print(f"Rogue asset found: {host_fqdns}")
