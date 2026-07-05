"""tenable_io_assets_hunting.py: Looks for assets that aren't our own for cleanup purposes"""
"""Reference pyTenable documentation: https://pytenable.readthedocs.io/en/stable/api/io/exports.html"""

# Setup modules
import logging
from tenable_config import get_tenable_io_client

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Bootstrap API connection
io = get_tenable_io_client()

# Define Excluded Domains
ex_domains = ['.domain1.net', '.domain2.com', '.domain3.net']

# Initialize list
assets = []
# Get around the 5000 result limit of the API
for asset in io.exports.assets(chunk_size=5000):
    assets.append(asset)

# Process assets that are just excluded domains
ex_assets = [(d['id'], d['agent_names']) for d in assets if any(fqdn.endswith(domain) for fqdn in d.get('fqdns', []) for domain in ex_domains) and not any(fqdn.endswith("change-to-my.fqdn.com") for fqdn in d.get('fqdns',[]))]
# Process assets that are just Clients and not the excluded ones
client_agents = [(d['id'], d['agent_names']) for d in assets if d.get('has_agent') == True and not any("Server" in os for os in d.get('operating_systems', [])) and not ex_assets]