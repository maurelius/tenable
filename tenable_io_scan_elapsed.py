"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed"""

import logging
import time
from time import localtime, strftime
from tenable_config import get_tenable_io_client

# Specify the scan ID for now instead of dynamically grabbing it
SCAN_ID = 0

# Set up logging
logging.basicConfig(level=logging.WARNING)


def check_scan_status(tio_client, target_scan_id):
    """Check and return status for the given scan ID."""
    try:
        return tio_client.scans.status(target_scan_id)
    except KeyError as e:
        print(f"KeyError: {e}. Possibly 'info' or 'status' key is missing in response.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error: {e}")
    return None


def process_scan_elapsed(tio_client, target_scan_id):
    """Process scan status and display scan duration/history details."""
    while True:
        status = check_scan_status(tio_client, target_scan_id)

        if status is None:
            print("Unable to retrieve scan status.")
            break

        print(f"Scan status: {status}")

        if status == 'completed':
            print("Scan is completed. Performing action...")
            # ⚡ BOLT Optimization: Hoist scan details API lookup outside history iteration loop.
            # This reduces API calls from O(N) to O(1) where N is history count.
            scan_details = tio_client.scans.details(target_scan_id)
            scan_name = scan_details.get("settings", {}).get("name", "Unknown Scan")

            for scan in tio_client.scans.history(target_scan_id):
                starttime = scan['time_start']
                endtime = scan['time_end']
                timediff = endtime - starttime
                hours, remainder = divmod(timediff, 3600)
                minutes, seconds = divmod(remainder, 60)
                print("Scan Name: ", scan_name)
                print("Scan Start: ", strftime('%Y-%m-%d %H:%M:%S', localtime(starttime)))
                print("Scan End: ", strftime('%Y-%m-%d %H:%M:%S', localtime(endtime)))
                print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")
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
    io = get_tenable_io_client()
    process_scan_elapsed(io, SCAN_ID)
