# PR Draft: Report Malformed Recent Changes Response Body Types

## Summary

`Site.get_recent_changes()` parses generated `changes/SiteChangesListModule` response `body` values for the first recent-changes page and, when pagination is present, for later pages. Issue 218 converted missing recent-changes response `body` fields into site/page-context `NoElementException` failures, while earlier recent-changes slices covered retry behavior, pagination batching, comment scoping, pager filtering, text spacing, and row parser diagnostics. One adjacent response-boundary gap remained: present but non-string response `body` values still reached BeautifulSoup, leaking low-level parser internals before wikidot.py could identify which site and recent-changes page produced the malformed generated module response.

This local slice validates present recent-changes response `body` values before BeautifulSoup parsing. Non-string bodies now raise `NoElementException` with site/page context plus `field=body`, expected type, and observed type. The diagnostic includes only compact structural context and type names; it does not include raw response JSON, generated recent-changes HTML, page titles, edit comments, account material, local rollout paths, credentials, or private site content.

## Outcome

Malformed recent-changes response body types now fail at the generated-module response boundary with actionable site/page context instead of BeautifulSoup `AttributeError`.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free recent-changes reads for moderation ledgers, archival indexing, publication audits, migration tooling, or activity monitoring.

## Related Issue

Builds on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), and [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md). Those drafts established recent-changes acquisition as a retry-aware, batched, parser-scoped, page-context-rich workflow while leaving present non-string response bodies as a separate parser-entry boundary.

This also follows the response-body type diagnostic pattern from [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md), [331-pr-page-source-response-body-type-context.md](331-pr-page-source-response-body-type-context.md), [332-pr-page-revision-list-response-body-type-context.md](332-pr-page-revision-list-response-body-type-context.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), and [335-pr-page-auxiliary-response-body-type-context.md](335-pr-page-auxiliary-response-body-type-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Preserve the existing missing-body diagnostics from Issue 218.
- Validate present first-page recent-changes response `body` values are strings before BeautifulSoup parsing.
- Validate present paginated recent-changes response `body` values are strings before BeautifulSoup parsing.
- Convert present non-string recent-changes response `body` values into site/page-specific `NoElementException`.
- Preserve retry-exhausted `None` handling, request payloads, zero-limit behavior, empty first-page behavior, first-page-before-pager behavior, structural pager parsing, comment-pager filtering, batched later-page requests, limit-based page trimming, row parser context, text-spacing behavior, and successful row parsing.

## Type Of Change

- Bug fix / diagnostics improvement
- Recent changes response-body type validation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A first-page recent-changes response with a present non-string `body` field must fail before BeautifulSoup parsing. |
| R2 | A paginated recent-changes response with a present non-string `body` field must fail before BeautifulSoup parsing and name the affected recent-changes page. |
| R3 | Malformed recent-changes response body type errors must identify the site, page number, `field=body`, expected type, and observed type while omitting raw generated content. |
| R4 | Existing missing-body diagnostics, retry-exhausted `None` handling, request payloads, zero-limit behavior, empty first-page behavior, pager handling, batching, row parser context, text spacing, and successful parsing must remain compatible. |
| R5 | Focused, recent-changes, site, adjacent site/page, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `Site.get_recent_changes()` raises contextual `NoElementException` when the first `changes/SiteChangesListModule` response returns a list-valued `body`. | `TestSiteGetRecentChanges.test_get_recent_changes_first_page_malformed_response_body_type_includes_site_context` expects `Recent changes response body is malformed for site: test, page: 1 (field=body, expected=str, actual=list)`. | Leaking BeautifulSoup `AttributeError`, returning an empty list, entering row parsing, or hiding the site/page context rejects this local completion claim. | First recent-changes response body | `tests/unit/test_site.py` |
| R2 | `Site.get_recent_changes()` raises contextual `NoElementException` when page 2 returns a list-valued `body`. | `TestSiteGetRecentChanges.test_get_recent_changes_paginated_malformed_response_body_type_includes_site_context` expects `Recent changes response body is malformed for site: test, page: 2 (field=body, expected=str, actual=list)`. | Returning partial page 1 results, silently truncating pagination, leaking BeautifulSoup internals, or reporting the wrong page rejects this local completion claim. | Paginated recent-changes response bodies | `tests/unit/test_site.py` |
| R3 | The malformed-body-type diagnostics include only structural identifiers, field name, expected type, and observed type. | The focused regressions match the full message shape using synthetic list-valued bodies. | Including raw response JSON, generated recent-changes HTML, page titles, edit comments, credentials, local rollout paths, account names, or private site content rejects this local completion claim. | Recent-changes diagnostics | `src/wikidot/module/site.py` |
| R4 | Existing recent-changes behavior remains green. | The focused compatibility group passed 10 tests, `TestSiteGetRecentChanges` passed 25 tests, `tests/unit/test_site.py` passed 84 tests, and the adjacent site/member/application/page run passed 314 tests. | Regressing missing-body diagnostics, retry exhaustion, successful parsing, empty response behavior, limit handling, pager handling, batched pagination, comment-pager filtering, row parse context, or text spacing rejects this local completion claim. | Recent-changes workflow | `tests/unit/test_site.py`; `tests/unit/test_site_member.py`; `tests/unit/test_site_application.py`; `tests/unit/test_page.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit passed 911 tests; `ruff`, format check, `mypy`, and whitespace checks passed before the code commit; `pyright` remained unavailable in this environment. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `dc7a954 fix(site): report malformed recent change bodies`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_malformed_response_body_type_includes_site_context -q` failed before the first-page fix with `AttributeError: 'list' object has no attribute 'startswith'` from BeautifulSoup.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_malformed_response_body_type_includes_site_context -q` passed after the first-page fix.
- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_malformed_response_body_type_includes_site_context -q` failed before the paginated fix with `AttributeError: 'list' object has no attribute 'startswith'` from BeautifulSoup.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_malformed_response_body_type_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_malformed_response_body_type_includes_site_context -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_missing_response_body_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_malformed_response_body_type_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_missing_response_body_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_malformed_response_body_type_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_success tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_retries_transient_amc_failures tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_retry_exhaustion_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_retry_exhaustion_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_batches_paginated_pages tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_batches_only_pages_needed_for_limit -q` passed 10 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 25 tests.
- `uv run --extra test pytest tests/unit/test_site.py -q` passed 84 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_page.py -q` passed 314 tests.
- `uv run --extra test pytest tests/unit -q` passed 911 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `Site.get_recent_changes()` still uses retry-aware AMC and the same `changes/SiteChangesListModule` request payload for page 1.
- `Site.get_recent_changes()` still uses retry-aware AMC and the same per-page request payloads for later pages.
- Missing first-page and paginated response `body` fields still raise the existing not-found diagnostics from Issue 218.
- Retry-exhausted `None` responses remain `UnexpectedException` failures and are not converted into malformed-body failures.
- Present non-string first-page response `body` values raise contextual `NoElementException` before BeautifulSoup parsing.
- Present non-string paginated response `body` values raise contextual `NoElementException` before BeautifulSoup parsing and include the affected page number.
- Valid recent-changes parsing, empty first-page return, zero-limit fast return, structural pager parsing, comment-pager filtering, batched pagination, limit-based page trimming, row parser context, and text-spacing behavior remain unchanged for valid string bodies.
- The malformed-body-type messages do not include raw response JSON, generated recent-changes HTML, page titles, edit comments, credentials, local rollout paths, private account material, or private site content.
- No live Wikidot action, upstream Issue, upstream PR, push, real recent-changes response body, account material, credentials, generated markup, edit comments, or private page content is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Type validation could treat a future bytes-like body as malformed. Mitigation: AMC JSON bodies are expected to decode generated module HTML as strings; preserving only string input keeps the parser boundary explicit.
- Risk: Type validation could mask missing-body diagnostics. Mitigation: `None` remains on the existing missing-body path; only present non-string values use the malformed-type diagnostic.
- Risk: Later-page validation could silently drop already-parsed first-page changes. Mitigation: the paginated regression asserts the affected page 2 failure path and rejects silent truncation or partial success.
- Risk: Diagnostics could expose generated recent-changes content. Mitigation: the error reports only site/page identifiers and type names, not raw generated module markup, page titles, edit comments, or response JSON.

## Dependencies

- The AMC connector already validates decoded response roots as dictionaries before normal module parsing; this slice targets the `body` field value within that dictionary.
- `changes/SiteChangesListModule` continues to expose recent changes as generated string markup for valid responses.

## Open Questions

None for this local slice. Remaining useful work should continue the response-body field-type audit on any remaining generated module helpers rather than expanding recent-changes behavior beyond the response boundary.

## Upstream-Safe Motivation

Recent-changes reads are practical browser-free workflows for moderation, auditing, archival indexing, migration tooling, and activity monitoring. If Wikidot returns a present non-string generated module body, wikidot.py should report the affected site and recent-changes page before parser internals obscure the failure.

## Local Evidence, Not For Upstream Paste

- The RED failure showed a list-valued first-page recent-changes response `body` leaking BeautifulSoup `AttributeError: 'list' object has no attribute 'startswith'`.
- The RED failure showed the same BeautifulSoup failure for a list-valued paginated recent-changes response `body`.
- Existing Issue 218 covered missing recent-changes response `body` fields but intentionally left present malformed values as a separate boundary.
- The recent response-body type series showed the same boundary pattern in private messages, forum categories, site members, site applications, page-file reads, forum-thread reads, forum-post reads, page-revision source/HTML reads, forum-post-revision reads, ListPages reads, page source reads, page revision-list reads, page vote reads, batched page file reads, and page auxiliary reads.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated recent-changes HTML, page titles, edit comments, and private site content out of upstream discussion.

## Additional Notes

This is a response-body field type diagnostics fix. It preserves valid recent-changes behavior while making malformed present response bodies actionable without retaining generated recent-changes content.
