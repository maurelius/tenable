""" tenable_io_agent_group_create.py: Creates an agent group that agent scans can reference"""
""" Reference pyTenable Documentation: https://pytenable.readthedocs.io/en/stable/api/io/scans.html#tenable.io.scans.ScansAPI.create """

### Import Modules
import logging
import os
from tenable.io import TenableIO

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
GROUP_NAME = input('Enter a name for the new agent group: ')
# Bootstrap API connection
io = TenableIO(os.getenv('TENABLE_ACCESS_KEY'), os.getenv('TENABLE_SECRET_KEY'))
# Create the agent group
io.agent_groups.create(GROUP_NAME)