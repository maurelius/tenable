""" tenable_io_move_assets.py: Move assets from Default Network with IP_NETWORK to DEST Network """

### Import Modules
import logging
import os
from tenable.io import TenableIO

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Bootstrap Tenable API connection
io = TenableIO(os.getenv('TENABLE_ACCESS_KEY'), os.getenv('TENABLE_SECRET_KEY'))
DEFAULT_NETWORK_UUID = [d for d in io.networks.list() if d['name'] == 'Default'][0]['uuid']
DEST_NETWORK_UUID = [nw for nw in io.networks.list() if nw['name'] == 'CHANGE_DESTINATION'][0]['uuid']
IP_NETWORK = "10.0.0.0/8"

print('Moving assets from Default to Destination Network...')
io.assets.move_assets(DEFAULT_NETWORK_UUID, DEST_NETWORK_UUID, [IP_NETWORK])