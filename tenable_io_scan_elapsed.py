"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed"""

# Import modules
import logging
import time
from time import strftime, localtime
from tenable_config import get_tenable_io_client

# Set up logging
logging.basicConfig(level=logging.WARNING)

# Specify the scan ID for now instead of dynamically grabbing it
SCAN_ID = 0

# Bootstrap API connection
io = get_tenable_io_client()


def check_scan_status(target_scan_id):
    """Check and return the status of the specified scan_id."""
    try:
        scan = io.scans.status(target_scan_id)
        return scan
    except KeyError as e:
        print(f"KeyError: {e}. Possibly 'info' or 'status' key is missing in the response.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error: {e}")
    return None


def print_scan_elapsed_times(target_scan_id):
    """Fetch scan details once and print elapsed times for all history entries."""
    # ⚡ BOLT Optimization: Fetch scan details once outside the history loop.
    # Previously, io.scans.details(target_scan_id) was called on every iteration of
    # io.scans.history(target_scan_id), causing N redundant network calls.
    scan_details = io.scans.details(target_scan_id)
    scan_name = scan_details.get("settings", {}).get("name", f"Scan {target_scan_id}")

    for scan in io.scans.history(target_scan_id):
        starttime = scan['time_start']
        endtime = scan['time_end']
        timediff = endtime - starttime
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)
        print("Scan Name: ", scan_name)
        print("Scan Start: ", strftime('%Y-%m-%d %H:%M:%S', localtime(starttime)))
        print("Scan End: ", strftime('%Y-%m-%d %H:%M:%S', localtime(endtime)))
        print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")


def main():
    """Main loop to monitor scan completion and print timing information."""
    while True:
        status = check_scan_status(SCAN_ID)

        if status is not None:
            print(f"Scan status: {status}")

            if status == 'completed':
                print("Scan is completed. Performing action...")
                print_scan_elapsed_times(SCAN_ID)
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
        else:
            print("Unable to retrieve scan status.")
            break


if __name__ == '__main__':
    main()
