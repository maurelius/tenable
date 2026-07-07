## 2025-05-15 - Batching Tenable.io Scan Configuration
**Learning:** Consolidating multiple `io.scans.configure` calls into a single call significantly reduces network overhead. The `pyTenable` library supports passing both `credentials` (as a list of dicts) and `acls` in one request, transforming $O(N \times M)$ complexity into $O(N)$.
**Action:** Always check if a configuration method in an API wrapper supports batching multiple settings before implementing loops that make sequential calls.

## 2026-07-03 - Caching Redundant Resource Lookups
**Learning:** In scripts that map shared resources (like tags) to multiple parent objects (like scans), sequential API lookups for the same resource ID create significant (N)$ network overhead. Implementing a simple dictionary-based cache for resource details transforms the complexity to (\text{Unique Resources})$.
**Action:** When iterating over parent objects with many-to-one relationships to child resources, always implement a cache for the child resource details to minimize API requests.
## 2026-07-04 - Caching Redundant API Lookups
**Learning:** In scripts that resolve scan-related resources (like tags), many scans frequently share the same resource references. Implementing a dictionary-based cache for these resources reduces API overhead from O(Total References) to O(Unique Resources), significantly improving execution time in large environments.
**Action:** Implement a cache for nested API lookups when processing lists of items that likely share common configuration elements.

## 2026-07-07 - Efficient Collection Accumulation
**Learning:** Accumulating data into a list and repeatedly performing deduplication (e.g., `list(set(accumulated_list))`) inside a loop creates an $O(N^2)$ performance bottleneck. Using a `set` with `.add()` or `.update()` inside the loop and converting to a list once after the loop ensures $O(N)$ complexity.
**Action:** Use sets for deduplicated accumulation in loops and defer list conversion/sorting until the collection is complete.
