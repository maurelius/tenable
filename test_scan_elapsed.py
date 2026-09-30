"""test_scan_elapsed.py - Unit tests for tenable_io_scan_elapsed.py"""

import unittest
from unittest.mock import MagicMock, patch
import logging

logging.basicConfig(level=logging.CRITICAL)

with patch('tenable.io.TenableIO'), patch('tenable_config.get_tenable_io_client'):
    from tenable_io_scan_elapsed import process_completed_scan, check_scan_status


class TestScanElapsed(unittest.TestCase):
    """Test suite for tenable_io_scan_elapsed.py performance optimizations and status checks."""

    def test_process_completed_scan_hoisted_details(self):
        """Verify io.scans.details is called exactly ONCE regardless of history record count."""
        mock_io = MagicMock()
        scan_id = 12345

        mock_io.scans.details.return_value = {
            "settings": {"name": "Test Scan Execution"}
        }
        mock_io.scans.history.return_value = [
            {"time_start": 1600000000, "time_end": 1600003600},
            {"time_start": 1600003600, "time_end": 1600007200},
            {"time_start": 1600007200, "time_end": 1600010800},
        ]

        process_completed_scan(mock_io, scan_id)

        # Confirm io.scans.details was called only ONCE (O(1) optimization)
        self.assertEqual(mock_io.scans.details.call_count, 1)
        mock_io.scans.details.assert_called_with(scan_id)
        mock_io.scans.history.assert_called_with(scan_id)

    def test_check_scan_status(self):
        """Test check_scan_status helper function."""
        mock_io = MagicMock()
        mock_io.scans.status.return_value = "completed"

        status = check_scan_status(12345, io_client=mock_io)
        self.assertEqual(status, "completed")
        mock_io.scans.status.assert_called_with(12345)


if __name__ == '__main__':
    unittest.main()
