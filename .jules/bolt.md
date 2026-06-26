## 2025-05-15 - Batching Tenable.io Scan Configuration
**Learning:** Consolidating multiple `io.scans.configure` calls into a single call significantly reduces network overhead. The `pyTenable` library supports passing both `credentials` (as a list of dicts) and `acls` in one request, transforming $O(N \times M)$ complexity into $O(N)$.
**Action:** Always check if a configuration method in an API wrapper supports batching multiple settings before implementing loops that make sequential calls.

## 2025-05-16 - Batching Asset Deletions with pyTenable
**Learning:** For bulk asset deletion in pyTenable 1.4.13, using `io.assets.bulk_delete` with multiple OR-connected filters `('id', 'eq', UUID)` is significantly more efficient than individual `io.assets.delete` calls, reducing API overhead from O(N) to O(1) requests.
**Action:** Prefer `bulk_delete` with filters for removing multiple assets instead of iterating over individual delete calls.
