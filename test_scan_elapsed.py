"""test_scan_elapsed.py: Unit tests for tenable_io_scan_elapsed.py"""

import logging
import unittest
from unittest.mock import MagicMock, patch

logging.basicConfig(level=logging.CRITICAL)

with patch("tenable.io.TenableIO"), patch("tenable_config.get_tenable_io_client"):
    from tenable_io_scan_elapsed import (
        check_scan_status,
        print_scan_history,
        monitor_scan,
    )


class TestScanElapsed(unittest.TestCase):
    """Test suite verifying optimization and logic in tenable_io_scan_elapsed.py."""

    def test_print_scan_history_hoists_details(self):
        """Verify io.scans.details is called exactly once for multiple history entries."""
        mock_io = MagicMock()
        scan_id = 12345

        # Mock scan details return value
        mock_io.scans.details.return_value = {
            "settings": {"name": "Test Scan Optimization"}
        }

        # Mock scan history with 3 separate entries
        mock_io.scans.history.return_value = [
            {"time_start": 1600000000, "time_end": 1600003600},
            {"time_start": 1600010000, "time_end": 1600013600},
            {"time_start": 1600020000, "time_end": 1600023600},
        ]

        print_scan_history(mock_io, scan_id)

        # Verify details was called exactly ONCE despite 3 history entries
        self.assertEqual(mock_io.scans.details.call_count, 1)
        mock_io.scans.details.assert_called_once_with(scan_id)
        mock_io.scans.history.assert_called_once_with(scan_id)

    def test_check_scan_status_success(self):
        """Verify check_scan_status returns the scan status string."""
        mock_io = MagicMock()
        mock_io.scans.status.return_value = "completed"

        status = check_scan_status(mock_io, 100)
        self.assertEqual(status, "completed")
        mock_io.scans.status.assert_called_once_with(100)

    @patch("time.sleep", return_value=None)
    def test_monitor_scan_completed(self, _mock_sleep):
        """Verify monitor_scan calls print_scan_history when completed."""
        mock_io = MagicMock()
        # First call returns 'running', second call returns 'completed'
        mock_io.scans.status.side_effect = ["running", "completed"]
        mock_io.scans.details.return_value = {"settings": {"name": "Monitored Scan"}}
        mock_io.scans.history.return_value = [
            {"time_start": 1600000000, "time_end": 1600001800}
        ]

        monitor_scan(mock_io, 100, poll_interval=1)

        self.assertEqual(mock_io.scans.status.call_count, 2)
        mock_io.scans.details.assert_called_once_with(100)


if __name__ == "__main__":
    unittest.main()
