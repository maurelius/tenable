"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed"""

import logging
import time
from time import localtime, strftime
from tenable_config import get_tenable_io_client

# Specify the scan ID for now instead of dynamically grabbing it
SCAN_ID = 0000

# Set up logging
logging.basicConfig(level=logging.WARNING)
# Bootstrap API connection
tio_client = get_tenable_io_client()

def check_scan_status(target_scan_id):
    """Checks and returns the status of the specified scan."""
    try:
        return tio_client.scans.status(target_scan_id)
    except KeyError as exc:
        print(f"KeyError: {exc}. Possibly 'info' or 'status' key is missing in response.")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"Error: {exc}")
    return None

def process_completed_scan(target_scan_id):
    """Processes scan history and prints start, end, and elapsed times."""
    print("Scan is completed. Performing action...")
    # Performance optimization: Hoist io.scans.details out of history loop.
    # Previously io.scans.details(target_scan_id) was called in every iteration,
    # causing O(N) network requests for N history records. Fetching it once reduces it to O(1).
    details = tio_client.scans.details(target_scan_id)
    scan_name = details.get("settings", {}).get("name", "Unknown")

    for scan_item in tio_client.scans.history(target_scan_id):
        starttime = scan_item['time_start']
        endtime = scan_item['time_end']
        timediff = endtime - starttime
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"Scan Name: {scan_name}")
        print(f"Scan Start: {strftime('%Y-%m-%d %H:%M:%S', localtime(starttime))}")
        print(f"Scan End: {strftime('%Y-%m-%d %H:%M:%S', localtime(endtime))}")
        print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")

def monitor_scan(target_scan_id):
    """Monitors scan until completion or terminal state."""
    while True:
        status = check_scan_status(target_scan_id)

        if status is None:
            print("Unable to retrieve scan status.")
            break

        print(f"Scan status: {status}")

        if status == 'completed':
            process_completed_scan(target_scan_id)
            break

        if status in (
            'canceled', 'empty', 'importing', 'paused',
            'pending', 'processing', 'quarantined', 'running'
        ):
            print("Scan is still in progress. Waiting...")
            time.sleep(60)
        else:
            print(f"Unexpected scan status: {status}")
            break

if __name__ == '__main__':
    monitor_scan(SCAN_ID)
