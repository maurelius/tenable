"""
tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed.

TODO:
- Dynamically grab scan_id from user input by name
- Loop through multiple scans if given a list []
"""

import logging
import time
from time import localtime, strftime
from tenable_config import get_tenable_io_client

# Set up logging
logging.basicConfig(level=logging.WARNING)

SCAN_ID = 0000


def check_scan_status(io_client, target_scan_id):
    """Check the status of a scan given its ID."""
    try:
        return io_client.scans.status(target_scan_id)
    except KeyError as exc:
        print(f"KeyError: {exc}. Possibly 'info' or 'status' key is missing in the response.")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"Error: {exc}")
    return None


def process_scan_history(io_client, target_scan_id):
    """Process and print scan history and elapsed time.

    ⚡ BOLT Optimization: Hoisting parent scan metadata lookup (io.scans.details)
    outside the history iteration loop reduces network API overhead from O(N) to O(1).
    """
    scan_details = io_client.scans.details(target_scan_id)
    scan_name = scan_details.get("settings", {}).get("name", "Unknown")

    for scan in io_client.scans.history(target_scan_id):
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
    """Main execution loop for checking scan status and processing scan history."""
    io_client = get_tenable_io_client()

    while True:
        status = check_scan_status(io_client, SCAN_ID)

        if status is not None:
            print(f"Scan status: {status}")

            if status == "completed":
                print("Scan is completed. Performing action...")
                process_scan_history(io_client, SCAN_ID)
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
        else:
            print("Unable to retrieve scan status.")
            break


if __name__ == "__main__":
    main()
