"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs time elapsed."""
import logging
import time
from time import strftime, localtime
from tenable_config import get_tenable_io_client

# Specify the scan ID for now instead of dynamically grabbing it
SCAN_ID = 0

# Set up logging
logging.basicConfig(level=logging.WARNING)


def check_scan_status(tio_client, target_scan_id):
    """Checks the status of a specific scan ID using the provided client."""
    try:
        return tio_client.scans.status(target_scan_id)
    except KeyError as err:
        print(f"KeyError: {err}. Possibly 'info' or 'status' key missing.")
    except Exception as err:  # pylint: disable=broad-exception-caught
        print(f"Error checking status: {err}")
    return None


def print_scan_history_elapsed(tio_client, target_scan_id):
    """Fetches scan details once and prints elapsed time for each historical run."""
    # ⚡ BOLT OPTIMIZATION: Hoist io.scans.details out of the history loop.
    # Previously, io.scans.details(scan_id) was called inside the loop for every
    # history entry, causing N redundant network calls. Fetching scan details once
    # reduces API calls from O(N) to O(1).
    scan_details = tio_client.scans.details(target_scan_id)
    scan_name = scan_details.get("settings", {}).get("name", f"Scan {target_scan_id}")

    for hist_record in tio_client.scans.history(target_scan_id):
        starttime = hist_record['time_start']
        endtime = hist_record['time_end']
        timediff = endtime - starttime
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)

        print("Scan Name: ", scan_name)
        print("Scan Start: ", strftime('%Y-%m-%d %H:%M:%S', localtime(starttime)))
        print("Scan End: ", strftime('%Y-%m-%d %H:%M:%S', localtime(endtime)))
        print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")


def monitor_scan_until_complete(tio_client, target_scan_id, poll_interval=60):
    """Monitors scan status in a loop until complete or ended."""
    while True:
        status = check_scan_status(tio_client, target_scan_id)

        if status is None:
            print("Unable to retrieve scan status.")
            break

        print(f"Scan status: {status}")

        if status == 'completed':
            print("Scan is completed. Performing action...")
            print_scan_history_elapsed(tio_client, target_scan_id)
            break

        if status in (
            'canceled', 'empty', 'importing', 'paused',
            'pending', 'processing', 'quarantined', 'running'
        ):
            print("Scan is still in progress. Waiting...")
            time.sleep(poll_interval)
        else:
            print(f"Unexpected scan status: {status}")
            break


if __name__ == '__main__':
    io = get_tenable_io_client()
    monitor_scan_until_complete(io, SCAN_ID)
