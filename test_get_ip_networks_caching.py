"""
Unit tests for tenable_io_get_ip_networks.py tag caching and extraction logic.
"""
import unittest
from unittest.mock import MagicMock
from tenable_io_get_ip_networks import (
    _get_tag_filters,
    _extract_item_value,
    collect_scan_target_networks,
)


class TestGetIpNetworksCaching(unittest.TestCase):
    """Test suite verifying caching behavior and value extraction in tenable_io_get_ip_networks."""

    def test_get_tag_filters_caching(self):
        """Verifies that _get_tag_filters caches lookups and reduces API calls."""
        mock_client = MagicMock()
        tag_uuid = "11111111-2222-3333-4444-555555555555"

        mock_client.tags.details.return_value = {
            "filters": {
                "asset": (
                    '{"and": [{"property": "ipv4", "operator": "eq", "value": ["10.0.0.0/24"]}]}'
                )
            }
        }

        tag_cache = {}
        stats = {"hits": 0, "misses": 0}

        # First lookup (cache miss)
        res1 = _get_tag_filters(mock_client, tag_uuid, tag_cache, stats)
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0]["property"], "ipv4")
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(mock_client.tags.details.call_count, 1)

        # Second lookup (cache hit)
        res2 = _get_tag_filters(mock_client, tag_uuid, tag_cache, stats)
        self.assertEqual(res2, res1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(mock_client.tags.details.call_count, 1)

    def test_extract_item_value(self):
        """Tests scalar and nested list extraction helper."""
        tag_uuid = "test-uuid"
        self.assertEqual(_extract_item_value("192.168.1.1", tag_uuid), "192.168.1.1")
        self.assertEqual(_extract_item_value(["10.0.0.1"], tag_uuid), "10.0.0.1")
        self.assertEqual(_extract_item_value([["172.16.0.1"]], tag_uuid), "172.16.0.1")

    def test_collect_scan_target_networks_integration(self):
        """Tests full scan targets collection with shared tag across multiple scans."""
        mock_client = MagicMock()
        tag_uuid = "shared-tag-uuid"

        mock_client.scans.list.return_value = [
            {"id": 1, "name": "Scan 1"},
            {"id": 2, "name": "Scan 2"},
        ]

        mock_client.scans.details.side_effect = lambda scan_id: {
            "settings": {"tag_targets": [tag_uuid]}
        }

        mock_client.tags.details.return_value = {
            "filters": {
                "asset": (
                    '{"and": [{"property": "ipv4", '
                    '"operator": "eq", "value": ["192.168.0.0/16"]}]}'
                )
            }
        }

        data = collect_scan_target_networks(mock_client)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["scan_name"], "Scan 1")
        self.assertEqual(data[1]["scan_name"], "Scan 2")
        self.assertEqual(data[0]["value"], "192.168.0.0/16")
        self.assertEqual(data[1]["value"], "192.168.0.0/16")

        # io.tags.details should be called only ONCE for the shared tag
        self.assertEqual(mock_client.tags.details.call_count, 1)


if __name__ == "__main__":
    unittest.main()
