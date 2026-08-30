"""Unit tests for tenable_io_scan_elapsed.py."""

from unittest.mock import MagicMock
from tenable_io_scan_elapsed import check_scan_status, print_scan_history, monitor_scan


def test_check_scan_status_success():
    """Tests check_scan_status returns status when scan status call succeeds."""
    mock_tio = MagicMock()
    mock_tio.scans.status.return_value = 'completed'

    status = check_scan_status(mock_tio, 123)
    assert status == 'completed'
    mock_tio.scans.status.assert_called_once_with(123)


def test_check_scan_status_key_error():
    """Tests check_scan_status handles KeyError gracefully."""
    mock_tio = MagicMock()
    mock_tio.scans.status.side_effect = KeyError("status")

    status = check_scan_status(mock_tio, 123)
    assert status is None


def test_print_scan_history_hoisted_details():
    """Verifies tio.scans.details is called exactly ONCE even with multiple history items.

    This ensures the performance optimization (hoisting details lookup out of history loop)
    prevents O(N) redundant network calls.
    """
    mock_tio = MagicMock()
    mock_tio.scans.details.return_value = {
        "settings": {"name": "Test Scan Name"}
    }
    mock_tio.scans.history.return_value = [
        {"time_start": 1700000000, "time_end": 1700003600},
        {"time_start": 1700003600, "time_end": 1700007200},
        {"time_start": 1700007200, "time_end": 1700010800},
    ]

    print_scan_history(mock_tio, 123)

    # Verify scans.details was called only once (O(1) complexity)
    mock_tio.scans.details.assert_called_once_with(123)
    mock_tio.scans.history.assert_called_once_with(123)


def test_monitor_scan_completed(capsys):
    """Tests monitor_scan when scan completes immediately."""
    mock_tio = MagicMock()
    mock_tio.scans.status.return_value = 'completed'
    mock_tio.scans.details.return_value = {"settings": {"name": "Sample Scan"}}
    mock_tio.scans.history.return_value = [
        {"time_start": 1000, "time_end": 4600}
    ]

    monitor_scan(mock_tio, 123)

    captured = capsys.readouterr().out
    assert "Scan is completed" in captured
    assert "Scan Name: Sample Scan" in captured
