# PR Draft: Report Malformed Page Source Response Body Types

## Summary

`PageCollection.get_page_sources()` batches `viewsource/ViewSourceModule` requests, groups duplicate page IDs, reuses cached source text, preserves neighboring successful source responses, and raises the first structural source error after processing the batch. Issue 221 converted missing source response `body` fields into contextual `NoElementException` failures while preserving later successes. One adjacent parser-boundary gap remained: a present but non-string source response `body` still reached `body.replace("&nbsp;", " ")`, leaking a low-level `AttributeError` and aborting the batch before later successes could be applied.

This local slice validates present page source response `body` values before normalization and BeautifulSoup parsing. Non-string bodies now record a site/page/id-specific `NoElementException` with `field=body`, expected type, and observed type, then continue processing later source responses before raising the first structural source error. The diagnostic includes only compact structural context and type names; it does not include raw source text, generated source HTML, response JSON, local rollout paths, credentials, account material, or private page content.

## Outcome

Malformed page source response body types now fail at the ViewSource response boundary with actionable site/page/id context while preserving successful neighboring source results in the same batch.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free source collection, source verification, source iterators, publication workflows, or local page inventory tools.

## Related Issue

Builds on [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md), [008-pr-skip-cached-source-fetches.md](008-pr-skip-cached-source-fetches.md), [014-pr-preserve-viewsource-text.md](014-pr-preserve-viewsource-text.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [025-pr-source-result-error-page-context.md](025-pr-source-result-error-page-context.md), [026-pr-source-iterator-parse-failure-isolation.md](026-pr-source-iterator-parse-failure-isolation.md), [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md), [051-pr-preserve-source-batch-successes.md](051-pr-preserve-source-batch-successes.md), [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [149-pr-page-source-failure-context.md](149-pr-page-source-failure-context.md), [194-pr-page-source-site-context.md](194-pr-page-source-site-context.md), [198-pr-page-source-parse-site-context.md](198-pr-page-source-parse-site-context.md), and [221-pr-page-source-batch-response-body-context.md](221-pr-page-source-batch-response-body-context.md). Those drafts established batched page source acquisition as a practical partial-success workflow with cached-source reuse, duplicate ID grouping, multiline ViewSource preservation, retry handling, and page-context diagnostics while leaving present non-string response bodies as a separate parser-entry boundary.

This also follows the response-body type diagnostic pattern from [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), and [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Preserve the existing missing-body diagnostic from Issue 221.
- Validate present batched page source response `body` values are strings before `&nbsp;` normalization and BeautifulSoup parsing.
- Convert present non-string source `body` values into site/page/id-specific `NoElementException`.
- Preserve later successful source responses in the same batch after a malformed body type.
- Preserve retry-exhausted `None` handling, cached-source reuse, duplicate page-ID grouping, page-ID acquisition, source wrapper parsing, `&nbsp;` normalization, multiline source extraction, lazy `Page.source`, and source refresh behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Page source response-body type validation
- Partial-success preservation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A page source response with a present non-string `body` field must fail before string normalization and BeautifulSoup parsing. |
| R2 | Malformed page source response body type errors must identify the affected site, page fullname, page ID, `field=body`, expected type, and observed type while omitting raw source content. |
| R3 | A malformed middle response in a source batch must not prevent later successful source responses from being applied before the first structural source error is raised. |
| R4 | Missing-body diagnostics, retry-exhausted `None` handling, cached-source reuse, duplicate page-ID grouping, page-ID acquisition, source wrapper parsing, `&nbsp;` normalization, multiline source extraction, lazy `Page.source`, and source refresh behavior must remain compatible. |
| R5 | Focused, acquisition, page, adjacent page/search/site, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `PageCollection.get_page_sources()` raises contextual `NoElementException` when a `viewsource/ViewSourceModule` response returns a list-valued `body`. | `TestPageCollectionAcquire.test_acquire_sources_malformed_response_body_type_preserves_later_successes_with_page_context` expects `Page source response body is malformed for site: test-site, page: malformed-body-page (id=222, field=body, expected=str, actual=list)`. | Leaking `AttributeError`, entering `body.replace`, entering BeautifulSoup parsing, fabricating empty source text, or silently skipping the malformed response rejects this local completion claim. | Batched page source response reads | `tests/unit/test_page.py` |
| R2 | The malformed-body-type diagnostic includes only structural identifiers, field name, expected type, and observed type. | The focused regression matches the full message shape using a synthetic list-valued body. | Including raw response JSON, generated ViewSource HTML, page source text, credentials, local rollout paths, account names, or private page content rejects this local completion claim. | Page source diagnostics | `src/wikidot/module/page.py` |
| R3 | The first and third pages in a three-entry source batch still receive source text when the middle response has a malformed body type. | The focused regression verifies `first source` and `third source` are applied while the malformed page remains uncached and the batch raises after processing. | Aborting before later successes, returning partial success without raising, or assigning source to the malformed page rejects this local completion claim. | Source batch partial-success behavior | `tests/unit/test_page.py` |
| R4 | Existing source acquisition and adjacent page behaviors remain green. | `TestPageCollectionAcquire` passed 45 tests, `tests/unit/test_page.py` passed 161 tests, and the adjacent page/search/site run passed 264 tests. | Regressing missing-body diagnostics, retry-exhausted `None` handling, cached-source reuse, duplicate source reuse, page-ID lookup, source wrapper parsing, ViewSource text normalization, lazy `Page.source`, source refresh, revision acquisition, vote acquisition, or file acquisition rejects this local completion claim. | Page source workflows | `tests/unit/test_page.py`; `tests/unit/test_search_pages_query.py`; `tests/unit/test_site.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit passed 904 tests; `ruff`, format check, `mypy`, and whitespace checks passed before the code commit; `pyright` remained unavailable in this environment. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4d7b1ee fix(page): report malformed source response bodies`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_malformed_response_body_type_preserves_later_successes_with_page_context -q` failed before the fix with `AttributeError: 'list' object has no attribute 'replace'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_malformed_response_body_type_preserves_later_successes_with_page_context -q` passed after the fix.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 45 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 161 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_search_pages_query.py tests/unit/test_site.py -q` passed 264 tests.
- `uv run pytest tests/unit -q` passed 904 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- `PageCollection.get_page_sources()` still batches uncached page source requests by page ID.
- Cached source reuse and duplicate page-ID source reuse remain unchanged.
- Retry-exhausted `None` responses remain skipped partial-success entries and are not converted into malformed-body failures.
- Missing source response `body` fields still raise the existing not-found diagnostic from Issue 221.
- Present non-string source response `body` values raise contextual `NoElementException` before `body.replace` and BeautifulSoup parsing.
- The malformed-body-type message includes site, page fullname, page ID, `field=body`, expected type, and observed type.
- Later successful responses in the same source batch are still applied before the first structural source error is raised.
- Source wrapper parsing, `&nbsp;` normalization, multiline source extraction, lazy `Page.source`, and source refresh behavior remain unchanged for valid string bodies.
- The malformed-body-type message does not include raw response JSON, generated ViewSource HTML, page source text, credentials, local rollout paths, private page content, or private account material.
- No live Wikidot action, upstream Issue, upstream PR, push, real source response body, account material, private page content, or generated ViewSource HTML is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Type validation could treat a future bytes-like body as malformed. Mitigation: AMC JSON bodies are expected to decode generated module HTML as strings; preserving only string input keeps the parser boundary explicit.
- Risk: Type validation could mask missing-body diagnostics. Mitigation: `None` remains on the existing missing-body path; only present non-string values use the malformed-type diagnostic.
- Risk: Diagnostics could expose source content. Mitigation: messages include only site/page/id identifiers and type names, not raw response JSON, ViewSource HTML, source text, or local evidence.
- Risk: Partial-success handling could accidentally change source caching behavior. Mitigation: the regression proves first and later successful sources are applied, the malformed page remains uncached, and acquisition/page/adjacent/full unit checks remain green.

## Dependencies

- The AMC connector already validates decoded response roots as dictionaries before normal module parsing; this slice targets the `body` field value within that dictionary.
- Source wrapper parsing and `extract_page_source_text()` remain unchanged after a valid string body is supplied.

## Open Questions

None for this local slice. Remaining useful work should continue the broader response-body field-type audit across page revision/vote/file batch helpers, page auxiliary helpers, and recent changes rather than expanding this page source change beyond the ViewSource response boundary.

## Upstream-Safe Motivation

Page source acquisition is a core browser-free read path for source verification, source iteration, publication checks, and corpus workflows. If Wikidot returns a present non-string generated module body, wikidot.py should keep successful neighboring results and report the affected site/page/id before parser internals obscure the failure.

## Local Evidence, Not For Upstream Paste

- The RED failure showed a list-valued ViewSource response `body` leaking `AttributeError` at `body.replace("&nbsp;", " ")`.
- Existing Issue 221 covered missing batched page source response `body` fields but intentionally left present malformed values as separate boundaries.
- The recent response-body type series showed the same boundary pattern in private messages, forum categories, site members, site applications, direct page-file reads, forum-thread reads, forum-post reads, page-revision reads, forum-post-revision reads, and ListPages reads.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated source HTML, page source text, and site content out of upstream discussion.

## Additional Notes

This is a response-body field type diagnostics fix. It preserves valid page source acquisition behavior while making malformed present response bodies actionable without retaining generated source content or response payloads.
