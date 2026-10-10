"""
Unit test for tenable_io_get_ip_networks.py tag details caching.
"""
import unittest
from unittest.mock import MagicMock, patch
import logging

logging.basicConfig(level=logging.CRITICAL)

with patch('tenable.io.TenableIO'), patch('tenable_config.get_tenable_io_client'):
    from tenable_io_get_ip_networks import extract_ip_networks


class TestIPNetworksCaching(unittest.TestCase):
    """
    Test suite for verifying caching behavior in extract_ip_networks.
    """

    def test_extract_ip_networks_caching(self):
        """
        Verify that io.tags.details is called only once for duplicate tag targets across scans.
        """
        mock_client = MagicMock()

        # Mock scans
        mock_client.scans.list.return_value = [
            {'id': 101, 'name': 'Scan 1'},
            {'id': 102, 'name': 'Scan 2'},
        ]

        # Tag UUID shared by both scans
        shared_tag_uuid = "11111111-2222-3333-4444-555555555555"

        # Mock scan details
        def mock_scan_details(scan_id):
            return {
                'settings': {
                    'name': f"Scan {scan_id}",
                    'tag_targets': [shared_tag_uuid]
                }
            }

        mock_client.scans.details.side_effect = mock_scan_details

        # Mock tag details
        mock_client.tags.details.return_value = {
            'filters': {
                'asset': '{"and": [{"property": "ipv4", "value": ["10.0.0.0/24"]}]}'
            }
        }

        results = extract_ip_networks(mock_client)

        # Expect 2 records extracted (one per scan)
        self.assertEqual(len(results), 2)

        # Verify tag details was called exactly ONCE due to memory caching
        self.assertEqual(mock_client.tags.details.call_count, 1)
        mock_client.tags.details.assert_called_with(shared_tag_uuid)

        # Verify extracted properties
        self.assertEqual(results[0]['scan_id'], 101)
        self.assertEqual(results[0]['value'], '10.0.0.0/24')
        self.assertEqual(results[1]['scan_id'], 102)
        self.assertEqual(results[1]['value'], '10.0.0.0/24')


if __name__ == '__main__':
    unittest.main()
