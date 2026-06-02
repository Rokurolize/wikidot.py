# PR Draft: Batch Page Metadata Updates

## Summary

Browser-free page publishing workflows commonly save source first, then update tags, parent page, and meta tags. Existing wikidot.py primitives could do each operation, but callers had to coordinate `Page.commit_tags()`, `Page.set_parent(...)`, and `Page.metas = ...` separately, producing several AMC requests and repeated raw workflow code.

The fix adds `Page.set_metadata(...)`, a small public helper that can save tags, parent, and meta tags as one AMC batch when the caller wants to update them together. Existing individual methods remain available and unchanged.

## Related Issue

Drafted from local rollout evidence; no upstream issue filed yet.

## Changes

- Add `Page.set_metadata(tags=..., parent_fullname=..., metas=...)`.
- Preserve omission semantics: omitted fields are left unchanged, `tags=[]` clears tags, `parent_fullname=None` clears the parent, and `metas={}` removes existing meta tags.
- Reuse the existing meta-tag diff behavior so unchanged meta entries do not send redundant `saveMetaTag` requests.
- Keep `Page.metas = ...` working through the same request-body builder.
- Update local caches only after the AMC request succeeds.
- Add regression tests for combined tags/parent/meta batching and explicit parent clearing.

## Type Of Change

- [ ] Bug fix
- [x] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Performance/reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Testing

Local implementation commit: `d2a6fe6 feat(page): batch page metadata updates`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_batches_tags_parent_and_metas tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_can_clear_parent tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_batches_changes tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_parses_decoded_flexible_markup -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 73 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 532 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`

## Acceptance Criteria

- `Page.set_metadata(...)` can update tags, parent, and meta tags with one `site.amc_request(...)` call when all three groups are supplied.
- Omitting a field leaves that field unchanged.
- Passing `parent_fullname=None` clears the parent by sending `parentName=""`.
- Passing `tags=[]` sends an empty tag string and updates the local `tags` cache to an empty list.
- Passing `metas={}` deletes cached existing meta tags through the same meta diff behavior as `Page.metas = {}`.
- Existing `Page.commit_tags()`, `Page.set_parent(...)`, and `Page.metas = ...` remain valid for separate operations.
- Local metadata caches are updated only after the write request path succeeds.

## Upstream-Safe Motivation

This helper gives callers a safer library-level way to perform the common post-save metadata phase of browser-free publishing. It reduces AMC round trips and avoids repeated hand-written request dictionaries without introducing a full publish workflow yet.

## Local Evidence, Not For Upstream Paste

- Local rollout `019e7a39-505b-76b3-bfb4-b68be3c71fb9` included a publishing script with a hand-written `set_metadata(...)` function that built one AMC request list for `saveTags`, `setParentPage`, and several `saveMetaTag` calls after `savePage`.
- Local rollout `019e6067-989d-73f1-86a4-a2f0abc22af7` recorded that browser-free AMC usage was preferred over browser automation for lock acquisition, `savePage`, public URL retrieval, tag saving, and related publish actions.
- The local feature draft in [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md) needs a metadata phase that can set tags, parent, and meta tags after saving source.
- The local meta write draft in [007-pr-batch-meta-tag-updates.md](007-pr-batch-meta-tag-updates.md) covers meta-only batching; this draft extends the same idea to the broader post-save metadata bundle.
- The local meta parsing draft in [011-pr-robust-meta-tag-parsing.md](011-pr-robust-meta-tag-parsing.md) improves the read/verification side for metadata workflows.

## Additional Notes

This is a small API slice toward the high-level publish helper. It deliberately does not add source round-trip verification, retry-after-save visibility polling, or structured publish result data; those remain in the broader feature draft.
