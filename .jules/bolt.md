## 2025-05-15 - Batching Tenable.io Scan Configuration
**Learning:** Consolidating multiple `io.scans.configure` calls into a single call significantly reduces network overhead. The `pyTenable` library supports passing both `credentials` (as a list of dicts) and `acls` in one request, transforming $O(N \times M)$ complexity into $O(N)$.
**Action:** Always check if a configuration method in an API wrapper supports batching multiple settings before implementing loops that make sequential calls.

## 2025-07-01 - Caching shared resources for bulk API processing
**Learning:** When processing a large collection of items (like scans) that reference shared metadata (like tags), implement a local cache to avoid redundant API calls. In scripts like `tenable_io_get_scans_from_tag.py`, multiple scans often point to the same tags, leading to a bottleneck when calling `io.tags.details(t)` repeatedly for the same UUID.
**Action:** Identify shared resource lookups in loop structures and wrap them with a dictionary-based cache to reduce network requests from O(Total Lookups) to O(Unique Resources).
