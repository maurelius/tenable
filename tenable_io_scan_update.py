""" tenable_io_scan_update.py: Updates the scans to be AUTO-ROUTED and to be associated to the target network by TARGET_NETWORK_UUID"""

### Import Modules
import tqdm
from pprint import pprint
from tenable.io import TenableIO

### Define some Variables
# Define API keys
accessKey = '1234'
secretKey = '1234'
# What folder are we looking in? [int]
FOLDER_ID = 0

# Bootstrap Tenable.io API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)

# This could also be written as (to return as a list).
# def get_nw_uuid(NETWORK):
#    return [nw['uuid'] for nw in io.networks.list(('name', 'eq', NETWORK))]
# TARGET_NETWORK_UUID = get_nw_uuid(NETWORK)

def get_nw_uuid():
    """Get properties of TARGET_NETWORK_NAME return its UUID."""
    TARGET_NETWORK_NAME = 'Network Name'
    for nw in io.networks.list(('name','eq', TARGET_NETWORK_NAME)):
        return(nw['uuid'])
# Store output to variable
TARGET_NETWORK_UUID = get_nw_uuid()

kw = {"scanner_id": "AUTO-ROUTED",
     'target_network_uuid': TARGET_NETWORK_UUID}

for each_scan in tqdm.tqdm(io.scans.list(folder_id=FOLDER_ID)):
    try:
        io.scans.configure(scan_id=each_scan['id'], **kw)
    except Exception as ex:
        print(ex)
        continue