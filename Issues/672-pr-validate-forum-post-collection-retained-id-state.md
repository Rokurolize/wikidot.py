# PR Draft: Validate Forum Post Collection Retained ID State

## Summary

`ForumPostCollection.find(id)` validates malformed caller-provided search-key types before scanning stored posts, but the scan still compared each retained `post.id` directly against the search ID. After local fixture, serialized, or rehydrated forum-post state has been mutated incorrectly, booleans and floats can satisfy Python equality against integer post IDs, while `None`, strings, lists, and negative IDs are treated as ordinary not-found misses instead of corrupted retained post-ID state.

This change validates each stored post's retained ID with the existing `_validate_post_id(...)` helper before comparing it to the caller search ID. Malformed retained post IDs now raise `ValueError("id must be an integer")`, negative retained post IDs now raise `ValueError("id must be non-negative")`, valid zero-ID lookup remains accepted, existing absent integer lookup behavior remains unchanged, and no forum post fetch, parser, cache, source, revision, edit, or live Wikidot behavior changes.

## Outcome

Loaded forum-post collections can no longer return a post by Python's loose numeric equality or hide corrupted retained post IDs behind an ordinary not-found result.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free forum indexes, moderation ledgers, translation review tooling, migration records, cached thread-post scans, local fixtures, or serialized and rehydrated `ForumPostCollection` objects.

## Current Evidence

Local rollout-backed drafts already established forum-post reads and post identity as practical boundaries. [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), [235-pr-forum-post-id-parse-context.md](235-pr-forum-post-id-parse-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [474-pr-validate-forum-post-collection-thread-field.md](474-pr-validate-forum-post-collection-thread-field.md), [504-pr-validate-forum-thread-posts-cache.md](504-pr-validate-forum-thread-posts-cache.md), [592-pr-validate-forum-post-collection-thread-ownership.md](592-pr-validate-forum-post-collection-thread-ownership.md), [641-pr-validate-non-negative-forum-post-ids.md](641-pr-validate-non-negative-forum-post-ids.md), [665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md](665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md), [666-pr-validate-forum-post-revisions-cache-retained-id-state.md](666-pr-validate-forum-post-revisions-cache-retained-id-state.md), and [667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md](667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md) cover forum-post acquisition, source acquisition, parser diagnostics, response diagnostics, lookup search-key type validation, collection shape, direct ID type/range, thread ownership, cached thread-post collections, and retained cache or revision owner identity.

This slice is not a duplicate of those drafts. Issue 378 validates caller-provided `ForumPostCollection.find(id=...)` search-key types before scanning stored posts, but it does not validate retained IDs already stored inside the collection. Issues 460 and 641 validate direct `ForumPost(id=...)` construction, but they cannot cover a valid post whose ID is corrupted after construction and then reused in a collection. Issues 665, 666, and 667 validate retained owner IDs in cached thread-post, post-revision, and revision-collection ownership paths, not loaded `ForumPostCollection.find(...)` lookup rows. Issue 641 explicitly left `ForumPostCollection.find(...)` lookup semantics unchanged.

## Related Issue / Non-Duplicate Analysis

Builds directly on [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [474-pr-validate-forum-post-collection-thread-field.md](474-pr-validate-forum-post-collection-thread-field.md), [592-pr-validate-forum-post-collection-thread-ownership.md](592-pr-validate-forum-post-collection-thread-ownership.md), [641-pr-validate-non-negative-forum-post-ids.md](641-pr-validate-non-negative-forum-post-ids.md), [665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md](665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md), [666-pr-validate-forum-post-revisions-cache-retained-id-state.md](666-pr-validate-forum-post-revisions-cache-retained-id-state.md), and [667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md](667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate each stored `ForumPost.id` before `ForumPostCollection.find(id)` compares it to the search key.
- Reject retained stored post IDs such as `None`, `True`, `False`, `"5001"`, `5001.0`, and `[]` with `ValueError("id must be an integer")`.
- Reject retained stored post IDs such as `-1` with `ValueError("id must be non-negative")`.
- Preserve valid zero-ID lookup, valid matching lookup, existing absent integer lookup behavior, malformed caller search-key type diagnostics, collection thread ownership, post-list acquisition, source acquisition, parser diagnostics, cached thread-post lists, lazy `ForumThread.posts`, and adjacent forum workflows.
- Do not add caller search-key range validation in this slice.

## Type Of Change

- Input validation
- Retained forum-post ID hardening
- Loaded collection lookup integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostCollection.find(id)` must reject retained stored `post.id` values such as `None`, `True`, `False`, `"5001"`, `5001.0`, and `[]` with `ValueError("id must be an integer")` before comparison. |
| R2 | `ForumPostCollection.find(id)` must reject retained stored `post.id=-1` with `ValueError("id must be non-negative")` before comparison. |
| R3 | Valid lookup where the stored post ID and search ID are both `0` must remain accepted. |
| R4 | Existing caller search-key type validation, valid matching lookup, existing absent integer lookup behavior, collection initialization, collection thread ownership, post-list acquisition, source acquisition, parser diagnostics, cached thread-post lists, lazy `ForumThread.posts`, and adjacent forum workflows must remain green. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-post module coverage, adjacent forum/site coverage, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained stored post IDs fail before lookup comparison. | `test_find_rejects_post_with_malformed_retained_ids` failed RED for six malformed values: booleans and `5001.0` could be accepted through Python equality, while `None`, `"5001"`, and `[]` returned ordinary misses. The test passed GREEN after stored post ID validation. | Accepting booleans/floats, returning ordinary `None` misses for corrupted IDs, coercing values, or returning a post from corrupted retained ID state rejects this local completion claim. | Stored `ForumPost.id` during collection lookup | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Negative retained stored post IDs fail before lookup comparison. | `test_find_rejects_post_with_negative_retained_id` failed RED with an ordinary not-found result, then passed GREEN after stored post ID range validation. | Treating negative stored IDs as ordinary misses, accepting them, matching them, or coercing them rejects this local completion claim. | Stored `ForumPost.id` during collection lookup | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Zero remains a valid retained post ID for lookup. | `test_find_accepts_post_with_zero_retained_id` passed RED and GREEN. | Rejecting `0`, treating it as missing, coercing it to false, or changing returned post identity rejects this local completion claim. | Forum-post collection lookup semantics | `tests/unit/test_forum_post.py` |
| R4 | Existing compatible behavior remains compatible. | Focused GREEN coverage passed 8 tests, `tests/unit/test_forum_post.py` passed 204 tests, adjacent forum/site coverage passed 1023 tests, and full unit passed 3197 tests. | Regressing caller search-key type validation, valid matching lookup, existing absent integer lookup behavior, collection initialization, collection thread ownership, post-list acquisition, source acquisition, parser diagnostics, cached thread-post lists, lazy `ForumThread.posts`, forum category/thread/revision behavior, site workflows, or any unit test rejects this local completion claim. | Forum-post collection and adjacent forum workflows | `tests/unit/test_forum_post.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit/test_site.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic forum-post objects and local unit helpers only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, forum source text, post titles or bodies from private forums, private forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, temporary pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `b97f601 fix(forum_post): validate collection retained ids`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_find_accepts_post_with_zero_retained_id tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_find_rejects_post_with_malformed_retained_ids tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_find_rejects_post_with_negative_retained_id -q` collected 8 tests: 7 retained stored post-ID cases failed before the fix, and the zero-ID compatibility guard passed.
- GREEN: the same focused command passed 8 tests after stored post IDs were validated before collection lookup comparison.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left both files unchanged.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 204 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_site.py -q` passed 1023 tests.
- `uv run pytest tests/unit -q` passed 3197 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPostCollection.find(5001)` raises `ValueError("id must be an integer")` when a stored post's retained `post.id` is `None`, `"5001"`, or `[]`.
- `ForumPostCollection.find(1)`, `find(0)`, and `find(5001)` raise `ValueError("id must be an integer")` when stored retained IDs are `True`, `False`, or `5001.0` before they can match through Python equality.
- `ForumPostCollection.find(5001)` raises `ValueError("id must be non-negative")` when a stored post's retained `post.id` is `-1`.
- `ForumPostCollection.find(0)` still returns a post whose retained ID is valid integer `0`.
- Existing malformed search-key type rejection, matching lookup, absent integer lookup behavior, collection initialization, collection thread ownership, post-list acquisition, source acquisition, parser diagnostics, cached thread-post lists, lazy `ForumThread.posts`, and adjacent forum workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private forum data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPostCollection.find(id)` is a local lookup over already loaded thread-post inventories. The caller search key already has type validation, and stored post rows should be held to the same retained-ID contract before comparison. Validating stored IDs prevents corrupted local state from matching through Python's bool/float equality rules or disappearing as an ordinary not-found result, while preserving valid zero IDs, existing absent integer behavior, and all parser/network behavior.

## Local Evidence

- Existing local drafts covered forum-post fetch retry behavior, duplicate cached post/source reuse, parser row scoping, response-body diagnostics, parser ID diagnostics, collection search-key type validation, collection constructor validation, collection parent-thread validation, direct post scalar type validation, direct post ID range validation, cache reuse, and retained owner-ID validation in cached thread-post and revision surfaces.
- None of those drafts covered malformed retained stored `ForumPost.id` values inside `ForumPostCollection.find(...)` because the scan still compared `post.id == id` directly.
- The focused RED failure showed booleans and floats could be accepted as stored post IDs when they compared equal to lookup integers, while `None`, strings, lists, and negative IDs could be misreported as ordinary not-found results.
- This slice only validates retained stored post IDs at the loaded collection lookup comparison boundary. It does not change post-list acquisition, parser field extraction, cached post collections, source acquisition, revision acquisition, edit behavior, lazy `ForumThread.posts`, forum category/thread/revision behavior, page behavior, site behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, forum source text, post titles from private forums, post bodies from private forums, page source text, private messages, private forum content, and private site data out of upstream discussion.

## Additional Notes

The change intentionally reuses `_validate_post_id(...)` only for stored collection rows. It does not add caller search-key range validation in `ForumPostCollection.find(...)`, preserving the prior lookup-surface scope from Issue 378 and the explicit Issue 641 note that direct `ForumPost.id` range validation did not change collection lookup semantics.
