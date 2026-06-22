## 2026-06-22 - Tenable.io Scan Configuration Batching

**Learning:** The `io.scans.configure` method in pyTenable allows updating multiple settings (e.g., credentials, ACLs, name) in a single API call. For credentials specifically, it accepts a list of dictionaries, allowing bulk updates that were previously performed sequentially, causing an O(N*M) performance bottleneck.

**Action:** Always prefer batching configuration changes into a single `io.scans.configure` call per resource to minimize network overhead and avoid potential race conditions or overwriting issues during sequential updates.
