# PR Draft: Include Site Context In Page Source Parse Failures

## Summary

`PageCollection.get_page_sources()` parses `viewsource/ViewSourceModule` responses and raises `NoElementException` when a response body lacks the expected `div.page-source` wrapper. Earlier local slices made source acquisition retry-aware, preserved later successes in a batch after a malformed response, exposed failed source iterator records, and added site-aware unresolved-source failures. The malformed source-wrapper parser error, however, still identified only the page fullname and ID: `Cannot find source element for page: scp-001 (id=123)`.

This follow-up keeps source request batching, retry behavior, duplicate page-ID reuse, cached source reuse, later-success preservation, parse-failure isolation, source text extraction, exception type, and lazy `Page.source` behavior unchanged. It only adds the site unix name to that existing source parser failure message: `Cannot find source element for site: <site>, page: <fullname> (id=<id>)`.

## Related Issue

Builds on [014-pr-preserve-viewsource-text.md](014-pr-preserve-viewsource-text.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [026-pr-source-iterator-parse-failure-isolation.md](026-pr-source-iterator-parse-failure-isolation.md), [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), [111-pr-page-source-cache-reuse.md](111-pr-page-source-cache-reuse.md), [194-pr-page-source-site-context.md](194-pr-page-source-site-context.md), [195-pr-source-iterator-site-context.md](195-pr-source-iterator-site-context.md), and [197-pr-page-id-site-context.md](197-pr-page-id-site-context.md). Those drafts established direct page-source parsing and source iterator failure ledgers as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Include `site.unix_name`, representative page fullname, and page ID in the `NoElementException` raised when a `ViewSourceModule` response lacks `div.page-source`.
- Preserve the existing behavior where a malformed response records the first source parse error but still parses later successful responses in the same batch before raising.
- Preserve source request construction, retry behavior, duplicate page-ID grouping, cached source reuse, source text extraction, lazy `Page.source`, and exception type.

## Type Of Change

- Bug fix / diagnostics improvement
- Source parser ledger context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed source responses still raise `NoElementException`, but identify site, page, and page ID. | `TestPageCollectionAcquire.test_acquire_sources_preserves_later_successes_when_parse_fails` asserts `Cannot find source element for site: test-site, page: malformed-page (id=222)`. | Changing exception type, returning a fabricated source, or leaving a page-only message rejects this local completion claim. |
| Later successful source responses in the same batch are still preserved before the first parse error is raised. | The focused regression still asserts the first and third pages receive source text while the malformed second page remains unset. | Aborting the batch before later successes or losing parsed sources rejects this local completion claim. |
| Request construction and retry-aware source acquisition remain unchanged. | The same focused test asserts `amc_request` is not used, while adjacent page/site tests cover source acquisition and source iterator workflows. | Regressions in request payloads, retry behavior, cached source reuse, duplicate ID handling, or source iterator behavior reject this local completion claim. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 182 tests. | Regressions in page ID lookup, source loading, direct page source reads, source iterator records, ListPages parsing, or publish-adjacent source verification reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `343d502 fix(page): include site in source parse failures`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_preserves_later_successes_when_parse_fails -q` failed before the fix because the message was `Cannot find source element for page: malformed-page (id=222)`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_preserves_later_successes_when_parse_fails -q`.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 182 tests.
- `uv run pytest tests/unit -q` passed 733 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageCollection.get_page_sources()` still uses retry-aware source acquisition and the existing `ViewSourceModule` payloads.
- Cached source reuse and duplicate page-ID grouping remain unchanged.
- A malformed source wrapper still raises `NoElementException`.
- That source parser failure now includes site unix name, page fullname, and page ID.
- Later successful source responses in the same batch remain cached on their pages before the first parse error is raised.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Large source collection workflows often aggregate parser failures into plain-text ledgers. A page-only source parse error is ambiguous when the same fullname exists on multiple Wikidot sites. Adding site context makes the existing strict source parser failure self-contained without changing request behavior, successful parsing, or how malformed responses are classified.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified source collection, source iterator failure records, and source parser failures as practical workflow surfaces for large corpus runs.
- Recent site-context slices showed the same low-risk pattern: add compact site/object identifiers to existing plain-text exceptions without changing successful behavior.
- This slice only claims source parser diagnostics. It does not claim any live Wikidot behavior change.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally keeps the existing representative-page wording for duplicate page-ID groups. Pages sharing the same page ID still share one parsed source response, and a malformed shared response reports the first page in that group just as the previous page-only message did.
