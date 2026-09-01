"""Unit tests for tenable_io_scan_elapsed performance optimizations."""

import unittest
from unittest.mock import patch

with patch('tenable_config.get_tenable_io_client'):
    from tenable_io_scan_elapsed import process_completed_scan

class TestScanElapsedOptimization(unittest.TestCase):
    """Test suite for verifying performance optimization in tenable_io_scan_elapsed.py."""

    @patch('tenable_io_scan_elapsed.tio_client')
    def test_process_completed_scan_hoisting(self, mock_io):
        """Verify that tio_client.scans.details is called exactly once for history items."""
        mock_io.scans.details.return_value = {
            "settings": {"name": "Test Scan Hoist"}
        }
        mock_io.scans.history.return_value = [
            {"time_start": 1700000000, "time_end": 1700003600},
            {"time_start": 1700003600, "time_end": 1700007200},
            {"time_start": 1700007200, "time_end": 1700010800},
        ]

        process_completed_scan(1234)

        # Assert details was called exactly ONCE (O(1)) instead of 3 times (O(N))
        self.assertEqual(mock_io.scans.details.call_count, 1)
        mock_io.scans.details.assert_called_once_with(1234)
        mock_io.scans.history.assert_called_once_with(1234)

if __name__ == '__main__':
    unittest.main()
