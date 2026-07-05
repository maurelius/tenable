## 2025-05-15 - [Batching Scan Configuration Updates]
**Learning:** The `io.scans.configure` method in pyTenable allows updating multiple settings, including `credentials` and `acls`, in a single API call.
**Action:** When updating multiple attributes of a scan, consolidate them into a single `io.scans.configure` call to minimize network requests and improve performance.
