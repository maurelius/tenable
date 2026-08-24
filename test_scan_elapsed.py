"""test_scan_elapsed.py: Unit tests for tenable_io_scan_elapsed.py optimization."""

import logging
import unittest
from unittest.mock import MagicMock, patch

# Configure logging to ignore messages during tests
logging.basicConfig(level=logging.CRITICAL)

with patch('tenable.io.TenableIO'), patch('tenable_config.get_tenable_io_client'):
    from tenable_io_scan_elapsed import (
        check_scan_status,
        process_scan_history,
        main,
    )


class TestScanElapsedOptimization(unittest.TestCase):
    """Unit test suite for scan elapsed history hoisting optimization."""

    def test_process_scan_history_hoisted_details_call(self):
        """Verify io.scans.details is called exactly ONCE for multiple scan history entries."""
        mock_io = MagicMock()
        scan_id = 1234

        mock_io.scans.details.return_value = {
            "settings": {"name": "Production Vulnerability Scan"}
        }
        mock_io.scans.history.return_value = [
            {"time_start": 1600000000, "time_end": 1600003600},
            {"time_start": 1600007200, "time_end": 1600010800},
            {"time_start": 1600014400, "time_end": 1600018000},
        ]

        process_scan_history(mock_io, scan_id)

        # Assert io.scans.details was called exactly 1 time (O(1) instead of O(N))
        self.assertEqual(mock_io.scans.details.call_count, 1)
        mock_io.scans.details.assert_called_with(scan_id)

        # Assert io.scans.history was called once
        mock_io.scans.history.assert_called_once_with(scan_id)

    def test_check_scan_status(self):
        """Verify check_scan_status retrieves scan status from client."""
        mock_io = MagicMock()
        mock_io.scans.status.return_value = "completed"

        status = check_scan_status(mock_io, 1234)
        self.assertEqual(status, "completed")
        mock_io.scans.status.assert_called_once_with(1234)

    @patch('tenable_io_scan_elapsed.get_tenable_io_client')
    @patch('tenable_io_scan_elapsed.process_scan_history')
    def test_main_completed_flow(self, mock_process_history, mock_get_client):
        """Verify main flow processes scan history upon completion."""
        mock_io = MagicMock()
        mock_get_client.return_value = mock_io
        mock_io.scans.status.return_value = "completed"

        main()

        mock_process_history.assert_called_once()


if __name__ == '__main__':
    unittest.main()
