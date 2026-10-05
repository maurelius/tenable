"""Unit tests for tag details caching in tenable_io_get_ip_networks.py."""
import json
from unittest.mock import MagicMock
from tenable_io_get_ip_networks import process_scan_tag_networks


def test_tag_caching_and_deduplication():
    """Verify that tag details lookups are cached across scans."""
    mock_tio = MagicMock()

    # Two scans sharing the same tag ID "tag-123" and scan 2 also having "tag-456"
    mock_tio.scans.list.return_value = [
        {'id': 101, 'name': 'Scan A'},
        {'id': 102, 'name': 'Scan B'},
    ]

    def mock_scan_details(scan_id):
        if scan_id == 101:
            return {'settings': {'tag_targets': ['tag-123']}}
        if scan_id == 102:
            return {'settings': {'tag_targets': ['tag-123', 'tag-456']}}
        return {}

    mock_tio.scans.details.side_effect = mock_scan_details

    def mock_tag_details(tag_id):
        if tag_id == 'tag-123':
            filter_obj = {
                'and': [
                    {'property': 'ipv4', 'value': ['192.168.1.0/24']}
                ]
            }
            return {'filters': {'asset': json.dumps(filter_obj)}}
        if tag_id == 'tag-456':
            filter_obj = {
                'and': [
                    {'property': 'ipv4', 'value': ['10.0.0.0/8']}
                ]
            }
            return {'filters': {'asset': json.dumps(filter_obj)}}
        return {}

    mock_tio.tags.details.side_effect = mock_tag_details

    data, stats = process_scan_tag_networks(mock_tio)

    # Verify results
    assert len(data) == 3  # Scan A: 1 item, Scan B: 2 items
    # tag-123 is looked up 2 times across scans -> 1 miss, 1 hit
    # tag-456 is looked up 1 time -> 1 miss
    # Total: 1 hit, 2 misses
    assert stats['hits'] == 1
    assert stats['misses'] == 2

    # Verify mock call count to io.tags.details
    assert mock_tio.tags.details.call_count == 2
