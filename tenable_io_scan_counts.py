"""tenable_io_scan_counts.py: Find scans by owner, then find how many of those have a keyword, then do some maths on how many of the subset make up the total"""

### Import Modules
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
# Specify the email addresses of the scan owners
emails = ['john.doe@example.com','richard.fitzenwell@example.com','jane.deer@example.com','stu.pedasso@example.com']
# Specify the substring you want to search for in scan names
search_string = 'my-string-name'
# Grab the list of scans
scans = io.scans.list()
# Create lists to store scan owner and name
owners = []
names = []

# Iterate through the list of scans, filter by email, and extract owner and name
for scan in scans:
    owner = scan['owner']
    if owner in emails:
        name = scan['name']
        owners.append(owner)
        names.append(name)

# Create a DataFrame from the lists
data = {'Scan Owner': owners, 'Scan Name': names}
df = pd.DataFrame(data)

# Set pandas options to not truncate the results
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 0)

# Remove duplicate values and store in a new DataFrame
df2 = df.drop_duplicates()

# Count the number of scan names that contain the search string
matching_scans = df2[df2['Scan Name'].str.contains(search_string, case=False, na=False)]
total_scans = len(df2)
count = len(matching_scans)

# Calculate the percentage
percentage = (count / total_scans) * 100

# Print total scans owned by specified emails
print(f"Results of all scans owned by previously specific owners: {emails}\n")
print(df2, "\n")

# Count the number of entries by scan owner
entry_counts = df2['Scan Owner'].value_counts()
print("Scan breakdown by owner:\n")

for owner, count in entry_counts.items():
    print(f"Owner: {owner}: {count}")

print("\n")
print("Total number of scans: ", len(df2))
print(f"Total number of legacy scans: ", len(matching_scans))

# Print the percentage of matched scans 
print(f"Percentage of legacy scans containing {search_string}: {percentage:.2f}%")