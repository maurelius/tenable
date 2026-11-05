"""Unit tests for tenable_io_get_scan_templates_by_plugin_id.py caching and logic."""

import unittest
from unittest.mock import MagicMock, patch
import logging

logging.basicConfig(level=logging.CRITICAL)

with patch('tenable.io.TenableIO'), patch('tenable_config.get_tenable_io_client'):
    from tenable_io_get_scan_templates_by_plugin_id import process_templates, _get_template_details


class TestTemplateCaching(unittest.TestCase):
    """Test suite for verifying scan template caching and optimization."""

    def test_get_template_details_caching(self):
        """Verify _get_template_details uses cache and updates stats correctly."""
        mock_io = MagicMock()
        uuid = "template-123"
        cache = {}
        stats = {'hits': 0, 'misses': 0}

        mock_io.editor.template_details.return_value = {
            "name": "Test Template",
            "uuid": uuid
        }

        # First call should miss cache and call API
        res1 = _get_template_details(mock_io, uuid, cache, stats)
        self.assertEqual(res1["name"], "Test Template")
        self.assertEqual(mock_io.editor.template_details.call_count, 1)
        self.assertEqual(stats['hits'], 0)
        self.assertEqual(stats['misses'], 1)

        # Second call should hit cache and not invoke API again
        res2 = _get_template_details(mock_io, uuid, cache, stats)
        self.assertEqual(res2["name"], "Test Template")
        self.assertEqual(mock_io.editor.template_details.call_count, 1)
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 1)

    def test_process_templates_deduplication_and_caching(self):
        """Verify process_templates deduplicates UUIDs and reuses cache."""
        mock_io = MagicMock()

        # Mock folder list
        mock_io.folders.list.return_value = [{"name": "My Scans", "id": 100}]

        # Mock scans with duplicate wizard_uuid
        shared_uuid = "shared-uuid-1"
        unique_uuid = "unique-uuid-2"
        mock_io.scans.list.return_value = [
            {"wizard_uuid": shared_uuid},
            {"wizard_uuid": shared_uuid},
            {"wizard_uuid": unique_uuid}
        ]

        # Mock scan templates including the shared UUID again
        mock_io.editor.template_list.return_value = [
            {"uuid": shared_uuid},
            {"uuid": unique_uuid}
        ]

        # Return mock details for template_details
        def mock_template_details(_type_arg, uuid_arg):
            modes = {"34220": True} if uuid_arg == shared_uuid else {}
            return {
                "name": f"Template {uuid_arg}",
                "uuid": uuid_arg,
                "settings": {
                    "discovery": {
                        "modes": modes
                    }
                }
            }

        mock_io.editor.template_details.side_effect = mock_template_details

        plugin_ids = ['34220']
        matching_policies, stats = process_templates(mock_io, plugin_ids)

        # Total unique template_details API calls should be exactly 2
        self.assertEqual(mock_io.editor.template_details.call_count, 2)
        # Check cache hit stats: 2 misses (1st time each UUID seen) and 2 hits
        self.assertEqual(stats['misses'], 2)
        self.assertEqual(stats['hits'], 2)
        # Matching policies should contain 2 entries for shared_uuid
        self.assertEqual(len(matching_policies), 2)


if __name__ == '__main__':
    unittest.main()
