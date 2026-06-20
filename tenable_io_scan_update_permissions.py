"""
tenable_io_scan_update_permissions.py: Update scan permissions for every scan in a specified folder
"""
import logging
from tqdm import tqdm
from tenable_config import get_tenable_io_client

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Bootstrap API connection
io = get_tenable_io_client()
# Store all the scans
MY_SCANS = io.scans.list()
# Store list of managed credentials
CRED_LIST = io.credentials.list()
required_types = ['SNMPv1/v2c', 'Windows', 'SSH', 'SNMPv3', 'Database']
# Store the UUIDs of the managed credentials we want
CRED_UUIDS = [
    CRED['uuid'] for CRED in CRED_LIST
    if 'MY-KEYWORD' in CRED['name'] and CRED['type'] in required_types
]

# Define the scan settings to be updated
# Note: We define the acls to be used in the batch update below.
SCAN_ACLS = [
    {
        "permissions": 16,
        "name": "View Only"
    }
]

# Prepare the credentials list once to avoid redundant processing in the loop
# This combines all required credentials into a single list for batch updating.
SCAN_CREDS = [{'uuid': uuid} for uuid in CRED_UUIDS]

# Iterate over the scans and update them
for SCAN in tqdm(MY_SCANS, desc="Updating scan permissions"):
    SCAN_ID = SCAN['id']
    # Update the scan with both the new credentials and permissions in a single call.
    # This reduces network overhead from O(N*M) to O(N) by batching updates.
    io.scans.configure(
        SCAN_ID,
        credentials=SCAN_CREDS,
        acls=SCAN_ACLS
    )

print("Scans have been updated with the specified managed credentials and permissions.")
