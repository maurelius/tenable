# Bolt Changelog

## 2026-06-21 - Batching pyTenable Scan Configurations

**Learning:** The `io.scans.configure` method in pyTenable allows updating both `credentials` and `acls` in a single call. In `tenable_io_scan_update_permissions.py`, credentials were being added one-by-one in a loop, followed by a separate call for permissions. This resulted in O(N*M) network calls where N is the number of scans and M is the number of credentials. By batching them, we reduce this to O(N).
**Action:** Always check if pyTenable update methods (like `configure`, `edit`, etc.) can accept multiple parameters at once to minimize API round-trips.

## 2025-05-15 - Batching Tenable.io Scan Configuration

**Learning:** Consolidating multiple `io.scans.configure` calls into a single call significantly reduces network overhead. The `pyTenable` library supports passing both `credentials` (as a list of dicts) and `acls` in one request, transforming $O(N \times M)$ complexity into $O(N)$.
**Action:** Always check if a configuration method in an API wrapper supports batching multiple settings before implementing loops that make sequential calls.

## 2025-05-22 - Batching Tenable.io Asset Deletion
**Learning:** In pyTenable 1.4.13, the `io.assets.delete` method only accepts a single UUID, leading to (N)$ API calls. However, `io.assets.bulk_delete` can be leveraged with a list of `('id', 'eq', UUID)` filters and `filter_type='or'` to perform multiple deletions in a single request, reducing network overhead to (N/BATCH\_SIZE)$.
**Action:** Prioritize `bulk_delete` with OR-ed filters for mass asset removal to minimize API latency and rate-limiting risks.
## 2025-05-16 - Batching Asset Deletions with pyTenable

**Learning:** For bulk asset deletion in pyTenable 1.4.13, using `io.assets.bulk_delete` with multiple OR-connected filters `('id', 'eq', UUID)` is significantly more efficient than individual `io.assets.delete` calls, reducing API overhead from O(N) to O(1) requests.
**Action:** Prefer `bulk_delete` with filters for removing multiple assets instead of iterating over individual delete calls.
