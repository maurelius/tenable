"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed"""
"""
# TODO://
---
- Dynamically grab scan_id from user input by name
- Loop through multiple scans if given a list []
"""

# Import modules
from time import strftime, localtime
import time
import logging
from tenable.io import TenableIO

# Specify the scan ID for now instead of dynamically grabbing it
scan_id = 0000

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Define keys to auth to API
accessKey = '1234'
secretKey = '1234'
# Bootstrap API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)

def check_scan_status(scan_id):
    try:
        scan = io.scans.status(scan_id)
        return scan
    except KeyError as e:
        print(f"KeyError: {e}. Possibly 'info' or 'status' key is missing in the response.")
    except Exception as e:
        print(f"Error: {e}")
    return None

while True:
    status = check_scan_status(scan_id)

    if status is not None:
        print(f"Scan status: {status}")

        if status == 'completed':
            # Perform your action here
            print("Scan is completed. Performing action...")
            # Add your code to perform the action
            for scan in io.scans.history(scan_id):
                starttime = scan['time_start']
                endtime = scan['time_end']
                timediff = endtime - starttime
                hours, remainder = divmod(timediff, 3600)
                minutes, seconds = divmod(remainder, 60)
                print(f"Scan Name: ", io.scans.details(scan_id).get("settings", {}).get("name", {}))
                print(f"Scan Start: ", strftime('%Y-%m-%d %H:%M:%S', localtime(scan['time_start'])))
                print(f"Scan End: ", strftime('%Y-%m-%d %H:%M:%S', localtime(scan['time_end'])))
                print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")
            # Exit the loop after the action is performed
            break

        elif status in ('canceled', 'empty', 'importing', 'paused', 'pending', 'processing', 'quarantined', 'running'):
            # The scan is not completed yet, wait for a while before checking again
            print("Scan is still in progress. Waiting...")
            time.sleep(60)  # Adjust the interval as needed

        else:
            # Handle other statuses as needed
            print(f"Unexpected scan status: {status}")
            break

    else:
        # Handle the case where the status cannot be retrieved
        print("Unable to retrieve scan status.")
        break