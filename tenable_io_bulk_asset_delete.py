"""tenable_io_bulk_asset_delete.py: Deletes assets listed in an exported CSV"""
"""The input CSV at a minimum should have the asset ID/uuid as a column"""
"""Reference pyTenable documentation: https://pytenable.readthedocs.io/en/stable/api/io/assets.html"""

from tenable.io import TenableIO
import logging

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Define keys to auth to API
accessKey = '1234'
secretKey = '1234'
# Bootstrap API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)

not_our_assets_csv = "./FilePath.csv"

for index, row in not_our_assets_csv.iterrows():
     print(f"Deleting Asset ID: {row['id']} - Host Name: {row['host_name']}")
     try:
         io.assets.delete(uuid=str(row['id']))
     except Exception as ex:
         print(ex)