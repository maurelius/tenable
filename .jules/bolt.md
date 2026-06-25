## 2025-05-15 - Batching Tenable.io Scan Configuration
**Learning:** Consolidating multiple `io.scans.configure` calls into a single call significantly reduces network overhead. The `pyTenable` library supports passing both `credentials` (as a list of dicts) and `acls` in one request, transforming $O(N \times M)$ complexity into $O(N)$.
**Action:** Always check if a configuration method in an API wrapper supports batching multiple settings before implementing loops that make sequential calls.

## 2025-05-22 - Optimized Bulk Asset Deletion and CSV Processing
**Learning:** Transitioning from individual asset deletions to the Tenable.io `bulk_delete` endpoint reduces network overhead from $O(N)$ to $O(N/BatchSize)$. Using the standard `csv` module instead of `pandas` for simple data extraction avoids heavy dependencies and improves script startup time in environments where `pandas` is not pre-installed.
**Action:** Always batch destructive operations in Tenable.io and prefer lightweight standard library modules for data ingestion unless complex transformations are required.
