"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed.

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

# Specify the scan ID for now instead of dynamically grabbing it
DEFAULT_SCAN_ID = 0


def check_scan_status(io, target_scan_id):
    """Retrieves the status of the specified scan."""
    try:
        return io.scans.status(target_scan_id)
    except KeyError as exc:
        print(f"KeyError: {exc}. Possibly 'info' or 'status' key is missing in the response.")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"Error: {exc}")
    return None


def process_scan_history(io, target_scan_id):
    """Fetches scan details and history, computing elapsed times for each run.

    ⚡ BOLT Optimization: Hoisting parent scan metadata lookup (io.scans.details)
    outside of the scan history iteration loop reduces network API requests from
    O(N) to O(1), where N is the number of historical scan runs.
    """
    scan_details = io.scans.details(target_scan_id)
    scan_name = scan_details.get("settings", {}).get("name", "Unknown Scan")

    history_entries = []
    for hist in io.scans.history(target_scan_id):
        starttime = hist['time_start']
        endtime = hist['time_end']
        timediff = endtime - starttime
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)
        start_str = strftime('%Y-%m-%d %H:%M:%S', localtime(starttime))
        end_str = strftime('%Y-%m-%d %H:%M:%S', localtime(endtime))

        print("Scan Name: ", scan_name)
        print("Scan Start: ", start_str)
        print("Scan End: ", end_str)
        print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")

        history_entries.append({
            "name": scan_name,
            "start": start_str,
            "end": end_str,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "timediff": timediff
        })

    return scan_name, history_entries


def monitor_scan_elapsed(io, target_scan_id, poll_interval=60):
    """Monitors the status of a scan until completion, then processes elapsed times."""
    while True:
        status = check_scan_status(io, target_scan_id)

        if status is None:
            print("Unable to retrieve scan status.")
            break

        print(f"Scan status: {status}")

        if status == 'completed':
            print("Scan is completed. Performing action...")
            process_scan_history(io, target_scan_id)
            break

        if status in (
            'canceled', 'empty', 'importing', 'paused', 'pending',
            'processing', 'quarantined', 'running'
        ):
            print("Scan is still in progress. Waiting...")
            time.sleep(poll_interval)
        else:
            print(f"Unexpected scan status: {status}")
            break


def main():
    """Main execution entry point."""
    io = get_tenable_io_client()
    monitor_scan_elapsed(io, DEFAULT_SCAN_ID)


if __name__ == '__main__':
    main()
