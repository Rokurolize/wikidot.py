# PR Draft: Validate Non-Negative ForumPost IDs

## Summary

`ForumPost.id` and `ForumPost._parent_id` identify concrete forum posts and reply relationships used by browser-free forum indexing, cached thread-post scans, source/revision fetches, edit workflows, migration ledgers, moderation summaries, translation review tooling, and collection lookup helpers. Existing local drafts validate direct `ForumPost.id` and `_parent_id` values as non-boolean integers or `None`, validate generated parser IDs, and validate reply-call parent IDs, but direct constructors still accepted negative integers such as `-1`. That allowed manually constructed fixtures, generated ledgers, or rehydrated records to carry impossible post identity or parent-link state.

This change validates direct `ForumPost.id` and `_parent_id` values as non-negative integers at the constructor boundary. It deliberately preserves `id=0` and `_parent_id=0` because prior identity-field drafts avoid stronger positive-ID requirements unless parser or live evidence proves one.

## Outcome

Directly constructed forum-post records can no longer store negative post IDs or negative parent post IDs, while zero-ID compatibility, malformed direct type diagnostics, generated post-list parsing, direct thread-post acquisition, lazy `ForumThread.posts`, source/revision reads, edit behavior, collection lookup, and adjacent forum workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum indexing, generated discussion migration ledgers, moderation tooling, translation review tooling, forum migration checks, cached thread-post scans, duplicate thread-post reads, reply-thread reconstruction, `ForumThread.posts`, forum post source reads, forum post edit workflows, forum post revisions, local fixtures, or serialized/rehydrated post records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum-post reads and stored post records as practical workflow surfaces. [235-pr-forum-post-id-parse-context.md](235-pr-forum-post-id-parse-context.md) validates malformed generated post and parent-post IDs with context. [369-pr-validate-forum-thread-reply-parent-id.md](369-pr-validate-forum-thread-reply-parent-id.md) validates write-side reply parent-ID inputs. [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md) validates caller-provided loaded-collection lookup ID types. [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md) validates direct `ForumPost.id` type, while [462-pr-validate-forum-post-parent-id-field.md](462-pr-validate-forum-post-parent-id-field.md) validates direct `_parent_id` type.

This slice is not a duplicate of Issues 235, 369, 378, 460, or 462. Issue 235 handles parser-created IDs, and generated post IDs already remain non-negative through the `post-<digits>` parser rule. Issue 369 validates action-time reply inputs, not stored post state. Issue 378 validates search-key shape, not stored post identity state. Issues 460 and 462 reject booleans, strings, floats, and other malformed direct fields, but still accept negative integers.

## Related Issue / Non-Duplicate Analysis

Builds directly on [235-pr-forum-post-id-parse-context.md](235-pr-forum-post-id-parse-context.md), [369-pr-validate-forum-thread-reply-parent-id.md](369-pr-validate-forum-thread-reply-parent-id.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md), and [462-pr-validate-forum-post-parent-id-field.md](462-pr-validate-forum-post-parent-id-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject direct `ForumPost(id=-1)` and `ForumPost(id=-100)` with `ValueError("id must be non-negative")`.
- Reject direct `ForumPost(_parent_id=-1)` and `ForumPost(_parent_id=-100)` with `ValueError("parent_id must be non-negative or None")`.
- Preserve direct `ForumPost(id=0)` and `ForumPost(_parent_id=0)` as non-negative identity values.
- Preserve existing malformed-ID and malformed-parent-ID diagnostics for non-integers and booleans.
- Leave generated post-list parsing, collection `find(...)` lookup semantics, source/revision acquisition, edit behavior, and adjacent forum workflows unchanged.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum-post identity and parent-link state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `ForumPost(id=-1)` and `ForumPost(id=-100)` must raise `ValueError("id must be non-negative")` when every other post field is valid. |
| R2 | Direct `ForumPost(_parent_id=-1)` and `ForumPost(_parent_id=-100)` must raise `ValueError("parent_id must be non-negative or None")` when every other post field is valid. |
| R3 | Direct `ForumPost(id=0)` and `ForumPost(_parent_id=0)` must remain valid and store `0`. |
| R4 | Existing malformed direct ID and parent-ID diagnostics must remain stable. |
| R5 | Generated post-list parsing, direct thread-post acquisition, lazy `ForumThread.posts`, source/revision reads, edit behavior, collection lookup, and adjacent forum workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, forum-post tests, adjacent forum tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct forum-post records cannot store negative post IDs. | `TestForumPostBasic.test_init_rejects_negative_id` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after `_validate_post_id(...)` rejected values below zero. | Accepting negative post IDs, coercing them to zero, or deferring failure to parser or lookup code rejects this local completion claim. | ForumPost constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Direct forum-post records cannot store negative parent post IDs. | `TestForumPostBasic.test_init_rejects_negative_parent_id` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after `_validate_optional_post_parent_id(...)` rejected values below zero. | Accepting negative parent IDs, coercing them to `None` or zero, or deferring failure to reply or parser code rejects this local completion claim. | ForumPost constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Zero remains valid for direct post identity fields. | `TestForumPostBasic.test_init_accepts_zero_id` and `test_init_accepts_zero_parent_id` passed in RED and GREEN runs. | Requiring positive-only post IDs without separate evidence rejects this local completion claim. | Constructor compatibility | `tests/unit/test_forum_post.py` |
| R4 | Existing malformed direct type diagnostics remain stable. | `TestForumPostBasic.test_init_rejects_malformed_id` and `test_init_rejects_malformed_parent_id` passed in the same focused RED and GREEN commands. | Changing `ValueError("id must be an integer")` or `ValueError("parent_id must be an integer or None")`, accepting booleans, or coercing strings/floats rejects this local completion claim. | ForumPost ID type validation | `tests/unit/test_forum_post.py` |
| R5 | Existing forum-post and adjacent forum workflows remain green. | Forum-post coverage passed 170 tests, adjacent forum coverage passed 566 tests, and the full unit suite passed 2897 tests. | Regressing parser diagnostics, post-list parsing, parent-ID parsing, source acquisition, revision acquisition, edit behavior, collection lookup, lazy `ForumThread.posts`, forum category behavior, forum thread behavior, or forum post revision behavior rejects this local completion claim. | Forum-post and adjacent workflows | `tests/unit/test_forum_post.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum titles, post bodies from real sites, response bodies, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, forum-post tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `10c5caa fix(forum_post): validate non-negative post ids`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_id tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_negative_id tests/unit/test_forum_post.py::TestForumPostBasic::test_init_accepts_zero_id tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_parent_id tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_negative_parent_id tests/unit/test_forum_post.py::TestForumPostBasic::test_init_accepts_zero_parent_id -q` failed 4 negative post-ID and parent-ID cases before the fix with `DID NOT RAISE`; 10 malformed-ID, malformed-parent-ID, zero-ID, and zero-parent-ID guards stayed green.
- GREEN: the same focused command passed 14 tests after direct post-ID and parent-ID range validation was added.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 170 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 566 tests.
- `uv run pytest tests/unit -q` passed 2897 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPost(id=-1)` and `ForumPost(id=-100)` raise `ValueError("id must be non-negative")`.
- `ForumPost(_parent_id=-1)` and `ForumPost(_parent_id=-100)` raise `ValueError("parent_id must be non-negative or None")`.
- `ForumPost(id=0)` remains accepted and stores `0`.
- `ForumPost(_parent_id=0)` remains accepted and exposes `post.parent_id == 0`.
- `ForumPost(id=None)`, `True`, `"5001"`, and `5001.0` continue to raise `ValueError("id must be an integer")`.
- `ForumPost(_parent_id=True)`, `"4999"`, `4999.0`, and `{"id": 4999}` continue to raise `ValueError("parent_id must be an integer or None")`.
- Generated post-list ID parsing, parser-side post/parent-ID diagnostics, direct acquisition, duplicate cached post reuse, collection lookup, lazy `ForumThread.posts`, `ForumPost.source`, `ForumPost.revisions`, `ForumPost.edit(...)`, and adjacent forum category/thread/revision workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Forum post IDs and parent post IDs are identity metadata for browser-free thread inventories, duplicate cached post reuse, generated migration ledgers, moderation summaries, reply reconstruction, and source/revision traversal. Negative IDs can look like valid integer state in direct fixtures or rehydrated records but are not useful post identifiers in the current public API surface. Non-negative validation catches that impossible state early while avoiding a stronger positive-only rule.

## Local Evidence

- Local rollout evidence used forum post reads, duplicate thread-post reuse, lazy `ForumThread.posts`, source reads, revision reads, edit workflows, reply-link reconstruction, moderation ledgers, translation review tooling, and generated records that construct or consume `ForumPost` objects directly.
- Existing local drafts covered generated malformed post IDs and parent IDs, direct reply-call parent IDs, collection lookup IDs, direct post identity/text types, and direct parent-ID types, but did not cover negative direct post IDs or parent IDs.
- The focused RED failures showed negative direct post IDs and parent IDs were accepted as stored state. The GREEN regressions cover invalid values, zero compatibility, and existing malformed type validation.
- This slice only validates non-negative direct post-ID and parent-ID semantics. It does not change generated row-ID parsing, lookup semantics, post-list selectors, title parsing, body parsing, user/timestamp parsing, edit metadata parsing, source acquisition, revision acquisition, edit behavior, live site behavior, or upstream actions.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, forum source text, post titles from private sites, post bodies from private sites, and private site data out of upstream discussion.

## Additional Notes

This change intentionally validates non-negative direct post IDs only. It does not require positive IDs, verify that a parent post exists in the same thread, coerce numeric strings, or change `ForumPostCollection.find(...)` lookup semantics because prior local search-key drafts preserved absent integer lookup behavior while generated parser IDs already reject non-digit post IDs.
