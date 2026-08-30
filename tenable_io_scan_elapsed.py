"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed"""

# Import modules
import logging
import time
from time import strftime, localtime
from tenable_config import get_tenable_io_client

# Default scan ID
DEFAULT_SCAN_ID = 0


def check_scan_status(tio, target_scan_id):
    """Checks and returns the status of the specified scan_id."""
    try:
        return tio.scans.status(target_scan_id)
    except KeyError as e:
        print(f"KeyError: {e}. Possibly 'info' or 'status' key is missing in the response.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error: {e}")
    return None


def print_scan_history(tio, target_scan_id):
    """Fetches scan history and prints elapsed time for each historical run.

    Performance Optimization: Hoisting `tio.scans.details(target_scan_id)`
    outside the history iteration loop reduces network API requests from O(N)
    to O(1), preventing redundant network calls for each history record.
    """
    scan_details = tio.scans.details(target_scan_id)
    scan_name = scan_details.get("settings", {}).get("name", f"Scan {target_scan_id}")

    for scan in tio.scans.history(target_scan_id):
        starttime = scan['time_start']
        endtime = scan['time_end']
        timediff = endtime - starttime
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"Scan Name: {scan_name}")
        print(f"Scan Start: {strftime('%Y-%m-%d %H:%M:%S', localtime(starttime))}")
        print(f"Scan End: {strftime('%Y-%m-%d %H:%M:%S', localtime(endtime))}")
        print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")


def monitor_scan(tio, target_scan_id):
    """Monitors the scan until completion and prints historical timing details."""
    while True:
        status = check_scan_status(tio, target_scan_id)

        if status is None:
            print("Unable to retrieve scan status.")
            break

        print(f"Scan status: {status}")

        if status == 'completed':
            print("Scan is completed. Performing action...")
            print_scan_history(tio, target_scan_id)
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


def main():
    """Main execution entry point."""
    logging.basicConfig(level=logging.WARNING)
    tio = get_tenable_io_client()
    monitor_scan(tio, DEFAULT_SCAN_ID)


if __name__ == '__main__':
    main()
