"""Gets scan templates that use a list of plugin IDs.

This is useful for finding what scans may be affected by template changes.
"""

import logging
from tenable.errors import APIError
from tenable_config import get_tenable_io_client

# Set up logging
logging.basicConfig(level=logging.WARNING)


def _get_template_details(io, wizard_uuid, cache, stats=None):
    """Fetches template details with caching to prevent redundant API calls."""
    if wizard_uuid in cache:
        if stats is not None:
            stats['hits'] += 1
        return cache[wizard_uuid]

    if stats is not None:
        stats['misses'] += 1

    details = io.editor.template_details('policy', wizard_uuid)
    cache[wizard_uuid] = details
    return details


def _check_template_match(io, uuid, plugin_ids, cache, stats):
    """Checks if a single template matches any plugin IDs using cache."""
    try:
        details = _get_template_details(io, uuid, cache, stats)
        preferences = (
            details.get("settings", {})
            .get("discovery", {})
            .get("modes", {})
        )
        if any(p_id in preferences for p_id in plugin_ids):
            name = details.get("name")
            print(f"Policy Name/Title: {name}")
            print(f"Policy UUID: {uuid}")
            return {"name": name, "uuid": uuid}
    except APIError as e:
        logging.warning("API error for template uuid %s: %s", uuid, e)
    return None


def process_templates(io, plugin_ids):
    """Processes scan templates to find matching plugin IDs.

    Args:
        io: TenableIO client instance.
        plugin_ids (list): List of plugin ID strings to search for.

    Returns:
        tuple: (matching_policies, cache_stats)
    """
    cache = {}
    stats = {'hits': 0, 'misses': 0}
    matching_policies = []

    folders = io.folders.list()
    my_scans = [d for d in folders if d.get('name') == "My Scans"]
    if not my_scans:
        return matching_policies, stats

    scans = io.scans.list(my_scans[0]['id'])

    # ⚡ BOLT Optimization: Deduplicate wizard_uuids directly using set comprehension
    wizard_uuids = {scan['wizard_uuid'] for scan in scans if scan.get('wizard_uuid')}

    for wizard_uuid in wizard_uuids:
        res = _check_template_match(io, wizard_uuid, plugin_ids, cache, stats)
        if res:
            matching_policies.append(res)

    for template in io.editor.template_list('policy'):
        uuid = template.get('uuid')
        if uuid:
            # ⚡ BOLT Optimization: Re-uses cached template details if fetched previously
            res = _check_template_match(io, uuid, plugin_ids, cache, stats)
            if res:
                matching_policies.append(res)

    logging.info("Template details cache stats: %s", stats)
    return matching_policies, stats


def main():
    """Main execution function."""
    client = get_tenable_io_client()
    default_plugin_ids = [
        '34220', '34252', '11219', '14272', '25221',
        '10736', '99265', '10335', '14274', '34277'
    ]
    process_templates(client, default_plugin_ids)


if __name__ == '__main__':
    main()
