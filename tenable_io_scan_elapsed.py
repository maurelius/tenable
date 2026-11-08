"""tenable_io_scan_elapsed.py: Gets the start and end time of a scan and outputs the time elapsed"""

# Import modules
import logging
import time
from time import localtime, strftime
from tenable_config import get_tenable_io_client

# Set up logging
logging.basicConfig(level=logging.WARNING)

# Specify the scan ID for now instead of dynamically grabbing it
SCAN_ID = 0000


def check_scan_status(io_client, target_scan_id):
    """
    Check the current status of a scan by ID.

    Args:
        io_client: TenableIO client instance.
        target_scan_id: Scan identifier.

    Returns:
        str or None: Current scan status or None on error.
    """
    try:
        scan = io_client.scans.status(target_scan_id)
        return scan
    except KeyError as exc:
        logging.error("KeyError: %s. Possibly 'info' or 'status' key is missing.", exc)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logging.error("Error: %s", exc)
    return None


def display_scan_history(io_client, target_scan_id):
    """
    Fetch and display elapsed time for all historical executions of a scan.

    ⚡ BOLT Optimization:
    Hoisting io_client.scans.details(target_scan_id) outside of the
    io_client.scans.history(target_scan_id) loop reduces API calls from O(N) to O(1),
    preventing N redundant network roundtrips for fetching the static scan name.

    Args:
        io_client: TenableIO client instance.
        target_scan_id: Scan identifier.

    Returns:
        list[dict]: List of parsed history records with elapsed timing information.
    """
    # ⚡ BOLT Optimization: Fetch scan details once before iterating over history records
    details = io_client.scans.details(target_scan_id)
    scan_name = details.get("settings", {}).get("name", "Unknown")

    history_records = []
    for hist in io_client.scans.history(target_scan_id):
        starttime = hist["time_start"]
        endtime = hist["time_end"]
        timediff = endtime - starttime
        hours, remainder = divmod(timediff, 3600)
        minutes, seconds = divmod(remainder, 60)

        record = {
            "name": scan_name,
            "start": strftime("%Y-%m-%d %H:%M:%S", localtime(starttime)),
            "end": strftime("%Y-%m-%d %H:%M:%S", localtime(endtime)),
            "elapsed_str": f"{hours}h {minutes}m {seconds}s",
            "timediff": timediff,
        }
        history_records.append(record)

        print(f"Scan Name: {scan_name}")
        print(f"Scan Start: {record['start']}")
        print(f"Scan End: {record['end']}")
        print(f"Total time elapsed: {record['elapsed_str']}")

    return history_records


def monitor_scan(io_client, target_scan_id):
    """Monitor scan status and print elapsed time upon completion."""
    while True:
        status = check_scan_status(io_client, target_scan_id)

        if status is None:
            print("Unable to retrieve scan status.")
            break

        print(f"Scan status: {status}")

        if status == "completed":
            print("Scan is completed. Performing action...")
            display_scan_history(io_client, target_scan_id)
            break

        if status in (
            "canceled",
            "empty",
            "importing",
            "paused",
            "pending",
            "processing",
            "quarantined",
            "running",
        ):
            print("Scan is still in progress. Waiting...")
            time.sleep(60)
        else:
            print(f"Unexpected scan status: {status}")
            break


if __name__ == "__main__":
    # Bootstrap API connection
    io = get_tenable_io_client()
    monitor_scan(io, SCAN_ID)
