"""Unit tests for tenable_io_scan_elapsed.py."""

import unittest
from unittest.mock import MagicMock
from tenable_io_scan_elapsed import check_scan_status, process_scan_history


class TestScanElapsed(unittest.TestCase):
    """Test cases for scan elapsed processing and optimization."""

    def test_process_scan_history_hoisted_details_call(self):
        """Verify that io.scans.details is called ONCE even with multiple history entries."""
        mock_io = MagicMock()
        mock_io.scans.details.return_value = {
            "settings": {"name": "Production Subnet Scan"}
        }
        mock_io.scans.history.return_value = [
            {"time_start": 1600000000, "time_end": 1600003600},
            {"time_start": 1600004000, "time_end": 1600007600},
            {"time_start": 1600008000, "time_end": 1600011600},
        ]

        target_scan_id = 1234
        process_scan_history(mock_io, target_scan_id)

        # Assert details was called exactly ONCE (O(1) instead of O(N))
        self.assertEqual(mock_io.scans.details.call_count, 1)
        mock_io.scans.details.assert_called_with(target_scan_id)

        # Assert history was called once
        self.assertEqual(mock_io.scans.history.call_count, 1)
        mock_io.scans.history.assert_called_with(target_scan_id)

    def test_check_scan_status_success(self):
        """Verify check_scan_status returns status correctly."""
        mock_io = MagicMock()
        mock_io.scans.status.return_value = "completed"

        status = check_scan_status(mock_io, 1234)
        self.assertEqual(status, "completed")
        mock_io.scans.status.assert_called_with(1234)


if __name__ == "__main__":
    unittest.main()
