"""tenable_io_scan_update_permissions.py: Update scan permissions for every scan in a specified folder"""
import logging
from tenable.io import TenableIO

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Define keys to auth to API
accessKey = '1234'
secretKey = '1234'
# Bootstrap API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)
# Store all the scans
MY_SCANS = io.scans.list()
# Store list of managed credentials
CRED_LIST = io.credentials.list()
required_types = ['SNMPv1/v2c', 'Windows', 'SSH', 'SNMPv3', 'Database']
# Store the UUIDs of the managed credentials we want
CRED_UUIDS = [CRED['uuid'] for CRED in CRED_LIST if 'MY-KEYWORD' in CRED['name'] and CRED['type'] in required_types]

# Define the permissions to be added
permissions = {
    "settings": {
        "name": "My Scan Name to Update",
        "acls": [
            {
                "permissions": 16,
                "name": "View Only"
            }
        ]
    }
}

# Iterate over the scans and update them
for SCAN in MY_SCANS:
    SCAN_ID = SCAN['id']
    # Update the scan with the new credentials using the UUIDs
    for UUID in CRED_UUIDS:
        io.scans.configure(SCAN_ID, credentials={'uuid': UUID})
    # Update the scan with the new permissions    
    io.scans.configure(SCAN_ID, acls=[permissions])
    
print("Scans have been updated with the specified managed credentials and permissions.")