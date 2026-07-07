"""tenable_io_bulk_asset_delete.py: Deletes assets listed in an exported CSV"""
"""The input CSV at a minimum should have the asset ID/uuid as a column"""
"""Reference pyTenable documentation: https://pytenable.readthedocs.io/en/stable/api/io/assets.html"""

import csv
import logging
from tenable_config import get_tenable_io_client

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Bootstrap API connection
io = get_tenable_io_client()

NOT_OUR_ASSETS_CSV = "./FilePath.csv"

asset_ids = []
try:
    with open(NOT_OUR_ASSETS_CSV, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if 'id' in row:
                asset_ids.append(row['id'])

    if asset_ids:
        print(f"Attempting to bulk delete {len(asset_ids)} assets...")
        # ⚡ BOLT Optimization: Use bulk_delete with filters to reduce API calls from O(N) to O(1).
        # In pyTenable 1.4.13, bulk_delete handles multiple IDs via filter criteria.
        io.assets.bulk_delete(('id', 'eq', asset_ids))
        print("Bulk delete operation requested successfully.")
    else:
        print("No asset IDs found to delete.")

except FileNotFoundError:
    logging.error("CSV file not found: %s", NOT_OUR_ASSETS_CSV)
except Exception as e:
    logging.error("An error occurred during bulk deletion: %s", e)
