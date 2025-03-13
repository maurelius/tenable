"""tenable_io_bulk_scan_create.py: Creates a custom host discovery scan within a specified folder from CSV"""
"""Reference pyTenable Documentation: https://pytenable.readthedocs.io/en/stable/api/io/scans.html#tenable.io.scans.ScansAPI.create"""

### Import Modules
import pandas as pd
import json
import logging
import tqdm
from tenable.io import TenableIO

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Define keys to auth to API
accessKey = '1234'
secretKey = '1234'
# Bootstrap API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)
# Define path of and import CSV as dataframe (df) using specific columns.
CSV_FILE = 'data/BulkScanCreate.csv'
CSV_DATA = pd.read_csv(CSV_FILE)
SCAN_DATA = CSV_DATA[['ScanName', 'FolderName', 'TagName']]
# Create list from df column
FOLDER_NAMES = list(SCAN_DATA['FolderName'])
SCAN_NAMES = list(SCAN_DATA['ScanName'])
## Define Scan Parameters - Change variables to desired values
# What policy/template do you want to attach? [int]
TEMPLATE = 0000
# What email(s) should scan notifications be sent to?
EMAILS = 'ChangeMy.Address@example.com'
# Let Tenable.io pick the best scanner for the scan
SCANNER = 'AUTO-ROUTED'
# What Network are you going to put this scan in? [str] - Change if not using 'Default'
NETWORK_NAME = "Default"

# Function for JSON serialization
def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

# Function to get the UUID of the network you want
def get_network_uuid(NETWORK_NAME):
    return[{nw['uuid'] for nw in io.networks.list(('name', 'match', NETWORK_NAME))}]
# Target Network UUID for Network
TARGET_NETWORK_UUID = json.dumps(get_network_uuid(NETWORK_NAME), default=set_default)

# Function to get UUID of tags to be used for the scan from TAG_NAME
def get_tag_uuid(TAG_NAMES): 
    return [{tag['uuid'] for tag in io.tags.list(('value','match',TAG_NAMES))}]

# Create a dictionary to map folder names to folder IDs
FOLDER_ID_MAPPING = {}
for FOLDER in io.folders.list():
    if FOLDER['name'] in FOLDER_NAMES:
        FOLDER_ID_MAPPING[FOLDER['name']] = FOLDER['id']

# Loop through the CSV data and create scans
for index, row in SCAN_DATA.iterrows():
    SCAN_NAME = row['ScanName']
    FOLDER_NAME = row['FolderName']
    TAG_NAME = row['TagName']

    # Check if the folder exists in the FOLDER_ID_MAPPING
    if FOLDER_NAME in FOLDER_ID_MAPPING:
        FOLDER_ID = FOLDER_ID_MAPPING[FOLDER_NAME]
    else:
        print(f"Folder not found for scan '{SCAN_NAME}'. Skipping.")
        continue

    try:
        # Create the scan using **kw
        SCAN_INFO = {
            'policy_id': TEMPLATE,
            'emails': EMAILS,
            'scanner_id': SCANNER,
            'name': SCAN_NAME,
            'folder_id': FOLDER_ID,
            'target_network_uuid': TARGET_NETWORK_UUID,
            'enabled': False
        }
        
        if TAG_NAME:
            SCAN_INFO['tags'] = [TAG_NAME]

        scan = tqdm.tqdm(io.scans.create(**SCAN_INFO))
        print(f"Scan '{SCAN_NAME}' created successfully in folder '{FOLDER_NAME}'")

    except Exception as e:
        print(f"Error creating scan '{SCAN_NAME}': {str(e)}")

print("Bulk scan creation completed.")