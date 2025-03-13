"""tenable_io_get_scan_templates_by_plugin_id.py: Gets scan templates that use a list of plugin IDs."""
"""This is useful for finding what scans may be affected by template changes"""

# Import Modules
import logging
import pandas as pd
from tenable.io import TenableIO

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Define keys to auth to API
accessKey = '1234'
secretKey = '1234'
# Bootstrap API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)
folders = io.folders.list()
folder_id = [d for d in folders if d['name'] == "My Scans"][0]['id']
scans = io.scans.list(folder_id)
df = pd.DataFrame({'wizard_uuid': [scan['wizard_uuid'] for scan in scans]})
df_dedup = df.drop_duplicates()

# Define Plugin IDs you want to use
plugin_ids = ['34220','34252','11219','14272','25221','10736','99265','10335','14274','34277']
scan_templates = io.editor.template_list('policy')

for wizard_uuid in df_dedup['wizard_uuid']:
    try:
        template_details = io.editor.template_details('policy', wizard_uuid)
        # Process template_details as needed
        preferences = template_details.get("settings", {}).get("discovery", {}).get("modes", {})
        matching_plugin_ids = [plugin_id for plugin_id in plugin_ids if plugin_id in preferences]
        if matching_plugin_ids:
            # Print the policy name/title and its UUID
            name = template_details.get("name")
            policy_uuid = template_details.get("uuid")
            print(f"Policy Name/Title: {name}")
            print(f"Policy UUID: {policy_uuid}")
    except Exception as e:
        print(f"Error for wizard_uuid {wizard_uuid}: {str(e)}")

for template in scan_templates:
    uuid = template['uuid']
    # Get the template details as a dictionary
    template_details = io.editor.template_details('policy', uuid)
    # Extract policy information from preferences
    preferences = template_details.get("settings", {}).get("discovery", {}).get("modes", {})
    # Check if any of the plugin IDs are in preferences
    matching_plugin_ids = [plugin_id for plugin_id in plugin_ids if plugin_id in preferences]
    if matching_plugin_ids:
        # Print the policy name/title and its UUID
        name = template_details.get("name")
        policy_uuid = uuid
        print(f"Policy Name/Title: {name}")
        print(f"Policy UUID: {policy_uuid}")