import unittest
from unittest.mock import MagicMock, patch
import json
from tenable_io_get_ip_networks import _process_scan, _get_tag_filters

class TestIPNetworksCaching(unittest.TestCase):
    def setUp(self):
        self.mock_io = MagicMock()
        self.tag_id = "tag-123"
        self.scan = {'id': 'scan-456', 'name': 'Test Scan'}
        self.filter_data = {'and': [{'property': 'ip', 'value': '192.168.1.0/24'}]}
        self.tag_details = {
            'filters': {
                'asset': json.dumps(self.filter_data)
            }
        }

    def test_get_tag_filters_caching(self):
        tag_cache = {}
        self.mock_io.tags.details.return_value = self.tag_details

        # First call - Miss
        filters, is_hit = _get_tag_filters(self.mock_io, self.tag_id, tag_cache)
        self.assertFalse(is_hit)
        self.assertEqual(filters, self.filter_data['and'])
        self.assertEqual(self.mock_io.tags.details.call_count, 1)

        # Second call - Hit
        filters, is_hit = _get_tag_filters(self.mock_io, self.tag_id, tag_cache)
        self.assertTrue(is_hit)
        self.assertEqual(filters, self.filter_data['and'])
        self.assertEqual(self.mock_io.tags.details.call_count, 1) # Still 1

    def test_process_scan_with_caching(self):
        tag_cache = {}
        stats = {'hits': 0, 'misses': 0}
        self.mock_io.scans.details.return_value = {
            'settings': {'tag_targets': [self.tag_id]}
        }
        self.mock_io.tags.details.return_value = self.tag_details

        # Process first scan - Cache Miss
        results1 = _process_scan(self.mock_io, self.scan, tag_cache, stats)
        self.assertEqual(len(results1), 1)
        self.assertEqual(stats['misses'], 1)
        self.assertEqual(stats['hits'], 0)

        # Process second scan (different scan, same tag) - Cache Hit
        scan2 = {'id': 'scan-789', 'name': 'Scan 2'}
        self.mock_io.scans.details.return_value = {
            'settings': {'tag_targets': [self.tag_id]}
        }
        results2 = _process_scan(self.mock_io, scan2, tag_cache, stats)
        self.assertEqual(len(results2), 1)
        self.assertEqual(stats['misses'], 1)
        self.assertEqual(stats['hits'], 1)

        # Verify API calls
        self.assertEqual(self.mock_io.tags.details.call_count, 1)

if __name__ == '__main__':
    unittest.main()
