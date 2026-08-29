"""Unit tests for tenable_io_scan_elapsed.py verifying performance optimization."""
import unittest
from unittest.mock import MagicMock
from tenable_io_scan_elapsed import print_scan_elapsed_history, process_scan_elapsed


class TestScanElapsed(unittest.TestCase):
    """Test suite for scan elapsed duration calculations and API call efficiency."""

    def test_print_scan_elapsed_history_calls_details_once(self):
        """Verify io.scans.details is called exactly once despite multiple history entries."""
        mock_io = MagicMock()
        mock_io.scans.details.return_value = {
            "settings": {"name": "Test Scan"}
        }
        mock_io.scans.history.return_value = [
            {"time_start": 1600000000, "time_end": 1600003600},
            {"time_start": 1600005000, "time_end": 1600008600},
            {"time_start": 1600010000, "time_end": 1600013600},
        ]

        scan_id = 1234
        print_scan_elapsed_history(mock_io, scan_id)

        # Optimization assertion: details should be called once, not 3 times (O(1) instead of O(N))
        self.assertEqual(mock_io.scans.details.call_count, 1)
        mock_io.scans.details.assert_called_once_with(scan_id)
        mock_io.scans.history.assert_called_once_with(scan_id)

    def test_process_scan_elapsed_completed(self):
        """Verify process_scan_elapsed terminates correctly when status is completed."""
        mock_io = MagicMock()
        mock_io.scans.status.return_value = 'completed'
        mock_io.scans.details.return_value = {"settings": {"name": "Completed Scan"}}
        mock_io.scans.history.return_value = [
            {"time_start": 1600000000, "time_end": 1600001800}
        ]

        process_scan_elapsed(mock_io, 1234)

        mock_io.scans.status.assert_called_once_with(1234)
        mock_io.scans.details.assert_called_once_with(1234)


if __name__ == '__main__':
    unittest.main()
