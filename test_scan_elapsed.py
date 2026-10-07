"""test_scan_elapsed.py: Unit tests for tenable_io_scan_elapsed.py"""
import logging
import unittest
from unittest.mock import MagicMock, patch

logging.basicConfig(level=logging.CRITICAL)

with patch('tenable.io.TenableIO'), patch('tenable_config.get_tenable_io_client'):
    from tenable_io_scan_elapsed import (
        check_scan_status,
        monitor_scan,
        process_completed_scan,
    )


class TestScanElapsed(unittest.TestCase):
    """Test suite for scan elapsed calculation functions."""

    def setUp(self):
        self.mock_client = MagicMock()

    def test_check_scan_status_success(self):
        """Test check_scan_status returns status when API call succeeds."""
        self.mock_client.scans.status.return_value = 'completed'
        status = check_scan_status(self.mock_client, 1234)
        self.assertEqual(status, 'completed')
        self.mock_client.scans.status.assert_called_once_with(1234)

    def test_check_scan_status_key_error(self):
        """Test check_scan_status handles KeyError gracefully."""
        self.mock_client.scans.status.side_effect = KeyError("status")
        status = check_scan_status(self.mock_client, 1234)
        self.assertIsNone(status)

    def test_check_scan_status_exception(self):
        """Test check_scan_status handles general exceptions gracefully."""
        self.mock_client.scans.status.side_effect = RuntimeError("API error")
        status = check_scan_status(self.mock_client, 1234)
        self.assertIsNone(status)

    def test_process_completed_scan_hoisted_details(self):
        """Test process_completed_scan invokes scans.details once for history items."""
        self.mock_client.scans.details.return_value = {
            "settings": {"name": "Weekly Network Vulnerability Scan"}
        }
        self.mock_client.scans.history.return_value = [
            {"time_start": 1600000000, "time_end": 1600003600},
            {"time_start": 1600086400, "time_end": 1600090000},
            {"time_start": 1600172800, "time_end": 1600176400},
        ]

        process_completed_scan(self.mock_client, 1234)

        # Assert scans.details is called exactly ONCE due to hoisting optimization
        self.assertEqual(self.mock_client.scans.details.call_count, 1)
        self.mock_client.scans.details.assert_called_once_with(1234)
        self.mock_client.scans.history.assert_called_once_with(1234)

    @patch('time.sleep')
    def test_monitor_scan_completed(self, mock_sleep):
        """Test monitor_scan processes completed status and terminates loop."""
        self.mock_client.scans.status.return_value = 'completed'
        self.mock_client.scans.details.return_value = {"settings": {"name": "Test Scan"}}
        self.mock_client.scans.history.return_value = []

        monitor_scan(self.mock_client, 1234)

        self.mock_client.scans.status.assert_called_once_with(1234)
        mock_sleep.assert_not_called()

    def test_monitor_scan_none_status(self):
        """Test monitor_scan handles status retrieval failure."""
        self.mock_client.scans.status.return_value = None

        monitor_scan(self.mock_client, 1234)

        self.mock_client.scans.status.assert_called_once_with(1234)


if __name__ == '__main__':
    unittest.main()
