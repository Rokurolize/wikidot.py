# PR Draft: Validate ForumThread.reply Parent Post IDs

## Summary

`ForumThread.reply(...)` documents `parent_post_id` as `int | None`, but malformed values were not rejected at the public API boundary. Values such as `True`, `"5001"`, `5001.0`, or `{"id": 5001}` reached login checks and `savePost` request construction, where they were stringified into the `parentId` payload or leaked later action-status failures instead of producing a stable caller-facing validation error.

This change validates `parent_post_id` before login checks, `savePost` request construction, action-status parsing, post-count increments, thread post-cache invalidation, or category cache updates. Invalid values now raise `ValueError("parent_post_id must be an integer or None")`. Direct replies with `None`, valid parent replies with integer post IDs, reply text validation, action-status diagnostics, thread-local state updates, and category-local cache synchronization remain unchanged.

## Outcome

Forum reply callers now get deterministic Python-side preflight validation for malformed parent-post IDs instead of accidentally sending invalid `parentId` payloads or observing unrelated action-response failures.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum replies in generated discussion workflows, migration scripts, moderation tooling, audit jobs, or local automation that may load reply targets from JSON, spreadsheets, CLI arguments, or scraped/generated records.

## Current Evidence

Local rollout-backed drafts repeatedly treat forum reply paths as practical mutation surfaces. Existing drafts [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md), [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), and [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md) establish forum thread reply, parent reply payloads, action-status validation, local state synchronization, and forum write input validation as active practical workflows.

Those prior slices are not duplicates. They covered retry/read boundaries, source/edit-form reads, forum post editing, `savePost` action-status validation, category cache synchronization after successful replies, and text-field validation for `source` and `title`. They did not validate malformed `parent_post_id` values before login checks or `savePost` request construction.

## Related Issue

Builds directly on [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), and [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a small `ForumThread.reply(...)` preflight helper for optional post IDs.
- Reject non-integer and boolean `parent_post_id` values with `ValueError("parent_post_id must be an integer or None")`.
- Validate before login checks, `savePost` request construction, action-status handling, thread post-count updates, thread post-cache invalidation, category post-count updates, or category thread-cache invalidation.
- Preserve direct replies where `parent_post_id is None`.
- Preserve valid parent replies where `parent_post_id` is an integer.
- Preserve forum reply text validation, action-status diagnostics, valid payload shape, method chaining, thread-local updates, and category-local updates after confirmed success.

## Type Of Change

- Input validation
- Public API behavior hardening
- Forum reply preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThread.reply(..., parent_post_id=...)` must reject values that are neither `None` nor non-boolean integers with `ValueError("parent_post_id must be an integer or None")`. |
| R2 | Invalid `parent_post_id` values must fail before login checks, AMC requests, action-status parsing, post-count changes, `_posts` cache invalidation, category `posts_count` changes, or category `_threads` invalidation. |
| R3 | Valid direct replies and valid integer parent replies must remain unchanged. |
| R4 | Existing forum reply text validation, action-status diagnostics, category cache synchronization, post-list acquisition, and forum-thread workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, affected forum-thread tests, adjacent forum tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed parent-post IDs fail with a stable public validation error. | `TestForumThreadReply.test_reply_rejects_invalid_parent_post_id_before_login` failed RED for `True`, `"5001"`, `5001.0`, and `{"id": 5001}` by reaching `savePost` action-status handling, then passed GREEN after validation was added. | Accepting booleans, strings, floats, dictionaries, or other non-integer values as parent post IDs; coercing them into `parentId`; or surfacing action-status errors rejects this local completion claim. | Forum reply preflight | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Invalid parent-post IDs fail before side effects. | The focused regression asserts `login_check()` and `amc_request(...)` are not called, `post_count` is unchanged, `_posts` remains cached, category `posts_count` is unchanged, and category `_threads` remains cached. | Login checks, AMC request construction, action-status parsing, thread cache clearing, thread count incrementing, category count incrementing, or category cache invalidation before validation rejects this local completion claim. | Forum reply side-effect boundary | `tests/unit/test_forum_thread.py` |
| R3 | Valid direct and parent replies remain unchanged. | `TestForumThreadReply` passed 12 tests, including direct replies, titled replies, integer parent replies, action-status failures, and category cache updates. | Regressing `parentId == ""` for direct replies, `parentId == "5001"` for valid parent replies, method chaining, or local state updates after `status: ok` rejects this local completion claim. | Forum reply behavior | `tests/unit/test_forum_thread.py` |
| R4 | Adjacent forum workflows remain unchanged. | `tests/unit/test_forum_thread.py` passed 72 tests, the adjacent forum set passed 240 tests, and the full unit suite passed 1042 tests. | Regressing forum thread acquisition, category thread-list acquisition, post-list acquisition, post source acquisition, post revision acquisition, forum write text validation, action-status diagnostics, parser diagnostics, cache synchronization, or retry/read behavior rejects this local completion claim. | Forum workflows | adjacent forum unit tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic thread/category objects plus malformed local values. | Using live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, sandbox details, upstream Issues, upstream PRs, raw action responses, forum post content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `24785e7 fix(forum_thread): validate reply parent post id`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_rejects_invalid_parent_post_id_before_login` failed before the fix with 4 failures; malformed `parent_post_id` values reached `savePost` action-status handling and raised `WikidotStatusCodeException`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_rejects_invalid_parent_post_id_before_login` passed 4 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_thread.py::TestForumThreadReply` passed 12 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_thread.py` passed 72 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py` passed 240 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1042 tests.
- `.venv/bin/ruff check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed.
- `.venv/bin/ruff format --check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with 2 files already formatted.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `ForumThread.reply(source="...", parent_post_id=True)` raises `ValueError("parent_post_id must be an integer or None")` before login checks or AMC work.
- `ForumThread.reply(source="...", parent_post_id="5001")`, `5001.0`, and `{"id": 5001}` raise the same stable error before side effects.
- Invalid parent-post IDs do not call `login_check()` or `amc_request(...)`.
- Invalid parent-post IDs do not mutate `post_count`, `_posts`, category `posts_count`, or category `_threads`.
- `ForumThread.reply(source="...")` still sends an empty `parentId` for direct replies.
- `ForumThread.reply(source="...", parent_post_id=5001)` still sends `parentId == "5001"`.
- Existing reply text validation, action-status diagnostics, successful thread/category local-state updates, forum thread acquisition, category acquisition, post acquisition, and post revision behavior remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Forum replies can be direct thread replies or replies to a specific post. The valid parent reply path depends on a real integer post ID because the implementation serializes it into Wikidot's `parentId` action payload. Generated workflows can accidentally pass serialized IDs, booleans, floats, dictionaries, or missing values into that argument. Those malformed values should fail deterministically before login checks or non-retried mutation requests. The change is narrow: it rejects malformed parent IDs instead of coercing them and leaves valid reply payloads unchanged.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established forum reply and forum mutation helpers as practical workflows.
- Existing drafts covered forum reply action-status validation, category cache synchronization after successful replies, and forum write text-field validation, but not malformed parent-post ID preflight.
- The focused RED failures showed malformed parent-post IDs crossing into `savePost` handling and leaking unrelated status errors instead of failing at the public call boundary.
- This slice only validates `ForumThread.reply(parent_post_id=...)`. It does not change thread acquisition, post acquisition, forum post parsing, post editing, category creation, reply action retry policy, response-body diagnostics, action-status diagnostics, live Wikidot behavior, or forum dataclass fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw action responses, forum post content from real sites, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects serialized parent IDs instead of silently converting them. Callers that ingest parent post IDs from JSON, YAML, CLI arguments, spreadsheets, generated structures, or scraped records should normalize them to integers before calling `ForumThread.reply(...)`.
