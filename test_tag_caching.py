"""Unit tests for tag caching across Tenable.io scripts."""

import unittest
from unittest.mock import MagicMock, patch
import logging

# Configure logging to ignore messages during tests
logging.basicConfig(level=logging.CRITICAL)

# Mocking the imports before they are used in the script
with patch('tenable.io.TenableIO'), patch('tenable_config.get_tenable_io_client'):
    from tenable_io_get_scans_from_tag import (
        collect_tag_filters_and_value as tag_collect_tag_filters
    )
    from tenable_io_diagram_scanner_architecture import (
        collect_tag_filters_and_value as arch_collect_tag_filters
    )


class TestTagCaching(unittest.TestCase):
    """Test suite verifying tag lookup caching behavior."""

    def test_collect_tag_filters_and_value_caching(self):
        """Test tag caching in tenable_io_get_scans_from_tag."""
        mock_io = MagicMock()

        # Define a common tag UUID
        tag_uuid = "00000000-0000-0000-0000-000000000000"

        # Mock response for io.tags.details
        mock_tag_details = {
            "value": "Test Tag",
            "filters": {
                "asset": '{"and": [{"property": "ip", "operator": "eq", "value": "192.168.1.1"}]}'
            }
        }
        mock_io.tags.details.return_value = mock_tag_details

        # Define tag_targets where multiple scans share the same tag
        tag_targets = {
            "scan_1": {
                "uuids": [tag_uuid],
                "scan_name": "Scan 1",
                "scanner_name": "Scanner A"
            },
            "scan_2": {
                "uuids": [tag_uuid],
                "scan_name": "Scan 2",
                "scanner_name": "Scanner A"
            }
        }

        # Call the function
        results = tag_collect_tag_filters(mock_io, tag_targets)

        # Assertions
        self.assertEqual(len(results), 2)
        # io.tags.details should be called exactly ONCE due to caching
        self.assertEqual(mock_io.tags.details.call_count, 1)
        mock_io.tags.details.assert_called_with(tag_uuid)

        # Verify results contain the expected data
        for res in results:
            self.assertEqual(res['tag_value_uuid'], tag_uuid)
            self.assertEqual(res['value'], "Test Tag")

    def test_diagram_architecture_tag_caching(self):
        """Test tag caching in tenable_io_diagram_scanner_architecture."""
        mock_io = MagicMock()

        tag_uuid = "11111111-2222-3333-4444-555555555555"
        mock_tag_details = {
            "value": "Prod Subnet Tag",
            "filters": {
                "asset": '{"and": [{"property": "ipv4", "operator": "eq", "value": "10.0.0.0/24"}]}'
            }
        }
        mock_io.tags.details.return_value = mock_tag_details

        tag_targets = {
            "scan_100": {
                "uuids": [tag_uuid],
                "scan_name": "Prod Scan 1",
                "scanner_name": "US-East Group"
            },
            "scan_101": {
                "uuids": [tag_uuid],
                "scan_name": "Prod Scan 2",
                "scanner_name": "US-East Group"
            },
            "scan_102": {
                "uuids": [tag_uuid],
                "scan_name": "Prod Scan 3",
                "scanner_name": "US-East Group"
            }
        }

        results = arch_collect_tag_filters(mock_io, tag_targets)

        self.assertEqual(len(results), 3)
        # io.tags.details should be called exactly ONCE despite 3 scans using the tag
        self.assertEqual(mock_io.tags.details.call_count, 1)
        mock_io.tags.details.assert_called_with(tag_uuid)

        for res in results:
            self.assertEqual(res['tag_value_uuid'], tag_uuid)
            self.assertEqual(res['value'], "Prod Subnet Tag")


if __name__ == '__main__':
    unittest.main()
