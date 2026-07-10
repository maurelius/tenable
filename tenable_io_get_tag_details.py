"""tenable_io_get_tag_details.py - Get all tag values for tags in a defined category"""

### Import Modules
import re
import logging
import pandas as pd
from tenable_config import get_tenable_io_client

# Define a regular expression pattern to match IP address subnets globally
SUBNET_PATTERN = re.compile(r'\d+\.\d+\.\d+\.\d+/\d+')

def get_tag_category_subnets(io_client, category_name):
    """
    Retrieves all unique subnets from the asset filters of tags within a specific category.
    """
    # Grab the UUIDs of every tag in category, don't process tag multiple times
    # ⚡ BOLT Optimization: Use server-side filtering to reduce network overhead and local
    # processing. Instead of iterating through all tags, we request only those in the
    # specified category.
    # API calls: O(1) for list
    uuids = {d['uuid'] for d in io_client.tags.list(('category_name', 'eq', category_name))}

    subnets_found = set()

    # Loop through the matching UUIDs
    # API calls: O(N) where N is unique tags in the category
    for uuid in uuids:
        # Retrieve the details for the UUID
        details = io_client.tags.details(uuid)

        # Extract the 'filters' dictionary from the details
        filters = details.get('filters', {})

        # Extract the 'asset' field from the filters dictionary as a string
        asset_filter_str = filters.get('asset', '')

        # Use regular expressions to find IP address subnets in the 'asset' field
        subnets = SUBNET_PATTERN.findall(asset_filter_str)

        # Add the found subnets to the set
        subnets_found.update(subnets)

    return sorted(list(subnets_found))

def main():
    """Main execution function"""
    # Set up logging
    logging.basicConfig(level=logging.WARNING)
    # Bootstrap API connection
    io = get_tenable_io_client()

    category = input('Enter the tag category to look up: ')

    # ⚡ BOLT Optimization: Moved core logic to a separate function for testability and clarity.
    subnet_list = get_tag_category_subnets(io, category)

    # Sort the subnets for a cleaner report
    df_subnets = pd.DataFrame(subnet_list).rename(columns={0: 'Subnet'})

    # Print the list of IP address subnets to a file
    output_file = 'TENABLE-SUBNETS.md'
    with open(output_file, 'w', encoding='utf-8') as fobj:
        fobj.write(f'# Tenable Subnets for Tag Category: {category}\n\n')
        if not df_subnets.empty:
            fobj.write(df_subnets.to_markdown(tablefmt='github'))
        else:
            fobj.write('No subnets found for this category.')
        fobj.write('\n')

    print(f"Results written to {output_file}")

if __name__ == '__main__':
    main()
