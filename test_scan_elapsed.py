"""Unit tests for tenable_io_scan_elapsed.py optimization and logic."""

import unittest
from unittest.mock import MagicMock, patch
import logging

logging.basicConfig(level=logging.CRITICAL)

with patch('tenable.io.TenableIO'), patch('tenable_config.get_tenable_io_client'):
    from tenable_io_scan_elapsed import (
        check_scan_status,
        process_scan_history,
        monitor_scan
    )


class TestScanElapsed(unittest.TestCase):
    """Test suite for verifying scan elapsed calculation and details call hoisting."""

    def test_check_scan_status(self):
        """Verify check_scan_status returns status or None on exceptions."""
        mock_io = MagicMock()
        mock_io.scans.status.return_value = "completed"

        status = check_scan_status(mock_io, 123)
        self.assertEqual(status, "completed")
        mock_io.scans.status.assert_called_once_with(123)

        mock_io.scans.status.side_effect = KeyError("status")
        self.assertIsNone(check_scan_status(mock_io, 123))

    def test_process_scan_history_hoisted_details(self):
        """Verify io.scans.details is called exactly once regardless of history length."""
        mock_io = MagicMock()
        mock_io.scans.details.return_value = {
            "settings": {
                "name": "Production Network Scan"
            }
        }

        # 3 historical scan executions
        mock_io.scans.history.return_value = [
            {"time_start": 1672531200, "time_end": 1672534865},  # 3665s = 1h 1m 5s
            {"time_start": 1672617600, "time_end": 1672621200},  # 3600s = 1h 0m 0s
            {"time_start": 1672704000, "time_end": 1672704125},  # 125s = 0h 2m 5s
        ]

        results = process_scan_history(mock_io, 999)

        # ⚡ Optimization check: io.scans.details must be called exactly once
        self.assertEqual(mock_io.scans.details.call_count, 1)
        mock_io.scans.details.assert_called_once_with(999)
        mock_io.scans.history.assert_called_once_with(999)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["scan_name"], "Production Network Scan")
        self.assertEqual(results[0]["elapsed"], "1h 1m 5s")
        self.assertEqual(results[1]["elapsed"], "1h 0m 0s")
        self.assertEqual(results[2]["elapsed"], "0h 2m 5s")

    @patch('tenable_io_scan_elapsed.process_scan_history')
    @patch('tenable_io_scan_elapsed.check_scan_status')
    def test_monitor_scan_completed(self, mock_status, mock_process):
        """Verify monitor_scan triggers history processing upon completion."""
        mock_io = MagicMock()
        mock_status.return_value = "completed"

        monitor_scan(mock_io, 100, poll_interval=0)

        mock_status.assert_called_once_with(mock_io, 100)
        mock_process.assert_called_once_with(mock_io, 100)


if __name__ == '__main__':
    unittest.main()
