"""test_scan_elapsed_optimization.py: Unit test for tenable_io_scan_elapsed optimization."""

import unittest
from unittest.mock import MagicMock
from tenable_io_scan_elapsed import process_scan_history


class TestScanElapsedOptimization(unittest.TestCase):
    """Tests for tenable_io_scan_elapsed.py performance optimization."""

    def test_process_scan_history_calls_details_once(self):
        """Verify that io.scans.details is called exactly once, regardless of history count."""
        mock_io = MagicMock()
        mock_io.scans.details.return_value = {
            "settings": {"name": "Test Scan Name"}
        }
        # Simulate 5 history runs
        mock_io.scans.history.return_value = [
            {"time_start": 1600000000, "time_end": 1600003600},
            {"time_start": 1600086400, "time_end": 1600090000},
            {"time_start": 1600172800, "time_end": 1600176400},
            {"time_start": 1600259200, "time_end": 1600262800},
            {"time_start": 1600345600, "time_end": 1600349200},
        ]

        process_scan_history(mock_io, 1234)

        # Confirm details was called only once (O(1)) instead of 5 times (O(N))
        self.assertEqual(mock_io.scans.details.call_count, 1)
        mock_io.scans.details.assert_called_once_with(1234)
        mock_io.scans.history.assert_called_once_with(1234)


if __name__ == '__main__':
    unittest.main()
