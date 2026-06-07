# PR Draft: Validate Forum Thread Posts Cache Ownership

## Summary

`ForumThread._posts` is the optional cached `ForumPostCollection` behind the public `ForumThread.posts` property. Issue 504 validated the direct cache shape and non-post entries, and Issue 592 validated that `ForumPostCollection` constructor entries belong to the collection thread. One direct cache ownership gap remained: a caller could construct `ForumThread(..., _posts=ForumPostCollection(other_thread, []))`, or mutate a valid same-thread collection to contain a `ForumPost` retained from another thread before passing it into the `ForumThread` constructor. The constructed thread then returned a cached post collection whose parent state or entries described a different thread.

This change validates cached post ownership during `ForumThread.__post_init__` after the existing `_posts` type and entry checks. Non-null cached collections now compare the collection parent thread, when present, and every cached post's retained thread against the constructing thread by thread ID and the same retained `Site` object. Mismatches raise `ValueError("thread.posts must belong to the thread")` before the malformed cache is stored. Valid same-thread cached collections, `_posts=None`, existing cache type diagnostics, malformed cache-entry diagnostics, lazy `ForumThread.posts`, thread post-list acquisition, duplicate cached thread-post reuse, forum post source/edit behavior, and adjacent forum workflows remain unchanged.

## Outcome

Directly constructed `ForumThread` objects reject cached post collections that belong to another thread before the public `thread.posts` property can return cross-thread cached state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free forum inventories, generated discussion migration ledgers, moderation tooling, translation review tooling, cached forum records, local fixtures, generated adapters, or serialized and rehydrated `ForumThread` objects.

## Current Evidence

Prior cache and ownership drafts establish the surrounding behavior. [504-pr-validate-forum-thread-posts-cache.md](504-pr-validate-forum-thread-posts-cache.md) validates the optional `_posts` cache object shape and non-post entries, and explicitly leaves collection ownership matching between `ForumPostCollection.thread` and the newly constructed `ForumThread` outside scope. [592-pr-validate-forum-post-collection-thread-ownership.md](592-pr-validate-forum-post-collection-thread-ownership.md) validates the public `ForumPostCollection(thread, posts=...)` constructor's own thread/post ownership. [585-pr-validate-forum-post-source-post-thread-ownership.md](585-pr-validate-forum-post-source-post-thread-ownership.md), [589-pr-reject-mixed-site-forum-post-batches.md](589-pr-reject-mixed-site-forum-post-batches.md), and [594-pr-validate-forum-post-revisions-cache-ownership.md](594-pr-validate-forum-post-revisions-cache-ownership.md) establish the retained-parent validation pattern for later forum post/revision surfaces. The remaining gap was direct `ForumThread(_posts=...)` construction with a valid `ForumPostCollection` object whose retained parent state did not match the constructed thread.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 504. Issue 504 rejects malformed `_posts` values and collections containing non-`ForumPost` entries; it does not compare a cached collection's parent thread or cached post parent threads with the `ForumThread` being constructed.

This is not a duplicate of Issue 592. Issue 592 validates `ForumPostCollection.__init__` before a collection stores mismatched entries. This slice covers a separate parent cache slot: a valid collection built for another thread can still be passed as `ForumThread._posts`, and a valid collection can be mutated after construction before direct `ForumThread` construction.

This is not a duplicate of Issue 594. Issue 594 applies the same direct cache-slot ownership rule to `ForumPost._revisions`; this slice applies it one level higher to `ForumThread._posts`.

No upstream issue was filed from this local workspace.

## Changes

- Add cached post ownership validation for direct `ForumThread(...)` construction.
- Reject cached `ForumPostCollection` objects whose own `thread` belongs to a different thread or site.
- Reject cached post entries whose retained `post.thread` belongs to a different thread or site, including post-construction collection mutations.
- Preserve `_posts=None`, valid same-thread cached collections, existing malformed-cache diagnostics, lazy post acquisition, thread post-list acquisition, cached duplicate thread-post reuse, forum post source/edit behavior, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached forum-thread post ownership integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThread(_posts=ForumPostCollection(other_thread, []))` must reject the different cached collection parent with `ValueError("thread.posts must belong to the thread")` before storing cached state. |
| R2 | `ForumThread(_posts=collection_mutated_with_post_from_other_thread)` must reject the different retained post parent with the same diagnostic before storing cached state. |
| R3 | Valid same-thread cached post collections must remain accepted and `thread.posts` must return the cached collection without triggering acquisition. |
| R4 | Existing malformed `_posts` value and non-post entry diagnostics from Issue 504 must remain unchanged. |
| R5 | Existing lazy post acquisition, direct and batched `ForumPostCollection` acquisition, duplicate cached thread-post reuse, forum post source/edit behavior, and adjacent forum category/thread/post/revision workflows must remain unchanged. |
| R6 | Focused RED/GREEN, forum-thread constructor coverage, forum-thread module coverage, adjacent forum module coverage, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Cached collection parent threads from another logical thread fail at the constructor boundary. | `TestForumThreadBasic.test_init_rejects_posts_cache_from_different_thread` failed RED with `DID NOT RAISE`, then passed GREEN after `ForumThread.__post_init__` called the ownership preflight. | Accepting `ForumPostCollection(other_thread, [])`, storing the mismatched cache, or deferring the failure to `thread.posts` rejects this local completion claim. | `ForumThread._posts` cache parent state | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Valid cached collections that are mutated with another thread's post fail at the same constructor boundary. | `TestForumThreadBasic.test_init_rejects_posts_cache_entry_from_different_thread` failed RED with `DID NOT RAISE`, then passed GREEN after each cached post's retained thread was checked. | Accepting a same-parent collection with a different-thread post entry, returning it through `thread.posts`, or relying only on later source/edit-time guards rejects this local completion claim. | `ForumThread._posts` cache entry ownership | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R3 | Valid same-thread caches remain a cache hit. | `TestForumThreadBasic.test_init_accepts_valid_posts_cache` passed in the focused cache group and asserts `thread.posts is posts`. | Triggering post acquisition, replacing the cached object, or rejecting a valid same-thread empty collection rejects this local completion claim. | `ForumThread.posts` cache access | `tests/unit/test_forum_thread.py` |
| R4 | Existing malformed-cache diagnostics remain stable. | The focused cache group also passed `test_init_rejects_malformed_posts_cache` and `test_init_rejects_malformed_posts_cache_entries`. | Changing Issue 504 diagnostics, accepting non-collection values, or accepting non-post cache entries rejects this local completion claim. | `ForumThread` constructor cache shape validation | `tests/unit/test_forum_thread.py` |
| R5 | Adjacent forum workflows remain green. | `tests/unit/test_forum_thread.py` passed 149 tests, adjacent forum category/thread/post/revision coverage passed 538 tests, and full unit coverage passed 2705 tests. | Regressing lazy `ForumThread.posts`, thread post-list acquisition, duplicate cached thread-post reuse, forum post source/edit workflows, parser-created posts, forum post revision behavior, or forum category behavior rejects this local completion claim. | Forum workflows | `tests/unit` |
| R6 | Repository quality gates pass in the local dependency environment. | Full `ruff check`, `ruff format --check`, `mypy`, `pyright`, and `git diff --check` passed after formatting. Full mypy found no issues in 87 source files; full pyright reported 0 errors, 0 warnings, and 0 informations; full format saw 87 files already formatted. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live auth material or private site state is needed to prove the behavior. | The regressions use synthetic valid `ForumThread` and `ForumPost` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page/forum content from real sites, forum post source text from real sites, revision HTML from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `d3c7ae7 fix(forum_thread): validate posts cache ownership`.

- RED cached collection parent ownership: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_posts_cache_from_different_thread -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused parent ownership regression: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_posts_cache_from_different_thread tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_accepts_valid_posts_cache -q` passed 2 tests after the collection-parent branch fix.
- RED cached post entry ownership: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_posts_cache_entry_from_different_thread -q` failed before the entry branch fix with `DID NOT RAISE`.
- GREEN focused cache coverage: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_posts_cache_from_different_thread tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_posts_cache_entry_from_different_thread tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_accepts_valid_posts_cache tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_posts_cache tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_posts_cache_entries -q` passed 9 tests.
- Constructor coverage: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic -q` passed 51 tests.
- Forum thread module coverage: `uv run pytest tests/unit/test_forum_thread.py -q` passed 149 tests.
- Adjacent forum category/thread/post/revision tests: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 538 tests.
- `uv run pytest tests/unit -q` passed 2705 tests.
- `uv run ruff format` left 87 files unchanged.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThread(_posts=ForumPostCollection(other_thread, []))` raises `ValueError("thread.posts must belong to the thread")` before storing cached state.
- `ForumThread(_posts=same_thread_collection_mutated_with_other_thread_post)` raises the same diagnostic before storing cached state.
- `ForumThread(_posts=ForumPostCollection(same_thread, []))` remains valid and `thread.posts` returns that cached object without a lookup.
- Existing `_posts=None`, malformed `_posts` object rejection, non-post cache-entry rejection, lazy post acquisition, direct and batched thread post-list acquisition, cached duplicate thread-post reuse, forum post source/edit behavior, and adjacent forum category/thread/post/revision behavior remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumThread._posts` is a direct cache slot for browser-free forum reads and generated discussion ledgers. If the cached collection or one of its retained post entries belongs to another thread, callers can read coherent-looking but cross-thread post state through `thread.posts`. Constructor-time ownership validation keeps direct fixtures, rehydrated records, and generated caches from silently storing another thread's post list under the current thread.

## Local Evidence, Not For Upstream Paste

- The first RED failure showed `ForumThread` could accept an empty `ForumPostCollection` whose collection parent was another thread.
- The second RED failure showed a same-thread collection mutated after construction with another thread's valid post could still be stored as `ForumThread._posts`.
- Existing local drafts covered thread post-list acquisition, parser diagnostics, response diagnostics, optional `_posts` cache shape, collection constructor ownership, retained thread/site validation, post source ownership, and mixed-site post batches, but did not validate that the cached post collection stored on a `ForumThread` belongs to that `ForumThread`.
- This slice only validates direct cached post ownership during `ForumThread` construction. It does not change post-list parsing, collection constructor semantics, public post lookup, lazy cache invalidation, forum post source/edit behavior, live site behavior, authentication semantics, or parser selectors.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page/forum source text from real sites, revision HTML from real sites, and private site data out of upstream discussion.

## Additional Notes

The ownership check intentionally matches the adjacent collection ownership style: thread ID and the same retained `Site` object must match. This allows duplicate `ForumThread` objects representing the same thread on the same site, while rejecting different-thread and different-site cached post state. Empty no-parent post collections remain valid collection objects; direct constructor cache validation rejects only ownership evidence that points away from the constructing thread.
