"""
Unit tests for tenable_io_scan_elapsed.py.
"""

import unittest
from unittest.mock import MagicMock
from tenable_io_scan_elapsed import process_completed_scan, monitor_and_report_scan


class TestScanElapsedOptimization(unittest.TestCase):
    """Test suite for scan elapsed time calculations and optimization."""

    def test_process_completed_scan_hoisted_details_call(self):
        """Verify io.scans.details is called exactly once when processing multiple history items."""
        mock_io = MagicMock()
        target_scan_id = 1234

        # Mock scan details response
        mock_io.scans.details.return_value = {
            "settings": {
                "name": "Production Subnet Scan"
            }
        }

        # Mock scan history with 3 historical runs
        mock_io.scans.history.return_value = [
            {"time_start": 1600000000, "time_end": 1600003600},
            {"time_start": 1600086400, "time_end": 1600090000},
            {"time_start": 1600172800, "time_end": 1600176400},
        ]

        # Process the scan
        results = process_completed_scan(mock_io, target_scan_id)

        # Assertions
        self.assertEqual(len(results), 3)
        # Ensure io.scans.details was called ONLY ONCE despite 3 history records
        self.assertEqual(mock_io.scans.details.call_count, 1)
        mock_io.scans.details.assert_called_once_with(target_scan_id)

        # Verify details were correctly passed into results
        for item in results:
            self.assertEqual(item["name"], "Production Subnet Scan")
            self.assertEqual(item["elapsed"], (1, 0, 0))

    def test_monitor_and_report_scan_completed(self):
        """Verify monitor_and_report_scan handles completed status."""
        mock_io = MagicMock()
        target_scan_id = 5678

        mock_io.scans.status.return_value = "completed"
        mock_io.scans.details.return_value = {"settings": {"name": "Test Scan"}}
        mock_io.scans.history.return_value = [
            {"time_start": 1600000000, "time_end": 1600001800}
        ]

        results = monitor_and_report_scan(mock_io, target_scan_id, poll_interval=1)

        self.assertIsNotNone(results)
        self.assertEqual(len(results), 1)
        self.assertEqual(mock_io.scans.details.call_count, 1)


if __name__ == '__main__':
    unittest.main()
