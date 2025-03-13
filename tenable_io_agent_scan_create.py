"""tenable_io_agent_scan_create.py: Creates an agent scan within a specified folder using an agent scan template"""
"""Reference pyTenable Documentation: https://pytenable.readthedocs.io/en/stable/api/io/scans.html#tenable.io.scans.ScansAPI.create"""

### Import Modules
import datetime
import json
import logging
import tqdm
from pprint import pprint
from tenable.io import TenableIO

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Define API Keys
accessKey = '1234'
secretKey = '1234'
# Bootstrap API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)

# Set date for scan schedule
scanDate = datetime.datetime(2023,5,6,19,0,0)

## Define Scan Parameters - Change variables to desired values
# Input name for the scan
NAME = input("Enter a name for the scan: ")
AGENT_GROUP = input("Enter a name for an agent group: ")
# Use the agent scan template ID [int]
TEMPLATE = 3471
# Use the Agent Scans folder [int]
FOLDERS = io.folders.list()
FOLDER_ID =  [d for d in FOLDERS if d['name'] == 'CHANGE-ME'][0]['id']
# What tag(s) do you want to target for the scan? [str]
TAG_NAME = input("Enter the tag name you wish to scan (E.g., Mac Agents): ")
# What Network are you going to put this scan in? [str] - Change if not using 'Default'
NETWORK_NAME = "Default"
# JSON file for sharing permissions
jsonFile = 'discovery_scan_settings.json'

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
def get_tag_uuid(TAG_NAME): 
    return [{tag['uuid'] for tag in io.tags.list(('value','match',TAG_NAME))}]

TAG_UUID = json.dumps(get_tag_uuid(TAG_NAME), default=set_default)

# What email(s) should scan notifications be sent to?
EMAILS = 'ChangeMy.Address@example.com'

# Set up keyword args to configure scans with [dict]
kw = {"policy_id": TEMPLATE, 
      "emails": EMAILS,
      "name": NAME,
      "folder_id": FOLDER_ID,
      "enabled": False
    }

# Create Agent Group
print('Creating agent group with name: ', AGENT_GROUP)
try:
    io.agent_groups.create(AGENT_GROUP)
except Exception as ex:
    print(ex)

print('Creating scan with name: ', NAME)
try:
    io.scans.create(**kw)
except Exception as ex:
    print(ex)
    
# Find your newly created scan and update its permissions with the pre-defined ACL
SCAN_LIST = io.scans.list()
# Function to find scan by name using SCAN_LIST 
def get_scan_uuid(NAME):
    return([d for d in SCAN_LIST if d['name'] == NAME][0]['id'])

# Call function to get scan ID of the new scan
SCAN_ID = get_scan_uuid(NAME)

# Update the newly created scan's schedule w/ scanDate
print(f"Updating scan '{NAME}' schedule to kick off on '{scanDate}'")
try:
    config_schedule = io.scans.configure_scan_schedule(SCAN_ID, enabled=True, frequency='WEEKLY', starttime=scanDate)
    io.scans.configure(SCAN_ID, schedule_scan=config_schedule)
except Exception as ex:
    print(ex)

# Configure the new scan with updated settings
scanFile = 'discovery_scan_settings.json'

# Define function to update scan with JSON file
def update_scan(scanFile):
    with open(scanFile, 'r') as jsonFile:
        data = json.load(jsonFile)
        print('Submitting the following data: \n')
        pprint(data)
        if input('\n\nLook good? y/N: ').lower() == 'y':
            new_scan_settings = data['newScan'][0]['settings']
            tqdm.tqdm(io.scans.configure(SCAN_ID, **new_scan_settings))

# Call function to update scan
print("Updating scan permissions...")             
try:
    update_scan(scanFile)
except Exception as ex:
    print(ex)
    
io.agent_groups.list()