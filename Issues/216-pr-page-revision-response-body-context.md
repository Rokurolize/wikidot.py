# PR Draft: Validate Page Revision Source And HTML Response Bodies

## Summary

`PageRevisionCollection.get_sources()` retrieves generated `history/PageSourceModule` responses, while `PageRevisionCollection.get_htmls()` retrieves generated `history/PageVersionModule` responses. These public flows are also reached through lazy `PageRevision.source` and `PageRevision.html`. Earlier local slices made revision source/HTML acquisition retry-aware, duplicate-ID-aware, parse-once, cached-duplicate-aware, multiline-source-preserving, lazy-failure-visible, and site/page/revision-context-rich for parser and exhausted-fetch failures. The remaining malformed response-body paths still read `response.json()["body"]`, so an AMC response without a `body` field leaked a raw `KeyError` before the revision source or HTML boundary could report which site, page, and revision produced the malformed response.

This follow-up keeps request payloads, retry-exhausted `None` handling, partial-success batch behavior, duplicate revision-ID grouping, cached duplicate source/HTML reuse, source text normalization, `div.page-source` parser strictness, rendered HTML separator trimming, direct body fallback for HTML, lazy property behavior, and exception types for existing paths unchanged. It only treats source and HTML revision responses without JSON `body` fields as malformed revision responses and raises `NoElementException` with site, page, and revision context before source parsing or HTML separator handling.

## Related Issue

Builds on [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [164-pr-page-revision-source-parse-context.md](164-pr-page-revision-source-parse-context.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [200-pr-page-revision-source-parse-site-context.md](200-pr-page-revision-source-parse-site-context.md), and [201-pr-page-revision-lazy-site-context.md](201-pr-page-revision-lazy-site-context.md). Those drafts established page revision source/HTML acquisition as a practical retry-aware workflow with parser boundaries, duplicate handling, cached reuse, text preservation, and site/page/revision diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Read revision source response bodies with `response.json().get("body")`.
- Read revision rendered HTML response bodies with `response.json().get("body")`.
- Convert missing `history/PageSourceModule` response `body` fields into `NoElementException` with site, page, and revision context.
- Convert missing `history/PageVersionModule` response `body` fields into `NoElementException` with site, page, and revision context.
- Preserve retry-exhausted `None` handling as the existing lazy or batch failure behavior.
- Preserve successful source extraction, multiline source normalization, source wrapper strictness, rendered HTML separator trimming, direct HTML body fallback, request payloads, duplicate revision-ID grouping, cached duplicate reuse, and lazy property behavior.
- Add focused regressions for missing source and HTML response-body handling through public collection APIs.

## Type Of Change

- Bug fix / diagnostics improvement
- Page revision response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A revision source response without JSON `body` fails before source wrapper parsing. | `TestPageRevisionCollection.test_get_sources_missing_response_body_includes_site_page_and_revision_context` returns `{}` from the source AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, fabricates empty source text, or enters source parsing rejects this local completion claim. |
| A revision HTML response without JSON `body` fails before separator trimming or direct body fallback. | `TestPageRevisionCollection.test_get_htmls_missing_response_body_includes_site_page_and_revision_context` returns `{}` from the HTML AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, stores empty HTML, or treats missing body as a valid direct body rejects this local completion claim. |
| Malformed revision source and HTML response errors identify site, page, and revision ID. | The focused regressions assert `Page revision source response body is not found for site: test-site, page: test-page, revision: 100` and `Page revision HTML response body is not found for site: test-site, page: test-page, revision: 100`. | A generic parser exception without site/page/revision context rejects this local completion claim. |
| Retry-exhausted `None` responses remain distinct from malformed JSON body responses. | Existing source and HTML retry-exhausted tests remain green and preserve `UnexpectedException` for lazy property access after `None` retry responses. | A change that turns skipped/exhausted `None` responses into body-validation failures rejects this local completion claim. |
| Existing page revision behavior remains green. | `uv run pytest tests/unit/test_page_revision.py -q` passed 37 tests. | Regressions in request payloads, successful source extraction, multiline source normalization, failed retry handling, duplicate revision-ID grouping, cached duplicate reuse, separator trimming, direct HTML fallback, or lazy properties reject this local completion claim. |
| Adjacent page workflows remain green. | `uv run pytest tests/unit/test_page_revision.py tests/unit/test_page.py -q` passed 153 tests. | Regressions in page revision-list acquisition, lazy `Page.revisions`, page source/revision/vote flows, page lookup, or page mutation boundaries reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `ead2941 fix(page_revision): validate revision response bodies`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_missing_response_body_includes_site_page_and_revision_context -q` failed before the fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_missing_response_body_includes_site_page_and_revision_context -q` passed after the source-body fix.
- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_missing_response_body_includes_site_page_and_revision_context -q` failed before the HTML-body fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_missing_response_body_includes_site_page_and_revision_context tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_success tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_skips_failed_retry_response tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_deduplicates_duplicate_revision_ids tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_missing_response_body_includes_site_page_and_revision_context tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_success tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_skips_failed_retry_response tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_deduplicates_duplicate_revision_ids -q` passed 8 tests.
- `uv run pytest tests/unit/test_page_revision.py -q` passed 37 tests.
- `uv run pytest tests/unit/test_page_revision.py tests/unit/test_page.py -q` passed 153 tests.
- `uv run pytest tests/unit -q` passed 755 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageRevisionCollection.get_sources()` still uses retry-aware AMC and the same `history/PageSourceModule` request payload.
- `PageRevisionCollection.get_htmls()` still uses retry-aware AMC and the same `history/PageVersionModule` request payload.
- A missing source response JSON `body` raises `NoElementException` naming the site, page, and revision ID.
- A missing HTML response JSON `body` raises `NoElementException` naming the site, page, and revision ID.
- Missing response-body handling does not convert retry-exhausted `None` responses into malformed-body failures.
- Successful source extraction, multiline source normalization, source wrapper strictness, rendered HTML separator trimming, direct HTML body fallback, duplicate revision-ID grouping, cached duplicate reuse, and lazy `PageRevision.source` / `PageRevision.html` behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Revision source and rendered HTML inspection depend on Wikidot returning JSON `body` fields for generated history module responses. If a response is malformed, wikidot.py should report a structured failure with the site, page, and revision ID, not a raw dictionary `KeyError`, so caller logs can route the failure without preserving raw response JSON, generated source/HTML payloads, credentials, local rollout paths, or private page history content.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established page revision source/HTML acquisition as retry-aware, deduplicated, parse-once, cache-aware, and used through both collection APIs and lazy `PageRevision.source` / `PageRevision.html`.
- Recent response-body validation slices in private-message, forum-post, forum-category, forum-thread, site-application, site-member, and page-file modules showed the same raw `KeyError` failure mode at AMC response-body boundaries.
- The refreshed complexity memo continues to list raw response-body boundaries in `forum_post_revision`, `page`, and `site` as follow-up leads, but this slice only claims page revision source/HTML response-body validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated source/HTML bodies, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, retry-exhausted `None` handling, duplicate revision-ID grouping, cached duplicate reuse, source text extraction, source wrapper parser strictness, rendered HTML separator handling, direct HTML body fallback, lazy property behavior, page revision-list parsing, mutation methods, or live Wikidot behavior. It only converts missing page revision source/HTML response `body` fields into site/page/revision-context `NoElementException` failures before parser work.
