"""Unit tests for tenable_io_scan_elapsed.py"""

import unittest
from unittest.mock import MagicMock, patch
from tenable_io_scan_elapsed import (
    process_scan_history,
    check_scan_status,
)


class TestScanElapsed(unittest.TestCase):
    """Test suite for scan elapsed processing and status checking."""

    def test_process_scan_history_hoisted_details_call(self):
        """Verify io.scans.details is called exactly once for multiple history items."""
        mock_io = MagicMock()
        scan_id = 1234

        mock_io.scans.details.return_value = {
            "settings": {"name": "Test Scan Name"}
        }
        mock_io.scans.history.return_value = [
            {"time_start": 1600000000, "time_end": 1600003600},
            {"time_start": 1600003600, "time_end": 1600007200},
            {"time_start": 1600007200, "time_end": 1600010800},
        ]

        with patch('builtins.print') as mock_print:
            process_scan_history(mock_io, scan_id)

        # Assert details was called exactly once despite 3 history entries
        self.assertEqual(mock_io.scans.details.call_count, 1)
        mock_io.scans.details.assert_called_with(scan_id)

        # Verify history was fetched for scan_id
        mock_io.scans.history.assert_called_with(scan_id)

        # Verify print was called with the scan name
        printed_args = [call.args for call in mock_print.call_args_list]
        self.assertTrue(any("Scan Name: " in args for args in printed_args))

    def test_check_scan_status_success(self):
        """Test check_scan_status returns status string."""
        mock_io = MagicMock()
        mock_io.scans.status.return_value = "completed"

        status = check_scan_status(mock_io, 5678)
        self.assertEqual(status, "completed")
        mock_io.scans.status.assert_called_once_with(5678)

    def test_check_scan_status_exception_handling(self):
        """Test check_scan_status handles exceptions and returns None."""
        mock_io = MagicMock()
        mock_io.scans.status.side_effect = Exception("API error")

        status = check_scan_status(mock_io, 5678)
        self.assertIsNone(status)


if __name__ == '__main__':
    unittest.main()
