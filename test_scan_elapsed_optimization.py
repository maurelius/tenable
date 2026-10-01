"""Unit tests for tenable_io_scan_elapsed.py performance optimization."""

from unittest.mock import MagicMock
from tenable_io_scan_elapsed import process_scan_history


def test_process_scan_history_hoisted_details_call():
    """Verify io.scans.details is called once regardless of number of history records."""
    mock_io = MagicMock()

    # Mock scan details response
    mock_io.scans.details.return_value = {
        "settings": {"name": "Test Scan Hoist Optimization"}
    }

    # Mock 5 history entries for the scan
    mock_history_entries = [
        {"time_start": 1600000000, "time_end": 1600003600},
        {"time_start": 1600010000, "time_end": 1600011800},
        {"time_start": 1600020000, "time_end": 1600020900},
        {"time_start": 1600030000, "time_end": 1600033600},
        {"time_start": 1600040000, "time_end": 1600047200},
    ]
    mock_io.scans.history.return_value = mock_history_entries

    # Execute process_scan_history with scan_id=123
    process_scan_history(mock_io, 123)

    # Verify io.scans.details(123) was called EXACTLY ONCE (O(1) call, not O(N))
    mock_io.scans.details.assert_called_once_with(123)

    # Verify io.scans.history(123) was called once to fetch history list
    mock_io.scans.history.assert_called_once_with(123)
