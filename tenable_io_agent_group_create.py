#!/usr/bin/python

""" tenable_io_agent_group_create.py: Creates an agent group that agent scans can reference"""
""" Reference pyTenable Documentation: https://pytenable.readthedocs.io/en/stable/api/io/scans.html#tenable.io.scans.ScansAPI.create """

### Import Modules
import logging
from pprint import pprint
from tenable.io import TenableIO

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
GROUP_NAME = input('Enter a name for the new agent group: ')
# Define keys to auth to API
accessKey = '1234'
secretKey = '1234'
# Bootstrap API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)
# Create the agent group
io.agent_groups.create(GROUP_NAME)