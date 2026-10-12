"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed"""

import logging
import time
from time import strftime, localtime
from tenable_config import get_tenable_io_client

# Specify the scan ID for now instead of dynamically grabbing it
SCAN_ID = 0000

# Set up logging
logging.basicConfig(level=logging.WARNING)


def check_scan_status(tio_client, target_scan_id):
    """Retrieves the current status of the scan."""
    try:
        return tio_client.scans.status(target_scan_id)
    except KeyError as e:
        print(f"KeyError: {e}. Possibly 'info' or 'status' key is missing in response.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error: {e}")
    return None


def process_completed_scan(tio_client, target_scan_id):
    """
    Fetches scan details and prints elapsed time for all historical executions.
    ⚡ BOLT Optimization: Hoisting tio_client.scans.details(target_scan_id) outside the loop
    reduces API requests from O(N) to O(1) for N historical scan runs.
    """
    scan_details = tio_client.scans.details(target_scan_id)
    scan_name = scan_details.get("settings", {}).get("name", f"Scan {target_scan_id}")

    for scan in tio_client.scans.history(target_scan_id):
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
    """Main execution loop for checking scan status until completion."""
    tio = get_tenable_io_client()

    while True:
        status = check_scan_status(tio, SCAN_ID)

        if status is not None:
            print(f"Scan status: {status}")

            if status == 'completed':
                print("Scan is completed. Performing action...")
                process_completed_scan(tio, SCAN_ID)
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
