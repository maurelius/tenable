"""tenable_io_scan_elapsed.py: Gets scan start and end time and outputs time elapsed."""

import logging
import time
from time import localtime, strftime
from tenable_config import get_tenable_io_client

# Set up logging
logging.basicConfig(level=logging.WARNING)

# Constant scan ID default
DEFAULT_SCAN_ID = 0


def check_scan_status(io_client, scan_id):
    """Retrieves the status of the specified scan."""
    try:
        return io_client.scans.status(scan_id)
    except KeyError as ex:
        print(f"KeyError: {ex}. Possibly 'info' or 'status' key is missing in response.")
    except Exception as ex:  # pylint: disable=broad-exception-caught
        print(f"Error: {ex}")
    return None


def process_scan_history(io_client, scan_id):
    """Fetches history and prints elapsed time for each historical run of a scan."""
    # ⚡ BOLT Optimization: Hoist scan details API call outside history loop.
    # Fetches scan name once instead of making O(N) redundant network API calls per run.
    details = io_client.scans.details(scan_id)
    scan_name = details.get("settings", {}).get("name", "")

    for history_item in io_client.scans.history(scan_id):
        starttime = history_item["time_start"]
        endtime = history_item["time_end"]
        timediff = endtime - starttime
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)

        start_formatted = strftime("%Y-%m-%d %H:%M:%S", localtime(starttime))
        end_formatted = strftime("%Y-%m-%d %H:%M:%S", localtime(endtime))

        print(f"Scan Name: {scan_name}")
        print(f"Scan Start: {start_formatted}")
        print(f"Scan End: {end_formatted}")
        print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")


def monitor_scan_elapsed(io_client, scan_id, poll_interval=60):
    """Polls scan status until completed and prints timing metrics."""
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
        status = check_scan_status(io_client, scan_id)

        if status is None:
            print("Unable to retrieve scan status.")
            break

        print(f"Scan status: {status}")

        if status == "completed":
            print("Scan is completed. Performing action...")
            process_scan_history(io_client, scan_id)
            break

        if status in in_progress_statuses:
            print("Scan is still in progress. Waiting...")
            time.sleep(poll_interval)
        else:
            print(f"Unexpected scan status: {status}")
            break


if __name__ == "__main__":
    io = get_tenable_io_client()
    monitor_scan_elapsed(io, DEFAULT_SCAN_ID)
