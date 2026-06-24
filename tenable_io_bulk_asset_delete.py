"""tenable_io_bulk_asset_delete.py: Deletes assets listed in an exported CSV"""
"""The input CSV at a minimum should have the asset ID/uuid as a column named 'id'"""
"""Reference pyTenable documentation: https://pytenable.readthedocs.io/en/stable/api/io/assets.html"""

import logging
import csv
from tenable_config import get_tenable_io_client

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Bootstrap API connection
io = get_tenable_io_client()

# Path to the CSV file containing assets to delete
# The CSV should have a column named 'id'
NOT_OUR_ASSETS_CSV = "./FilePath.csv"

def bulk_delete_assets(csv_filepath):
    """
    Reads asset IDs from a CSV and performs a bulk deletion.
    """
    asset_ids = []

    try:
        with open(csv_filepath, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'id' in row:
                    asset_ids.append(str(row['id']))
                else:
                    logging.error("CSV row missing 'id' column: %s", row)
    except FileNotFoundError:
        print(f"Error: {csv_filepath} not found. Please ensure the file exists.")
        return
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    if not asset_ids:
        print("No asset IDs found to delete.")
        return

    print(f"Found {len(asset_ids)} assets. Starting bulk deletion...")

    # ⚡ BOLT Optimization: Use bulk deletion to reduce network overhead.
    # Instead of calling io.assets.delete() in a loop (O(N) network requests),
    # we pass all UUIDs to io.assets.delete() which performs a single
    # bulk_delete call (O(1) network request) internally in pyTenable.
    try:
        # In pyTenable, io.assets.delete can take multiple UUIDs as positional arguments
        io.assets.delete(*asset_ids)
        print(f"Successfully initiated bulk deletion for {len(asset_ids)} assets.")
    except Exception as ex:
        print(f"Error during bulk deletion: {ex}")

if __name__ == "__main__":
    bulk_delete_assets(NOT_OUR_ASSETS_CSV)
