## 2025-05-15 - Batching Tenable.io Scan Configuration
**Learning:** Consolidating multiple `io.scans.configure` calls into a single call significantly reduces network overhead. The `pyTenable` library supports passing both `credentials` (as a list of dicts) and `acls` in one request, transforming $O(N \times M)$ complexity into $O(N)$.
**Action:** Always check if a configuration method in an API wrapper supports batching multiple settings before implementing loops that make sequential calls.

## 2026-07-03 - Caching Redundant Resource Lookups
**Learning:** In scripts that map shared resources (like tags) to multiple parent objects (like scans), sequential API lookups for the same resource ID create significant (N)$ network overhead. Implementing a simple dictionary-based cache for resource details transforms the complexity to (\text{Unique Resources})$.
**Action:** When iterating over parent objects with many-to-one relationships to child resources, always implement a cache for the child resource details to minimize API requests.
