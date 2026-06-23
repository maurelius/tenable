"""tenable_io_scan_update_permissions.py: Update scan permissions for every scan in a folder"""
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
# Store the managed credentials we want to add
CREDENTIALS_TO_ADD = [{'uuid': CRED['uuid']} for CRED in CRED_LIST
                      if 'MY-KEYWORD' in CRED['name'] and CRED['type'] in required_types]

# Define the scan name and permissions (ACLs) to be added
# Performance Pattern: Preparation outside the loop
SCAN_NAME = "My Scan Name to Update"
ACLS_TO_ADD = [
    {
        "permissions": 16,
        "name": "View Only"
    }
]

# Iterate over the scans and update them
# ⚡ BOLT Optimization: Consolidate multiple io.scans.configure calls into one.
# This reduces the number of API calls from O(N*M) to O(N).
for SCAN in tqdm(MY_SCANS, desc="Updating Scans"):
    SCAN_ID = SCAN['id']
    # Consolidate credential and ACL updates into a single call
    io.scans.configure(
        SCAN_ID,
        credentials=CREDENTIALS_TO_ADD,
        acls=ACLS_TO_ADD,
        name=SCAN_NAME
    )

print("Scans have been updated with the specified managed credentials and permissions.")
