## 2025-05-15 - Batching Tenable.io Scan Configuration
**Learning:** Consolidating multiple `io.scans.configure` calls into a single call significantly reduces network overhead. The `pyTenable` library supports passing both `credentials` (as a list of dicts) and `acls` in one request, transforming $O(N \times M)$ complexity into $O(N)$.
**Action:** Always check if a configuration method in an API wrapper supports batching multiple settings before implementing loops that make sequential calls.

## 2026-07-02 - Caching Shared Resources in Nested API Lookups
**Learning:** When resolving attributes (like tag details) for items returned by a list endpoint (like scans), many items often share the same attributes. Fetching these redundantly results in O(Total Applications) network calls. Implementing a dictionary-based cache reduces this to O(Unique Resources).
**Action:** Always check for repeated resource identifiers in nested loops and implement a local cache to minimize redundant API traffic.
