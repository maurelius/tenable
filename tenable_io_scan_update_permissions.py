"""
tenable_io_scan_update_permissions.py: Update scan permissions for every scan in a specified folder
"""
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
REQUIRED_TYPES = ['SNMPv1/v2c', 'Windows', 'SSH', 'SNMPv3', 'Database']
# Store the UUIDs of the managed credentials we want
CRED_UUIDS = [
    CRED['uuid'] for CRED in CRED_LIST
    if 'MY-KEYWORD' in CRED['name'] and CRED['type'] in REQUIRED_TYPES
]

# Define the permissions to be added
# ⚡ BOLT NOTE: We've simplified this to match the expected ACL object structure.
NEW_ACLS = [
    {
        "permissions": 16,
        "name": "View Only",
        "type": "default"
    }
]

# Aggregate credentials into a list for batch update
CREDENTIALS_TO_ADD = [{'uuid': uuid} for uuid in CRED_UUIDS]

# Iterate over the scans and update them
for scan in MY_SCANS:
    scan_id = scan['id']
    # ⚡ BOLT OPTIMIZATION: Update the scan with both credentials and permissions in a single call.
    # This reduces network overhead from O(N*M) to O(N), where N is the number of scans
    # and M is the number of credentials.
    io.scans.configure(scan_id, credentials=CREDENTIALS_TO_ADD, acls=NEW_ACLS)

print("Scans have been updated with the specified managed credentials and permissions.")
