"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed"""

import logging
import time
from time import localtime, strftime
from tenable_config import get_tenable_io_client

# Specify the scan ID for now instead of dynamically grabbing it
SCAN_ID = 0000

# Set up logging
logging.basicConfig(level=logging.WARNING)


def check_scan_status(io_client, target_scan_id):
    """Retrieves status for a given scan ID."""
    try:
        return io_client.scans.status(target_scan_id)
    except KeyError as exc:
        print(f"KeyError: {exc}. Possibly 'info' or 'status' key is missing in response.")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"Error: {exc}")
    return None


def process_scan_history(io_client, target_scan_id):
    """Prints elapsed time details for all history runs of a completed scan."""
    # BOLT OPTIMIZATION: Hoist scan details lookup outside of history iteration loop.
    # Look up scan name once instead of calling io.scans.details inside every iteration.
    # Reduces API network overhead from O(N) to O(1) where N is number of history records.
    details = io_client.scans.details(target_scan_id)
    scan_name = details.get("settings", {}).get("name")

    for history_item in io_client.scans.history(target_scan_id):
        starttime = history_item['time_start']
        endtime = history_item['time_end']
        timediff = endtime - starttime
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)
        print("Scan Name: ", scan_name)
        print("Scan Start: ", strftime('%Y-%m-%d %H:%M:%S', localtime(starttime)))
        print("Scan End: ", strftime('%Y-%m-%d %H:%M:%S', localtime(endtime)))
        print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")


def monitor_and_report_scan(io_client, target_scan_id):
    """Monitors scan status in a loop until completion or unexpected status."""
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
    monitor_and_report_scan(io, SCAN_ID)
