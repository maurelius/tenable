"""tenable_io_scan_update_permissions.py: Update scan permissions for every scan in a folder"""
import logging
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

# Optimization: Prepare a list of all credential dictionaries to update in bulk
# This allows us to reduce network overhead from O(N*M) to O(N)
CREDENTIALS_TO_BATCH = [{'uuid': uuid} for uuid in CRED_UUIDS]

# Define the permissions to be added
# Optimization: Define ACLs as a list of objects as required by the API.
permissions = [
    {
        "permissions": 16,
        "name": "View Only"
    }
]

# Iterate over the scans and update them
for SCAN in MY_SCANS:
    SCAN_ID = SCAN['id']

    # Optimization: Combine credential and ACL updates into a single call.
    # pyTenable's io.scans.configure allows updating multiple settings at once,
    # and accepts a list of credentials. This reduces total requests from (M+1)*N to N.
    io.scans.configure(
        SCAN_ID,
        credentials=CREDENTIALS_TO_BATCH,
        acls=permissions
    )

print("Scans have been updated with the specified managed credentials and permissions.")
