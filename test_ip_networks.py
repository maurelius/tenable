"""Unit tests for tenable_io_get_ip_networks caching and scan network processing."""
import unittest
from unittest.mock import MagicMock
import pandas as pd
from tenable_io_get_ip_networks import _get_tag_filters, process_scan_ip_networks


class TestIPNetworksCaching(unittest.TestCase):
    """Test suite for IP network extraction tag caching logic."""

    def test_get_tag_filters_caching(self):
        """Verifies tag details lookup caching and hit/miss stats."""
        mock_io = MagicMock()
        tag_id = "tag-uuid-123"
        mock_tag_details = {
            "filters": {
                "asset": '{"and": [{"property": "ip", "value": ["10.0.0.0/16"]}]}'
            }
        }
        mock_io.tags.details.return_value = mock_tag_details

        cache = {}
        stats = {'hits': 0, 'misses': 0}

        # First call - cache miss
        result1 = _get_tag_filters(mock_io, tag_id, cache, stats)
        self.assertEqual(stats['hits'], 0)
        self.assertEqual(stats['misses'], 1)
        self.assertEqual(mock_io.tags.details.call_count, 1)

        # Second call - cache hit
        result2 = _get_tag_filters(mock_io, tag_id, cache, stats)
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 1)
        # Should not call io.tags.details again
        self.assertEqual(mock_io.tags.details.call_count, 1)
        self.assertEqual(result1, result2)

    def test_process_scan_ip_networks(self):
        """Verifies end-to-end processing of scan tag targets with caching."""
        mock_io = MagicMock()
        mock_io.scans.list.return_value = [
            {'id': 101, 'name': 'Scan A'},
            {'id': 102, 'name': 'Scan B'}
        ]

        tag_uuid = "shared-tag-uuid"
        mock_io.scans.details.side_effect = lambda scan_id: {
            'settings': {'tag_targets': [tag_uuid]}
        }

        mock_io.tags.details.return_value = {
            "filters": {
                "asset": '{"and": [{"property": "ip", "value": [["192.168.1.0/24"]]}]}'
            }
        }

        df = process_scan_ip_networks(mock_io)

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        # Verify tag details API was only called once across both scans due to caching
        self.assertEqual(mock_io.tags.details.call_count, 1)
        self.assertEqual(df.iloc[0]['value'], '192.168.1.0/24')
        self.assertEqual(df.iloc[1]['value'], '192.168.1.0/24')


if __name__ == '__main__':
    unittest.main()
