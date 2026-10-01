"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed"""

import logging
import time
from time import localtime, strftime
from tenable_config import get_tenable_io_client

# Set up logging
logging.basicConfig(level=logging.WARNING)

# Default scan ID
SCAN_ID = 0


def check_scan_status(io, scan_id):
    """Retrieves current status for a scan."""
    try:
        scan = io.scans.status(scan_id)
        return scan
    except KeyError as e:
        print(f"KeyError: {e}. Possibly 'info' or 'status' key is missing in the response.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error: {e}")
    return None


def process_scan_history(io, scan_id):
    """
    Processes and prints scan history.

    ⚡ BOLT Performance Optimization:
    Hoisting `io.scans.details(scan_id)` outside the `io.scans.history(scan_id)` loop.
    Previously, `io.scans.details(scan_id)` was called inside the history iteration loop,
    causing O(N) network calls for N history items to retrieve the static scan name.
    Retrieving details once outside the loop reduces network overhead from O(N) to O(1).
    """
    scan_details = io.scans.details(scan_id)
    scan_name = scan_details.get("settings", {}).get("name", "Unknown")

    for scan in io.scans.history(scan_id):
        starttime = scan["time_start"]
        endtime = scan["time_end"]
        timediff = endtime - starttime
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)

        print("Scan Name: ", scan_name)
        print("Scan Start: ", strftime("%Y-%m-%d %H:%M:%S", localtime(starttime)))
        print("Scan End: ", strftime("%Y-%m-%d %H:%M:%S", localtime(endtime)))
        print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")


def main():
    """Main execution loop for checking scan status and displaying elapsed scan durations."""
    io = get_tenable_io_client()

    while True:
        status = check_scan_status(io, SCAN_ID)

        if status is None:
            print("Unable to retrieve scan status.")
            break

        print(f"Scan status: {status}")

        if status == "completed":
            print("Scan is completed. Performing action...")
            process_scan_history(io, SCAN_ID)
            break

        if status in (
            "canceled",
            "empty",
            "importing",
            "paused",
            "pending",
            "processing",
            "quarantined",
            "running",
        ):
            print("Scan is still in progress. Waiting...")
            time.sleep(60)
        else:
            print(f"Unexpected scan status: {status}")
            break


if __name__ == "__main__":
    main()
