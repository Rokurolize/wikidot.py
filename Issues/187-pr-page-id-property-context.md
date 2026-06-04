# PR Draft: Include Page Context In Page ID Property Fallback Errors

## Summary

`Page.id` automatically calls `PageCollection.get_page_ids()` when a page object does not yet have an ID. Most concrete lookup failures now include the affected page fullname, including missing `WIKIREQUEST.info.pageId` and non-HTTP response slots. The final defensive fallback in the property still raised only `Cannot find page id` if acquisition returned without setting `_id`.

This change keeps automatic ID acquisition, batching, duplicate URL reuse, cached ID propagation, successful ID parsing, and exception type unchanged, but includes the page fullname in that final property fallback: `Cannot find page id: <fullname>`.

## Related Issue

Builds on [186-pr-page-id-response-type-context.md](186-pr-page-id-response-type-context.md), [060-pr-deduplicate-page-id-fetches.md](060-pr-deduplicate-page-id-fetches.md), and earlier page source/revision/file/vote context drafts. Those drafts made the concrete page-ID lookup paths diagnosable; this follow-up fills the direct property fallback so caller logs do not lose the page name at the final boundary.

No upstream issue was filed from this local workspace.

## Changes

- Include `self.fullname` in the final `Page.id` `NotFoundException` fallback.
- Add a focused regression where `get_page_ids()` returns without setting `_id`.
- Preserve automatic lookup, successful cached ID reads, and the page-ID batch helper behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Direct page property context
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| `Page.id` still attempts automatic ID acquisition when `_id` is missing. | The focused regression patches `PageCollection.get_page_ids()` and asserts it is called once before the fallback exception. | A change that stops the automatic acquisition path rejects this local completion claim. |
| The final fallback still raises `NotFoundException` if `_id` remains unset. | `TestPageProperties.test_id_property_includes_page_context_when_acquire_leaves_id_missing` leaves `_id` unset and expects `NotFoundException`. | A change that returns `None`, fabricates an ID, or caches an invalid value rejects this local completion claim. |
| The fallback identifies the page. | The focused regression asserts `Cannot find page id: test-page`. | The RED test failed before the fix because the message was only `Cannot find page id`. |
| Page workflows remain green. | `uv run pytest tests/unit/test_page.py -q` passed 111 tests. | Regressions in page properties, page ID lookup, source/revision/vote/file acquisition, or write helpers reject this local completion claim. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py -q` passed 251 tests. | Regressions in site publishing, source collection, revision/file/vote detail acquisition, or page metadata behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `dbb3755 fix(page): include page in id fallback errors`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_id_property_includes_page_context_when_acquire_leaves_id_missing -q` failed before the fix because the exception message was `Cannot find page id`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_id_property_includes_page_context_when_acquire_leaves_id_missing -q`.
- `uv run pytest tests/unit/test_page.py -q` passed 111 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py -q` passed 251 tests.
- `uv run pytest tests/unit -q` passed 729 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Page.id` still returns a previously acquired ID without calling the batch helper.
- `Page.id` still calls `PageCollection.get_page_ids()` when `_id` is missing.
- If the helper leaves `_id` unset, `Page.id` raises `NotFoundException` naming the affected page fullname.
- Concrete page-ID lookup errors in `PageCollection.get_page_ids()` remain unchanged.
- Source, revision, vote, file, publish, and metadata workflows remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

`Page.id` is a shared direct property used by page source, revision, vote, file, publish, and metadata paths. Even though concrete lookup failures usually happen earlier, the final defensive fallback should still identify the page so automation logs can route the failure without storing raw request URLs, raw HTML, raw response bodies, private rollout paths, credentials, or page contents.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work repeatedly used direct page properties while diagnosing source, revision, file, vote, and publish flows.
- Recent local slices aligned page-level failures around page fullname context; this slice only claims the final `Page.id` property fallback.
- The refreshed complexity memo continues to list parser/source collection helpers and direct property/parser failure messages as follow-up leads, but this slice only claims direct page-ID property fallback context.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw page HTML, raw response bodies, and page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change request batching, `PageCollection.get_page_ids()`, URL construction, duplicate URL handling, cached ID handling, successful ID parsing, source/revision/vote/file acquisition, or publish behavior. It only adds the page fullname to one defensive `Page.id` fallback exception.
