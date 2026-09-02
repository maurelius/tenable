"""
tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed
"""

import logging
import time
from time import strftime, localtime
from tenable_config import get_tenable_io_client

# Set up logging
logging.basicConfig(level=logging.WARNING)


def check_scan_status(io_client, target_scan_id):
    """Checks the status of a scan given its ID."""
    try:
        return io_client.scans.status(target_scan_id)
    except KeyError as e:
        print(f"KeyError: {e}. Possibly 'info' or 'status' key is missing in the response.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error: {e}")
    return None


def process_completed_scan(io_client, target_scan_id):
    """
    Processes history for a completed scan and prints duration information.

    ⚡ BOLT Optimization: Hoist io.scans.details(target_scan_id) call outside the history loop.
    Fetching scan details once before looping through history entries reduces network API
    calls from O(N) to O(1), where N is the number of historical scan runs.
    """
    # Fetch scan details once outside the loop
    scan_details = io_client.scans.details(target_scan_id)
    scan_name = scan_details.get("settings", {}).get("name", {})

    history_records = io_client.scans.history(target_scan_id)
    results = []

    for scan in history_records:
        timediff = scan['time_end'] - scan['time_start']
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)

        fmt_start = strftime('%Y-%m-%d %H:%M:%S', localtime(scan['time_start']))
        fmt_end = strftime('%Y-%m-%d %H:%M:%S', localtime(scan['time_end']))

        print("Scan Name: ", scan_name)
        print("Scan Start: ", fmt_start)
        print("Scan End: ", fmt_end)
        print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")

        results.append({
            "name": scan_name,
            "start": fmt_start,
            "end": fmt_end,
            "elapsed": (hours, minutes, seconds)
        })

    return results


def monitor_and_report_scan(io_client, target_scan_id, poll_interval=60):
    """Monitors scan status until completed, then outputs elapsed time."""
    while True:
        status = check_scan_status(io_client, target_scan_id)

        if status is not None:
            print(f"Scan status: {status}")

            if status == 'completed':
                print("Scan is completed. Performing action...")
                return process_completed_scan(io_client, target_scan_id)

            if status in ('canceled', 'empty', 'importing', 'paused', 'pending',
                          'processing', 'quarantined', 'running'):
                print("Scan is still in progress. Waiting...")
                time.sleep(poll_interval)
            else:
                print(f"Unexpected scan status: {status}")
                break
        else:
            print("Unable to retrieve scan status.")
            break

    return None


if __name__ == "__main__":
    # Specify the scan ID for now instead of dynamically grabbing it
    SCAN_ID = 0000
    # Bootstrap API connection
    IO_CLIENT = get_tenable_io_client()
    monitor_and_report_scan(IO_CLIENT, SCAN_ID)
