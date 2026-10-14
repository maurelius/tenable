"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs time elapsed"""

import logging
import time
from time import localtime, strftime
from tenable_config import get_tenable_io_client

# Specify default scan ID (to be dynamically supplied in future versions)
DEFAULT_SCAN_ID = 0

# Set up logging
logging.basicConfig(level=logging.WARNING)


def check_scan_status(io_client, target_scan_id):
    """Check the current execution status of a specified scan ID."""
    try:
        return io_client.scans.status(target_scan_id)
    except KeyError as exc:
        print(f"KeyError: {exc}. Possibly 'info' or 'status' key is missing in response.")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"Error checking scan status: {exc}")
    return None


def print_scan_history(io_client, target_scan_id):
    """Print details and elapsed execution time for all historical runs of a scan.

    Optimization: Hoist the io.scans.details lookup outside the scan history loop.
    Fetching scan details once before looping over history records reduces API network calls
    from O(N) to O(1) where N is the number of history items.
    """
    scan_details = io_client.scans.details(target_scan_id)
    scan_name = scan_details.get("settings", {}).get("name", "")

    for scan in io_client.scans.history(target_scan_id):
        starttime = scan["time_start"]
        endtime = scan["time_end"]
        timediff = endtime - starttime
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)

        print("Scan Name:", scan_name)
        print("Scan Start:", strftime("%Y-%m-%d %H:%M:%S", localtime(starttime)))
        print("Scan End:", strftime("%Y-%m-%d %H:%M:%S", localtime(endtime)))
        print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")


def monitor_scan(io_client, target_scan_id, poll_interval=60):
    """Poll scan status until completion or unexpected status, then report elapsed times."""
    in_progress_statuses = (
        "canceled",
        "empty",
        "importing",
        "paused",
        "pending",
        "processing",
        "quarantined",
        "running",
    )

    while True:
        status = check_scan_status(io_client, target_scan_id)

        if status is None:
            print("Unable to retrieve scan status.")
            break

        print(f"Scan status: {status}")

        if status == "completed":
            print("Scan is completed. Performing action...")
            print_scan_history(io_client, target_scan_id)
            break

        if status in in_progress_statuses:
            print("Scan is still in progress. Waiting...")
            time.sleep(poll_interval)
        else:
            print(f"Unexpected scan status: {status}")
            break


if __name__ == "__main__":
    io = get_tenable_io_client()
    monitor_scan(io, DEFAULT_SCAN_ID)
