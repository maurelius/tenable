"""
tenable_io_bulk_asset_delete.py: Deletes assets listed in an exported CSV.
The input CSV at a minimum should have the asset ID/uuid as a column.
Reference pyTenable documentation: https://pytenable.readthedocs.io/en/stable/api/io/assets.html
"""

import csv
import logging
import csv
from tenable_config import get_tenable_io_client

# Set up logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

def bulk_delete_assets_from_csv(io_client, csv_path):
    """
    Reads asset IDs from a CSV and deletes them in bulk.
    """
    # ⚡ BOLT Optimization: Use io.assets.bulk_delete to minimize API calls.
    # This reduces the number of API calls from O(N) to O(1) for a batch of assets.
    # By batching deletions, we significantly reduce network overhead and API rate limiting risk.
    try:
        asset_ids = []
        with open(csv_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row.get('id'):
                    asset_ids.append(row['id'])

        if asset_ids:
            LOGGER.info("Deleting %d assets in bulk...", len(asset_ids))
            # Construct filters for bulk_delete. We use 'or' to match any of the IDs.
            filters = [('id', 'eq', asset_id) for asset_id in asset_ids]
            io_client.assets.bulk_delete(*filters, filter_type='or')
            LOGGER.info("Bulk delete operation completed.")
            return True

        LOGGER.warning("No asset IDs found in CSV.")
        return False

    except FileNotFoundError:
        LOGGER.error("CSV file not found: %s", csv_path)
        return False
    except Exception as ex: # pylint: disable=broad-exception-caught
        LOGGER.error("An error occurred: %s", ex)
        return False

if __name__ == "__main__":
    ### Define some Variables
    # Bootstrap API connection
    IO_CLIENT = get_tenable_io_client()
    NOT_OUR_ASSETS_CSV = "./FilePath.csv"

    bulk_delete_assets_from_csv(IO_CLIENT, NOT_OUR_ASSETS_CSV)
