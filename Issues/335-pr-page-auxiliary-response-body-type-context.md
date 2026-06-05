# PR Draft: Report Malformed Page Auxiliary Response Body Types

## Summary

`Page.discussion` parses `forum/ForumCommentsListModule` response `body` values with a generated `WIKIDOT.forumThreadId` regex, while `Page.metas` parses `edit/EditMetaModule` response `body` values as generated meta-tag HTML. Issue 219 converted missing auxiliary response `body` fields into page-context `NoElementException` failures, and Issue 309 made present malformed discussion thread IDs fail with page/id context. One adjacent response-boundary gap remained: present but non-string auxiliary response `body` values still reached parser code, leaking low-level `TypeError` from `re.search(...)` or `AttributeError` from string replacement.

This local slice validates present page discussion and metas response `body` values before regex or HTML parsing. Non-string bodies now raise `NoElementException` with site/page/id context plus `field=body`, expected type, and observed type. The diagnostic includes only compact structural context and type names; it does not include raw generated discussion markup, generated meta markup, response JSON, page source, forum content, metadata values, local rollout paths, credentials, account material, or private site content.

## Outcome

Malformed page discussion and metas response body types now fail at the generated-module response boundary with actionable site/page/id context instead of parser internals.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page auxiliary reads for page navigation, publication checks, archival indexing, moderation ledgers, metadata reconciliation, or migration tooling.

## Related Issue

Builds on [045-pr-retry-page-discussion-fetch.md](045-pr-retry-page-discussion-fetch.md), [046-pr-retry-page-meta-fetch.md](046-pr-retry-page-meta-fetch.md), [192-pr-page-auxiliary-fetch-site-context.md](192-pr-page-auxiliary-fetch-site-context.md), [219-pr-page-auxiliary-response-body-context.md](219-pr-page-auxiliary-response-body-context.md), and [309-pr-page-discussion-thread-id-context.md](309-pr-page-discussion-thread-id-context.md). Those drafts established page auxiliary reads as retry-aware, page-context-rich workflows with missing-body diagnostics and discussion thread-ID validation while leaving present non-string auxiliary response bodies as a separate parser-entry boundary.

This also follows the response-body type diagnostic pattern from [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md), [331-pr-page-source-response-body-type-context.md](331-pr-page-source-response-body-type-context.md), [332-pr-page-revision-list-response-body-type-context.md](332-pr-page-revision-list-response-body-type-context.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), and [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Preserve the existing missing-body diagnostics from Issue 219.
- Validate present page discussion response `body` values are strings before `WIKIDOT.forumThreadId` regex parsing.
- Validate present page metas response `body` values are strings before entity-boundary restoration and BeautifulSoup parsing.
- Convert present non-string auxiliary response `body` values into site/page/id-specific `NoElementException`.
- Preserve retry-exhausted `None` handling, request payloads, valid discussion lookup, no-discussion caching, malformed thread-ID diagnostics, meta tag decoding, flexible meta attribute parsing, meta mutation batching, cached property reads, and adjacent page workflows.

## Type Of Change

- Bug fix / diagnostics improvement
- Page auxiliary response-body type validation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A page discussion response with a present non-string `body` field must fail before regex parsing. |
| R2 | A page metas response with a present non-string `body` field must fail before string replacement or BeautifulSoup parsing. |
| R3 | Malformed page auxiliary response body type errors must identify the affected site, page fullname, page ID, `field=body`, expected type, and observed type while omitting raw discussion/meta content. |
| R4 | Existing missing-body diagnostics, retry-exhausted `None` handling, request payloads, valid discussion lookup, no-discussion caching, malformed thread-ID diagnostics, meta tag decoding, meta parsing, meta mutation batching, and cached property behavior must remain compatible. |
| R5 | Focused, page, adjacent page/page-file/page-revision/page-votes/site, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `Page.discussion` raises contextual `NoElementException` when `forum/ForumCommentsListModule` returns a list-valued `body`. | `TestPageProperties.test_discussion_malformed_response_body_type_includes_page_context` expects `Page discussion response body is malformed for site: test-site, page: test-page (id=12345, field=body, expected=str, actual=list)`. | Leaking raw `TypeError`, entering thread-ID regex handling, calling `ForumThread.get_from_id(...)`, fabricating no discussion, or setting `_discussion_checked = True` rejects this local completion claim. | Page discussion reads | `tests/unit/test_page.py` |
| R2 | `Page.metas` raises contextual `NoElementException` when `edit/EditMetaModule` returns a list-valued `body`. | `TestPageWriteMethods.test_metas_getter_malformed_response_body_type_includes_page_context` expects `Page metas response body is malformed for site: test-site, page: test-page (id=12345, field=body, expected=str, actual=list)`. | Leaking raw `AttributeError`, entering entity replacement, fabricating an empty metas dict, storing `_metas`, or parsing metadata from non-string input rejects this local completion claim. | Page metas reads | `tests/unit/test_page.py` |
| R3 | The malformed-body-type diagnostics include only structural identifiers, field name, expected type, and observed type. | The focused regressions match the full message shape using synthetic list-valued bodies. | Including raw response JSON, generated discussion markup, generated meta markup, metadata values, page source, forum content, credentials, local rollout paths, account names, or private site content rejects this local completion claim. | Auxiliary diagnostics | `src/wikidot/module/page.py` |
| R4 | Existing page auxiliary behavior remains green. | The focused auxiliary group passed 10 tests, `tests/unit/test_page.py` passed 166 tests, and the adjacent page/page-file/page-revision/page-votes/site run passed 332 tests. | Regressing missing-body diagnostics, retry exhaustion, valid discussion lookup, malformed thread-ID diagnostics, no-discussion caching, meta decoding, meta parsing, meta mutation batching, or adjacent page workflows rejects this local completion claim. | Page auxiliary workflows | `tests/unit/test_page.py`; `tests/unit/test_page_file.py`; `tests/unit/test_page_revision.py`; `tests/unit/test_page_votes.py`; `tests/unit/test_site.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit passed 909 tests; `ruff`, format check, `mypy`, and whitespace checks passed before the code commit; `pyright` remained unavailable in this environment. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `747197b fix(page): report malformed auxiliary bodies`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_discussion_malformed_response_body_type_includes_page_context tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_malformed_response_body_type_includes_page_context -q` failed before the fix with `TypeError: expected string or bytes-like object, got 'list'` for discussion and `AttributeError: 'list' object has no attribute 'replace'` for metas.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_discussion_malformed_response_body_type_includes_page_context tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_malformed_response_body_type_includes_page_context -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_discussion_retries_transient_fetch_failures tests/unit/test_page.py::TestPageProperties::test_discussion_raises_when_retry_is_exhausted tests/unit/test_page.py::TestPageProperties::test_discussion_missing_response_body_includes_page_context tests/unit/test_page.py::TestPageProperties::test_discussion_malformed_response_body_type_includes_page_context tests/unit/test_page.py::TestPageProperties::test_discussion_malformed_thread_id_includes_page_context tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_parses_decoded_flexible_markup tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_retries_transient_fetch_failures tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_raises_when_retry_is_exhausted tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_missing_response_body_includes_page_context tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_malformed_response_body_type_includes_page_context -q` passed 10 tests.
- `uv run --extra test pytest tests/unit/test_page.py -q` passed 166 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 332 tests.
- `uv run --extra test pytest tests/unit -q` passed 909 tests.
- `uv run ruff format --check src tests` passed with 80 files already formatted.
- `uv run ruff check src tests` passed.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `Page.discussion` still uses retry-aware AMC and the same `forum/ForumCommentsListModule` request payload.
- `Page.metas` still uses retry-aware AMC and the same `edit/EditMetaModule` request payload.
- Missing page discussion and metas response `body` fields still raise the existing not-found diagnostics from Issue 219.
- Retry-exhausted `None` responses remain `UnexpectedException` failures and are not converted into malformed-body failures.
- Present non-string discussion response `body` values raise contextual `NoElementException` before regex parsing.
- Present non-string metas response `body` values raise contextual `NoElementException` before string replacement or BeautifulSoup parsing.
- The malformed-body-type messages include site, page fullname, page ID, `field=body`, expected type, and observed type.
- Valid discussion lookup, no-discussion checked-state behavior, malformed discussion thread-ID diagnostics, meta tag decoding, flexible meta tag parsing, metadata mutation batching, cached property reads, and adjacent page/site workflows remain unchanged for valid string bodies.
- The malformed-body-type messages do not include raw response JSON, generated discussion markup, generated meta markup, metadata values, page source, forum content, credentials, local rollout paths, private account material, or private site content.
- No live Wikidot action, upstream Issue, upstream PR, push, real discussion response body, real meta response body, account material, credentials, generated markup, metadata values, forum content, or private page content is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Type validation could treat a future bytes-like body as malformed. Mitigation: AMC JSON bodies are expected to decode generated module HTML as strings; preserving only string input keeps the parser boundary explicit.
- Risk: Type validation could mask missing-body diagnostics. Mitigation: `None` remains on the existing missing-body path; only present non-string values use the malformed-type diagnostic.
- Risk: Discussion diagnostics could accidentally expose generated discussion content. Mitigation: the error reports only site/page/id identifiers and type names, not raw generated module markup or forum content.
- Risk: Metas diagnostics could expose private metadata values. Mitigation: the error reports only site/page/id identifiers and type names, not raw metadata markup or parsed metadata values.
- Risk: The guard could alter no-discussion caching. Mitigation: the discussion cache is not updated until after body validation and thread-ID parsing, and adjacent discussion tests remain green.

## Dependencies

- The AMC connector already validates decoded response roots as dictionaries before normal module parsing; this slice targets the `body` field value within that dictionary.
- `forum/ForumCommentsListModule` continues to expose discussion thread links through generated string markup when a page has a discussion.
- `edit/EditMetaModule` continues to expose meta tags through generated string markup.

## Open Questions

None for this local slice. Remaining useful work should continue the response-body field-type audit on remaining generated module helpers, especially recent changes, rather than expanding page auxiliary getters beyond their response boundary.

## Upstream-Safe Motivation

Page discussion and metadata reads are practical browser-free auxiliary workflows for navigation, audits, metadata reconciliation, publication checks, and archival tooling. If Wikidot returns a present non-string generated module body, wikidot.py should report the affected site/page/id and type mismatch before parser internals obscure the failure.

## Local Evidence, Not For Upstream Paste

- The RED failure showed a list-valued discussion response `body` leaking `TypeError: expected string or bytes-like object, got 'list'` from `re.search(...)`.
- The RED failure showed a list-valued metas response `body` leaking `AttributeError: 'list' object has no attribute 'replace'`.
- Existing Issue 219 covered missing page discussion and metas response `body` fields but intentionally left present malformed values as separate boundaries.
- Existing Issue 309 covered present malformed discussion thread ID scalar values but intentionally left the generated-module response body type boundary unchanged.
- The recent response-body type series showed the same boundary pattern in private messages, forum categories, site members, site applications, page-file reads, forum-thread reads, forum-post reads, page-revision source/HTML reads, forum-post-revision reads, ListPages reads, page source reads, page revision-list reads, page vote reads, and batched page file reads.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated discussion markup, generated meta markup, metadata values, forum content, page source text, and private site content out of upstream discussion.

## Additional Notes

This is a response-body field type diagnostics fix. It preserves valid page auxiliary behavior while making malformed present response bodies actionable without retaining generated discussion or metadata content.
