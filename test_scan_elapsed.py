"""test_scan_elapsed.py: Unit tests for tenable_io_scan_elapsed module."""

from unittest.mock import MagicMock
from tenable_io_scan_elapsed import process_scan_elapsed


def test_process_scan_elapsed_hoists_scan_details_call():
    """Verify that scans.details is called exactly once when processing multiple history records."""
    mock_client = MagicMock()
    mock_client.scans.status.return_value = 'completed'
    mock_client.scans.details.return_value = {'settings': {'name': 'Test Scan'}}
    mock_client.scans.history.return_value = [
        {'time_start': 1000, 'time_end': 2000},
        {'time_start': 3000, 'time_end': 4000},
        {'time_start': 5000, 'time_end': 6000},
    ]

    process_scan_elapsed(mock_client, 1234)

    # Verify status was checked
    mock_client.scans.status.assert_called_once_with(1234)

    # Verify details was called exactly ONCE (hoisted outside loop)
    mock_client.scans.details.assert_called_once_with(1234)

    # Verify history was fetched once
    mock_client.scans.history.assert_called_once_with(1234)
