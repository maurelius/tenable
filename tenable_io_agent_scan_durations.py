"""tenable_io_agent_scan_durations.py: Grabs the scan durations from every agent, averages them, then calculates a total combined average"""

# Setup modules
import re
from tenable.io import TenableIO
import logging
from collections import defaultdict

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
## Define API keys
accessKey = '1234'
secretKey = '1234'
# Bootstrap Tenable API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)

# Retrieve vulnerability outputs for the specified plugin
plugin_id = 19506  # Adjust as necessary
data = io.workbenches.vuln_outputs(plugin_id=plugin_id)

# Initialize a dictionary to store scan durations by asset
asset_scans = defaultdict(list)

# Regular expression to extract scan duration
duration_pattern = re.compile(r'Scan duration\s*:\s*(\d+)\s*sec')

# Process each entry in the data
for entry in data:
    plugin_output = entry.get('plugin_output', '')
    # Extract scan duration
    match = duration_pattern.search(plugin_output)
    if match:
        duration = int(match.group(1))
        # Extract asset information
        for state in entry.get('states', []):
            for result in state.get('results', []):
                for asset in result.get('assets', []):
                    fqdn = asset.get('fqdn', 'Unknown')
                    asset_scans[fqdn].append(duration)

# Calculate average scan duration for each asset
average_durations = {}
total_sum = 0  # Initialize the total sum of scan durations
for fqdn, durations in asset_scans.items():
    average_durations[fqdn] = sum(durations) / len(durations)
    total_sum += sum(durations)  # Add the sum of durations for this asset to the total
    total_len = len(asset_scans) # How many entries are there? We'll calculate the total average later
    total_avg = total_sum / total_len # Divide the sum by total number of entries in durations
    total_minutes = total_avg / 60 # Divide total_avg (combined total) by 60 to convert to minutes

# Output the results
for fqdn, avg_duration in average_durations.items():
    print(f'Asset: {fqdn}, Average Scan Duration: {avg_duration:.2f} seconds')

# Output the total sum of scan durations and combined average
print(f'\nTotal Sum of All Scan Durations: {total_sum} seconds\nCombined average of all scans (seconds): {total_avg:.2f}\nCombined average of all scans (minutes): {total_minutes}')