"""Unit tests for tenable_io_scan_elapsed.py"""
import unittest
from unittest.mock import MagicMock
from tenable_io_scan_elapsed import (
    check_scan_status,
    print_scan_history_elapsed,
    monitor_scan_until_complete
)


class TestScanElapsed(unittest.TestCase):
    """Tests for scan status and elapsed history logic."""

    def test_check_scan_status_success(self):
        """Test check_scan_status returns the correct status string."""
        mock_client = MagicMock()
        mock_client.scans.status.return_value = 'completed'

        status = check_scan_status(mock_client, 123)
        self.assertEqual(status, 'completed')
        mock_client.scans.status.assert_called_once_with(123)

    def test_check_scan_status_key_error(self):
        """Test check_scan_status handles KeyError gracefully."""
        mock_client = MagicMock()
        mock_client.scans.status.side_effect = KeyError("info")

        status = check_scan_status(mock_client, 123)
        self.assertIsNone(status)

    def test_print_scan_history_elapsed_hoisting(self):
        """Verify scans.details is called exactly ONCE across all history items."""
        mock_client = MagicMock()
        mock_client.scans.details.return_value = {
            "settings": {"name": "Test Scan"}
        }
        mock_client.scans.history.return_value = [
            {"time_start": 1600000000, "time_end": 1600003600},
            {"time_start": 1600010000, "time_end": 1600017200},
            {"time_start": 1600020000, "time_end": 1600020300},
        ]

        print_scan_history_elapsed(mock_client, 123)

        # Confirm details was called ONCE, not 3 times
        mock_client.scans.details.assert_called_once_with(123)
        mock_client.scans.history.assert_called_once_with(123)

    def test_monitor_scan_until_complete_completed(self):
        """Test monitor_scan_until_complete when scan completes immediately."""
        mock_client = MagicMock()
        mock_client.scans.status.return_value = 'completed'
        mock_client.scans.details.return_value = {"settings": {"name": "Test"}}
        mock_client.scans.history.return_value = []

        monitor_scan_until_complete(mock_client, 123, poll_interval=0)
        mock_client.scans.status.assert_called_once_with(123)


if __name__ == '__main__':
    unittest.main()
