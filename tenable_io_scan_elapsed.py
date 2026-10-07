"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs time elapsed."""
import logging
import time
from time import localtime, strftime
from tenable_config import get_tenable_io_client

# Set up logging
logging.basicConfig(level=logging.WARNING)

SCAN_ID = 0000


def check_scan_status(tio_client, target_scan_id):
    """Check the current status of a scan by ID."""
    try:
        scan_status = tio_client.scans.status(target_scan_id)
        return scan_status
    except KeyError as exc:
        print(f"KeyError: {exc}. Possibly 'info' or 'status' key missing.")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"Error: {exc}")
    return None


def process_completed_scan(tio_client, target_scan_id):
    """Fetch scan history and output elapsed timing information for each run."""
    print("Scan is completed. Performing action...")
    # ⚡ BOLT Optimization: Hoist scan details lookup outside the history iteration loop.
    # Previously, io.scans.details(scan_id) was called inside the loop for every historical run,
    # resulting in O(N) network requests for static metadata. Hoisting it reduces network API calls
    # from O(N) to O(1).
    scan_details = tio_client.scans.details(target_scan_id)
    scan_name = scan_details.get("settings", {}).get("name", "")

    for history_entry in tio_client.scans.history(target_scan_id):
        starttime = history_entry['time_start']
        endtime = history_entry['time_end']
        timediff = endtime - starttime
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)
        print("Scan Name:", scan_name)
        print("Scan Start:", strftime('%Y-%m-%d %H:%M:%S', localtime(starttime)))
        print("Scan End:", strftime('%Y-%m-%d %H:%M:%S', localtime(endtime)))
        print(f"Total time elapsed: {hours}h {minutes}m {seconds}s")


def monitor_scan(tio_client, target_scan_id):
    """Monitor scan until completion or terminal state."""
    while True:
        status = check_scan_status(tio_client, target_scan_id)

        if status is None:
            print("Unable to retrieve scan status.")
            break

        print(f"Scan status: {status}")

        if status == 'completed':
            process_completed_scan(tio_client, target_scan_id)
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
    tio = get_tenable_io_client()
    monitor_scan(tio, SCAN_ID)


if __name__ == '__main__':
    main()
