# PR Draft: Validate Forum Thread Href ID Shape

## Summary

`ForumThreadCollection.acquire_all_in_category(...)`, exposed through `ForumCategory.threads` and `ForumCategory.reload_threads()`, parses category thread-list links returned by `forum/ForumViewCategoryModule` and uses the title link's `t-<id>` path segment as `ForumThread.id`. Earlier parser hardening added category/page/row context for missing thread IDs, but the extraction still searched for any `t-<digits>` substring. A malformed generated href such as `/forum/t-3001-latest/test-thread` was therefore accepted as thread ID `3001`.

This change treats `t-<digits>` as a thread ID only when it is a complete URL path segment, with optional query/hash/end delimiters. Digit-bearing malformed hrefs now raise `NoElementException` with site, category, page, row, field, and raw href context before constructing `ForumThread`.

## Outcome

Category thread-list acquisition no longer fabricates forum-thread IDs from malformed generated title hrefs. Valid thread links such as `/forum/t-3001/test-thread` still parse the same `ForumThread.id` values, and hrefs without any thread ID keep the existing `Thread ID is not found ...` diagnostic.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum indexing, category-owned thread traversal, generated discussion migration ledgers, moderation tooling, translation review tooling, cached category scans, `ForumCategory.threads`, `ForumCategory.reload_threads()`, or local fixtures where thread identity must come from structurally valid Wikidot thread-list links.

## Current Evidence

Local rollout-backed drafts repeatedly identify category thread-list acquisition as a practical read-heavy workflow and as the entry point for direct thread, post, and revision traversal. Existing drafts cover retry-aware thread-list fetching, nested-table scoping, title/description text fidelity, row-level parser context, response-body diagnostics, post-count parsing, created-by and created-at parser diagnostics, direct thread-detail ID parsing, direct `ForumThread.id` validation, thread-ID range validation, retained category ID validation before thread-list acquisition, and generated category href ID-shape validation.

This slice is not a duplicate of [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), [642-pr-validate-non-negative-forum-thread-ids.md](642-pr-validate-non-negative-forum-thread-ids.md), [681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md](681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md), or [726-pr-validate-forum-category-href-id-shape.md](726-pr-validate-forum-category-href-id-shape.md). Issue 158 covers missing thread-list field context, Issues 159 and 311 cover direct thread-detail parsing, Issue 234 covers thread-list count cells, Issues 291 and 292 cover user and timestamp metadata, Issues 455 and 642 cover direct `ForumThread(id=...)` and direct lookup ID validation, Issue 681 covers retained parent category IDs before acquisition, and Issue 726 covers generated category-list hrefs before `ForumCategory` construction. This slice covers generated category thread-list title href parsing before `ForumThread` construction.

No upstream issue was filed from this local workspace.

## Changes

- Add a focused helper for forum thread-list href ID parsing.
- Accept thread IDs only from a complete `t-<digits>` URL path segment, preserving valid `/forum/t-3001/test-thread` links.
- Reject digit-bearing malformed thread hrefs, such as `/forum/t-3001-latest/test-thread`, with `NoElementException` containing site, category, page, row, `field=id`, and raw href value.
- Preserve the existing missing-ID `Thread ID is not found ...` diagnostic for hrefs without a thread ID segment.
- Preserve successful category thread-list parsing, pagination, retry behavior, response-body validation, nested-table filtering, title/description text fidelity, post-count parsing, created-by and created-at parsing, cache population, direct thread reads, post access, and reply behavior.

## Type Of Change

- Parser hardening
- Forum thread identity validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated category thread-list title href containing `t-<digits>` plus trailing path-segment text, such as `/forum/t-3001-latest/test-thread`, must fail before constructing `ForumThread`. |
| R2 | The malformed thread-ID error must identify site, category, page, structural row, `field=id`, and the raw href value. |
| R3 | Valid generated thread hrefs must continue to parse into the same `ForumThread.id` values. |
| R4 | Hrefs without any thread-ID segment must keep the existing `Thread ID is not found ...` diagnostic. |
| R5 | Existing thread-list parser behavior, pagination, retry handling, response-body diagnostics, nested-table filtering, title/description extraction, post-count parsing, created metadata parsing, cache population, direct thread reads, post access, and reply behavior must remain unchanged. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum names, raw generated HTML, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `/forum/t-3001-latest/test-thread` fails instead of becoming thread ID `3001`. | `test_acquire_all_malformed_thread_id_includes_category_context` failed RED with `DID NOT RAISE`, then passed GREEN after strict path-segment thread ID parsing was added. | Returning a `ForumThread`, extracting the first digit run, or silently dropping trailing href text rejects this local completion claim. | Category thread-list generated parser | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | The malformed href diagnostic includes the structural context and observed value. | The regression matches `Thread ID is malformed for site: test-site (category=1001, page=1, row=1, field=id, value=/forum/t-3001-latest/test-thread)`. | Omitting site, category, page, row, field, or raw href value rejects this local completion claim. | Forum thread-list ID diagnostics | `tests/unit/test_forum_thread.py` |
| R3 | Valid thread-list links still parse. | `test_acquire_all_single_page`, `tests/unit/test_forum_thread.py`, and adjacent forum coverage passed with existing valid `/forum/t-3001/test-thread` fixtures. | Rejecting valid thread-list links or changing parsed thread IDs rejects this local completion claim. | Successful category thread-list acquisition | `tests/unit/test_forum_thread.py` |
| R4 | Existing missing-ID behavior remains distinct from malformed digit-bearing hrefs. | Source inspection shows hrefs without a strict `t-<digits>` segment and without a malformed `t-...` segment still raise `Thread ID is not found ...` with the existing context. | Reclassifying no-ID links as malformed digit-bearing links or dropping the existing parse context rejects this local completion claim. | Existing parser diagnostic compatibility | `src/wikidot/module/forum_thread.py` |
| R5 | Adjacent repository behavior stays green. | Full unit, ruff, ruff format, mypy, pyright, and `git diff --check` passed. | Any test, lint, format, type, or whitespace failure rejects this local completion claim. | Repository quality gates | `tests/unit`, `src`, `tests` |
| R6 | No private or live-site material is needed. | The regression mutates a synthetic unit fixture and uses mocks only. | Using credentials, cookies, auth JSON, live Wikidot actions, raw private generated HTML, private forum names, upstream Issues, upstream PRs, or pushes rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `e1b8394 fix(forum_thread): validate thread href ids`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_thread_id_includes_category_context -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_thread_id_includes_category_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_missing_name_cell_class_includes_category_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_post_count_includes_category_context -q` passed 4 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 224 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 886 tests.
- `uv run pytest tests/unit -q` passed 3600 tests.
- `uv run ruff check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed.
- `uv run ruff format --check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with 2 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThreadCollection.acquire_all_in_category(...)` raises `NoElementException` for a thread-list title href such as `/forum/t-3001-latest/test-thread`.
- The exception includes site `unix_name`, parent category ID, thread-list page number, structural row number, `field=id`, and the raw href value.
- Valid thread-list title hrefs with a complete `t-<digits>` path segment still parse the same thread IDs.
- Hrefs without any thread ID keep the existing `Thread ID is not found ...` parser diagnostic.
- Successful thread-list parsing, pagination, retry behavior, empty-result behavior, response-body validation, nested thread-table filtering, title and description text spacing, post-count parsing, created metadata parsing, cache population, lazy `ForumCategory.threads`, `reload_threads(...)`, direct thread detail acquisition, post access, and reply behavior remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Thread links may include query strings or fragments. Mitigation: the helper accepts `t-<digits>` followed by `/`, `?`, `#`, or end of string.
- Risk: Overly loose parsing could continue accepting malformed hrefs. Mitigation: the helper requires the ID marker to be a complete path segment instead of searching for any digit run.
- Risk: This could be confused with direct thread ID validation. Mitigation: Issues 455 and 642 cover direct or retained thread IDs after object construction or direct lookup input; this slice validates generated href input before construction.

## Dependencies

- Existing `ForumThreadCollection.acquire_all_in_category(...)` request construction, retry helper usage, response-body validation, row selection, pagination, and cache population remain unchanged.
- Existing `ForumThread` constructor validation remains responsible for direct local record construction.
- Existing `NoElementException` remains the generated-parser exception for malformed thread-list fields.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice. Future work should continue with fresh duplicate-checked parser boundaries, public input validation, result ergonomics, or measured complexity candidates outside this forum thread href ID-shape path.

## Upstream-Safe Motivation

`ForumThread.id` is durable identity metadata for browser-free forum inventories, moderation summaries, migration checks, cached category ledgers, category-owned post traversal, and downstream forum revision traversal. A generated thread-list href with trailing text in the ID segment should not be accepted merely because it contains a `t-<digits>` substring. Path-segment validation keeps malformed Wikidot module output visible while preserving valid thread rows.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established category thread-list acquisition as a practical workflow through retry-aware fetching, parser scoping, nested-table filtering, response-body validation, title/description text fidelity, post-count diagnostics, created metadata diagnostics, direct thread validation, retained category ID validation, and adjacent forum traversal workflows.
- Existing local drafts covered missing thread-list field diagnostics, direct thread-detail ID diagnostics, thread-list count/user/timestamp diagnostics, direct thread ID type/range validation, parent category retained ID validation, and generated category-list href ID-shape validation; they did not reject digit-bearing malformed generated thread-list title hrefs before construction.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated forum-category HTML, private forum names, private thread titles, saved page contents, and private edit comments out of upstream discussion.
