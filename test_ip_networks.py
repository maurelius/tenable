"""Unit tests for tenable_io_get_ip_networks.py"""
import json
import unittest
from unittest.mock import MagicMock, patch
import logging

logging.basicConfig(level=logging.CRITICAL)

with patch('tenable.io.TenableIO'), patch('tenable_config.get_tenable_io_client'):
    from tenable_io_get_ip_networks import fetch_scan_ip_networks, _extract_item_value


class TestIPNetworks(unittest.TestCase):
    """Test suite for IP network extraction and tag caching logic."""

    def test_extract_item_value(self):
        """Verify _extract_item_value properly unpacks nested lists and scalar values."""
        self.assertEqual(_extract_item_value({'value': [['192.168.1.0/24']]}), '192.168.1.0/24')
        self.assertEqual(_extract_item_value({'value': ['10.0.0.0/8']}), '10.0.0.0/8')
        self.assertEqual(_extract_item_value({'value': '172.16.0.0/12'}), '172.16.0.0/12')
        self.assertIsNone(_extract_item_value({'value': [[]]}))

    def test_fetch_scan_ip_networks_caching(self):
        """Verify io.tags.details is called once for repeated tag IDs across multiple scans."""
        mock_io = MagicMock()

        tag_id = "tag-123-abc"
        filter_dict = {
            "asset": json.dumps({
                "and": [
                    {"property": "ip", "value": [["192.168.1.0/24"]]}
                ]
            })
        }

        mock_io.scans.list.return_value = [
            {'id': 101, 'name': 'Scan A'},
            {'id': 102, 'name': 'Scan B'}
        ]

        mock_io.scans.details.side_effect = [
            {'settings': {'tag_targets': [tag_id]}},
            {'settings': {'tag_targets': [tag_id]}}
        ]

        mock_io.tags.details.return_value = {'filters': filter_dict}

        results = fetch_scan_ip_networks(mock_io)

        self.assertEqual(len(results), 2)
        # Verify tag details endpoint was called only ONCE due to caching
        self.assertEqual(mock_io.tags.details.call_count, 1)
        mock_io.tags.details.assert_called_with(tag_id)

        self.assertEqual(results[0]['scan_id'], 101)
        self.assertEqual(results[0]['value'], '192.168.1.0/24')
        self.assertEqual(results[1]['scan_id'], 102)
        self.assertEqual(results[1]['value'], '192.168.1.0/24')


if __name__ == '__main__':
    unittest.main()
