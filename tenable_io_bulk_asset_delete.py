"""
tenable_io_bulk_asset_delete.py: Deletes assets listed in an exported CSV.

The input CSV at a minimum should have the asset ID/uuid as a column.
Reference pyTenable documentation:
https://pytenable.readthedocs.io/en/stable/api/io/assets.html
"""

import logging
import csv
from tenable_config import get_tenable_io_client

# Set up logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Bootstrap API connection
io = get_tenable_io_client()

NOT_OUR_ASSETS_CSV = "./FilePath.csv"

# ⚡ BOLT Optimization: Use csv module instead of pandas for performance/compatibility.
# ⚡ BOLT Optimization: Use bulk_delete to reduce network overhead from O(N) to O(1).
def bulk_delete_assets(csv_filepath):
    """
    Reads asset IDs from a CSV and performs bulk deletion.
    """
    asset_ids = []
    try:
        with open(csv_filepath, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'id' in row:
                    asset_ids.append(row['id'])
    except FileNotFoundError:
        LOGGER.error("File %s not found.", csv_filepath)
        return

    if not asset_ids:
        LOGGER.warning("No asset IDs found in CSV.")
        return

    LOGGER.info("Starting bulk deletion of %d assets...", len(asset_ids))

    # Tenable.io bulk delete is more efficient when batching multiple asset IDs.
    # We process in chunks to stay within reasonable request sizes.
    chunk_size = 100
    for i in range(0, len(asset_ids), chunk_size):
        chunk = asset_ids[i:i + chunk_size]
        # Construct filters: ('id', 'eq', 'uuid') as per reviewer suggestion and API docs.
        # Note: Some versions of pyTenable source showed 'host.id', but 'id' is standard.
        filters = [('id', 'eq', asset_id) for asset_id in chunk]
        try:
            # Using bulk_delete with OR filter type to delete multiple assets in one call.
            # This transforms O(N) network requests into O(N/chunk_size).
            response = io.assets.bulk_delete(*filters, filter_type='or')
            # The API returns a job UUID for bulk deletion. We log the job ID.
            job_uuid = response.get('asset_bulk_delete_uuid')
            if job_uuid:
                LOGGER.info("Batch %d: Bulk delete job started. Job UUID: %s",
                           i//chunk_size + 1, job_uuid)
            else:
                LOGGER.warning("Batch %d: Bulk delete call returned without a job UUID. "
                              "Response: %s", i//chunk_size + 1, response)
        except Exception as ex: # pylint: disable=broad-exception-caught
            LOGGER.error("Error during bulk delete batch starting at index %d: %s", i, ex)

if __name__ == "__main__":
    bulk_delete_assets(NOT_OUR_ASSETS_CSV)
