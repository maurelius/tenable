"""tenable_io_scan_bulk_delete.py: Bulk delete scans with a specific keyword in the scan name"""
"""Reference pyTenable Documentation: https://pytenable.readthedocs.io/en/stable/api/io/scans.html#tenable.io.scans.ScansAPI.delete"""

### Import Modules
import logging
from pprint import pprint
from tenable.io import TenableIO
from tqdm import tqdm

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Define API keys
accessKey = '1234'
secretKey = '1234'
# Bootstrap Tenable API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)

### Let's move on
# Start a loop to keep asking for input until everything is confirmed good
while True:
    # Define the word in the scan name so you can get all of those scans
    KEYWORD = input("Enter the keyword or string that you want to search for:")
    # Print out what was entered
    pprint(f"You entered: {KEYWORD}")
    # Get a list of all the scans
    SCAN_LIST = io.scans.list()
    # Get all the names for the scans in the list that match your scan name keyword
    SCAN_NAMES = [d['name'] for d in SCAN_LIST if KEYWORD in d['name']]
    # Get all the IDs of the scans from above
    SCAN_IDS = [d['id'] for d in SCAN_LIST if KEYWORD in d['name']]
    # Print out the names of the scans that will get deleted
    pprint(SCAN_NAMES)
    # Print out the number of scans that will be deleted
    pprint(f"You are about to delete", len(SCAN_NAMES), "scans...")
    # If you confirm that everything looks good, break the loop
    CONFIRM = input("Does this look right? (Y/n):")
    if CONFIRM.lower() == 'y':
        break
# Print out that the scans are now being deleted
pprint("Deleting scans...")
# Loop through the scan IDs, delete them, with a progress bar
for SCAN in tqdm(SCAN_IDS):
    io.scans.delete(scan_id=SCAN)
# Print out that everything was completed successfully
pprint("Delete operation was successfully completed.")