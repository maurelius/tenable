"""test_scan_elapsed.py: Unit tests for tenable_io_scan_elapsed.py"""

import unittest
from unittest.mock import MagicMock
from tenable_io_scan_elapsed import process_scan_history, check_scan_status


class TestScanElapsed(unittest.TestCase):
    """Tests for scan elapsed history and status functions."""

    def test_process_scan_history_calls_details_once(self):
        """Verify that io.scans.details is called exactly once despite N history items."""
        mock_io = MagicMock()
        scan_id = 1234
        mock_io.scans.details.return_value = {
            "settings": {"name": "Test Scan"}
        }
        mock_io.scans.history.return_value = [
            {"time_start": 1600000000, "time_end": 1600003600},
            {"time_start": 1600100000, "time_end": 1600103600},
            {"time_start": 1600200000, "time_end": 1600203600},
            {"time_start": 1600300000, "time_end": 1600303600},
            {"time_start": 1600400000, "time_end": 1600403600},
        ]

        process_scan_history(scan_id, io_client=mock_io)

        # Ensure scans.details was called only once (O(1) complexity)
        mock_io.scans.details.assert_called_once_with(scan_id)
        # Ensure scans.history was called once
        mock_io.scans.history.assert_called_once_with(scan_id)

    def test_check_scan_status(self):
        """Verify check_scan_status returns correct status from client."""
        mock_io = MagicMock()
        scan_id = 1234
        mock_io.scans.status.return_value = 'completed'

        status = check_scan_status(scan_id, io_client=mock_io)

        self.assertEqual(status, 'completed')
        mock_io.scans.status.assert_called_once_with(scan_id)


if __name__ == '__main__':
    unittest.main()
