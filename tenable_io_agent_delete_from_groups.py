"""tenable_io_agent_delete_from_groups.py: Deletes agents from every group that doesn't start with a specific string and excludes agents from specific subnets. """
""" This preserves agents that are not in the previously specified group so they won't get deleted. Also helps identify any stragglers that should be in other groups. """

import logging

from tqdm import tqdm
import ipaddress
from tenable_config import get_tenable_io_client

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Bootstrap API connection
io = get_tenable_io_client()

agent_groups = [(d['id'], d['name']) for d in io.agent_groups.list() if not d['name'].startswith('CHANGE-ME')]
agents = io.agents.list()
# Change to the subnets you want excluded
exclude_subnets = [ipaddress.ip_network('10.10.0.0/12'), ipaddress.ip_network('172.16.0.0/16'), ipaddress.ip_network('192.168.1.0/24')]
agents_filtered = [d for d in agents if not any(ipaddress.ip_address(d['ip']) in subnet for subnet in exclude_subnets) and 'CHANGE-ME' not in d]

for id, name in agent_groups:
    try:
        print(f"Deleting agents from group: {name}")
        io.agent_groups.delete_agent(group_id=id)
    except:
        print(f"Error deleting agent(s) in group {name}", {Exception})
        
for id, name in tqdm(agent_groups):
    try:
        print(f"Deleting agent group {name}...")
        io.agent_groups.delete(id)
    except:
        print(f"Error deleting group {name}", Exception)