"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs elapsed time."""

import logging
import time
from time import localtime, strftime
from tenable_config import get_tenable_io_client

# Specify default scan ID
DEFAULT_SCAN_ID = 0

# Set up logging
logging.basicConfig(level=logging.WARNING)


def check_scan_status(target_scan_id, io_client=None):
    """Checks the status of a scan."""
    client = io_client or get_tenable_io_client()
    try:
        scan_info = client.scans.status(target_scan_id)
        return scan_info
    except KeyError as e:
        print(f"KeyError: {e}. Possibly 'info' or 'status' key is missing in response.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error: {e}")
    return None


def process_completed_scan(io_client, target_scan_id):
    """Outputs scan duration details for all historical runs of a completed scan."""
    print("Scan is completed. Performing action...")
    # ⚡ BOLT Optimization: Fetch scan details once outside the history loop.
    # Hoisting io.scans.details reduces API network overhead from O(N) to O(1).
    details = io_client.scans.details(target_scan_id)
    scan_name = details.get("settings", {}).get("name", "")

    for scan in io_client.scans.history(target_scan_id):
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
    """Main loop for monitoring scan status until completion."""
    io_client = get_tenable_io_client()
    while True:
        status = check_scan_status(DEFAULT_SCAN_ID, io_client=io_client)

        if status is not None:
            print(f"Scan status: {status}")

            if status == 'completed':
                process_completed_scan(io_client, DEFAULT_SCAN_ID)
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
