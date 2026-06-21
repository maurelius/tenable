## 2026-06-21 - Tenable.io API Batching Optimization
**Learning:** The `io.scans.configure` method in pyTenable allows updating both `credentials` (as a list of dictionaries) and `acls` in a single call. However, the `acls` argument must be a list of correctly formatted ACL objects (including `type`, `permissions`, etc.), not a nested settings dictionary.
**Action:** Batch configuration updates to reduce network overhead from O(N*M) to O(N), but ensure the payload matches the expected API schema for each field.
