"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed"""

import logging
import time
from time import localtime, strftime
from tenable_config import get_tenable_io_client

# Specify the scan ID for now instead of dynamically grabbing it
DEFAULT_SCAN_ID = 0000


def check_scan_status(tio, scan_id):
    """Retrieve current status of a scan by scan_id."""
    try:
        return tio.scans.status(scan_id)
    except KeyError as exc:
        logging.warning("KeyError checking status for scan %s: %s", scan_id, exc)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logging.error("Error checking scan status: %s", exc)
    return None


def _format_history_entry(scan_name, item):
    """Calculate elapsed time and print/format history entry."""
    timediff = item["time_end"] - item["time_start"]
    hours, remainder = divmod(timediff, 3600)
    minutes, seconds = divmod(remainder, 60)

    start_str = strftime("%Y-%m-%d %H:%M:%S", localtime(item["time_start"]))
    end_str = strftime("%Y-%m-%d %H:%M:%S", localtime(item["time_end"]))
    elapsed_str = f"{hours}h {minutes}m {seconds}s"

    print("Scan Name: ", scan_name)
    print("Scan Start: ", start_str)
    print("Scan End: ", end_str)
    print(f"Total time elapsed: {elapsed_str}")

    return {
        "scan_name": scan_name,
        "start": start_str,
        "end": end_str,
        "elapsed": elapsed_str
    }


def process_scan_history(tio, scan_id):
    """Fetch scan details and output elapsed time for each historical execution.

    ⚡ BOLT Optimization: Hoist parent scan details lookup outside the loop.
    Previously, io.scans.details(scan_id) was called inside the history loop,
    making O(N) redundant network calls for N historical runs.
    Extracting scan details once reduces API calls from O(N) to O(1).
    """
    scan_details = tio.scans.details(scan_id)
    scan_name = scan_details.get("settings", {}).get("name", "")
    history_runs = tio.scans.history(scan_id)

    return [_format_history_entry(scan_name, item) for item in history_runs]


def monitor_scan(tio, scan_id, poll_interval=60):
    """Poll scan status until completion or termination."""
    in_progress_statuses = {
        "canceled", "empty", "importing", "paused", "pending",
        "processing", "quarantined", "running"
    }

    while True:
        status = check_scan_status(tio, scan_id)

        if status is None:
            print("Unable to retrieve scan status.")
            break

        print(f"Scan status: {status}")

        if status == "completed":
            print("Scan is completed. Performing action...")
            process_scan_history(tio, scan_id)
            break

        if status in in_progress_statuses:
            print("Scan is still in progress. Waiting...")
            time.sleep(poll_interval)
        else:
            print(f"Unexpected scan status: {status}")
            break


def main():
    """Main entry point to execute scan monitoring."""
    logging.basicConfig(level=logging.WARNING)
    tio = get_tenable_io_client()
    monitor_scan(tio, DEFAULT_SCAN_ID)


if __name__ == "__main__":
    main()
