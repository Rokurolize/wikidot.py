# PR Draft: Validate Forum Thread Reply Site State

## Summary

`ForumThread.reply(...)` validates reply source/title text and optional parent-post IDs before sending Wikidot's `savePost` action. Existing local slices also validate direct `ForumThread(site=...)` construction, direct thread acquisition inputs, reply action response status, reply cache synchronization, and forum-thread URL parent state. One action-time retained-state boundary still trusted `ForumThread.site` after construction: if a caller, fixture, or rehydrated thread object replaced `thread.site` with a malformed non-`Site` object, `reply(...)` could reach mocked login/request/action-status handling before reporting the parent-state problem.

This change revalidates `self.site` inside `ForumThread.reply(...)` after reply input validation and before login checks or AMC request construction. Malformed action-time thread parent state now raises `ValueError("site must be a Site")`. Valid replies, reply input validation precedence, action-status diagnostics, local post-count/cache updates, category cache synchronization, and adjacent forum workflows remain unchanged.

## Outcome

Forum-thread replies now have explicit action-time parent-site preflight before malformed local thread state can influence authentication checks, request routing, response diagnostics, or local reply-side cache mutation.

## Current Evidence

Existing drafts [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [369-pr-validate-forum-thread-reply-parent-id.md](369-pr-validate-forum-thread-reply-parent-id.md), [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md), [503-pr-validate-forum-thread-site-field.md](503-pr-validate-forum-thread-site-field.md), [543-pr-validate-forum-thread-direct-site.md](543-pr-validate-forum-thread-direct-site.md), [557-pr-validate-page-destroy-site.md](557-pr-validate-page-destroy-site.md), [564-pr-validate-page-edit-site.md](564-pr-validate-page-edit-site.md), and [573-pr-validate-forum-thread-url-site.md](573-pr-validate-forum-thread-url-site.md) establish forum-thread replies, retained parent state, and adjacent action-time site validation as practical workflow surfaces.

This slice is not a duplicate of those issues. Issue 503 validates `ForumThread(site=...)` at construction time. Issue 543 validates the `site` argument to direct thread acquisition before request work. Issues 354 and 369 validate reply input values before login. Issue 251 validates malformed `savePost` responses after a valid request path returns. Issue 573 validates URL-time retained parent state, not write-time authentication/request routing. This slice covers mutated retained `ForumThread.site` at reply action time, not constructor input validation, direct acquisition arguments, reply input shape, reply action-status shape, URL generation, or live Wikidot request behavior.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.site` inside `ForumThread.reply(...)` after reply input validation and before login checks.
- Use the validated `site` for login and `savePost` AMC request construction.
- Add a regression for a mutated non-`Site` thread parent that previously reached mocked login/request/action-status handling.
- Preserve valid reply behavior and adjacent forum workflows.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThread.reply(...)` must reject a mutated non-`Site` `thread.site` with `ValueError("site must be a Site")` before login checks or AMC requests. |
| R2 | Existing reply source/title and parent-post ID validation must keep precedence before action-time site validation. |
| R3 | Valid replies must continue to send the same `savePost` payload, increment `thread.post_count`, clear the thread post cache, and synchronize category post/thread-cache state after confirmed success. |
| R4 | Existing reply action-status diagnostics and adjacent forum behavior must remain stable. |
| R5 | Focused RED/GREEN, reply tests, forum-thread tests, adjacent forum tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Mutated retained thread parent state fails before login or request work. | `TestForumThreadReply.test_reply_rejects_mutated_site_before_login` failed RED with `WikidotStatusCodeException` after mocked request/action-status handling, then passed GREEN after `ForumThread.reply(...)` revalidated `self.site`. | Calling `login_check`, calling `amc_request`, coercing malformed parents, or deferring failure to action-status diagnostics rejects this local completion claim. | `ForumThread.reply(...)` | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Reply input validation precedence remains unchanged. | `TestForumThreadReply.test_reply_rejects_non_string_text_inputs_before_login` and `TestForumThreadReply.test_reply_rejects_invalid_parent_post_id_before_login` stayed green in focused reply coverage. | Checking site state before rejecting malformed source/title/parent-post ID inputs, changing error messages, or allowing malformed inputs to reach login/request work rejects this local completion claim. | Reply public input preflight | `tests/unit/test_forum_thread.py` |
| R3 | Valid reply behavior remains unchanged. | `TestForumThreadReply.test_reply_success`, `test_reply_success_updates_category_post_count_and_invalidates_threads`, `test_reply_with_title`, and `test_reply_to_parent_post` stayed green. | Changing payload fields, losing parent ID serialization, failing to increment confirmed post counts, failing to clear caches, or changing category synchronization rejects this local completion claim. | Forum reply mutation workflow | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R4 | Adjacent workflows remain stable. | `tests/unit/test_forum_thread.py` passed 145 tests, adjacent forum workflow tests passed 511 tests, and the full unit suite passed 2672 tests. | Regressing category thread-list acquisition, direct thread-detail acquisition, parser diagnostics, response diagnostics, collection initialization, loaded-collection lookup, lazy category thread reads, direct thread lookup, batched thread lookup, lazy post reads, forum category behavior, forum post behavior, or forum post revision behavior rejects this local completion claim. | Forum thread and adjacent forum workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regression uses synthetic mutated thread state and local fixtures; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `7e0f686 fix(forum_thread): validate reply site`.

- RED reply-site validation: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_rejects_mutated_site_before_login -q` failed before the fix with `WikidotStatusCodeException` after the malformed site reached mocked request/action-status handling.
- GREEN focused regression: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_rejects_mutated_site_before_login -q` passed.
- Focused reply coverage: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadReply -q` passed 13 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 145 tests.
- Adjacent forum: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 511 tests.
- `uv run pytest tests/unit -q` passed 2672 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThread.reply(...)` rejects mutated malformed `thread.site` values with `ValueError("site must be a Site")` before login checks or AMC requests.
- Existing reply input validation remains earlier than login, request construction, and local state mutation.
- Valid reply payloads, action-status handling, post-count updates, cache invalidation, and category synchronization remain unchanged.
- Adjacent forum behavior remains intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed mutated retained `ForumThread.site` state reached mocked login/request/action-status handling and raised `WikidotStatusCodeException` instead of the existing parent-site diagnostic.
- This slice only validates retained forum-thread parent state before reply action work. It does not change thread construction, direct thread acquisition, thread-list parsing, direct thread-detail parsing, collection lookup semantics, URL generation, forum category/post/revision behavior, live site behavior, reply input validation, action-status validation, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, private forum content, and live Wikidot account details out of upstream discussion.
