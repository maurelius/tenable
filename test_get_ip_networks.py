"""Unit tests for tenable_io_get_ip_networks.py tag caching and extraction logic."""

import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

with patch('tenable.io.TenableIO'):
    from tenable_io_get_ip_networks import (
        extract_all_scan_networks,
        _extract_filter_value
    )


class TestGetIPNetworks(unittest.TestCase):
    """Test suite for IP networks extraction and tag caching."""

    def test_extract_filter_value(self):
        """Verify extraction of flat values from different nested list formats."""
        self.assertEqual(_extract_filter_value('10.0.0.0/24'), '10.0.0.0/24')
        self.assertEqual(_extract_filter_value(['192.168.1.0/24']), '192.168.1.0/24')
        self.assertEqual(_extract_filter_value([['172.16.0.0/12']]), '172.16.0.0/12')
        self.assertEqual(_extract_filter_value([]), [])

    def test_tag_caching_and_extraction(self):
        """Verify tag details are cached across multiple scans using the same tag ID."""
        mock_io = MagicMock()

        tag_id = "tag-uuid-1234"
        mock_io.scans.list.return_value = [
            {'id': 101, 'name': 'Scan A'},
            {'id': 102, 'name': 'Scan B'},
        ]

        def mock_scan_details(_scan_id):
            return {
                'settings': {
                    'tag_targets': [tag_id]
                }
            }

        mock_io.scans.details.side_effect = mock_scan_details

        asset_filters = '{"and": [{"property": "ip", "operator": "eq", "value": "10.0.0.0/24"}]}'
        mock_io.tags.details.return_value = {
            'filters': {
                'asset': asset_filters
            }
        }

        df = extract_all_scan_networks(mock_io)

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        # Verify tag details was called exactly ONCE due to caching across both scans
        self.assertEqual(mock_io.tags.details.call_count, 1)
        mock_io.tags.details.assert_called_with(tag_id)

        # Verify extracted properties
        self.assertListEqual(df['scan_id'].tolist(), [101, 102])
        self.assertListEqual(df['value'].tolist(), ['10.0.0.0/24', '10.0.0.0/24'])


if __name__ == '__main__':
    unittest.main()
