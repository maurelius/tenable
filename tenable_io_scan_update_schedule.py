""" tenable_io_scan_update_schedule.py: Updates the schedule for scans in FOLDER_ID"""
""" See: https://pytenable.readthedocs.io/en/stable/api/io/scans.html#tenable.io.scans.ScansAPI.create_scan_schedule"""

### Import Modules
import tqdm
import datetime
from tenable_config import get_tenable_io_client

### Define some Variables
# What folder are the scans in? [int]
FOLDER_ID = 0000

# What date/time do you want the scan to be scheduled?
# There's probably a better way to do this, but for now use this
d = datetime.datetime(2023,1,1,19,00,00,00)

# Bootstrap API connection
io = get_tenable_io_client()

### Loop through scans in folder, configure and update the schedule
# ⚡ BOLT Optimization: Move schedule configuration outside the loop.
# This reduces O(N) redundant dictionary constructions to O(1) and fixes a TypeError
# where each_scan['id'] was incorrectly passed as the 'enabled' parameter.
# Use this for timezone reference: https://developer.tenable.com/reference/scans-timezones
config_schedule = io.scans.configure_scan_schedule(
    enabled=False,
    frequency='ONETIME',
    interval=2,
    weekdays='SA',
    day_of_month=4,
    starttime=d,
    timezone='America/Chicago'
)

for each_scan in tqdm.tqdm(io.scans.list(folder_id=FOLDER_ID)):
    try:
        io.scans.configure(each_scan['id'], schedule_scan=config_schedule)
    except Exception as ex:
        print(ex)
        continue