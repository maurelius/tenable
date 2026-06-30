## 2025-05-15 - Batching Tenable.io Scan Configuration
**Learning:** Consolidating multiple `io.scans.configure` calls into a single call significantly reduces network overhead. The `pyTenable` library supports passing both `credentials` (as a list of dicts) and `acls` in one request, transforming $O(N \times M)$ complexity into $O(N)$.
**Action:** Always check if a configuration method in an API wrapper supports batching multiple settings before implementing loops that make sequential calls.

## 2025-05-15 - Caching Shared Tag Details
**Learning:** In scripts that iterate over scans and their associated tags, shared tags across different scans cause redundant `io.tags.details` API calls. Implementing a simple dictionary-based cache for tag details within the resolution loop reduces network overhead from O(Total Tags) to O(Unique Tags).
**Action:** When performing nested API lookups (e.g., Resources -> Sub-resources), always check if sub-resources are likely to be shared and implement a local cache if the SDK doesn't provide one.
