# PR Draft: Report Malformed Page Revision Response Body Types

## Summary

`PageRevisionCollection.get_sources()` parses `history/PageSourceModule` response `body` values as generated source-form HTML before extracting `div.page-source`. `PageRevisionCollection.get_htmls()` parses `history/PageVersionModule` response `body` values as generated rendered revision HTML before trimming the version-info wrapper. Both public collection methods are also reached through lazy `PageRevision.source` and `PageRevision.html`. Earlier local slices made these paths retry-aware, duplicate-aware, cache-aware, parse-once, context-rich for missing response bodies, context-rich for malformed source wrappers, and safe around lazy fetch failures. One adjacent response-boundary gap remained: if the decoded AMC response was a dictionary with a present but non-string `body` value, the source path called string normalization on it and the HTML path called string separator logic on it, leaking low-level `AttributeError` failures.

This local slice validates present page revision source and HTML response `body` values before string normalization, BeautifulSoup parsing, or separator trimming. Non-string bodies now raise `NoElementException` with site/page/revision context plus `field=body`, expected type, and observed type. The diagnostic reports only compact structural context and type names; it does not include raw generated source HTML, rendered revision HTML, response JSON, page source text, revision comments, local rollout paths, credentials, account material, or private page content.

## Outcome

Malformed page revision source and HTML response body types now fail at the module response boundary with actionable site/page/revision context instead of string-method internals.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page history inspection, source auditing, rollback helpers, publication verification, or revision rendering workflows.

## Related Issue

Builds on [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [164-pr-page-revision-source-parse-context.md](164-pr-page-revision-source-parse-context.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [200-pr-page-revision-source-parse-site-context.md](200-pr-page-revision-source-parse-site-context.md), [201-pr-page-revision-lazy-site-context.md](201-pr-page-revision-lazy-site-context.md), and [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md). Those drafts established page revision source and HTML acquisition as practical retry-aware workflows with parser boundaries, duplicate handling, cached reuse, text preservation, and site/page/revision diagnostics while leaving present non-string response bodies as a separate parser-entry boundary.

This also follows the response-body type diagnostic pattern from [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), and [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate page revision source response `body` values are strings before source normalization and BeautifulSoup parsing.
- Convert present non-string source body values into site/page/revision-specific `NoElementException`.
- Validate page revision HTML response `body` values are strings before separator trimming or direct body fallback.
- Convert present non-string HTML body values into site/page/revision-specific `NoElementException`.
- Preserve missing-body diagnostics, retry-exhausted behavior, duplicate revision-ID grouping, cached duplicate reuse, source extraction, source wrapper strictness, rendered HTML separator trimming, direct HTML body fallback, lazy property behavior, and adjacent page workflows.

## Type Of Change

- Bug fix / diagnostics improvement
- Page revision response-body type validation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A revision source response with a present non-string `body` field must fail before source normalization or BeautifulSoup parsing. |
| R2 | A revision HTML response with a present non-string `body` field must fail before separator trimming or direct body fallback. |
| R3 | Malformed-body-type errors must identify the affected site, page, revision, `field=body`, expected type, and observed type while omitting raw generated revision content. |
| R4 | Existing missing-body diagnostics, retry handling, duplicate handling, cache behavior, source extraction, HTML trimming, lazy behavior, and adjacent page workflows must remain compatible. |
| R5 | Focused, page-revision, adjacent page, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `PageRevisionCollection.get_sources()` raises contextual `NoElementException` when `history/PageSourceModule` returns a list-valued `body`. | `TestPageRevisionCollection.test_get_sources_malformed_response_body_type_includes_site_page_revision_and_type_context` expects `Page revision source response body is malformed for site: test-site, page: test-page, revision: 100 (field=body, expected=str, actual=list)` and asserts `_source is None`. | Leaking low-level `AttributeError`, fabricating empty source text, marking source acquired, or entering source-wrapper parsing rejects this local completion claim. | Page revision source reads | `tests/unit/test_page_revision.py` |
| R2 | `PageRevisionCollection.get_htmls()` raises contextual `NoElementException` when `history/PageVersionModule` returns a list-valued `body`. | `TestPageRevisionCollection.test_get_htmls_malformed_response_body_type_includes_site_page_revision_and_type_context` expects `Page revision HTML response body is malformed for site: test-site, page: test-page, revision: 100 (field=body, expected=str, actual=list)` and asserts `_html is None`. | Leaking low-level `AttributeError`, storing a non-string body, or treating malformed input as direct rendered HTML rejects this local completion claim. | Page revision HTML reads | `tests/unit/test_page_revision.py` |
| R3 | The malformed-body-type diagnostics include only structural identifiers, field name, expected type, and observed type. | The focused regressions match the full message shapes using synthetic list-valued bodies. | Including raw response JSON, generated source HTML, rendered revision HTML, page source text, revision comments, credentials, local rollout paths, or account names rejects this local completion claim. | Page revision diagnostics | `src/wikidot/module/page_revision.py` |
| R4 | Existing page-revision and adjacent page behavior remain green. | The page-revision suite passed 39 tests, the adjacent page/page-revision run passed 197 tests, and the full unit suite passed 899 tests. | Regressing missing-body diagnostics, retry exhaustion, duplicate revision-ID grouping, cached duplicate reuse, source extraction, source wrapper strictness, HTML trimming, direct HTML fallback, lazy behavior, or page workflows rejects this local completion claim. | Page revision workflows | `tests/unit/test_page_revision.py`; `tests/unit/test_page.py` |
| R5 | Repository quality gates pass in the local dependency environment. | `ruff`, `mypy`, full unit, and whitespace checks passed before the code commit; `pyright` remained unavailable in this environment. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4527a53 fix(page_revision): report malformed body types`.

- RED: `uv run --extra test pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_malformed_response_body_type_includes_site_page_revision_and_type_context -q` failed before the fix with `AttributeError` for the list-valued source body.
- GREEN: `uv run --extra test pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_malformed_response_body_type_includes_site_page_revision_and_type_context tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_missing_response_body_includes_site_page_and_revision_context tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_success tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_skips_failed_retry_response tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_deduplicates_duplicate_revision_ids -q` passed 5 tests.
- RED: `uv run --extra test pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_malformed_response_body_type_includes_site_page_revision_and_type_context -q` failed before the fix with `AttributeError` for the list-valued HTML body.
- GREEN: `uv run --extra test pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_malformed_response_body_type_includes_site_page_revision_and_type_context tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_missing_response_body_includes_site_page_and_revision_context tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_success tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_skips_failed_retry_response tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_deduplicates_duplicate_revision_ids tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_malformed_response_body_type_includes_site_page_revision_and_type_context tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_missing_response_body_includes_site_page_and_revision_context tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_success tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_skips_failed_retry_response tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_deduplicates_duplicate_revision_ids -q` passed 10 tests.
- `uv run --extra test pytest tests/unit/test_page_revision.py -q` passed 39 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_revision.py -q` passed 197 tests.
- `uv run --extra test pytest tests/unit -q` passed 899 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- `PageRevisionCollection.get_sources()` still requests `history/PageSourceModule` with the existing revision payload.
- `PageRevisionCollection.get_htmls()` still requests `history/PageVersionModule` with the existing revision payload.
- Missing `body` fields still raise the existing not-found diagnostics from Issue 216.
- Present non-string source `body` values raise contextual `NoElementException` before source normalization or BeautifulSoup parsing.
- Present non-string HTML `body` values raise contextual `NoElementException` before separator trimming or direct body fallback.
- The malformed source-body-type message includes site, page, revision, `field=body`, expected type, and observed type.
- The malformed HTML-body-type message includes site, page, revision, `field=body`, expected type, and observed type.
- The malformed-body-type messages do not include raw response JSON, generated source HTML, rendered revision HTML, page source text, revision comments, credentials, local rollout paths, private page content, or private account material.
- Existing retry-exhausted behavior, duplicate revision-ID grouping, cached duplicate reuse, source extraction, source wrapper strictness, rendered HTML separator trimming, direct HTML body fallback, lazy `PageRevision.source`, lazy `PageRevision.html`, and adjacent page workflows remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real revision response body, local rollout path, account material, private page content, page source text, or generated revision HTML is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Type validation could treat a future bytes-like body as malformed. Mitigation: AMC JSON bodies are expected to decode generated source or rendered HTML as strings; preserving only string input keeps the parser boundary explicit.
- Risk: Type validation could mask missing-body diagnostics. Mitigation: `None` remains on the existing missing-body path; only present non-string values use the malformed-type diagnostic.
- Risk: Diagnostics could expose page history content. Mitigation: messages include only site/page/revision identifiers and type names, not raw generated HTML, source text, comments, or page content.
- Risk: HTML validation could accidentally change direct body fallback behavior. Mitigation: the type check runs before separator trimming but leaves all valid string bodies on the existing fallback path.

## Dependencies

- The AMC connector already validates decoded response roots as dictionaries before normal module parsing; this slice targets the `body` field value within that dictionary.
- Page revision source extraction and rendered HTML trimming behavior remains unchanged after a valid string body is supplied.

## Open Questions

None for this local slice. Remaining useful work should continue the broader response-body field-type audit across other modules rather than expanding this page-revision change beyond source and HTML response boundaries.

## Upstream-Safe Motivation

Page revision source and rendered HTML inspection are practical browser-free workflows for history review, rollback preparation, publication verification, and source auditing. If Wikidot returns a present non-string generated response body, wikidot.py should report the affected revision read path and type mismatch before string-method internals obscure the failure.

## Local Evidence, Not For Upstream Paste

- The RED failures showed list-valued source and HTML `body` values leaking low-level `AttributeError`.
- Existing Issue 216 covered missing revision source and HTML `body` fields but intentionally left present malformed values as separate boundaries.
- The recent response-body type series showed the same boundary pattern in private messages, forum categories, site members, site applications, direct page-file reads, forum-thread reads, and forum-post reads.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated source HTML, rendered revision HTML, page source text, revision comments, and private page content out of upstream discussion.

## Additional Notes

This is a response-body field type diagnostics fix. It preserves valid page revision source and HTML behavior while making malformed present response bodies actionable without retaining generated revision content or source text.
