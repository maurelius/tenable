"""tenable_io_published_dates.py: Grabs a subset of CVE publication dates, Tenable plugin publication dates and calculates the average time between CVE and Plugin publications"""

import logging
from tenable.io import TenableIO
from datetime import datetime, timedelta
import statistics

### Define some Variables
# Set up logging
logging.basicConfig(level=logging.WARNING)
# Define keys to auth to API
accessKey = '1234'
secretKey = '1234'
# Bootstrap API connection
io = TenableIO(access_key=accessKey, secret_key=secretKey)

# Get the current date and the date 90 days ago
current_date = datetime.now()
past_date = current_date - timedelta(days=90)

# Get the list of CVEs published in the last 90 days
cves = io.vulns.cves(published_since=past_date.strftime('%Y-%m-%d'), published_until=current_date.strftime('%Y-%m-%d'))

# Initialize a list to store the time spans
time_spans = []

# Iterate over each CVE
for cve in cves:
    cve_pub_date = datetime.strptime(cve['published'], '%Y-%m-%dT%H:%M:%S.%fZ')
    
    # Get the list of plugins associated with the CVE
    plugins = io.plugins.cve(cve['id'])
    
    # Iterate over each plugin
    for plugin in plugins:
        plugin_pub_date = datetime.strptime(plugin['published'], '%Y-%m-%dT%H:%M:%S.%fZ')
        
        # Calculate the time span
        time_span = (plugin_pub_date - cve_pub_date).days
        time_spans.append(time_span)

# Calculate the average time span in days
average_time_span = statistics.mean(time_spans)
print(f"The average time span between CVE and plugin publication dates is {average_time_span} days.")