# PR Draft: Include Page Context In Page ID Response Type Errors

## Summary

`PageCollection.get_page_ids()` fetches each missing page ID by requesting the page's `norender/true/noredirect/true` URL and parsing `WIKIREQUEST.info.pageId`. The existing missing-ID error already names the affected page, but the adjacent non-HTTP response guard only reported the Python type, for example `Unexpected response type: <class 'wikidot.common.exceptions.UnexpectedException'>`.

This change keeps batching, duplicate URL reuse, cached ID propagation, request URLs, successful ID parsing, and exception type unchanged, but reports the representative page fullname when a response slot is not an `httpx.Response`: `Unexpected response type for page: <fullname>, type: <type>`.

## Related Issue

Builds on [060-pr-deduplicate-page-id-fetches.md](060-pr-deduplicate-page-id-fetches.md), because that draft established page-ID lookup as a batched URL-keyed path where duplicate pages share a response slot. It also complements later page/source/revision/file/vote context fixes that made caller logs identify the affected page without storing raw HTTP bodies.

No upstream issue was filed from this local workspace.

## Changes

- Include the representative page fullname in page-ID lookup non-HTTP response errors.
- Keep the existing missing `WIKIREQUEST.info.pageId` page-context error unchanged.
- Preserve duplicate URL batching and propagation to all matching `Page` objects.
- Add a focused regression for a non-HTTP response object returned from `RequestUtil.request(...)`.

## Type Of Change

- Bug fix / diagnostics improvement
- Page ID lookup context
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A non-HTTP page-ID response still raises `UnexpectedException`. | `TestPageCollectionAcquire.test_acquire_page_ids_unexpected_response_type_includes_page_context` returns an `UnexpectedException` object from the request utility and expects `UnexpectedException`. | A change that silently skips the failed response, fabricates an ID, or caches an invalid ID rejects this local completion claim. |
| The exception identifies the affected page. | The focused regression asserts `Unexpected response type for page: test-page`. | The RED test failed before the fix because the message only reported the Python response type. |
| Successful page-ID lookup behavior remains unchanged. | `uv run pytest tests/unit/test_page.py -q` passed 110 tests. | Regressions in duplicate URL dedupe, cached ID reuse, source/revision/vote/file acquisition, parsing, or page accessors reject this local completion claim. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py -q` passed 250 tests. | Regressions in site publishing, source collection, revision/file/vote detail acquisition, or page metadata behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `0a73e68 fix(page): include context in page id response errors`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_unexpected_response_type_includes_page_context -q` failed before the fix because the exception message was `Unexpected response type: <class 'wikidot.common.exceptions.UnexpectedException'>`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_unexpected_response_type_includes_page_context -q`.
- `uv run pytest tests/unit/test_page.py -q` passed 110 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py -q` passed 250 tests.
- `uv run pytest tests/unit -q` passed 728 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageCollection.get_page_ids()` still batches missing page-ID lookups by page URL.
- Pages sharing the same request URL still reuse a single fetched ID.
- Already acquired duplicate page IDs still propagate without a new request.
- A successful response still parses `WIKIREQUEST.info.pageId` and assigns it to all pages represented by the response slot.
- A response body missing `WIKIREQUEST.info.pageId` still raises the existing page-specific `Cannot find page id: <fullname>` error.
- A non-HTTP response slot now raises `UnexpectedException` naming the representative page fullname and observed type.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Page ID lookup is a shared prerequisite for source, revision, vote, file, publish, and fallback workflows. When a request utility returns an exception object or other non-HTTP value in a batched response slot, caller logs need the affected page fullname to route the failure without preserving raw HTML, raw response bodies, private rollout paths, credentials, or page contents.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work repeatedly used page ID acquisition as a recovery point for source, revision, file, vote, and publishing paths.
- Earlier local drafts made missing IDs page-specific and deduplicated page-ID URLs; this slice only fills the adjacent non-HTTP response-type diagnostic gap.
- The refreshed complexity memo continues to list parser/source collection helpers and direct property/parser failure messages as follow-up leads, but this slice only claims page-ID response-type context.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw page HTML, raw response bodies, and page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change request batching, retry behavior in callers, URL construction, duplicate URL handling, cached ID handling, successful ID parsing, missing-ID errors, source/revision/vote/file acquisition, or publish behavior. It only adds the page fullname to one existing response-type exception path.
