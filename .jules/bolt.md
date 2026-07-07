# Bolt Changelog

## 2026-06-21 - Batching pyTenable Scan Configurations

**Learning:** The `io.scans.configure` method in pyTenable allows updating both `credentials` and `acls` in a single call. In `tenable_io_scan_update_permissions.py`, credentials were being added one-by-one in a loop, followed by a separate call for permissions. This resulted in O(N*M) network calls where N is the number of scans and M is the number of credentials. By batching them, we reduce this to O(N).
**Action:** Always check if pyTenable update methods (like `configure`, `edit`, etc.) can accept multiple parameters at once to minimize API round-trips.

## 2025-05-15 - Batching Tenable.io Scan Configuration

**Learning:** Consolidating multiple `io.scans.configure` calls into a single call significantly reduces network overhead. The `pyTenable` library supports passing both `credentials` (as a list of dicts) and `acls` in one request, transforming $O(N \times M)$ complexity into $O(N)$.
**Action:** Always check if a configuration method in an API wrapper supports batching multiple settings before implementing loops that make sequential calls.

## 2026-07-02 - Caching Shared Resources in Nested API Lookups

**Learning:** When resolving attributes (like tag details) for items returned by a list endpoint (like scans), many items often share the same attributes. Fetching these redundantly results in O(Total Applications) network calls. Implementing a dictionary-based cache reduces this to O(Unique Resources).
**Action:** Always check for repeated resource identifiers in nested loops and implement a local cache to minimize redundant API traffic.
