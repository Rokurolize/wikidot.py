# PR Draft: Validate Non-Negative Forum Thread Reply Parent Post IDs

## Summary

`ForumThread.reply(...)` already validates `parent_post_id` as `None` or a non-boolean integer before login checks and before constructing the `savePost` request. That type check still allowed negative integers such as `-1`, which were serialized into Wikidot's `parentId` mutation payload and only failed later through unrelated action-status handling.

This change rejects negative `parent_post_id` values before login checks, `savePost` request construction, action-status parsing, post-count increments, thread post-cache invalidation, or category cache invalidation. It deliberately preserves direct replies with `None`, zero-ID compatibility, valid positive parent replies, text-input validation, action-status diagnostics, and local cache/count updates after confirmed successful replies.

## Outcome

Caller-supplied negative parent post IDs now fail deterministically at the public reply API boundary with `ValueError("parent_post_id must be non-negative or None")`. Valid direct replies and integer parent replies continue to use the same request payload shape as before.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who rely on browser-free forum reply helpers, generated forum migration scripts, local automation, fixtures, or adapters where invalid reply-parent state must not become a mutation payload.

## Current Evidence

Forum reply drafts [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [369-pr-validate-forum-thread-reply-parent-id.md](369-pr-validate-forum-thread-reply-parent-id.md), and [574-pr-validate-forum-thread-reply-site.md](574-pr-validate-forum-thread-reply-site.md) establish `ForumThread.reply(...)` as a practical local automation and mutation-boundary surface.

This slice is not a duplicate of those drafts or of [641-pr-validate-non-negative-forum-post-ids.md](641-pr-validate-non-negative-forum-post-ids.md). Issue 369 validates malformed reply `parent_post_id` values such as booleans, strings, floats, and dictionaries, but it intentionally accepted ordinary integers and did not reject negative integers. Issue 641 validates directly constructed `ForumPost.id` and stored `_parent_id` values, not caller-supplied action-time reply inputs. Issue 235 validates malformed generated post-list parent IDs before parser-side `ForumPost` construction. None of those existing drafts prevent `ForumThread.reply(source="...", parent_post_id=-1)` from reaching `savePost`.

## Related Issue / Non-Duplicate Analysis

Builds directly on [369-pr-validate-forum-thread-reply-parent-id.md](369-pr-validate-forum-thread-reply-parent-id.md), [641-pr-validate-non-negative-forum-post-ids.md](641-pr-validate-non-negative-forum-post-ids.md), and [235-pr-forum-post-id-parse-context.md](235-pr-forum-post-id-parse-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject negative `ForumThread.reply(..., parent_post_id=...)` values with `ValueError("parent_post_id must be non-negative or None")`.
- Reject negative values before login checks, AMC requests, action-status parsing, thread post-count updates, thread `_posts` cache invalidation, category `posts_count` updates, or category `_threads` cache invalidation.
- Preserve the existing malformed-type diagnostic `ValueError("parent_post_id must be an integer or None")`.
- Preserve direct replies where `parent_post_id is None`.
- Preserve zero as a valid integer input for compatibility.
- Preserve valid positive parent replies where `parentId` is serialized as the decimal post ID string.
- Leave live Wikidot behavior, pushes, upstream Issues, and upstream PRs unchanged.

## Type Of Change

- Input validation
- Mutation-boundary hardening
- Forum reply workflow integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A negative reply `parent_post_id` such as `-1` or `-100` must raise `ValueError("parent_post_id must be non-negative or None")` before `savePost` is attempted. |
| R2 | Malformed non-integer and boolean `parent_post_id` values must keep the existing `ValueError("parent_post_id must be an integer or None")` diagnostic. |
| R3 | Direct replies with `None`, zero parent IDs, and valid positive parent IDs must preserve their existing request payload behavior. |
| R4 | Existing successful reply behavior, action-status validation, thread post-count/cache updates, and category post-count/cache updates must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, reply-class tests, adjacent forum tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative reply parent post IDs cannot reach the save mutation. | `test_reply_rejects_negative_parent_post_id_before_login` failed RED for `-1` and `-100` because both values reached `savePost` action handling, then passed GREEN after the non-negative guard was added. | Accepting negative values, sending them as `parentId`, silently coercing them, or surfacing action-status errors rejects this local completion claim. | `ForumThread.reply` public input preflight | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Existing malformed-type diagnostics remain stable. | `test_reply_rejects_invalid_parent_post_id_before_login` passed in the focused RED and GREEN commands. | Changing the existing type error message, accepting booleans, coercing strings or floats, or allowing malformed values to reach login/request work rejects this local completion claim. | Reply parent-ID type validation | `tests/unit/test_forum_thread.py` |
| R3 | Valid direct and integer parent reply payloads remain stable. | `test_reply_to_parent_post` and `test_reply_accepts_zero_parent_post_id` passed in the focused RED and GREEN commands. | Regressing empty `parentId` for direct replies, `parentId == "0"` for zero, or `parentId == "5001"` for valid parent replies rejects this local completion claim. | Reply request construction | `tests/unit/test_forum_thread.py` |
| R4 | Forum reply and adjacent forum behavior stay green. | The reply class passed 16 tests, adjacent forum category/thread/post/revision suites passed 581 tests, and the full unit suite passed 2944 tests. | Regressing successful replies, action-status diagnostics, thread/category count updates, cache invalidation, forum category/thread/post/revision behavior, or any existing unit test rejects this local completion claim. | Forum workflows | `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level fixtures only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum markup from real sites, private post data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, reply-class tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `3ca61ac fix(forum_thread): validate reply parent post id range`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_rejects_invalid_parent_post_id_before_login tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_rejects_negative_parent_post_id_before_login tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_to_parent_post tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_accepts_zero_parent_post_id -q` failed 2 negative parent-ID cases before the fix; 6 malformed-input, valid-parent, and zero guards stayed green.
- GREEN: the same focused command passed 8 tests after the non-negative guard was added.
- `uv run ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` left both files unchanged.
- Re-running the same focused command after formatting passed 8 tests.
- `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadReply -q` passed 16 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 581 tests.
- `uv run pytest tests/unit -q` passed 2944 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThread.reply(source="...", parent_post_id=-1)` raises `ValueError`.
- The exception message is `parent_post_id must be non-negative or None`.
- `login_check` is not called for negative parent post IDs.
- `site.amc_request(...)` is not called for negative parent post IDs.
- Thread `post_count`, thread `_posts`, category `posts_count`, and category `_threads` are unchanged for rejected negative values.
- `ForumThread.reply(source="...", parent_post_id=True)`, serialized strings, floats, and dictionaries still raise `parent_post_id must be an integer or None`.
- `ForumThread.reply(source="...", parent_post_id=None)` still sends an empty `parentId`.
- `ForumThread.reply(source="...", parent_post_id=0)` still sends `parentId == "0"`.
- `ForumThread.reply(source="...", parent_post_id=5001)` still sends `parentId == "5001"`.
- Live Wikidot behavior, pushes, upstream Issues, and upstream PRs remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumThread.reply(...)` is a mutation helper that serializes an optional parent post ID into Wikidot's `parentId` action field. Negative post IDs are not valid Wikidot parent-post identity values, but the library previously accepted them as ordinary integers and sent them to the mutation path. Rejecting them locally keeps invalid caller state from becoming a write payload while preserving all direct, zero, and positive parent reply flows.

## Local Evidence

- Local rollout-backed drafts repeatedly use browser-free forum reply, forum post parsing, generated fixtures, and automation where invalid parent-post identity should fail before mutation.
- Existing local drafts covered reply text inputs, reply action-status responses, reply category cache synchronization, malformed non-integer `parent_post_id` inputs, direct `ForumPost` ID state, and generated parent-post parser diagnostics, but did not cover negative integer reply parent IDs.
- The focused RED failure showed negative `parent_post_id` values reached the save path before this slice.
- This slice only validates non-negative reply parent-post IDs. It does not change direct replies, valid positive parent replies, text validation, login behavior, action-status validation, cache invalidation, direct forum-post records, parser behavior, live Wikidot behavior, or upstream actions.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum markup from real sites, private post data, and private site data out of upstream discussion.

## Additional Notes

This change intentionally extends the existing optional post-ID helper instead of adding reply-only branching. The helper remains type-strict, keeps booleans out, preserves `None`, and now treats the range invariant as part of the same public preflight boundary.
