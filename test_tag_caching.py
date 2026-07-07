import unittest
from unittest.mock import MagicMock, patch
import logging

# Configure logging to ignore messages during tests
logging.basicConfig(level=logging.CRITICAL)

# Mocking the imports before they are used in the script
with patch('tenable.io.TenableIO'), patch('tenable_config.get_tenable_io_client'):
    from tenable_io_get_scans_from_tag import collect_tag_filters_and_value

class TestTagCaching(unittest.TestCase):
    def test_collect_tag_filters_and_value_caching(self):
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
        results = collect_tag_filters_and_value(mock_io, tag_targets)

        # Assertions
        self.assertEqual(len(results), 2)
        # io.tags.details should be called exactly ONCE due to caching
        self.assertEqual(mock_io.tags.details.call_count, 1)
        mock_io.tags.details.assert_called_with(tag_uuid)

        # Verify results contain the expected data
        for res in results:
            self.assertEqual(res['tag_value_uuid'], tag_uuid)
            self.assertEqual(res['value'], "Test Tag")

if __name__ == '__main__':
    unittest.main()
