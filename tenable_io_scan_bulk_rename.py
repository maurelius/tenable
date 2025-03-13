"""tenable_io_scan_bulk_rename.py: Bulk rename scans with a specific keyword in the scan name"""
"""Reference pyTenable Documentation: https://pytenable.readthedocs.io/en/stable/api/io/scans.html#tenable.io.scans.ScansAPI.delete"""

### Import Modules
import logging
from tenable.io import TenableIO
from tenable.errors import BadRequestError

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Define API keys
accessKey = '1234'
secretKey = '1234'
# Bootstrap Tenable API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)
# Get a list of current scans
SCANS = io.scans.list()
# Define the word in the scan name so you can get all of those scans
KEYWORD = input("Enter the keyword of scans you want to rename (E.g., All scans with 'keyword' in the name):")

### Let's move on
print(f'Renaming any scans with {KEYWORD} in the name and prepending ''Keyword: ''')
# Loop through the scans looking for your keyword, then rename them
for scan in SCANS:
    if KEYWORD in scan['name']:
        try:
            print(f'Renaming', scan['name'], '...')
            # Prepend some text for better organization
            io.scans.configure(scan['id'], name='Discovery Scan: ' + scan['name'])
        # Catch any exceptions thrown by Tenable, skip 'em, and move on
        except BadRequestError:
            print(f'Skipping scan {scan['id']} due to BadRequestError')
            continue                           