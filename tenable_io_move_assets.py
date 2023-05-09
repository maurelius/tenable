#!/usr/bin/python
""" tenable_io_move_assets.py: Move assets from Default Network with IP_NETWORK to DEST Network """

### Import Modules
import logging
from pprint import pprint
from tenable.io import TenableIO

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Set up Azure KeyVault access
accessKey = '1234' 
secretKey = '1234'
# Bootstrap Tenable API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)
DEFAULT_NETWORK_UUID = [d for d in io.networks.list() if d['name'] == 'Default'][0]['uuid']
DEST_NETWORK_UUID = [nw for nw in io.networks.list() if nw['name'] == 'CHANGE_DESTINATION'][0]['uuid']
IP_NETWORK = "10.0.0.0/8"

print('Moving assets from Default to Destination Network...')
io.assets.move_assets(DEFAULT_NETWORK_UUID, DEST_NETWORK_UUID, [IP_NETWORK])