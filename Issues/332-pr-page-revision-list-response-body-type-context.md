# PR Draft: Report Malformed Page Revision List Response Body Types

## Summary

`PageCollection.get_page_revisions()` batches `history/PageRevisionListModule` requests, groups duplicate page IDs, reuses cached revision collections, and parses each generated revision-list response `body` as HTML before extracting page-history rows. Issue 222 converted missing batched revision-list response `body` fields into contextual `NoElementException` failures. Issue 328 covered present non-string `body` values for direct `PageRevisionCollection.get_sources()` and `get_htmls()` revision source/HTML reads. One adjacent batch boundary remained: a present but non-string revision-list `body` still reached BeautifulSoup, leaking low-level parser internals such as `AttributeError: 'list' object has no attribute 'startswith'`.

This local slice validates present batched page revision-list response `body` values before BeautifulSoup parsing. Non-string bodies now raise `NoElementException` with site/page/id context plus `field=body`, expected type, and observed type. The diagnostic includes only compact structural context and type names; it does not include raw generated revision-list HTML, response JSON, revision comments, user markup, local rollout paths, credentials, account material, or private page content.

## Outcome

Malformed batched page revision-list response body types now fail at the module response boundary with actionable site/page/id context instead of BeautifulSoup internals.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page history inspection, page inventory workflows, publication verification, rollback preparation, or source/history audit tooling.

## Related Issue

Builds on [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [035-pr-page-revisions-retry-visibility.md](035-pr-page-revisions-retry-visibility.md), [053-pr-deduplicate-page-revision-list-fetches.md](053-pr-deduplicate-page-revision-list-fetches.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [200-pr-page-revision-source-parse-site-context.md](200-pr-page-revision-source-parse-site-context.md), [201-pr-page-revision-lazy-site-context.md](201-pr-page-revision-lazy-site-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), and [222-pr-page-revision-batch-response-body-context.md](222-pr-page-revision-batch-response-body-context.md). Those drafts established page revision acquisition as a practical retry-aware and cache-aware workflow with duplicate ID grouping, lazy fetch diagnostics, source/HTML body validation, and site/page/revision row diagnostics while leaving present non-string revision-list response bodies as a separate parser-entry boundary.

This also follows the response-body type diagnostic pattern from [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md), and [331-pr-page-source-response-body-type-context.md](331-pr-page-source-response-body-type-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Preserve the existing missing-body diagnostic from Issue 222.
- Validate present batched page revision-list response `body` values are strings before BeautifulSoup parsing.
- Convert present non-string revision-list `body` values into site/page/id-specific `NoElementException`.
- Preserve retry-exhausted `None` handling, cached revision collection reuse, duplicate page-ID grouping, page-ID acquisition, revision row parsing, revision number parsing, revision user/timestamp diagnostics, comment spacing, lazy `Page.revisions`, and adjacent page detail workflows.

## Type Of Change

- Bug fix / diagnostics improvement
- Page revision-list response-body type validation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A batched page revision-list response with a present non-string `body` field must fail before BeautifulSoup parsing. |
| R2 | Malformed page revision-list response body type errors must identify the affected site, page fullname, page ID, `field=body`, expected type, and observed type while omitting raw revision-list content. |
| R3 | Existing missing-body diagnostics, retry-exhausted `None` handling, cached revision reuse, duplicate page-ID grouping, page-ID acquisition, row parsing, user/timestamp diagnostics, comment spacing, and lazy page revision behavior must remain compatible. |
| R4 | Focused, acquisition, page, adjacent page/page-revision/page-file/site, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `PageCollection.get_page_revisions()` raises contextual `NoElementException` when `history/PageRevisionListModule` returns a list-valued `body`. | `TestPageCollectionAcquire.test_acquire_revisions_malformed_response_body_type_includes_site_page_and_type_context` expects `Page revision list response body is malformed for site: test-site, page: test-page (id=12345, field=body, expected=str, actual=list)`. | Leaking BeautifulSoup `AttributeError`, entering parser row extraction, fabricating an empty revision collection, or silently skipping the malformed body rejects this local completion claim. | Batched page revision-list reads | `tests/unit/test_page.py` |
| R2 | The malformed-body-type diagnostic includes only structural identifiers, field name, expected type, and observed type. | The focused regression matches the full message shape using a synthetic list-valued body. | Including raw response JSON, generated revision-list HTML, revision comments, user markup, credentials, local rollout paths, account names, or private page content rejects this local completion claim. | Page revision-list diagnostics | `src/wikidot/module/page.py` |
| R3 | Existing page revision acquisition and adjacent page detail behavior remain green. | `TestPageCollectionAcquire` passed 46 tests, `tests/unit/test_page.py` passed 162 tests, and the adjacent page/page-revision/page-file/site run passed 319 tests. | Regressing missing-body diagnostics, retry-exhausted `None` handling, cached revision reuse, duplicate page-ID grouping, page-ID acquisition, row parsing, revision number parsing, user/timestamp diagnostics, comment spacing, lazy `Page.revisions`, source/HTML revision reads, page file reads, or adjacent site workflows rejects this local completion claim. | Page revision workflows | `tests/unit/test_page.py`; `tests/unit/test_page_revision.py`; `tests/unit/test_page_file.py`; `tests/unit/test_site.py` |
| R4 | Repository quality gates pass in the local dependency environment. | Full unit passed 905 tests; `ruff`, format check, `mypy`, and whitespace checks passed before the code commit; `pyright` remained unavailable in this environment. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `563aa97 fix(page): report malformed revision list bodies`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_response_body_type_includes_site_page_and_type_context -q` failed before the fix with `AttributeError: 'list' object has no attribute 'startswith'` inside BeautifulSoup parser setup.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_response_body_type_includes_site_page_and_type_context -q` passed after the fix.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 46 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 162 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_site.py -q` passed 319 tests.
- `uv run pytest tests/unit -q` passed 905 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- `PageCollection.get_page_revisions()` still batches uncached revision-list requests by page ID.
- Cached revision reuse and duplicate page-ID revision reuse remain unchanged.
- Retry-exhausted `None` responses remain skipped entries and are not converted into malformed-body failures.
- Missing revision-list response `body` fields still raise the existing not-found diagnostic from Issue 222.
- Present non-string revision-list response `body` values raise contextual `NoElementException` before BeautifulSoup parsing.
- The malformed-body-type message includes site, page fullname, page ID, `field=body`, expected type, and observed type.
- Revision row parsing, revision number parsing, user diagnostics, timestamp diagnostics, comment spacing, lazy `Page.revisions`, revision source/HTML reads, and adjacent page detail workflows remain unchanged for valid string bodies.
- The malformed-body-type message does not include raw response JSON, generated revision-list HTML, revision comments, user markup, credentials, local rollout paths, private page content, or private account material.
- No live Wikidot action, upstream Issue, upstream PR, push, real revision-list response body, account material, private page content, generated revision-list HTML, or revision comment content is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Type validation could treat a future bytes-like body as malformed. Mitigation: AMC JSON bodies are expected to decode generated module HTML as strings; preserving only string input keeps the parser boundary explicit.
- Risk: Type validation could mask missing-body diagnostics. Mitigation: `None` remains on the existing missing-body path; only present non-string values use the malformed-type diagnostic.
- Risk: Diagnostics could expose page history content. Mitigation: messages include only site/page/id identifiers and type names, not raw response JSON, generated revision-list HTML, user markup, comments, or page content.
- Risk: A small guard could drift from adjacent page detail behavior. Mitigation: the change is immediately after the existing missing-body branch and leaves all valid string body parsing unchanged.

## Dependencies

- The AMC connector already validates decoded response roots as dictionaries before normal module parsing; this slice targets the `body` field value within that dictionary.
- Revision row parsing, user parsing, timestamp parsing, and comment extraction remain unchanged after a valid string body is supplied.

## Open Questions

None for this local slice. Remaining useful work should continue the broader response-body field-type audit across page vote batches, page file batches, page auxiliary helpers, and recent changes rather than expanding this revision-list change beyond the response boundary.

## Upstream-Safe Motivation

Page revision-list acquisition is a core browser-free read path for history inspection, rollback preparation, publication verification, and page inventory workflows. If Wikidot returns a present non-string generated module body, wikidot.py should report the affected site/page/id and type mismatch before parser internals obscure the failure.

## Local Evidence, Not For Upstream Paste

- The RED failure showed a list-valued revision-list response `body` leaking `AttributeError: 'list' object has no attribute 'startswith'` inside BeautifulSoup.
- Existing Issue 222 covered missing batched page revision-list response `body` fields but intentionally left present malformed values as separate boundaries.
- Existing Issue 328 covered direct page revision source and HTML response-body type diagnostics, not the batched page revision-list parser boundary.
- The recent response-body type series showed the same boundary pattern in private messages, forum categories, site members, site applications, direct page-file reads, forum-thread reads, forum-post reads, page-revision source/HTML reads, forum-post-revision reads, ListPages reads, and page source reads.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated revision-list HTML, revision comments, user markup, and private page content out of upstream discussion.

## Additional Notes

This is a response-body field type diagnostics fix. It preserves valid page revision-list acquisition behavior while making malformed present response bodies actionable without retaining generated revision-list content or response payloads.
