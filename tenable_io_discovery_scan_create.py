#!/usr/bin/python

""" tenable_io_scan_create.py: Creates a custom host discovery scan within a specified folder which targets specifc tags"""
""" Reference pyTenable Documentation: https://pytenable.readthedocs.io/en/stable/api/io/scans.html#tenable.io.scans.ScansAPI.create """

### Import Modules
import json
import logging
import tqdm
from pprint import pprint
from tenable.io import TenableIO

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Define keys to auth to API
accessKey = '1234'
secretKey = '1234'
# Bootstrap API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)

## Define Scan Parameters - Change variables to desired values
# Input name for the scan
NAME = input("Enter a name for the scan: ")
# What policy/template do you want to attach? [int]
TEMPLATE = 0000
# What folder do you want this scan to be created in? [int]
FOLDER_ID = 0000
# What tag(s) do you want to target for the scan? [str]
TAG_NAME = "TAG-NAME"
# What Network are you going to put this scan in? [str]
NETWORK_NAME = "NETWORK"
# What scanner group should this scan use? [str]
SCANNER_NAME = "SCANNER GROUP"

# Function for JSON serialization
def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

# Function to get the UUID of the network you want
def get_network_uuid(NETWORK_NAME):
    return[{nw['uuid'] for nw in io.networks.list(('name', 'match', NETWORK_NAME))}]
# Target Network UUID for NETWORK
TARGET_NETWORK_UUID = json.dumps(get_network_uuid(NETWORK_NAME), default=set_default)

# Function to get UUID of tags to be used for the scan from TAG_NAME
def get_tag_uuid(TAG_NAME): 
    return [{tag['uuid'] for tag in io.tags.list(('value','match',TAG_NAME))}]

TAG_UUID = json.dumps(get_tag_uuid(TAG_NAME), default=set_default)
#TAG_UUID = get_tag_uuid(TAG_NAME)
""" 
This function is not needed for discovery scans. 
Keeping in as reference code, for now.

# Function to get UUID of credentials to be used for the scan
def get_cred_uuid(CREDENTIAL):
    # Get properties of CREDs return its UUID.
    return [{cred['uuid'] for cred in io.credentials.list(('name', 'eq', CREDENTIAL))}]
# Define name(s) of credentials to get [list]
CRED_NAME = ['CRED-NAME', 'CRED-NAME']
# Call function to get UUID of CRED_NAME [list of dict]
CRED_UUID = get_cred_uuid(CRED_NAME)
"""
# Let Tenable.io pick the best scanner for the scan
SCANNER = 'AUTO-ROUTED'
# What email(s) should scan notifications be sent to?
EMAILS = 'emailAddress@example.com'

# Set up keyword args to configure scans with [dict]
kw = {"policy_id": TEMPLATE, 
      "emails": EMAILS,
      "name": NAME,
      "scanner_id": SCANNER,
      "folder_id": FOLDER_ID,
      "target_network_uuid": [TARGET_NETWORK_UUID],
      "tag_targets": [TAG_UUID],
      "enabled": False,
      "scanner_name": SCANNER_NAME
    }

try:
    tqdm.tqdm(io.scans.create(**kw))
except Exception as ex:
    print(ex)

# Find your newly created scan and update its permissions with the pre-defined ACL
SCAN_LIST = io.scans.list()    
def get_scan_uuid(NAME):
     next(scan for scan in SCAN_LIST if scan["name"] == NAME)['id']

SCAN_ID = get_scan_uuid(NAME)

# Configure the new scan with updated settings
scanFile = 'discovery_scan_settings.json'

def update_scan(scanFile):
    with open(scanFile, 'r') as jsonFile:
        data = json.load(jsonFile)
        print('Submitting the following data: \n')
        pprint(data)
        if input('\n\nLook good? y/N: ').lower() == 'y':
            tqdm.tqdm(io.scans.configure(SCAN_ID,**data['newScan']))