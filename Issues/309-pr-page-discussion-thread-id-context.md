# PR Draft: Report Malformed Page Discussion Thread IDs

## Summary

`Page.discussion` retrieves generated `forum/ForumCommentsListModule` markup and looks for `WIKIDOT.forumThreadId` before delegating to `ForumThread.get_from_id(...)`. Earlier local slices made this read retry-aware, kept exhausted retries from caching false negatives, and converted missing response `body` fields into page-context `NoElementException` failures. One adjacent parser-boundary gap remained: when the generated comments module included a present `forumThreadId` assignment with a malformed non-numeric value, wikidot.py silently treated the page as having no discussion and set `_discussion_checked = True`.

This local slice keeps successful discussion lookup, no-discussion behavior, retry handling, response-body validation, caching, and direct `ForumThread.get_from_id(...)` delegation unchanged. It validates present `forumThreadId` assignments before converting them to `int` and raises `NoElementException` with site unix name, page fullname, page ID, `field=thread_id`, and the observed value when the assignment is malformed.

## Outcome

Malformed page discussion thread IDs now fail with page-local context instead of being cached as a false no-discussion result.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who navigate from pages to their backing forum discussion threads for browser-free archival, moderation, migration, or indexing workflows.

## Related Issue

Builds on [045-pr-retry-page-discussion-fetch.md](045-pr-retry-page-discussion-fetch.md), [192-pr-page-auxiliary-fetch-site-context.md](192-pr-page-auxiliary-fetch-site-context.md), and [219-pr-page-auxiliary-response-body-context.md](219-pr-page-auxiliary-response-body-context.md). Those drafts established `Page.discussion` as a retry-aware page auxiliary read with explicit site/page diagnostics for fetch exhaustion and malformed response bodies.

This slice also follows the scalar parser-boundary pattern from [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md), [240-pr-listpages-rating-parse-context.md](240-pr-listpages-rating-parse-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), and [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md).

No upstream issue was filed from this local workspace.

## Changes

- Parse present `WIKIDOT.forumThreadId` assignments with a value-capturing regex instead of a digit-only regex.
- Reject present non-numeric or empty thread ID values with contextual `NoElementException`.
- Include site unix name, page fullname, page ID, `field=thread_id`, and observed value in the parser error.
- Preserve `None` behavior for comments-module bodies without a thread ID marker.
- Preserve retry-aware comments-module acquisition, missing body diagnostics, valid thread lookup, cached discussion state, and direct forum-thread lookup behavior.
- Add a focused public `Page.discussion` regression for `WIKIDOT.forumThreadId = latest;`.

## Type Of Change

- Bug fix / diagnostics improvement
- Page auxiliary parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated page comments-module response with a present non-numeric `WIKIDOT.forumThreadId` assignment must fail at the `Page.discussion` parser boundary. |
| R2 | The malformed thread ID error must identify the affected site, page, page ID, field, and observed value. |
| R3 | A generated comments-module response without any `forumThreadId` marker must still return `None` and cache the checked no-discussion state. |
| R4 | Valid discussion thread IDs, retry-aware acquisition, missing response-body diagnostics, exhausted retry behavior, and direct `ForumThread.get_from_id(...)` delegation must remain compatible. |
| R5 | Focused, page-level, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `Page.discussion` raises `NoElementException` for `WIKIDOT.forumThreadId = latest;`. | `TestPageProperties.test_discussion_malformed_thread_id_includes_page_context` expects `NoElementException`. | Returning `None`, setting `_discussion_checked = True`, leaking a raw scalar parse error, or calling `ForumThread.get_from_id(...)` rejects this local completion claim. | `src/wikidot/module/page.py` | `tests/unit/test_page.py` |
| R2 | The error names `site: test-site`, `page: test-page`, `id=12345`, `field=thread_id`, and `value=latest`. | The focused regression matches all fields. | Omitting site, page, page ID, field, or observed value makes the failure ambiguous and rejects this local completion claim. | Discussion diagnostics | `tests/unit/test_page.py` |
| R3 | Bodies without a thread ID marker continue to mean no discussion. | Existing `Page.discussion` behavior and broader page property tests remained green. | Treating an absent marker as malformed would reject valid no-discussion pages and rejects this local completion claim. | Page discussion cache | `tests/unit/test_page.py` |
| R4 | Valid discussion IDs still fetch the backing `ForumThread`, missing bodies still fail with page context, and exhausted retries remain retryable. | The focused discussion group passed 3 existing tests plus the new malformed-ID regression; the full page suite passed 158 tests. | Regressing valid lookup, missing body behavior, retry exhaustion, or cache state rejects this local completion claim. | Page auxiliary reads | `tests/unit/test_page.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `c52487c fix(page): report malformed discussion thread ids`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_discussion_malformed_thread_id_includes_page_context -q` failed before the fix with `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>`.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_discussion_malformed_thread_id_includes_page_context -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_discussion_retries_transient_fetch_failures tests/unit/test_page.py::TestPageProperties::test_discussion_raises_when_retry_is_exhausted tests/unit/test_page.py::TestPageProperties::test_discussion_missing_response_body_includes_page_context -q` passed 3 tests.
- `uv run --extra test pytest tests/unit/test_page.py -q` passed 158 tests.
- `uv run --extra test pytest tests/unit -q` passed 867 tests.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- A generated comments-module response whose present `WIKIDOT.forumThreadId` value is non-numeric raises `NoElementException`.
- The malformed thread ID message includes site unix name, page fullname, page ID, `field=thread_id`, and observed value.
- Valid numeric discussion IDs still call `ForumThread.get_from_id(...)` with the parsed integer.
- Comments-module responses without a discussion thread ID marker still return `None` and cache the checked state.
- Missing response-body diagnostics, retry-exhausted behavior, cached discussion behavior, and adjacent page property workflows remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, generated discussion HTML from real sites, forum content, page content, credentials, cookies, auth JSON, or private site data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Treating absent thread markers as malformed would break valid no-discussion pages. Mitigation: this slice raises only when a `WIKIDOT.forumThreadId` assignment is present and malformed.
- Risk: The new regex could alter valid discussion parsing. Mitigation: the existing valid discussion regression still asserts `ForumThread.get_from_id(site, 3001)`.
- Risk: Diagnostics could expose generated page or forum content. Mitigation: the error reports only site/page identifiers, page ID, field name, and the scalar thread ID value, not raw response bodies or discussion content.

## Dependencies

- `forum/ForumCommentsListModule` continues to expose discussion links through a generated `WIKIDOT.forumThreadId = <id>;` assignment when a page has a discussion thread.
- `ForumThread.get_from_id(...)` remains the source of truth for loading a valid backing thread after the page-level thread ID is parsed.
- Existing no-discussion pages continue to omit the generated thread ID assignment.

## Open Questions

None for this local slice. A future cleanup could centralize small scalar context wrappers only if it removes duplication without hiding parser-specific diagnostics.

## Upstream-Safe Motivation

Page discussion lookup is a read-heavy navigation path for archival, moderation, migration, and indexing tools. If Wikidot emits a malformed generated discussion thread ID, wikidot.py should fail with structured page-local diagnostics instead of caching a false no-discussion result. That keeps logs actionable without retaining raw generated discussion markup, forum content, credentials, local rollout paths, or private page data.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established page discussion reads as retry-aware and page-context-rich.
- Issue 219 explicitly left thread-ID extraction unchanged while fixing missing response bodies, making the present malformed-ID assignment a separate adjacent boundary.
- The immediate RED failure showed the existing digit-only regex silently skipped `WIKIDOT.forumThreadId = latest;` and set `_discussion_checked = True`.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated discussion HTML, forum contents, page source text, page names from real sites, and private site data out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It preserves valid discussion lookup and no-discussion caching while preventing a malformed present thread ID from becoming a cached false negative.
