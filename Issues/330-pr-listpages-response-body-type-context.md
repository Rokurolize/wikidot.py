# PR Draft: Report Malformed ListPages Response Body Types

## Summary

`PageCollection.search_pages()` retrieves generated `list/ListPagesModule` markup, parses the first page, detects pager targets, and optionally fetches additional pages through retry-aware AMC. Earlier local slices made this path retry-aware, pagination-sensitive, offset-preserving, limit-aware, field-parser-scoped, and context-rich for missing response bodies. One adjacent response-boundary gap remained: if the decoded AMC response was a dictionary with a present but non-string `body` value, first-page and additional-page ListPages reads passed it directly to BeautifulSoup, leaking a low-level parser `AttributeError`.

This local slice validates present ListPages response `body` values before BeautifulSoup parsing. Non-string bodies now raise `NoElementException` with site/offset context plus `field=body`, expected type, and observed type. The diagnostic reports only compact structural context and type names; it does not include raw generated ListPages HTML, response JSON, site content, search parameters, local rollout paths, credentials, account material, or private page content.

## Outcome

Malformed ListPages response body types now fail at the module response boundary with actionable site/offset context instead of BeautifulSoup internals.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page search, source collection, publication verification, page inventory, or ListPages-backed corpus workflows.

## Related Issue

Builds on [005-pr-bound-listpages-pagination-by-limit.md](005-pr-bound-listpages-pagination-by-limit.md), [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [023-pr-search-pagination-validation.md](023-pr-search-pagination-validation.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md), [220-pr-listpages-response-body-context.md](220-pr-listpages-response-body-context.md), [305-pr-listpages-timestamp-context.md](305-pr-listpages-timestamp-context.md), and [306-pr-listpages-user-context.md](306-pr-listpages-user-context.md). Those drafts established `search_pages()` as a practical retry-aware, pagination-sensitive workflow with parser boundaries, field-value fidelity, and site/offset diagnostics while leaving present non-string response bodies as a separate parser-entry boundary.

This also follows the response-body type diagnostic pattern from [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), and [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Reuse the existing ListPages response-body helper for first and additional pages.
- Preserve existing missing-body diagnostics from Issue 220.
- Validate present ListPages `body` values are strings before BeautifulSoup parsing.
- Convert present non-string first-page ListPages body values into site/offset-specific `NoElementException`.
- Convert present non-string additional-page ListPages body values into site/offset-specific `NoElementException`.
- Preserve retry-exhausted behavior, private-site `not_ok` mapping, retry use, pager detection, offset preservation, limit capping, field-value spacing, field parser behavior, and page parsing.

## Type Of Change

- Bug fix / diagnostics improvement
- ListPages response-body type validation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A first ListPages response with a present non-string `body` field must fail before BeautifulSoup parsing. |
| R2 | An additional ListPages response with a present non-string `body` field must identify the affected offset and fail before BeautifulSoup parsing. |
| R3 | Malformed-body-type errors must identify the affected site, offset, `field=body`, expected type, and observed type while omitting raw generated ListPages content. |
| R4 | Existing missing-body diagnostics, retry handling, private-site mapping, pager behavior, offset behavior, limit capping, field parsing, and page parsing must remain compatible. |
| R5 | Focused, search-pages, page, adjacent page/search/site, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `PageCollection.search_pages(site, SearchPagesQuery(offset=500))` raises contextual `NoElementException` when the first `list/ListPagesModule` response returns a list-valued `body`. | `TestPageCollectionSearchPages.test_search_pages_malformed_first_response_body_type_includes_site_offset_and_type_context` expects `ListPages response body is malformed for site: test-site, offset: 500 (field=body, expected=str, actual=list)`. | Leaking BeautifulSoup `AttributeError`, fabricating an empty collection, entering pager detection, or entering page parsing rejects this local completion claim. | First ListPages response reads | `tests/unit/test_page.py` |
| R2 | `PageCollection.search_pages(site, SearchPagesQuery(offset=500, perPage=100))` raises contextual `NoElementException` when the additional page at offset `600` returns a list-valued `body`. | `TestPageCollectionSearchPages.test_search_pages_malformed_additional_response_body_type_includes_site_offset_and_type_context` expects `ListPages response body is malformed for site: test-site, offset: 600 (field=body, expected=str, actual=list)`. | Returning partial first-page results, dropping the additional offset, leaking BeautifulSoup internals, or silently skipping the malformed response rejects this local completion claim. | Additional ListPages response reads | `tests/unit/test_page.py` |
| R3 | The malformed-body-type diagnostics include only structural identifiers, field name, expected type, and observed type. | The focused regressions match the full message shapes using synthetic list-valued bodies. | Including raw response JSON, generated ListPages HTML, site content, search parameters, credentials, local rollout paths, or account names rejects this local completion claim. | ListPages diagnostics | `src/wikidot/module/page.py` |
| R4 | Existing search-pages and adjacent page/site behavior remain green. | The focused run passed 10 tests, the `TestPageCollectionSearchPages` class passed 19 tests, the page suite passed 160 tests, the adjacent page/search/site run passed 263 tests, and the full unit suite passed 903 tests. | Regressing missing-body diagnostics, retry exhaustion, private-site mapping, pager filtering, additional-page retry use, offset calculation, limit capping, field-value spacing, field parser behavior, or page parsing rejects this local completion claim. | Page search workflows | `tests/unit/test_page.py`; `tests/unit/test_search_pages_query.py`; `tests/unit/test_site.py` |
| R5 | Repository quality gates pass in the local dependency environment. | `ruff`, `mypy`, full unit, and whitespace checks passed before the code commit; `pyright` remained unavailable in this environment. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `9f34706 fix(page): report malformed ListPages bodies`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_malformed_first_response_body_type_includes_site_offset_and_type_context -q` failed before the fix with `AttributeError` from BeautifulSoup for the list-valued first ListPages body.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_malformed_first_response_body_type_includes_site_offset_and_type_context -q` passed after the fix.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_malformed_first_response_body_type_includes_site_offset_and_type_context tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_malformed_additional_response_body_type_includes_site_offset_and_type_context -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_missing_first_response_body_includes_site_and_offset_context tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_malformed_first_response_body_type_includes_site_offset_and_type_context tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_basic tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_retries_transient_first_page_failures tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_raises_when_first_page_retry_is_exhausted tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_additional_pager_requests_use_retry tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_missing_additional_response_body_includes_site_and_offset_context tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_malformed_additional_response_body_type_includes_site_offset_and_type_context tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_failed_retry_additional_page_raises tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_limit_within_first_page_skips_additional_pager_requests -q` passed 10 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed 19 tests.
- `uv run --extra test pytest tests/unit/test_page.py -q` passed 160 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_search_pages_query.py tests/unit/test_site.py -q` passed 263 tests.
- `uv run --extra test pytest tests/unit -q` passed 903 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- `PageCollection.search_pages()` still uses the same `list/ListPagesModule` request payload.
- First ListPages fetches still use the existing retry-aware helper and private-site `not_ok` mapping.
- Additional ListPages fetches still use `site.amc_request_with_retry()`.
- Missing `body` fields still raise the existing not-found diagnostics from Issue 220.
- Present non-string first ListPages `body` values raise contextual `NoElementException` before BeautifulSoup parsing.
- Present non-string additional ListPages `body` values raise contextual `NoElementException` before BeautifulSoup parsing.
- The malformed first-body-type message includes site, offset, `field=body`, expected type, and observed type.
- The malformed additional-body-type message includes site, affected offset, `field=body`, expected type, and observed type.
- The malformed-body-type messages do not include raw response JSON, generated ListPages HTML, site content, search parameters, credentials, local rollout paths, private page content, or private account material.
- Existing retry-exhausted behavior, private-site mapping, pager detection, offset preservation, additional-page retry use, limit capping, field-value spacing, field parser behavior, and page parsing remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real ListPages response body, local rollout path, account material, private page content, search parameter payload, or generated ListPages HTML is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Type validation could treat a future bytes-like body as malformed. Mitigation: AMC JSON bodies are expected to decode generated ListPages HTML as strings; preserving only string input keeps the parser boundary explicit.
- Risk: Type validation could mask missing-body diagnostics. Mitigation: `None` remains on the existing missing-body path; only present non-string values use the malformed-type diagnostic.
- Risk: Diagnostics could expose search content or parameters. Mitigation: messages include only site/offset identifiers and type names, not raw generated HTML, query payloads, page fields, or response JSON.
- Risk: Additional-page validation could accidentally change pagination behavior. Mitigation: the regression reuses the existing pager shape and the focused/broad checks cover retry use, offset calculation, limit capping, and normal parsing.

## Dependencies

- The AMC connector already validates decoded response roots as dictionaries before normal module parsing; this slice targets the `body` field value within that dictionary.
- ListPages field parsing, pager detection, and page construction remain unchanged after a valid string body is supplied.

## Open Questions

None for this local slice. Remaining useful work should continue the broader response-body field-type audit across other page and site module helpers rather than expanding this ListPages change beyond `search_pages()` response boundaries.

## Upstream-Safe Motivation

ListPages is one of wikidot.py's core browser-free read paths for search, source collection, publication verification, and page inventory. If Wikidot returns a present non-string generated response body, wikidot.py should report the affected site and offset before parser internals obscure the failure.

## Local Evidence, Not For Upstream Paste

- The RED failure showed a list-valued first ListPages `body` leaking BeautifulSoup `AttributeError`.
- Existing Issue 220 covered missing first and additional ListPages `body` fields but intentionally left present malformed values as separate boundaries.
- The recent response-body type series showed the same boundary pattern in private messages, forum categories, site members, site applications, direct page-file reads, forum-thread reads, forum-post reads, page-revision reads, and forum-post-revision reads.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated ListPages HTML, site content, search payloads, and private page content out of upstream discussion.

## Additional Notes

This is a response-body field type diagnostics fix. It preserves valid ListPages search behavior while making malformed present response bodies actionable without retaining generated ListPages content or query payloads.
