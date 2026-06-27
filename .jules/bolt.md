## 2025-05-15 - Batching Tenable.io Scan Configuration
**Learning:** Consolidating multiple `io.scans.configure` calls into a single call significantly reduces network overhead. The `pyTenable` library supports passing both `credentials` (as a list of dicts) and `acls` in one request, transforming $O(N \times M)$ complexity into $O(N)$.
**Action:** Always check if a configuration method in an API wrapper supports batching multiple settings before implementing loops that make sequential calls.

## 2025-05-22 - Batching Tenable.io Asset Deletion
**Learning:** In pyTenable 1.4.13, the `io.assets.delete` method only accepts a single UUID, leading to (N)$ API calls. However, `io.assets.bulk_delete` can be leveraged with a list of `('id', 'eq', UUID)` filters and `filter_type='or'` to perform multiple deletions in a single request, reducing network overhead to (N/BATCH\_SIZE)$.
**Action:** Prioritize `bulk_delete` with OR-ed filters for mass asset removal to minimize API latency and rate-limiting risks.
