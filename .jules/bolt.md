## 2025-05-15 - Batching Tenable.io Scan Configuration
**Learning:** Consolidating multiple `io.scans.configure` calls into a single call significantly reduces network overhead. The `pyTenable` library supports passing both `credentials` (as a list of dicts) and `acls` in one request, transforming $O(N \times M)$ complexity into $O(N)$.
**Action:** Always check if a configuration method in an API wrapper supports batching multiple settings before implementing loops that make sequential calls.

## 2025-05-16 - Hoisting Local Configuration Helpers
**Learning:** `io.scans.configure_scan_schedule` in `pyTenable` v1.4.13 is a local helper that returns a dictionary rather than making an API call. Moving it outside of loops reduces O(N) redundant dictionary constructions to O(1). Additionally, passing `scan_id` to this specific helper was a logic bug, as its first parameter is `enabled`.
**Action:** Identify helper methods in SDKs that perform local data transformation and hoist them outside of loops to minimize redundant work.
