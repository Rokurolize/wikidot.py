# PR Draft: Batch Meta Tag Updates

## Summary

`Page.metas` used one `site.amc_request(...)` call per deleted, added, or updated meta tag. The setter already computes the full diff before sending changes, so those individual requests can be sent as a single AMC batch without changing the public API.

The fix builds one ordered request body list for delete, add, and update operations, submits it once when there is work to do, and then updates the cached `_metas` value.

## Related Issue

Drafted from local rollout evidence; no upstream issue filed yet.

## Changes

- Batch all `deleteMetaTag` and `saveMetaTag` bodies from one `Page.metas = ...` assignment into a single `site.amc_request(...)` call.
- Preserve the existing delete, add, then update operation order.
- Preserve the existing `login_check()` gate before writes.
- Add a regression test covering simultaneous delete, add, and update meta changes.

## Type Of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Performance/reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Testing

Local implementation commit: `6f41847 perf(page): batch meta tag updates`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_batches_changes -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 64 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 523 tests.
- [x] `uv run --extra lint ruff check src tests`
- [x] `uv run --extra format ruff format --check src tests`
- [x] `uv run --extra lint mypy src tests --install-types --non-interactive`
- [x] `git diff --check`

## Acceptance Criteria

- One `Page.metas = ...` assignment sends at most one AMC request for the computed meta diff.
- Delete, add, and update requests remain ordered deterministically as delete operations first, add operations second, and update operations third.
- Assignments that include several meta changes use one request body list rather than several single-body AMC calls.
- The setter still calls `login_check()` before attempting a write.
- The `_metas` cache is updated after the successful request path.

## Upstream-Safe Motivation

Meta tags are part of browser-free page publishing workflows. Batching meta writes reduces AMC round trips for callers that update several page attributes after saving source, and it keeps the setter consistent with other wikidot.py APIs that already pass multi-body AMC requests.

## Local Evidence, Not For Upstream Paste

- Local rollout `019e7a39-505b-76b3-bfb4-b68be3c71fb9` included a publishing script with explicit metadata and meta-tag operations after page save.
- Local rollout `019e6067-989d-73f1-86a4-a2f0abc22af7` recorded that browser-free AMC usage was preferred over browser automation for lock acquisition, `savePage`, public URL retrieval, tag saving, and related publish actions.
- The local feature draft in [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md) includes meta tags as part of the high-level publishing workflow.

## Additional Notes

This is a small prerequisite for the broader browser-free publisher draft, not the full publisher feature itself.
