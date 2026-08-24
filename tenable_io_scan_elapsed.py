"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed"""

import logging
import time
from time import localtime, strftime
from tenable_config import get_tenable_io_client

# Set up logging
logging.basicConfig(level=logging.WARNING)

# Default scan ID for execution
SCAN_ID = 0000


def check_scan_status(io_client, scan_id_val):
    """Retrieves the status of a specified scan."""
    try:
        return io_client.scans.status(scan_id_val)
    except KeyError as err:
        logging.error("KeyError: %s. Possibly 'info' or 'status' key is missing.", err)
    except Exception as err:  # pylint: disable=broad-exception-caught
        logging.error("Error retrieving status: %s", err)
    return None


def process_scan_history(io_client, scan_id_val):
    """Processes scan history and prints elapsed time for each run.

    BOLT OPTIMIZATION: Hoisted `io.scans.details(scan_id)` outside the history loop.
    Fetching scan details once before iterating history records reduces API network calls
    from O(N) to O(1) where N is the number of historical scan runs.
    """
    scan_details = io_client.scans.details(scan_id_val)
    settings = scan_details.get("settings", {})
    if isinstance(settings, dict):
        scan_name = settings.get("name", "Unknown Scan")
    else:
        scan_name = "Unknown Scan"

    for scan_run in io_client.scans.history(scan_id_val):
        starttime = scan_run['time_start']
        endtime = scan_run['time_end']
        timediff = endtime - starttime
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)

        print("Scan Name: ", scan_name)
        print("Scan Start: ", strftime('%Y-%m-%d %H:%M:%S', localtime(starttime)))
        print("Scan End: ", strftime('%Y-%m-%d %H:%M:%S', localtime(endtime)))
        print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")


def main():
    """Monitors scan status until completion and prints elapsed time statistics."""
    io_client = get_tenable_io_client()

    while True:
        status = check_scan_status(io_client, SCAN_ID)

        if status is None:
            print("Unable to retrieve scan status.")
            break

        print(f"Scan status: {status}")

        if status == 'completed':
            print("Scan is completed. Performing action...")
            process_scan_history(io_client, SCAN_ID)
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
    main()
