"""Unit tests for tenable_io_get_ip_networks.py tag caching and extraction."""

import json
import unittest
from unittest.mock import MagicMock
import pandas as pd
from tenable_io_get_ip_networks import (
    extract_scan_ip_networks,
    generate_report,
    _get_tag_filters
)


class TestGetIpNetworksCaching(unittest.TestCase):
    """Test suite for tag caching and scan extraction logic."""

    def test_get_tag_filters_cache_hit_and_miss(self):
        """Verify _get_tag_filters uses cache on subsequent lookups and records stats."""
        mock_client = MagicMock()
        tag_id = "tag-uuid-1"
        asset_filters = json.dumps({"and": [{"property": "ipv4", "value": "10.0.0.0/24"}]})
        mock_client.tags.details.return_value = {"filters": {"asset": asset_filters}}

        tag_cache = {}
        cache_stats = {'hits': 0, 'misses': 0}

        # First call: cache miss
        filters1 = _get_tag_filters(mock_client, tag_id, tag_cache, cache_stats)
        self.assertEqual(len(filters1), 1)
        self.assertEqual(cache_stats['misses'], 1)
        self.assertEqual(cache_stats['hits'], 0)
        self.assertEqual(mock_client.tags.details.call_count, 1)

        # Second call: cache hit
        filters2 = _get_tag_filters(mock_client, tag_id, tag_cache, cache_stats)
        self.assertEqual(filters2, filters1)
        self.assertEqual(cache_stats['misses'], 1)
        self.assertEqual(cache_stats['hits'], 1)
        self.assertEqual(mock_client.tags.details.call_count, 1)

    def test_extract_scan_ip_networks_shared_tags(self):
        """Verify extract_scan_ip_networks avoids redundant tag API calls across multiple scans."""
        mock_client = MagicMock()

        # Mock 2 scans sharing tag-uuid-1
        mock_client.scans.list.return_value = [
            {'id': 101, 'name': 'Scan A'},
            {'id': 102, 'name': 'Scan B'}
        ]

        # Both scans target tag-uuid-1
        mock_client.scans.details.side_effect = [
            {'settings': {'tag_targets': ['tag-uuid-1']}},
            {'settings': {'tag_targets': ['tag-uuid-1']}}
        ]

        asset_filters = json.dumps({"and": [{"property": "ipv4", "value": [["192.168.1.0/24"]]}]})
        mock_client.tags.details.return_value = {"filters": {"asset": asset_filters}}

        df, cache_stats = extract_scan_ip_networks(io_client=mock_client)

        self.assertEqual(len(df), 2)
        self.assertEqual(cache_stats['hits'], 1)
        self.assertEqual(cache_stats['misses'], 1)
        # Verify tag API called only once despite 2 scans referencing it
        self.assertEqual(mock_client.tags.details.call_count, 1)
        self.assertIn('192.168.1.0/24', df['value'].values)

    def test_generate_report(self):
        """Verify generate_report executes without error."""
        df = pd.DataFrame([
            {
                'scan_id': 101,
                'scan_name': 'Scan A',
                'tag_id': 'tag-1',
                'property': 'ipv4',
                'value': '10.0.0.0/24'
            }
        ])
        mock_open = MagicMock()
        with unittest.mock.patch("builtins.open", mock_open):
            generate_report(df, output_filepath='dummy.md')
        mock_open.assert_called_once_with('dummy.md', 'w', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
