# PR Draft: Retry Page Discussion Fetch

## Summary

`Page.discussion` fetches `forum/ForumCommentsListModule` to discover the page's `WIKIDOT.forumThreadId` before delegating to `ForumThread.get_from_id(...)`. That first comments-module lookup is a read-only AMC request, but it still used plain `site.amc_request(...)`. A transient AMC failure could therefore be treated as a response and fail with an attribute/parsing error before the existing retry mechanism could run.

The fix routes only the discussion module lookup through `site.amc_request_with_retry(...)`. If the retry succeeds, `Page.discussion` preserves the existing behavior: it parses `WIKIDOT.forumThreadId`, fetches the corresponding `ForumThread`, caches that the discussion was checked, and returns `None` when the page has no discussion thread ID. If retries are exhausted, it raises `UnexpectedException("Cannot retrieve page discussion: <fullname>")` and leaves `_discussion_checked` false so a later access can retry.

## Related Issue

Complements [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), which made `ForumThread.get_from_id(...)` and direct thread detail reads retry-aware. It also follows the read-path retry pattern from [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), and [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md). No upstream issue filed yet.

## Changes

- Use `self.site.amc_request_with_retry(...)` for `Page.discussion`'s `forum/ForumCommentsListModule` lookup.
- Raise `UnexpectedException("Cannot retrieve page discussion: <fullname>")` when the discussion lookup retry result is `None`.
- Preserve existing parsing of `WIKIDOT.forumThreadId = <id>;`.
- Preserve existing `None` behavior for pages whose comments module response has no discussion thread ID.
- Preserve existing `ForumThread.get_from_id(...)` delegation for a discovered thread ID.
- Leave page write, delete, vote, tag, parent, rename, and save actions unchanged.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [ ] Security/privacy hardening
- [x] Reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Requirements Traceability

| Requirement | Acceptance | Verification | Negative Control |
| --- | --- | --- | --- |
| R1: Discussion lookup is retry-aware | `Page.discussion` retries transient failures while fetching `forum/ForumCommentsListModule` | `test_discussion_retries_transient_fetch_failures` | The test failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` |
| R2: Exhausted discussion lookup fails explicitly | A `None` retry result raises `UnexpectedException` with the page fullname and does not mark `_discussion_checked` true | `test_discussion_raises_when_retry_is_exhausted` | Exhausted retry leaves the property eligible for a later retry instead of caching a false negative |
| R3: Successful discussion behavior is preserved | A successful response still parses `WIKIDOT.forumThreadId` and calls `ForumThread.get_from_id(...)` | `test_discussion_retries_transient_fetch_failures` | The test asserts the parsed thread ID and returned thread object |
| R4: Adjacent page and thread behavior is preserved | Page properties, page operations, and direct thread fetch tests remain green | `tests/unit/test_page.py`; `tests/unit/test_page.py tests/unit/test_forum_thread.py`; `tests/unit` | Broad unit coverage still passes after the discussion retry change |

## Testing

Local implementation commit: `d7bd3fa fix(page): retry discussion fetch`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_discussion_retries_transient_fetch_failures -q` failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_discussion_raises_when_retry_is_exhausted -q` passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties -q` passed with 12 tests.
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 85 tests.
- [x] `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_forum_thread.py -q` passed with 113 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 597 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] Complexity scan refreshed at `/home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/artifacts/complexity_analysis_wikidot.md`

## Acceptance Criteria

- `Page.discussion` uses retry-aware AMC for the read-only comments-module lookup.
- A transient comments-module fetch failure is retried before the response body is parsed.
- An exhausted comments-module fetch retry raises an explicit page-fullname-specific `UnexpectedException`.
- Exhausted retry does not mark `_discussion_checked` true, so the next property access can try again.
- Existing successful discussion parsing and `None` for pages without discussion thread IDs remain unchanged.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Page discussion access is a read path used by clients that navigate from a page to its forum thread. Retrying the read-only `ForumCommentsListModule` lookup avoids exposing transient AMC failures as unrelated attribute/parsing errors and aligns the first discussion lookup with the already retry-aware direct forum-thread lookup. The change deliberately avoids retrying any page mutation action.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence repeatedly used `wikidot.py` for page evidence, forum inspection, source collection, and browser-free workflows where read-heavy AMC paths needed retry-aware behavior.
- Existing local issue [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md) established that the direct thread detail lookup after a discovered thread ID should be retry-aware.
- Existing local issues [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md) and [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md) established that page lazy properties should not cache false negatives when acquisition retries are exhausted.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice intentionally does not retry page destroy, tag save, parent setting, rename, vote, create/edit save, or other mutation paths. Those paths can have duplicate-action or idempotency risks and should be evaluated separately only when the mutation semantics are proven safe.
