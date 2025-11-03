""" tenable_io_agent_group_create.py: Creates an agent group that agent scans can reference"""
""" Reference pyTenable Documentation: https://pytenable.readthedocs.io/en/stable/api/io/scans.html#tenable.io.scans.ScansAPI.create """

### Import Modules
import logging
from tenable_config import get_tenable_io_client

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
GROUP_NAME = input('Enter a name for the new agent group: ')
# Bootstrap API connection
io = get_tenable_io_client()
# Create the agent group
io.agent_groups.create(GROUP_NAME)