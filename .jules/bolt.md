## 2025-05-15 - Batching Tenable.io Scan Configuration
**Learning:** Consolidating multiple `io.scans.configure` calls into a single call significantly reduces network overhead. The `pyTenable` library supports passing both `credentials` (as a list of dicts) and `acls` in one request, transforming $O(N \times M)$ complexity into $O(N)$.
**Action:** Always check if a configuration method in an API wrapper supports batching multiple settings before implementing loops that make sequential calls.

## 2026-07-04 - Caching Redundant API Lookups
**Learning:** In scripts that resolve scan-related resources (like tags), many scans frequently share the same resource references. Implementing a dictionary-based cache for these resources reduces API overhead from O(Total References) to O(Unique Resources), significantly improving execution time in large environments.
**Action:** Implement a cache for nested API lookups when processing lists of items that likely share common configuration elements.
