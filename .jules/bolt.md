## 2025-05-15 - [Tag Detail Caching]
**Learning:** Scans in Tenable.io often share the same tag targets. By implementing a local cache for `io.tags.details(t)`, we can avoid redundant API calls.
**Action:** In scripts that iterate through multiple scans and process their tags, always implement a cache for tag metadata to reduce network overhead and stay within API rate limits.
