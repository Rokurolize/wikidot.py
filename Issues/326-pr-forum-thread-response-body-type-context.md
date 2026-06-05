# PR Draft: Report Malformed Forum Thread Response Body Types

## Summary

`ForumThreadCollection.acquire_all_in_category(category)` parses `forum/ForumViewCategoryModule` response `body` values as generated category thread-list HTML, while `ForumThreadCollection.acquire_from_thread_ids(site, thread_ids, category)` parses `forum/ForumViewThreadModule` response `body` values as generated direct thread-detail HTML. Earlier local slices made these forum-thread reads retry-aware, cache-aware, duplicate-ID-aware, parser-scoped, text-preserving, and context-rich for missing response bodies and malformed parser values. One adjacent response-boundary gap remained: if the decoded AMC response was a dictionary with a present but non-string `body` value, the code passed that value into BeautifulSoup and leaked a low-level parser `AttributeError`.

This local slice validates present forum thread-list and thread-detail response `body` values before HTML parsing. Non-string bodies now raise `NoElementException` with site/category/page or site/thread context plus `field=body`, expected type, and observed type. The diagnostic reports only compact structural context and type names; it does not include raw forum HTML, response JSON, local rollout paths, credentials, account material, thread titles, descriptions, or post content.

## Outcome

Malformed forum-thread response body types now fail at the module response boundary with actionable forum context instead of BeautifulSoup internals.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum indexing, moderation tooling, archival scans, migration helpers, or publishing-adjacent discussion inspection.

## Related Issue

Builds on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [170-pr-forum-thread-detail-fetch-failure-context.md](170-pr-forum-thread-detail-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), and [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md). Those drafts established forum thread acquisition as a practical read-heavy workflow with explicit site/category/page or site/thread diagnostics while leaving present non-string response bodies as a separate parser-entry boundary.

This also follows the response-body type diagnostic pattern from [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), and [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate category thread-list response `body` values are strings before BeautifulSoup parsing.
- Convert present non-string category thread-list body values into site/category/page-specific `NoElementException`.
- Validate direct thread-detail response `body` values are strings before BeautifulSoup parsing.
- Convert present non-string direct thread-detail body values into site/thread-specific `NoElementException`.
- Preserve missing-body diagnostics, retry-exhausted behavior, category cache reuse/reload, pagination, duplicate direct thread-ID handling, input-order restoration, requested/parsed thread mismatch checks, thread-list parsing, thread-detail parsing, post access, and reply behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum thread response-body type validation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A category thread-list response with a present non-string `body` field must fail before BeautifulSoup parsing. |
| R2 | A direct thread-detail response with a present non-string `body` field must fail before BeautifulSoup parsing. |
| R3 | Malformed-body-type errors must identify the affected site/category/page or site/thread, `field=body`, expected type, and observed type while omitting raw generated forum content. |
| R4 | Existing missing-body diagnostics, retry handling, category cache behavior, direct thread deduplication, parser diagnostics, and adjacent forum workflows must remain compatible. |
| R5 | Focused, forum-thread, adjacent forum, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `ForumThreadCollection.acquire_all_in_category(category)` raises contextual `NoElementException` when `forum/ForumViewCategoryModule` returns a list-valued `body`. | `TestForumThreadCollectionAcquireAll.test_acquire_all_malformed_first_page_response_body_type_includes_context` expects `Forum thread list response body is malformed for site: test-site, category: 1001, page: 1 (field=body, expected=str, actual=list)`. | Leaking BeautifulSoup `AttributeError`, silently returning an empty collection, seeding `category._threads`, or entering thread-row parsing rejects this local completion claim. | Category thread-list reads | `tests/unit/test_forum_thread.py` |
| R2 | `ForumThreadCollection.acquire_from_thread_ids(site, [3001])` raises contextual `NoElementException` when `forum/ForumViewThreadModule` returns a list-valued `body`. | `TestForumThreadCollectionAcquireFromIds.test_acquire_from_ids_malformed_response_body_type_includes_thread_context` expects `Forum thread detail response body is malformed for site: test-site, thread: 3001 (field=body, expected=str, actual=list)`. | Leaking BeautifulSoup `AttributeError`, fabricating a thread, returning an empty collection, or entering thread-detail parsing rejects this local completion claim. | Direct thread-detail reads | `tests/unit/test_forum_thread.py` |
| R3 | The malformed-body-type diagnostics include only structural identifiers, field name, expected type, and observed type. | The focused regressions match the full message shapes using synthetic list-valued bodies. | Including raw response JSON, generated forum HTML, thread descriptions, thread titles, post content, credentials, local rollout paths, or account names rejects this local completion claim. | Forum thread diagnostics | `src/wikidot/module/forum_thread.py` |
| R4 | Existing forum-thread behavior and adjacent forum behavior remain green. | The forum-thread suite passed 57 tests, the adjacent forum category/thread/post/revision run passed 195 tests, and the full unit suite passed 894 tests. | Regressing missing-body diagnostics, retry exhaustion, cached category threads, reload behavior, pagination, duplicate direct IDs, input order, requested/parsed mismatch handling, parser contexts, text spacing, post access, replies, or adjacent forum workflows rejects this local completion claim. | Forum workflows | `tests/unit/test_forum_thread.py`; `tests/unit/test_forum_category.py`; `tests/unit/test_forum_post.py`; `tests/unit/test_forum_post_revision.py` |
| R5 | Repository quality gates pass in the local dependency environment. | `ruff`, `mypy`, full unit, and whitespace checks passed before the code commit; `pyright` remained unavailable in this environment. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4fb4f94 fix(forum_thread): report malformed body types`.

- RED: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_first_page_response_body_type_includes_context -q` failed before the fix with BeautifulSoup `AttributeError` for the list-valued category thread-list body.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_first_page_response_body_type_includes_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_missing_first_page_response_body_includes_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_raises_when_paginated_retry_is_exhausted -q` passed 4 tests.
- RED: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_malformed_response_body_type_includes_thread_context -q` failed before the fix with BeautifulSoup `AttributeError` for the list-valued direct thread-detail body.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_first_page_response_body_type_includes_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_missing_first_page_response_body_includes_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_raises_when_paginated_retry_is_exhausted tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_malformed_response_body_type_includes_thread_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_missing_response_body_includes_thread_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_success tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_raises_when_retry_is_exhausted -q` passed 8 tests.
- `uv run --extra test pytest tests/unit/test_forum_thread.py -q` passed 57 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 195 tests.
- `uv run --extra test pytest tests/unit -q` passed 894 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- Category thread-list reads still request `forum/ForumViewCategoryModule` with the existing category/page payloads.
- Direct thread-detail reads still request `forum/ForumViewThreadModule` with the existing thread ID payloads.
- Missing `body` fields still raise the existing not-found diagnostics from Issue 214.
- Present non-string `body` values raise contextual `NoElementException` before BeautifulSoup parsing.
- The category thread-list malformed-body-type message includes site, category, page, `field=body`, expected type, and observed type.
- The direct thread-detail malformed-body-type message includes site, thread ID, `field=body`, expected type, and observed type.
- The malformed-body-type messages do not include raw response JSON, generated forum HTML, thread titles, descriptions, post content, credentials, local rollout paths, private site data, or private account material.
- Existing retry-exhausted behavior, pagination, cached category thread reuse/reload, duplicate direct thread-ID handling, input-order restoration, requested/parsed thread mismatch detection, parser-context diagnostics, text spacing, `ForumThread.posts`, and `ForumThread.reply(...)` remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real forum response body, local rollout path, account material, private forum content, or generated forum HTML is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Type validation could treat a future bytes-like body as malformed. Mitigation: AMC JSON bodies are expected to decode generated HTML as strings; preserving only string input keeps the parser boundary explicit.
- Risk: Type validation could mask missing-body diagnostics. Mitigation: `None` remains on the existing missing-body path; only present non-string values use the malformed-type diagnostic.
- Risk: Diagnostics could expose forum content. Mitigation: messages include only site/category/page or site/thread identifiers and type names, not raw generated HTML or forum text.

## Dependencies

- The AMC connector already validates decoded response roots as dictionaries before normal module parsing; this slice targets the `body` field value within that dictionary.
- Forum thread-list and direct thread-detail HTML parser behavior remains unchanged after a valid string body is supplied.

## Open Questions

None for this local slice. Remaining useful work should continue the broader response-body field-type audit across other modules rather than expanding this forum-thread change beyond the thread-list and direct-detail response boundaries.

## Upstream-Safe Motivation

Forum thread-list and direct thread-detail acquisition are practical browser-free workflows for indexing, moderation, archival, migration, and publishing-adjacent checks. If Wikidot returns a present non-string generated response body, wikidot.py should report the affected forum read path and type mismatch before BeautifulSoup internals obscure the failure.

## Local Evidence, Not For Upstream Paste

- The RED failures showed list-valued category thread-list and direct thread-detail `body` values leaking BeautifulSoup `AttributeError`.
- Existing Issue 214 covered missing `body` fields but intentionally left present malformed values as a separate boundary.
- The recent response-body type series showed the same boundary pattern in private messages, forum categories, site members, site applications, and direct page-file reads.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated forum HTML, thread titles, descriptions, post content, and private site data out of upstream discussion.

## Additional Notes

This is a response-body field type diagnostics fix. It preserves valid forum thread behavior while making malformed present response bodies actionable without retaining generated forum content.
