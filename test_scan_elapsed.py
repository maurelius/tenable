"""Unit tests for tenable_io_scan_elapsed.py optimization and history processing."""

import unittest
from unittest.mock import MagicMock, patch
import logging

logging.basicConfig(level=logging.CRITICAL)

with patch('tenable.io.TenableIO'), patch('tenable_config.get_tenable_io_client'):
    from tenable_io_scan_elapsed import (
        check_scan_status,
        process_scan_history,
        monitor_scan_elapsed
    )


class TestScanElapsedOptimization(unittest.TestCase):
    """Test suite for verifying scan elapsed calculation and metadata hoisting optimization."""

    def test_process_scan_history_hoisted_details_call(self):
        """Verify that io.scans.details is called exactly once regardless of history length."""
        mock_io = MagicMock()
        scan_id = 1234

        mock_io.scans.details.return_value = {
            "settings": {
                "name": "Production Vulnerability Scan"
            }
        }

        # 5 scan history entries
        mock_io.scans.history.return_value = [
            {"time_start": 1700000000, "time_end": 1700003665},
            {"time_start": 1700010000, "time_end": 1700017200},
            {"time_start": 1700020000, "time_end": 1700020060},
            {"time_start": 1700030000, "time_end": 1700033600},
            {"time_start": 1700040000, "time_end": 1700047320},
        ]

        scan_name, history_entries = process_scan_history(mock_io, scan_id)

        self.assertEqual(scan_name, "Production Vulnerability Scan")
        self.assertEqual(len(history_entries), 5)

        # ⚡ BOLT Optimization Verification:
        # Details should be called exactly ONCE (O(1)), NOT 5 times (O(N)).
        self.assertEqual(mock_io.scans.details.call_count, 1)
        mock_io.scans.details.assert_called_once_with(scan_id)

        # Verify time calculations on the first history item (3665s = 1h 1m 5s)
        first_entry = history_entries[0]
        self.assertEqual(first_entry["timediff"], 3665)
        self.assertEqual(first_entry["hours"], 1)
        self.assertEqual(first_entry["minutes"], 1)
        self.assertEqual(first_entry["seconds"], 5)
        self.assertEqual(first_entry["name"], "Production Vulnerability Scan")

    def test_check_scan_status(self):
        """Verify check_scan_status delegates to io.scans.status."""
        mock_io = MagicMock()
        mock_io.scans.status.return_value = "completed"
        status = check_scan_status(mock_io, 42)
        self.assertEqual(status, "completed")
        mock_io.scans.status.assert_called_once_with(42)

    def test_monitor_scan_elapsed_completed(self):
        """Verify monitor_scan_elapsed processes scan history when scan completes."""
        mock_io = MagicMock()
        mock_io.scans.status.return_value = "completed"
        mock_io.scans.details.return_value = {"settings": {"name": "Test Scan"}}
        mock_io.scans.history.return_value = []

        monitor_scan_elapsed(mock_io, 99, poll_interval=0)
        self.assertEqual(mock_io.scans.status.call_count, 1)
        self.assertEqual(mock_io.scans.details.call_count, 1)


if __name__ == '__main__':
    unittest.main()
