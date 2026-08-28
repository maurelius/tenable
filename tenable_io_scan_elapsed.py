"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed"""

import logging
import time
from time import strftime, localtime
from tenable_config import get_tenable_io_client

# Specify the scan ID for now instead of dynamically grabbing it
SCAN_ID = 0000

# Set up logging
logging.basicConfig(level=logging.WARNING)

def check_scan_status(io, scan_id_param):
    """Check the status of a scan given its ID."""
    try:
        return io.scans.status(scan_id_param)
    except KeyError as e:
        print(f"KeyError: {e}. Possibly 'info' or 'status' key is missing in the response.")
    except Exception as e:
        print(f"Error: {e}")
    return None

def process_scan_elapsed(io, scan_id_param):
    """Process elapsed times for all history records of a scan."""
    # ⚡ BOLT Optimization: Hoist parent scan details lookups outside the scan history loop.
    # This reduces network requests from O(N) to O(1) where N is the number of history items.
    details = io.scans.details(scan_id_param)
    scan_name = details.get("settings", {}).get("name", f"Scan {scan_id_param}")

    for scan_hist in io.scans.history(scan_id_param):
        starttime = scan_hist['time_start']
        endtime = scan_hist['time_end']
        timediff = endtime - starttime
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)
        print("Scan Name: ", scan_name)
        print("Scan Start: ", strftime('%Y-%m-%d %H:%M:%S', localtime(starttime)))
        print("Scan End: ", strftime('%Y-%m-%d %H:%M:%S', localtime(endtime)))
        print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")

def main():
    """Main execution loop to monitor scan status and output elapsed history."""
    io = get_tenable_io_client()
    while True:
        status = check_scan_status(io, SCAN_ID)

        if status is None:
            print("Unable to retrieve scan status.")
            break

        print(f"Scan status: {status}")

        if status == 'completed':
            print("Scan is completed. Performing action...")
            process_scan_elapsed(io, SCAN_ID)
            break

        if status in ('canceled', 'empty', 'importing', 'paused', 'pending',
                      'processing', 'quarantined', 'running'):
            print("Scan is still in progress. Waiting...")
            time.sleep(60)
        else:
            print(f"Unexpected scan status: {status}")
            break

if __name__ == '__main__':
    main()
