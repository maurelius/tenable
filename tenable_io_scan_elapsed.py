"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed"""

import logging
import time
from time import strftime, localtime
from tenable_config import get_tenable_io_client

# Set up logging
logging.basicConfig(level=logging.WARNING)

# Default scan ID for execution
DEFAULT_SCAN_ID = 0


def check_scan_status(io_client, target_scan_id):
    """Check and return the status of a specific scan."""
    try:
        scan_status = io_client.scans.status(target_scan_id)
        return scan_status
    except KeyError as exc:
        logging.warning("KeyError: %s. Possibly 'info' or 'status' key is missing.", exc)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logging.warning("Error retrieving status: %s", exc)
    return None


def process_scan_history(io_client, target_scan_id):
    """Process scan history and display start, end, and total time elapsed."""
    # ⚡ BOLT Optimization: Hoist scan details API call outside the history iteration loop.
    # The scan_id metadata does not change per history entry. Hoisting this call reduces
    # API network overhead from O(N) redundant HTTP requests to O(1).
    scan_details = io_client.scans.details(target_scan_id)
    scan_name = scan_details.get("settings", {}).get("name", {})

    for scan in io_client.scans.history(target_scan_id):
        starttime = scan['time_start']
        endtime = scan['time_end']
        timediff = endtime - starttime
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)
        print("Scan Name: ", scan_name)
        print("Scan Start: ", strftime('%Y-%m-%d %H:%M:%S', localtime(starttime)))
        print("Scan End: ", strftime('%Y-%m-%d %H:%M:%S', localtime(endtime)))
        print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")


def monitor_scan(io_client, target_scan_id):
    """Monitor scan status until completion or unexpected status."""
    while True:
        status = check_scan_status(io_client, target_scan_id)

        if status is None:
            print("Unable to retrieve scan status.")
            break

        print(f"Scan status: {status}")

        if status == 'completed':
            print("Scan is completed. Performing action...")
            process_scan_history(io_client, target_scan_id)
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
    monitor_scan(io, DEFAULT_SCAN_ID)
