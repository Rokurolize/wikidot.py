# PR Draft: Report Malformed Batched Page File Response Body Types

## Summary

`PageCollection.get_page_files()` batches `files/PageFilesModule` requests for pages whose attached-file data is still uncached, reuses cached duplicate page-ID file collections, and parses each generated file-list response `body` as HTML before extracting file rows. Issue 224 converted missing batched file response `body` fields into contextual `NoElementException` failures. One adjacent parser-boundary gap remained: a present but non-string file response `body` still reached BeautifulSoup, leaking low-level parser internals such as `AttributeError: 'list' object has no attribute 'startswith'`.

This local slice validates present batched page file response `body` values before BeautifulSoup parsing. Non-string bodies now raise `NoElementException` with site/page/id context plus `field=body`, expected type, and observed type. The diagnostic includes only compact structural context and type names; it does not include raw generated file-list HTML, response JSON, file names, file URLs, local rollout paths, credentials, account material, or private page content.

## Outcome

Malformed batched page file response body types now fail at the module response boundary with actionable site/page/id context instead of BeautifulSoup internals.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page inventory, file attachment collection, publication verification, archival indexing, or audit workflows that collect attached-file lists.

## Related Issue

Builds on [004-pr-batched-revision-vote-file-fetch.md](004-pr-batched-revision-vote-file-fetch.md), [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [224-pr-page-file-batch-response-body-context.md](224-pr-page-file-batch-response-body-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), and [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md). Those drafts established page file reads as retry-aware, duplicate-aware, cache-aware workflows with scoped row parsing, direct-response body type validation, and site/page diagnostics while leaving present non-string batched response bodies as a separate parser-entry boundary.

This also follows the response-body type diagnostic pattern from [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md), [331-pr-page-source-response-body-type-context.md](331-pr-page-source-response-body-type-context.md), [332-pr-page-revision-list-response-body-type-context.md](332-pr-page-revision-list-response-body-type-context.md), and [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Preserve the existing missing-body diagnostic from Issue 224.
- Validate present batched page file response `body` values are strings before BeautifulSoup parsing.
- Convert present non-string file response `body` values into site/page/id-specific `NoElementException`.
- Preserve retry-exhausted `None` handling, cached file collection reuse, duplicate page-ID grouping, page-ID acquisition, file row parsing, URL construction, MIME title parsing, size parsing, lazy `Page.files`, and adjacent site workflows.

## Type Of Change

- Bug fix / diagnostics improvement
- Batched page file response-body type validation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A batched page file response with a present non-string `body` field must fail before BeautifulSoup parsing. |
| R2 | Malformed batched page file response body type errors must identify the affected site, page fullname, page ID, `field=body`, expected type, and observed type while omitting raw file-list content. |
| R3 | Existing missing-body diagnostics, retry-exhausted `None` handling, cached file reuse, duplicate page-ID grouping, page-ID acquisition, file row parsing, URL construction, MIME title parsing, size parsing, and lazy file behavior must remain compatible. |
| R4 | Focused, acquisition, page-file, page, adjacent page/page-file/page-revision/page-votes/site, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `PageCollection.get_page_files()` raises contextual `NoElementException` when `files/PageFilesModule` returns a list-valued `body`. | `TestPageCollectionAcquire.test_acquire_files_malformed_response_body_type_includes_site_page_and_type_context` expects `Page file response body is malformed for site: test-site, page: test-page (id=12345, field=body, expected=str, actual=list)`. | Leaking BeautifulSoup `AttributeError`, entering file row extraction, fabricating an empty file collection, or silently skipping the malformed body rejects this local completion claim. | Batched page file reads | `tests/unit/test_page.py` |
| R2 | The malformed-body-type diagnostic includes only structural identifiers, field name, expected type, and observed type. | The focused regression matches the full message shape using a synthetic list-valued body. | Including raw response JSON, generated file-list HTML, file names, file URLs, credentials, local rollout paths, account names, or private page content rejects this local completion claim. | Page file diagnostics | `src/wikidot/module/page.py` |
| R3 | Existing page file acquisition and adjacent page behavior remain green. | `TestPageCollectionAcquire` passed 48 tests, `tests/unit/test_page_file.py` passed 36 tests, `tests/unit/test_page.py` passed 164 tests, and the adjacent page/page-file/page-revision/page-votes/site run passed 330 tests. | Regressing missing-body diagnostics, retry-exhausted `None` handling, cached file reuse, duplicate page-ID grouping, page-ID acquisition, file row parsing, URL construction, MIME title parsing, size parsing, lazy `Page.files`, or adjacent site workflows rejects this local completion claim. | Page file workflows | `tests/unit/test_page.py`; `tests/unit/test_page_file.py`; `tests/unit/test_page_revision.py`; `tests/unit/test_page_votes.py`; `tests/unit/test_site.py` |
| R4 | Repository quality gates pass in the local dependency environment. | Full unit passed 907 tests; `ruff`, format check, `mypy`, and whitespace checks passed before the code commit; `pyright` remained unavailable in this environment. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `ae24974 fix(page): report malformed file response bodies`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_malformed_response_body_type_includes_site_page_and_type_context -q` failed before the fix with `AttributeError: 'list' object has no attribute 'startswith'` inside BeautifulSoup parser setup.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_malformed_response_body_type_includes_site_page_and_type_context -q` passed after the fix.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 48 tests.
- `uv run pytest tests/unit/test_page_file.py -q` passed 36 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 164 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 330 tests.
- `uv run pytest tests/unit -q` passed 907 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- `PageCollection.get_page_files()` still batches uncached file requests by page ID.
- Cached file reuse and duplicate page-ID file reuse remain unchanged.
- Retry-exhausted `None` responses remain skipped entries and are not converted into malformed-body failures.
- Missing file response `body` fields still raise the existing not-found diagnostic from Issue 224.
- Present non-string file response `body` values raise contextual `NoElementException` before BeautifulSoup parsing.
- The malformed-body-type message includes site, page fullname, page ID, `field=body`, expected type, and observed type.
- File row parsing, URL construction, MIME title parsing, size parsing, lazy `Page.files`, and adjacent page/site workflows remain unchanged for valid string bodies.
- The malformed-body-type message does not include raw response JSON, generated file-list HTML, file names, file URLs, credentials, local rollout paths, private page content, or private account material.
- No live Wikidot action, upstream Issue, upstream PR, push, real file-list response body, account material, private page content, generated file-list HTML, file name, or file URL content is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Type validation could treat a future bytes-like body as malformed. Mitigation: AMC JSON bodies are expected to decode generated module HTML as strings; preserving only string input keeps the parser boundary explicit.
- Risk: Type validation could mask missing-body diagnostics. Mitigation: `None` remains on the existing missing-body path; only present non-string values use the malformed-type diagnostic.
- Risk: Diagnostics could expose file data. Mitigation: messages include only site/page/id identifiers and type names, not raw response JSON, generated file-list HTML, file names, file URLs, or page content.
- Risk: A small guard could drift from adjacent file parser behavior. Mitigation: the change is immediately after the existing missing-body branch and leaves all valid string body parsing unchanged.

## Dependencies

- The AMC connector already validates decoded response roots as dictionaries before normal module parsing; this slice targets the `body` field value within that dictionary.
- File row parsing, URL construction, MIME title parsing, and size parsing remain unchanged after a valid string body is supplied.

## Open Questions

None for this local slice. Remaining useful work should continue the broader response-body field-type audit across page auxiliary helpers and recent changes rather than expanding this file change beyond the response boundary.

## Upstream-Safe Motivation

Page file acquisition is a practical browser-free file inventory path for page audits, source publication verification, attachment reconciliation, and archival workflows. If Wikidot returns a present non-string generated module body, wikidot.py should report the affected site/page/id and type mismatch before parser internals obscure the failure.

## Local Evidence, Not For Upstream Paste

- The RED failure showed a list-valued batched file response `body` leaking `AttributeError: 'list' object has no attribute 'startswith'` inside BeautifulSoup.
- Existing Issue 224 covered missing batched page file response `body` fields but intentionally left present malformed values as separate boundaries.
- Issue 325 covered direct single-page file-list response body types; this slice covers the batched `PageCollection.get_page_files()` path reached by lazy `Page.files`.
- The recent response-body type series showed the same boundary pattern in private messages, forum categories, site members, site applications, direct page-file reads, forum-thread reads, forum-post reads, page-revision source/HTML reads, forum-post-revision reads, ListPages reads, page source reads, page revision-list reads, and page vote reads.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated file-list HTML, file names, file URLs, and private page content out of upstream discussion.

## Additional Notes

This is a response-body field type diagnostics fix. It preserves valid page file acquisition behavior while making malformed present response bodies actionable without retaining generated file-list content or response payloads.
