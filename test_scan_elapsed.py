"""Unit tests for tenable_io_scan_elapsed.py."""

import unittest
from unittest.mock import MagicMock, patch
import logging

logging.basicConfig(level=logging.CRITICAL)

with patch('tenable.io.TenableIO'), patch('tenable_config.get_tenable_io_client'):
    from tenable_io_scan_elapsed import (
        check_scan_status,
        display_scan_history,
        monitor_scan,
    )


class TestScanElapsed(unittest.TestCase):
    """Test suite for verifying scan elapsed logic and optimization."""

    def test_display_scan_history_hoisted_details_call(self):
        """Verify io.scans.details is called exactly once even with multiple history items."""
        mock_io = MagicMock()
        scan_id = 12345

        # Mock scan details response
        mock_io.scans.details.return_value = {
            "settings": {
                "name": "Production Vulnerability Scan"
            }
        }

        # Mock 5 history runs
        mock_io.scans.history.return_value = [
            {"time_start": 1700000000, "time_end": 1700003665},
            {"time_start": 1700010000, "time_end": 1700017200},
            {"time_start": 1700020000, "time_end": 1700020050},
            {"time_start": 1700030000, "time_end": 1700033600},
            {"time_start": 1700040000, "time_end": 1700041800},
        ]

        records = display_scan_history(mock_io, scan_id)

        # Ensure details was called only ONCE, not 5 times (O(1) instead of O(N))
        self.assertEqual(mock_io.scans.details.call_count, 1)
        mock_io.scans.details.assert_called_with(scan_id)

        # Ensure history was fetched once
        self.assertEqual(mock_io.scans.history.call_count, 1)
        mock_io.scans.history.assert_called_with(scan_id)

        # Ensure all 5 records were processed
        self.assertEqual(len(records), 5)
        for r in records:
            self.assertEqual(r["name"], "Production Vulnerability Scan")

        # First run: 3665s = 1h 1m 5s
        self.assertEqual(records[0]["elapsed_str"], "1h 1m 5s")
        self.assertEqual(records[0]["timediff"], 3665)

    def test_display_scan_history_fallback_name(self):
        """Verify fallback scan name when settings or name key is missing."""
        mock_io = MagicMock()
        mock_io.scans.details.return_value = {}
        mock_io.scans.history.return_value = [
            {"time_start": 100, "time_end": 160}
        ]

        records = display_scan_history(mock_io, 999)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["name"], "Unknown")
        self.assertEqual(records[0]["elapsed_str"], "0h 1m 0s")

    def test_check_scan_status(self):
        """Verify check_scan_status handles valid status and exceptions."""
        mock_io = MagicMock()
        mock_io.scans.status.return_value = "completed"

        status = check_scan_status(mock_io, 123)
        self.assertEqual(status, "completed")

        mock_io.scans.status.side_effect = KeyError("missing key")
        self.assertIsNone(check_scan_status(mock_io, 123))

        mock_io.scans.status.side_effect = RuntimeError("network error")
        self.assertIsNone(check_scan_status(mock_io, 123))

    def test_monitor_scan_completed(self):
        """Verify monitor_scan stops after scan is completed."""
        mock_io = MagicMock()
        mock_io.scans.status.return_value = "completed"
        mock_io.scans.details.return_value = {"settings": {"name": "Test Scan"}}
        mock_io.scans.history.return_value = []

        monitor_scan(mock_io, 123)
        self.assertEqual(mock_io.scans.status.call_count, 1)
        self.assertEqual(mock_io.scans.details.call_count, 1)


if __name__ == "__main__":
    unittest.main()
