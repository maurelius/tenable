"""tenable_io_check_scanners.py: Checks the list of scanners and writes to a txt file for use elsewhere"""
"""If you use a separate or multiple networks, you can filter out scanners you don't want using the NETWORK variable"""
"""Networks are found in the Tenable.io console under Settings > Sensors > Networks"""

### Import Modules
import logging
import os
from tenable.io import TenableIO

### Define some Variables
## Define what Network you want to filter out
NETWORK = "NETWORK_NAME"
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Bootstrap Tenable API connection
io = TenableIO(os.getenv('TENABLE_ACCESS_KEY'), os.getenv('TENABLE_SECRET_KEY'))
scanner_list = io.scanners.list()

# Create a text file in the working directory of the script and add scanner IPs to it
with open('scanner_ips.txt', 'w') as f:
    for scanner in scanner_list:
        ip_addresses = scanner.get('ip_addresses')
        network_name = scanner.get('network_name')
        # Filter out scanners in a specific network and Tenable Cloud Scanners
        if ip_addresses is not None and network_name not in [NETWORK, 'Default']:
            f.write(ip_addresses[0])
            f.write('\n')