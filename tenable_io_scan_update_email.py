#!/usr/bin/python

""" tenable_io_scan_update_email.py: Updates the notification emails for scans in FOLDER_ID"""

### Import Modules
import tqdm
from pprint import pprint
from tenable.io import TenableIO

### Define some Variables
# Define API keys
accessKey = '1234'
secretKey = '1234'
# What folder are the scans in? [int]
FOLDER_ID = 0
# What policy/template do you want to attach?
# POLICY_ID = 3468
# What email(s) should scan notifications be sent to?
EMAILS = 'emailAddress@example.com'
# Set up keyword args to configure scans with
kw = {"emails": EMAILS}

# Bootstrap API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)

### Loop through scans in folder and update using kw
for each_scan in tqdm.tqdm(io.scans.list(folder_id=FOLDER_ID)):
    try:
        io.scans.configure(each_scan['id'], **kw)
    except Exception as ex:
        print(ex)
        continue