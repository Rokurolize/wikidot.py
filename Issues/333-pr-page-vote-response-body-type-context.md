# PR Draft: Report Malformed Page Vote Response Body Types

## Summary

`PageCollection.get_page_votes()` batches `pagerate/WhoRatedPageModule` requests for pages whose vote data is still uncached, reuses cached duplicate page-ID vote collections, and parses each generated WhoRated response `body` as HTML before extracting voter/value pairs. Issue 223 converted missing batched vote response `body` fields into contextual `NoElementException` failures. One adjacent parser-boundary gap remained: a present but non-string vote response `body` still reached BeautifulSoup, leaking low-level parser internals such as `AttributeError: 'list' object has no attribute 'startswith'`.

This local slice validates present batched page vote response `body` values before BeautifulSoup parsing. Non-string bodies now raise `NoElementException` with site/page/id context plus `field=body`, expected type, and observed type. The diagnostic includes only compact structural context and type names; it does not include raw generated WhoRated HTML, response JSON, user names, vote values, local rollout paths, credentials, account material, or private page content.

## Outcome

Malformed batched page vote response body types now fail at the module response boundary with actionable site/page/id context instead of BeautifulSoup internals.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free rating reads, page inventory tooling, publication verification, or audit workflows that collect page votes.

## Related Issue

Builds on [004-pr-batched-revision-vote-file-fetch.md](004-pr-batched-revision-vote-file-fetch.md), [106-pr-page-vote-mismatch-site-context.md](106-pr-page-vote-mismatch-site-context.md), [112-pr-page-vote-row-scope.md](112-pr-page-vote-row-scope.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), and [307-pr-whorated-user-context.md](307-pr-whorated-user-context.md). Those drafts established page vote collection reads as cached, duplicate-aware workflows with scoped WhoRated parsing, vote/user diagnostics, mutation cache invalidation, and site/page context while leaving present non-string response bodies as a separate parser-entry boundary.

This also follows the response-body type diagnostic pattern from [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md), [331-pr-page-source-response-body-type-context.md](331-pr-page-source-response-body-type-context.md), and [332-pr-page-revision-list-response-body-type-context.md](332-pr-page-revision-list-response-body-type-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Preserve the existing missing-body diagnostic from Issue 223.
- Validate present batched page vote response `body` values are strings before BeautifulSoup parsing.
- Convert present non-string vote response `body` values into site/page/id-specific `NoElementException`.
- Preserve retry-exhausted `None` handling, cached vote collection reuse, duplicate page-ID grouping, page-ID acquisition, WhoRated container discovery, non-vote colored span filtering, user/value mismatch diagnostics, user parsing, vote value parsing, lazy `Page.votes`, and adjacent site workflows.

## Type Of Change

- Bug fix / diagnostics improvement
- Page vote response-body type validation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A batched page vote response with a present non-string `body` field must fail before BeautifulSoup parsing. |
| R2 | Malformed page vote response body type errors must identify the affected site, page fullname, page ID, `field=body`, expected type, and observed type while omitting raw WhoRated content. |
| R3 | Existing missing-body diagnostics, retry-exhausted `None` handling, cached vote reuse, duplicate page-ID grouping, page-ID acquisition, vote container parsing, user/value diagnostics, user parsing, vote value parsing, and lazy page vote behavior must remain compatible. |
| R4 | Focused, acquisition, page, adjacent page/page-votes/site, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `PageCollection.get_page_votes()` raises contextual `NoElementException` when `pagerate/WhoRatedPageModule` returns a list-valued `body`. | `TestPageCollectionAcquire.test_acquire_votes_malformed_response_body_type_includes_site_page_and_type_context` expects `Page vote response body is malformed for site: test-site, page: test-page (id=12345, field=body, expected=str, actual=list)`. | Leaking BeautifulSoup `AttributeError`, entering vote parser extraction, fabricating an empty vote collection, or silently skipping the malformed body rejects this local completion claim. | Batched page vote reads | `tests/unit/test_page.py` |
| R2 | The malformed-body-type diagnostic includes only structural identifiers, field name, expected type, and observed type. | The focused regression matches the full message shape using a synthetic list-valued body. | Including raw response JSON, generated WhoRated HTML, user names, vote values, credentials, local rollout paths, account names, or private page content rejects this local completion claim. | Page vote diagnostics | `src/wikidot/module/page.py` |
| R3 | Existing page vote acquisition and adjacent site behavior remain green. | `TestPageCollectionAcquire` passed 47 tests, `tests/unit/test_page.py` passed 163 tests, and the adjacent page/page-votes/site run passed 254 tests. | Regressing missing-body diagnostics, retry-exhausted `None` handling, cached vote reuse, duplicate page-ID grouping, page-ID acquisition, vote container discovery, non-vote colored span filtering, user/value mismatch diagnostics, user parsing, vote value parsing, lazy `Page.votes`, or adjacent site workflows rejects this local completion claim. | Page vote workflows | `tests/unit/test_page.py`; `tests/unit/test_page_votes.py`; `tests/unit/test_site.py` |
| R4 | Repository quality gates pass in the local dependency environment. | Full unit passed 906 tests; `ruff`, format check, `mypy`, and whitespace checks passed before the code commit; `pyright` remained unavailable in this environment. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `ef448cf fix(page): report malformed vote response bodies`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_malformed_response_body_type_includes_site_page_and_type_context -q` failed before the fix with `AttributeError: 'list' object has no attribute 'startswith'` inside BeautifulSoup parser setup.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_malformed_response_body_type_includes_site_page_and_type_context -q` passed after the fix.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 47 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 163 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 254 tests.
- `uv run pytest tests/unit -q` passed 906 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- `PageCollection.get_page_votes()` still batches uncached vote requests by page ID.
- Cached vote reuse and duplicate page-ID vote reuse remain unchanged.
- Retry-exhausted `None` responses remain skipped entries and are not converted into malformed-body failures.
- Missing vote response `body` fields still raise the existing not-found diagnostic from Issue 223.
- Present non-string vote response `body` values raise contextual `NoElementException` before BeautifulSoup parsing.
- The malformed-body-type message includes site, page fullname, page ID, `field=body`, expected type, and observed type.
- Vote container discovery, non-vote colored span filtering, user/value mismatch diagnostics, user parsing, vote value parsing, lazy `Page.votes`, and adjacent site workflows remain unchanged for valid string bodies.
- The malformed-body-type message does not include raw response JSON, generated WhoRated HTML, user names, vote values, credentials, local rollout paths, private page content, or private account material.
- No live Wikidot action, upstream Issue, upstream PR, push, real vote response body, account material, private page content, generated WhoRated HTML, user name, or vote value content is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Type validation could treat a future bytes-like body as malformed. Mitigation: AMC JSON bodies are expected to decode generated module HTML as strings; preserving only string input keeps the parser boundary explicit.
- Risk: Type validation could mask missing-body diagnostics. Mitigation: `None` remains on the existing missing-body path; only present non-string values use the malformed-type diagnostic.
- Risk: Diagnostics could expose vote data or user names. Mitigation: messages include only site/page/id identifiers and type names, not raw response JSON, generated WhoRated HTML, user markup, user names, vote values, or page content.
- Risk: A small guard could drift from adjacent vote parser behavior. Mitigation: the change is immediately after the existing missing-body branch and leaves all valid string body parsing unchanged.

## Dependencies

- The AMC connector already validates decoded response roots as dictionaries before normal module parsing; this slice targets the `body` field value within that dictionary.
- WhoRated container discovery, user parsing, and vote value parsing remain unchanged after a valid string body is supplied.

## Open Questions

None for this local slice. Remaining useful work should continue the broader response-body field-type audit across page file batches, page auxiliary helpers, and recent changes rather than expanding this vote change beyond the response boundary.

## Upstream-Safe Motivation

Page vote acquisition is a practical browser-free rating read path for page inventory, audit, and publication workflows. If Wikidot returns a present non-string generated module body, wikidot.py should report the affected site/page/id and type mismatch before parser internals obscure the failure.

## Local Evidence, Not For Upstream Paste

- The RED failure showed a list-valued vote response `body` leaking `AttributeError: 'list' object has no attribute 'startswith'` inside BeautifulSoup.
- Existing Issue 223 covered missing batched page vote response `body` fields but intentionally left present malformed values as separate boundaries.
- The recent response-body type series showed the same boundary pattern in private messages, forum categories, site members, site applications, direct page-file reads, forum-thread reads, forum-post reads, page-revision source/HTML reads, forum-post-revision reads, ListPages reads, page source reads, and page revision-list reads.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated WhoRated HTML, user names, vote values, user markup, and private page content out of upstream discussion.

## Additional Notes

This is a response-body field type diagnostics fix. It preserves valid page vote acquisition behavior while making malformed present response bodies actionable without retaining generated WhoRated content or response payloads.
