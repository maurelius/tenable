"""test_tag_details.py - Unit tests for tenable_io_get_tag_details.py optimization"""

import sys
import unittest
from unittest.mock import MagicMock, patch, mock_open

import pandas as _pd  # pylint: disable=unused-import


class TestTagDetailsOptimization(unittest.TestCase):
    """Test suite verifying server-side category filtering optimization in tag details script."""

    @patch('builtins.input', return_value='Location')
    @patch('tenable_config.get_tenable_io_client')
    def test_server_side_tag_category_filtering(self, mock_get_client, _mock_input):
        """Verify server-side category filter ('category_name', 'eq', category)."""
        mock_io = MagicMock()
        mock_get_client.return_value = mock_io

        tag_uuid = '11111111-1111-1111-1111-111111111111'
        mock_io.tags.list.return_value = [
            {'category_name': 'Location', 'uuid': tag_uuid}
        ]

        mock_io.tags.details.return_value = {
            'filters': {
                'asset': '{"and": [{"property": "ip", "operator": "eq", "value": "10.0.0.0/24"}]}'
            }
        }

        real_open = open
        m_open = mock_open()

        def custom_open(file, *args, **kwargs):
            if isinstance(file, str) and file == 'TENABLE-SUBNETS.md':
                return m_open(file, *args, **kwargs)
            return real_open(file, *args, **kwargs)

        if 'tenable_io_get_tag_details' in sys.modules:
            del sys.modules['tenable_io_get_tag_details']

        with patch('builtins.open', side_effect=custom_open):
            import tenable_io_get_tag_details  # pylint: disable=import-outside-toplevel,unused-import

        mock_io.tags.list.assert_called_once_with(('category_name', 'eq', 'Location'))


if __name__ == '__main__':
    unittest.main()
