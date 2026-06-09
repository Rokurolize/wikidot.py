# PR Draft: Validate Forum Thread Collection Retained ID State

## Summary

`ForumThreadCollection.find(id)` validates malformed caller-provided search-key types before scanning stored threads, but the scan still compared each retained `thread.id` directly against the search ID. After local fixture, serialized, or rehydrated forum-thread state has been mutated incorrectly, booleans and floats can satisfy Python equality against integer thread IDs, while `None`, strings, lists, and negative IDs are treated as ordinary not-found misses instead of corrupted retained thread-ID state.

This change validates each stored thread's retained ID with the existing `_validate_thread_id(...)` helper before comparing it to the caller search ID. Malformed retained thread IDs now raise `ValueError("thread_id must be an integer")`, negative retained thread IDs now raise `ValueError("thread_id must be non-negative")`, valid zero-ID lookup remains accepted, existing absent integer lookup behavior remains unchanged, and no category thread-list fetch, direct thread-detail fetch, parser, cache, post-list, reply, or live Wikidot behavior changes.

## Outcome

Loaded forum-thread collections can no longer return a thread by Python's loose numeric equality or hide corrupted retained thread IDs behind an ordinary not-found result.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free forum indexes, moderation ledgers, translation review tooling, migration records, cached category thread scans, local fixtures, or serialized and rehydrated `ForumThreadCollection` objects.

## Current Evidence

Local rollout-backed drafts already established forum-thread reads and thread identity as practical boundaries. [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [170-pr-forum-thread-detail-fetch-failure-context.md](170-pr-forum-thread-detail-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md), [592-pr-validate-forum-post-collection-thread-ownership.md](592-pr-validate-forum-post-collection-thread-ownership.md), [595-pr-validate-forum-thread-posts-cache-ownership.md](595-pr-validate-forum-thread-posts-cache-ownership.md), [642-pr-validate-non-negative-forum-thread-ids.md](642-pr-validate-non-negative-forum-thread-ids.md), and [665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md](665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md) cover forum-thread acquisition, direct-detail lookup, parser diagnostics, response diagnostics, lookup search-key type validation, collection shape, direct ID type/range, site ownership, cached posts ownership, direct lookup IDs, and retained posts-cache owner identity.

This slice is not a duplicate of those drafts. Issue 379 validates caller-provided `ForumThreadCollection.find(id=...)` search-key types before scanning stored threads, but it does not validate retained IDs already stored inside the collection. Issues 455 and 642 validate direct `ForumThread(id=...)` construction and direct lookup IDs, but they cannot cover a valid thread whose ID is corrupted after construction and then reused in a collection. Issues 595 and 665 validate posts-cache ownership and retained thread IDs in `ForumThread._posts`, not loaded `ForumThreadCollection.find(...)` lookup rows. Issue 642 explicitly left `ForumThreadCollection.find(...)` lookup semantics unchanged.

## Related Issue / Non-Duplicate Analysis

Builds directly on [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md), [592-pr-validate-forum-post-collection-thread-ownership.md](592-pr-validate-forum-post-collection-thread-ownership.md), [595-pr-validate-forum-thread-posts-cache-ownership.md](595-pr-validate-forum-thread-posts-cache-ownership.md), [642-pr-validate-non-negative-forum-thread-ids.md](642-pr-validate-non-negative-forum-thread-ids.md), and [665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md](665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate each stored `ForumThread.id` before `ForumThreadCollection.find(id)` compares it to the search key.
- Reject retained stored thread IDs such as `None`, `True`, `False`, `"3001"`, `3001.0`, and `[]` with `ValueError("thread_id must be an integer")`.
- Reject retained stored thread IDs such as `-1` with `ValueError("thread_id must be non-negative")`.
- Preserve valid zero-ID lookup, valid matching lookup, existing absent integer lookup behavior, malformed caller search-key type diagnostics, collection site ownership, category thread-list acquisition, direct thread-detail acquisition, parser diagnostics, cached category thread lists, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, and adjacent forum workflows.
- Do not add caller search-key range validation in this slice.

## Type Of Change

- Input validation
- Retained forum-thread ID hardening
- Loaded collection lookup integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThreadCollection.find(id)` must reject retained stored `thread.id` values such as `None`, `True`, `False`, `"3001"`, `3001.0`, and `[]` with `ValueError("thread_id must be an integer")` before comparison. |
| R2 | `ForumThreadCollection.find(id)` must reject retained stored `thread.id=-1` with `ValueError("thread_id must be non-negative")` before comparison. |
| R3 | Valid lookup where the stored thread ID and search ID are both `0` must remain accepted. |
| R4 | Existing caller search-key type validation, valid matching lookup, existing absent integer lookup behavior, collection initialization, collection site ownership, category thread-list acquisition, direct thread-detail acquisition, parser diagnostics, cached category thread lists, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, and adjacent forum workflows must remain green. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-thread module coverage, adjacent forum/site coverage, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained stored thread IDs fail before lookup comparison. | `test_find_rejects_thread_with_malformed_retained_ids` failed RED for six malformed values: booleans and `3001.0` could be accepted through Python equality, while `None`, `"3001"`, and `[]` returned ordinary misses. The test passed GREEN after stored thread ID validation. | Accepting booleans/floats, returning ordinary `None` misses for corrupted IDs, coercing values, or returning a thread from corrupted retained ID state rejects this local completion claim. | Stored `ForumThread.id` during collection lookup | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Negative retained stored thread IDs fail before lookup comparison. | `test_find_rejects_thread_with_negative_retained_id` failed RED with an ordinary not-found result, then passed GREEN after stored thread ID range validation. | Treating negative stored IDs as ordinary misses, accepting them, matching them, or coercing them rejects this local completion claim. | Stored `ForumThread.id` during collection lookup | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R3 | Zero remains a valid retained thread ID for lookup. | `test_find_accepts_thread_with_zero_retained_id` passed RED and GREEN. | Rejecting `0`, treating it as missing, coercing it to false, or changing returned thread identity rejects this local completion claim. | Forum-thread collection lookup semantics | `tests/unit/test_forum_thread.py` |
| R4 | Existing compatible behavior remains compatible. | Focused GREEN coverage passed 8 tests, `tests/unit/test_forum_thread.py` passed 188 tests, adjacent forum/site coverage passed 1031 tests, and full unit passed 3205 tests. | Regressing caller search-key type validation, valid matching lookup, existing absent integer lookup behavior, collection initialization, collection site ownership, category thread-list acquisition, direct thread-detail acquisition, parser diagnostics, cached category thread lists, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, forum category/post/revision behavior, site workflows, or any unit test rejects this local completion claim. | Forum-thread collection and adjacent forum workflows | `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit/test_site.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic forum-thread objects and local unit helpers only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, forum source text, thread titles or descriptions from private forums, private forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, temporary pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `71b2a70 fix(forum_thread): validate collection retained ids`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_find_accepts_thread_with_zero_retained_id tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_find_rejects_thread_with_malformed_retained_ids tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_find_rejects_thread_with_negative_retained_id -q` collected 8 tests: 7 retained stored thread-ID cases failed before the fix, and the zero-ID compatibility guard passed.
- GREEN: the same focused command passed 8 tests after stored thread IDs were validated before collection lookup comparison.
- `uv run ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` left both files unchanged.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 188 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_site.py -q` passed 1031 tests.
- `uv run pytest tests/unit -q` passed 3205 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThreadCollection.find(3001)` raises `ValueError("thread_id must be an integer")` when a stored thread's retained `thread.id` is `None`, `"3001"`, or `[]`.
- `ForumThreadCollection.find(1)`, `find(0)`, and `find(3001)` raise `ValueError("thread_id must be an integer")` when stored retained IDs are `True`, `False`, or `3001.0` before they can match through Python equality.
- `ForumThreadCollection.find(3001)` raises `ValueError("thread_id must be non-negative")` when a stored thread's retained `thread.id` is `-1`.
- `ForumThreadCollection.find(0)` still returns a thread whose retained ID is valid integer `0`.
- Existing malformed search-key type rejection, matching lookup, absent integer lookup behavior, collection initialization, collection site ownership, category thread-list acquisition, direct thread-detail acquisition, parser diagnostics, cached category thread lists, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, and adjacent forum workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private forum data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumThreadCollection.find(id)` is a local lookup over already loaded category thread inventories. The caller search key already has type validation, and stored thread rows should be held to the same retained-ID contract before comparison. Validating stored IDs prevents corrupted local state from matching through Python's bool/float equality rules or disappearing as an ordinary not-found result, while preserving valid zero IDs, existing absent integer behavior, and all parser/network behavior.

## Local Evidence

- Existing local drafts covered category thread-list fetch retry behavior, direct thread-detail fetch retry behavior, duplicate direct-thread reuse, parser diagnostics, response-body diagnostics, collection search-key type validation, collection constructor validation, collection parent-site validation, direct thread scalar type validation, direct thread ID range validation, posts-cache ownership, and retained owner-ID validation in cached thread-post surfaces.
- None of those drafts covered malformed retained stored `ForumThread.id` values inside `ForumThreadCollection.find(...)` because the scan still compared `thread.id == id` directly.
- The focused RED failure showed booleans and floats could be accepted as stored thread IDs when they compared equal to lookup integers, while `None`, strings, lists, and negative IDs could be misreported as ordinary not-found results.
- This slice only validates retained stored thread IDs at the loaded collection lookup comparison boundary. It does not change category thread-list acquisition, direct thread-detail acquisition, parser field extraction, cached category thread collections, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, forum post behavior, forum category behavior, forum post revision behavior, page behavior, site behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, forum source text, thread titles from private forums, thread descriptions from private forums, page source text, private messages, private forum content, and private site data out of upstream discussion.

## Additional Notes

The change intentionally reuses `_validate_thread_id(...)` only for stored collection rows. It does not add caller search-key range validation in `ForumThreadCollection.find(...)`, preserving the prior lookup-surface scope from Issue 379 and the explicit Issue 642 note that direct `ForumThread.id` range validation did not change collection lookup semantics.
