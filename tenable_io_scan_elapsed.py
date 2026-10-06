"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed"""

import logging
import time
from time import localtime, strftime
from tenable_config import get_tenable_io_client

# Set up logging
logging.basicConfig(level=logging.WARNING)

# Specify the scan ID for now instead of dynamically grabbing it
SCAN_ID = 0


def check_scan_status(target_scan_id, io_client=None):
    """Retrieves the status of a given scan ID."""
    if io_client is None:
        io_client = get_tenable_io_client()
    try:
        return io_client.scans.status(target_scan_id)
    except KeyError as err:
        logging.warning("KeyError: %s. Possibly 'info' or 'status' key missing.", err)
    except Exception as err:  # pylint: disable=broad-exception-caught
        logging.error("Error retrieving scan status: %s", err)
    return None


def process_scan_history(target_scan_id, io_client=None):
    """
    Fetches history for a completed scan and prints duration stats.
    ⚡ BOLT Optimization: Hoist scan details lookup outside history loop
    to reduce API calls from O(N) to O(1).
    """
    if io_client is None:
        io_client = get_tenable_io_client()

    scan_details = io_client.scans.details(target_scan_id)
    scan_name = scan_details.get("settings", {}).get("name", "Unknown")

    for scan in io_client.scans.history(target_scan_id):
        starttime = scan.get('time_start', 0)
        endtime = scan.get('time_end', 0)
        timediff = endtime - starttime
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)
        print("Scan Name: ", scan_name)
        print("Scan Start: ", strftime('%Y-%m-%d %H:%M:%S', localtime(starttime)))
        print("Scan End: ", strftime('%Y-%m-%d %H:%M:%S', localtime(endtime)))
        print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")


def main():
    """Main execution loop for checking scan status until completion."""
    io_client = get_tenable_io_client()
    while True:
        status = check_scan_status(SCAN_ID, io_client=io_client)

        if status is None:
            print("Unable to retrieve scan status.")
            break

        print(f"Scan status: {status}")

        if status == 'completed':
            print("Scan is completed. Performing action...")
            process_scan_history(SCAN_ID, io_client=io_client)
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
