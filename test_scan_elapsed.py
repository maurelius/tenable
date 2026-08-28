"""test_scan_elapsed.py: Unit tests for tenable_io_scan_elapsed.py optimization"""

import unittest
from unittest.mock import MagicMock
from tenable_io_scan_elapsed import process_scan_elapsed

class TestScanElapsedOptimization(unittest.TestCase):
    """Test suite to verify scan details lookup is hoisted outside history loop."""

    def test_process_scan_elapsed_hoisting(self):
        """Verify io.scans.details is called exactly ONCE even with multiple history items."""
        mock_io = MagicMock()
        mock_io.scans.details.return_value = {
            "settings": {"name": "Test Scan Name"}
        }
        mock_io.scans.history.return_value = [
            {"time_start": 1600000000, "time_end": 1600003600},
            {"time_start": 1600010000, "time_end": 1600017200},
            {"time_start": 1600020000, "time_end": 1600021800},
        ]

        process_scan_elapsed(mock_io, 1234)

        # Verify details was called exactly once with scan ID 1234
        mock_io.scans.details.assert_called_once_with(1234)
        # Verify history was called once
        mock_io.scans.history.assert_called_once_with(1234)

if __name__ == '__main__':
    unittest.main()
