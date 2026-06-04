# PR Draft: Sync Page Edit Revision Count From The Edit Result

## Summary

`Page.edit(...)` now updates the calling `Page` object's title, source cache, and revision-list cache after a successful save. One adjacent consistency gap remained: the calling object could keep its old `revisions_count` even when the post-save `Page.create_or_edit(...)` result already carried a newer count from `ListPages`. Since `Page.latest_revision` selects the latest revision by comparing each fetched revision's `rev_no` with `self.revisions_count`, leaving that count stale can make the original page object resolve the pre-edit revision after a successful edit.

This follow-up syncs `revisions_count` from the successful edit result only when the result is newer than the caller's current value. That preserves the existing stale-search fallback behavior: if immediate post-save search returns an older fallback page, the caller does not lose its already-known revision count.

## Related Issue

Builds on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [153-pr-latest-revision-failure-context.md](153-pr-latest-revision-failure-context.md), [259-pr-page-edit-local-cache-sync.md](259-pr-page-edit-local-cache-sync.md), and [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md). Those drafts established create/edit fallback behavior, contextual latest-revision failures, caller-side title/source cache sync, and revision-list invalidation after edit success.

No upstream issue was filed from this local workspace.

## Changes

- Sync the calling `Page` object's `revisions_count` from the successful `Page.create_or_edit(...)` result when the result has a larger count.
- Preserve the caller's known `revisions_count` when the immediate post-save result is stale or fallback-like and reports a lower count.
- Keep the existing title sync, source cache sync, revision-list invalidation, request payload, login guard, and return value behavior unchanged.
- Add focused regressions for both newer result sync and stale result non-regression.

## Type Of Change

- Page edit cache consistency
- Revision metadata sync
- Browser-free page mutation ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A successful `Page.edit(...)` syncs a newer `revisions_count` from the returned edited page to the calling object. | `TestPageEdit.test_edit_updates_local_revisions_count_from_result` sets the caller count to 2, returns an edited page with count 3, and asserts the caller now has 3. | Keeping the caller at 2 after an edit result with count 3 rejects this local completion claim. |
| A stale or fallback edit result must not reduce the caller's known revision count. | `TestPageEdit.test_edit_keeps_local_revisions_count_when_result_is_stale` sets the caller count to 5, returns an edited page with count 1, and asserts the caller remains at 5. | Unconditionally assigning the result count and rolling back to 1 rejects this local completion claim. |
| Edit success still invalidates cached revision lists and refreshes the caller's source cache. | Existing `TestPageEdit.test_edit_invalidates_local_revision_cache` and `TestPageEdit.test_edit_updates_local_source_cache` continue to pass. | Reusing old revision lists or old source text after edit success rejects this local completion claim. |
| `Page.latest_revision` remains compatible with the synced count contract. | Adjacent `TestPageProperties` latest-revision coverage and the new edit count regressions passed together. | Returning a pre-edit revision because the caller kept an older count rejects this local completion claim. |
| Existing edit, create/edit, and site page access behavior remains intact. | `uv run --extra test pytest tests/unit/test_page.py::TestPageEdit tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageProperties tests/unit/test_site.py::TestSitePageAccessor -q` passed 54 tests. | Regressions in edit fallback, page lookup, or latest-revision properties reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `6209dd8 fix(page): sync edit revision count`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageEdit::test_edit_updates_local_revisions_count_from_result -q` failed before the fix because the caller kept `revisions_count == 2` after the edit result reported 3.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageEdit::test_edit_updates_local_revisions_count_from_result -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageEdit -q` passed 8 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageEdit tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageProperties tests/unit/test_site.py::TestSitePageAccessor -q` passed 54 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 223 tests.
- `uv run --extra test pytest tests/unit -q` passed 814 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- After a successful `Page.edit(...)`, the calling `Page` object adopts a larger `revisions_count` from the returned edited page.
- A stale immediate search result or fallback page cannot reduce the calling object's known `revisions_count`.
- The calling object still invalidates `_revisions` and refreshes its local `PageSource` after successful edit.
- `Page.latest_revision` can use the caller's synced `revisions_count` instead of selecting an older revision solely because the caller retained pre-edit metadata.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

`Page.edit(...)` mutates page content while `Page.latest_revision` depends on the page object's `revisions_count` field. When the successful edit result has fresher revision metadata, syncing that larger count keeps the original page instance coherent with the mutation that just completed. Guarding the assignment so lower counts are ignored preserves the existing stale-search fallback path and avoids replacing good local metadata with a fallback value.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established that practical page publishing and editing workflows often reuse the original `Page` instance after a browser-free edit; this slice targets the remaining revision-count metadata on that same caller object.
- This change intentionally does not alter `Page.create_or_edit(...)`, post-save search retries, live Wikidot behavior, revision-list parsing, latest-revision lookup logic, source fetching, or title/source sync semantics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved page contents, source text from real pages, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This is a narrow follow-up to caller-side edit cache consistency. It does not claim that every edit always produces a new remote revision; it only trusts the returned edited page when that result reports a larger revision count than the caller already knows.
