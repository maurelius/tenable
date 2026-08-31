"""test_scan_elapsed.py: Unit tests for tenable_io_scan_elapsed.py optimization."""

import unittest
from unittest.mock import MagicMock
from tenable_io_scan_elapsed import process_scan_history, monitor_scan_elapsed


class TestScanElapsedOptimization(unittest.TestCase):
    """Test suite for verifying scan elapsed processing and API call optimizations."""

    def test_process_scan_history_hoists_scan_details(self):
        """Verifies io.scans.details is called only once for multiple history items."""
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
        process_scan_history(mock_io, scan_id)

        # Ensure scans.details was called exactly once (O(1) instead of O(N))
        self.assertEqual(mock_io.scans.details.call_count, 1)
        mock_io.scans.details.assert_called_with(scan_id)
        mock_io.scans.history.assert_called_with(scan_id)

    def test_monitor_scan_elapsed_completed(self):
        """Verifies monitor_scan_elapsed triggers process_scan_history on 'completed' status."""
        mock_io = MagicMock()
        mock_io.scans.status.return_value = "completed"
        mock_io.scans.details.return_value = {"settings": {"name": "Test Scan"}}
        mock_io.scans.history.return_value = []

        monitor_scan_elapsed(mock_io, 5678)

        mock_io.scans.status.assert_called_with(5678)
        mock_io.scans.details.assert_called_with(5678)


if __name__ == "__main__":
    unittest.main()
