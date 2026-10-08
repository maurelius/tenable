"""Unit tests for tenable_io_scan_elapsed.py optimization."""

import unittest
from unittest.mock import patch, MagicMock

# Patch get_tenable_io_client before importing module to avoid environment variable error
with patch("tenable_config.get_tenable_io_client") as mock_get_client:
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    import tenable_io_scan_elapsed


class TestScanElapsedOptimization(unittest.TestCase):
    """Tests to verify performance optimization in tenable_io_scan_elapsed.py."""

    @patch("tenable_io_scan_elapsed.io")
    def test_print_scan_elapsed_times_calls_details_once(self, mock_io):
        """Verify that io.scans.details is called exactly once for multiple history items."""
        mock_io.scans.details.return_value = {
            "settings": {"name": "Test Scan"}
        }
        mock_io.scans.history.return_value = [
            {"time_start": 1000, "time_end": 2000},
            {"time_start": 3000, "time_end": 4500},
            {"time_start": 5000, "time_end": 7200},
        ]

        # Call function
        tenable_io_scan_elapsed.print_scan_elapsed_times(1234)

        # Assert details was called exactly once, preventing O(N) redundant network calls
        mock_io.scans.details.assert_called_once_with(1234)
        mock_io.scans.history.assert_called_once_with(1234)


if __name__ == "__main__":
    unittest.main()
