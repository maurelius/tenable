"""tenable_io_bulk_asset_delete.py: Deletes assets listed in an exported CSV"""
"""The input CSV at a minimum should have the asset ID/uuid as a column"""
"""Reference pyTenable documentation: https://pytenable.readthedocs.io/en/stable/api/io/assets.html"""

import logging
import os
from tenable.io import TenableIO

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Bootstrap API connection
io = TenableIO(os.getenv('TENABLE_ACCESS_KEY'), os.getenv('TENABLE_SECRET_KEY'))

not_our_assets_csv = "./FilePath.csv"

for index, row in not_our_assets_csv.iterrows():
     print(f"Deleting Asset ID: {row['id']} - Host Name: {row['host_name']}")
     try:
         io.assets.delete(uuid=str(row['id']))
     except Exception as ex:
         print(ex)