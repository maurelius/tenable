## 2025-05-15 - [Batching Tenable.io API calls]
**Learning:** The `io.scans.configure` method in pyTenable allows updating both `credentials` and `acls` in a single call. Previously, credentials were being updated individually in a loop, leading to redundant network overhead and potentially overwriting state.
**Action:** Always check if the API supports bulk or batch operations for configuration updates to reduce network round-trips from O(N*M) to O(N).
