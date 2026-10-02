"""Unit test for tenable_io_scan_elapsed.py optimization"""
import unittest
from unittest.mock import MagicMock, patch

class TestScanElapsedOptimization(unittest.TestCase):
    """Test case verifying that io.scans.details is called O(1) times instead of O(N)"""

    @patch('tenable_config.get_tenable_io_client')
    def test_scan_details_called_once(self, mock_get_client):
        """Verify scan.details is only called once when processing multiple history records"""
        mock_io = MagicMock()
        mock_get_client.return_value = mock_io

        # Set status to completed
        mock_io.scans.status.return_value = 'completed'

        # Return mock details
        mock_io.scans.details.return_value = {
            "settings": {"name": "Test Scan"}
        }

        # Return 3 history items
        mock_io.scans.history.return_value = [
            {'time_start': 1000, 'time_end': 2000},
            {'time_start': 3000, 'time_end': 4000},
            {'time_start': 5000, 'time_end': 6000},
        ]

        # Import and execute logic under mock patch
        # Executing the script code directly via exec in isolated globals
        with open('tenable_io_scan_elapsed.py', 'r', encoding='utf-8') as f:
            script_code = f.read()

        exec_globals = {
            '__name__': '__main__',
            'get_tenable_io_client': mock_get_client,
        }

        exec(script_code, exec_globals)

        # Verify io.scans.details was called exactly ONCE despite 3 history records
        self.assertEqual(mock_io.scans.details.call_count, 1)
        mock_io.scans.details.assert_called_with(0)

if __name__ == '__main__':
    unittest.main()
