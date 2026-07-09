# Bolt Changelog

## 2026-06-21 - Batching pyTenable Scan Configurations

**Learning:** The `io.scans.configure` method in pyTenable allows updating both `credentials` and `acls` in a single call. In `tenable_io_scan_update_permissions.py`, credentials were being added one-by-one in a loop, followed by a separate call for permissions. This resulted in O(N*M) network calls where N is the number of scans and M is the number of credentials. By batching them, we reduce this to O(N).
**Action:** Always check if pyTenable update methods (like `configure`, `edit`, etc.) can accept multiple parameters at once to minimize API round-trips.

## 2025-05-15 - Batching Tenable.io Scan Configuration

**Learning:** Consolidating multiple `io.scans.configure` calls into a single call significantly reduces network overhead. The `pyTenable` library supports passing both `credentials` (as a list of dicts) and `acls` in one request, transforming $O(N \times M)$ complexity into $O(N)$.
**Action:** Always check if a configuration method in an API wrapper supports batching multiple settings before implementing loops that make sequential calls.

## 2026-07-03 - Caching Redundant Resource Lookups

**Learning:** In scripts that map shared resources (like tags) to multiple parent objects (like scans), sequential API lookups for the same resource ID create significant (N)$ network overhead. Implementing a simple dictionary-based cache for resource details transforms the complexity to (\text{Unique Resources})$.
**Action:** When iterating over parent objects with many-to-one relationships to child resources, always implement a cache for the child resource details to minimize API requests.

## 2026-07-04 - Caching Redundant API Lookups

**Learning:** In scripts that resolve scan-related resources (like tags), many scans frequently share the same resource references. Implementing a dictionary-based cache for these resources reduces API overhead from O(Total References) to O(Unique Resources), significantly improving execution time in large environments.
**Action:** Implement a cache for nested API lookups when processing lists of items that likely share common configuration elements.

## 2026-07-05 - Bulk Asset Export for Tag Retrieval

**Learning:** Sequential `io.assets.tags()` calls for every asset retrieved via `io.assets.list()` creates an O(N) network bottleneck. Replacing this with `io.exports.assets()` reduces overhead to O(1) export job, as the Export API includes tags in the asset record payload.
**Action:** Use bulk Export APIs instead of sequential lookup methods whenever processing attributes (like tags) across a large set of assets.

## 2026-07-06 - Tag Detail Caching for Network Export

**Learning:** In scripts that extract scan target networks, multiple scans often share identical tag targets. Performing sequential `io.tags.details()` calls for each reference creates an $O(\text{Total Tags})$ bottleneck. Implementing a dictionary-based cache for parsed tag filters reduces API overhead to $O(\text{Unique Tags})$, significantly accelerating reporting in large-scale environments.
**Action:** Use a local cache for resource details when processing repeated references across many parent objects (like scans or assets) to minimize redundant network requests.
