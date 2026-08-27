"""
Unit tests for tag details lookup caching in tenable_io_get_ip_networks.py
"""
import json
import unittest
from unittest.mock import MagicMock
from tenable_io_get_ip_networks import extract_ip_networks_from_scans

class TestIPNetworksCaching(unittest.TestCase):
    """Tests tag details lookup caching and data extraction logic."""

    def test_tag_details_caching(self):
        """Verify that identical tag IDs across multiple scans reuse cached tag details."""
        mock_tio = MagicMock()

        # Mock scans.list returning 3 scans sharing tag 'tag-uuid-1'
        mock_tio.scans.list.return_value = [
            {'id': 101, 'name': 'Scan A'},
            {'id': 102, 'name': 'Scan B'},
            {'id': 103, 'name': 'Scan C'}
        ]

        # Mock scans.details returning tag_targets = ['tag-uuid-1']
        mock_tio.scans.details.side_effect = lambda scan_id: {
            'settings': {
                'tag_targets': ['tag-uuid-1']
            }
        }

        # Mock tags.details returning filter structure
        mock_tio.tags.details.return_value = {
            'filters': {
                'asset': json.dumps({
                    'and': [
                        {'property': 'ipv4', 'value': ['192.168.1.0/24']}
                    ]
                })
            }
        }

        df = extract_ip_networks_from_scans(mock_tio)

        # Confirm tag details was only called ONCE for 'tag-uuid-1' despite 3 scans
        self.assertEqual(mock_tio.tags.details.call_count, 1)
        mock_tio.tags.details.assert_called_once_with('tag-uuid-1')

        # Confirm all 3 scans extracted data correctly
        self.assertEqual(len(df), 3)
        self.assertListEqual(list(df['scan_id']), [101, 102, 103])
        self.assertTrue(all(val == '192.168.1.0/24' for val in df['value']))

if __name__ == '__main__':
    unittest.main()
