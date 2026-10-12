"""Unit tests for tenable_io_scan_elapsed.py"""

import unittest
from unittest.mock import MagicMock, patch
import logging

logging.basicConfig(level=logging.CRITICAL)

with patch('tenable.io.TenableIO'), patch('tenable_config.get_tenable_io_client'):
    from tenable_io_scan_elapsed import process_completed_scan, check_scan_status


class TestScanElapsed(unittest.TestCase):
    """Tests for scan elapsed processing and API optimizations."""

    def test_process_completed_scan_hoisting(self):
        """Verify io.scans.details is called exactly once for multiple history runs."""
        mock_io = MagicMock()

        mock_io.scans.details.return_value = {
            "settings": {"name": "Test Scan Name"}
        }

        # Mock 3 historical runs
        mock_io.scans.history.return_value = [
            {"time_start": 1600000000, "time_end": 1600003600},
            {"time_start": 1600010000, "time_end": 1600017200},
            {"time_start": 1600020000, "time_end": 1600021800},
        ]

        # Call process_completed_scan
        process_completed_scan(mock_io, 1234)

        # Verify io.scans.details was called EXACTLY ONCE despite 3 history records
        self.assertEqual(mock_io.scans.details.call_count, 1)
        mock_io.scans.details.assert_called_once_with(1234)

        # Verify io.scans.history was called with scan_id 1234
        mock_io.scans.history.assert_called_once_with(1234)

    def test_check_scan_status(self):
        """Verify check_scan_status returns status from client."""
        mock_io = MagicMock()
        mock_io.scans.status.return_value = "completed"

        status = check_scan_status(mock_io, 5678)
        self.assertEqual(status, "completed")
        mock_io.scans.status.assert_called_once_with(5678)


if __name__ == '__main__':
    unittest.main()
