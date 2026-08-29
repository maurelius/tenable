"""Gets the start and end time of a scan and outputs the time elapsed."""
import logging
import time
from time import strftime, localtime
from tenable_config import get_tenable_io_client

# Specify the scan ID for now instead of dynamically grabbing it
DEFAULT_SCAN_ID = 0


def check_scan_status(io, target_scan_id):
    """Retrieves the status of the specified scan ID."""
    try:
        return io.scans.status(target_scan_id)
    except KeyError as exc:
        logging.warning("KeyError: %s. Possibly 'info' or 'status' key missing.", exc)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logging.error("Error retrieving scan status: %s", exc)
    return None


def print_scan_elapsed_history(io, target_scan_id):
    """Fetches scan details once and prints elapsed time for each history entry."""
    # Optimization: Hoist scan details lookup outside the loop to eliminate O(N) redundant API calls
    details = io.scans.details(target_scan_id)
    scan_name = details.get("settings", {}).get("name", f"Scan {target_scan_id}")

    for history_entry in io.scans.history(target_scan_id):
        starttime = history_entry['time_start']
        endtime = history_entry['time_end']
        timediff = endtime - starttime
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)

        print("Scan Name: ", scan_name)
        print("Scan Start: ", strftime('%Y-%m-%d %H:%M:%S', localtime(starttime)))
        print("Scan End: ", strftime('%Y-%m-%d %H:%M:%S', localtime(endtime)))
        print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")


def process_scan_elapsed(io, target_scan_id, poll_interval=60):
    """Monitors scan status until completion or unexpected status."""
    while True:
        status = check_scan_status(io, target_scan_id)

        if status is None:
            print("Unable to retrieve scan status.")
            break

        print(f"Scan status: {status}")

        if status == 'completed':
            print("Scan is completed. Performing action...")
            print_scan_elapsed_history(io, target_scan_id)
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
    logging.basicConfig(level=logging.WARNING)
    client = get_tenable_io_client()
    process_scan_elapsed(client, DEFAULT_SCAN_ID)
