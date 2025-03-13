"""tenable_io_export_vulns.py: Exports vulnerability data observed in the last 24 hours based on tag and VPR score to disk"""
"""Reference pyTenable Documentation: https://pytenable.readthedocs.io/en/stable/api/io/exports.html"""

### Import Modules
import arrow
import json
import logging
import tqdm
from tenable.io import TenableIO

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Define keys to auth to API
accessKey = '1234'
secretKey = '1234'
# Bootstrap API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)
# Only use data from assets in the Default Network - Change if you need to
NETWORK = 'Default'
### Define export parameters
# What tag should you use? [('Category', 'Value')]
TAGS = [('Category', 'NY Windows Servers')]
# What VPR Score (and higher) do you want to filter for? [int]
VPR_SCORE = 8.5
# Set timestamp for the last 24 hours
D = int(arrow.now().shift(days=-1).timestamp())

# Bootstrap API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey, vendor='John Doe', product='Export Vuln Data')

### Define functions to get stuff
# Function for JSON serialization
def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

# Function to get UUID of Network NAME
def get_network_uuid(NETWORK):
    for nw in io.networks.list(('name', 'match', NETWORK)):
        return(nw['uuid'])
# Call function to get UUID for the Default network
NETWORK_ID = get_network_uuid(NETWORK)

# Function to download vuln data in chunks and write them to disk
def write_chunk(data,
                export_uuid: str,
                export_type: str,
                export_chunk_id: int
                ):
    fn = f'{export_type}-{export_uuid}-{export_chunk_id}.json'
    with open(fn,'w') as fobj:
            json.dump(data, fobj)

# Grab vulnerabilities using above filters/variables
export = io.exports.vulns(network_id=NETWORK_ID, tags=TAGS, vpr_score=({'gte':VPR_SCORE}), since=D)
tqdm.tqdm(export.run_threaded(write_chunk, num_threads=4))