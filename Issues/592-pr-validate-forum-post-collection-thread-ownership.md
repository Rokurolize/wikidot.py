# PR Draft: Validate Forum Post Collection Thread Ownership

## Summary

`ForumPostCollection` validates explicit collection parent-thread types, validates its `posts` container and entries, each `ForumPost` validates its own retained `thread`, and `get_post_sources()` revalidates mutated target-post ownership before source-form requests. The public collection constructor still did not ensure contained posts all belonged to the effective collection thread. A caller could construct `ForumPostCollection(thread_a, [post_from_thread_b])`; a caller could also rely on parent inference with `ForumPostCollection(thread=None, posts=[post_from_thread_a, post_from_thread_b])`, which inferred `thread_a` from the first post while retaining a valid post from another thread.

This change validates post entry ownership at the public `ForumPostCollection.__init__` boundary after entry validation and effective thread selection but before list state is stored. Posts whose retained `post.thread` does not match the collection thread and site now raise `ValueError("posts must belong to the collection thread")`. Valid explicit same-thread collections, valid inferred same-thread collections, empty no-parent collections, `find(...)`, forum post-list parsing, lazy `ForumThread.posts`, source acquisition, edit workflows, and adjacent forum category/thread/revision workflows remain unchanged.

## Outcome

Forum post collections reject different-thread post entries before local collection state can represent one thread while storing another thread's posts.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum post inventories, generated forum migration or moderation ledgers, cached thread post lists, lazy `ForumThread.posts`, post source capture, post edit workflows, forum revision capture, or local tests that construct `ForumPostCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post-list reads, cached thread post lists, source acquisition, edit workflows, and generated forum ledgers as practical workflow surfaces. Existing drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [228-pr-cache-direct-thread-post-acquisition.md](228-pr-cache-direct-thread-post-acquisition.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [474-pr-validate-forum-post-collection-thread-field.md](474-pr-validate-forum-post-collection-thread-field.md), [504-pr-validate-forum-thread-posts-cache.md](504-pr-validate-forum-thread-posts-cache.md), [537-pr-preserve-empty-forum-post-parent.md](537-pr-preserve-empty-forum-post-parent.md), [576-pr-validate-forum-post-source-collection-thread.md](576-pr-validate-forum-post-source-collection-thread.md), [577-pr-validate-forum-post-source-thread-site.md](577-pr-validate-forum-post-source-thread-site.md), [584-pr-reject-mixed-site-forum-post-list-batches.md](584-pr-reject-mixed-site-forum-post-list-batches.md), [585-pr-validate-forum-post-source-target-thread.md](585-pr-validate-forum-post-source-target-thread.md), [590-pr-validate-forum-thread-collection-site-ownership.md](590-pr-validate-forum-thread-collection-site-ownership.md), and [591-pr-validate-forum-category-collection-site-ownership.md](591-pr-validate-forum-category-collection-site-ownership.md) establish post-list acquisition, source acquisition, parser diagnostics, cache behavior, collection shape, retained parent validation, and adjacent collection ownership as active operational boundaries.

This slice is not a duplicate of those issues. Issue 474 validates explicit non-`None` `ForumPostCollection.thread` field type while preserving inference and empty no-parent semantics. Issue 422 validates the collection's `posts` container and entries. Issue 446 validates each `ForumPost.thread` field type. Issue 504 validates a `ForumThread` object's optional `_posts` cache slot. Issue 537 preserves empty `thread=None` collection readability. Issue 585 validates target-post ownership at source-acquisition time for post-construction mutated collections. Issues 590 and 591 cover forum thread/category collections, not forum post collections. None validates a valid `ForumPost` entry whose retained `post.thread` is individually valid but does not match the collection thread selected explicitly or inferred from the first post.

No upstream issue was filed from this local workspace.

## Changes

- Add a forum-post collection ownership preflight at `ForumPostCollection.__init__`.
- Reject explicit different-thread post entries with `ValueError("posts must belong to the collection thread")`.
- Reject inferred-parent mixed-thread post collections with the same diagnostic.
- Keep the source-acquisition mutation guard by updating its test to append a different-thread post after constructing a valid empty collection.
- Preserve explicit valid parents, inferred valid parents, empty no-parent collections, valid post lists, lookup, post-list parsing, lazy `ForumThread.posts`, source acquisition, edit workflows, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public collection constructor behavior hardening
- Forum post parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostCollection(thread_a, [post_from_thread_b])` must reject the different-thread post with `ValueError("posts must belong to the collection thread")` before storing collection list state. |
| R2 | `ForumPostCollection(thread=None, posts=[post_from_thread_a, post_from_thread_b])` must infer `thread_a` from the first post and reject the second different-thread post with the same diagnostic before storing collection list state. |
| R3 | Valid explicit same-thread post collections, valid inferred same-thread post collections, and empty no-parent collections must remain valid. |
| R4 | Existing source-time mutation validation, `find(...)`, post-list acquisition, parser diagnostics, cached duplicate thread-post reuse, lazy `ForumThread.posts`, source acquisition, edit workflows, and adjacent forum category/thread/revision workflows must remain unchanged. |
| R5 | Focused RED/GREEN, forum-post module coverage, adjacent forum module coverage, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Explicit different-thread post entries fail at the public collection constructor boundary. | `TestForumPostCollectionInit.test_init_rejects_post_from_different_thread` failed RED with `DID NOT RAISE`, then passed GREEN with `ValueError("posts must belong to the collection thread")`. | Accepting the different-thread post, storing a collection for `thread_a` that contains a post retained from `thread_b`, or deferring failure to source/cache code rejects this local completion claim. | `ForumPostCollection.__init__` | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Inferred-parent mixed-thread post entries fail at the same constructor boundary. | `TestForumPostCollectionInit.test_init_rejects_mixed_thread_posts_when_thread_is_inferred` failed RED with `DID NOT RAISE`, then passed GREEN with the same diagnostic. | Inferring `thread_a` from the first post while storing a post retained from `thread_b`, accepting mixed inferred collections, or rejecting all inferred collections rejects this local completion claim. | `ForumPostCollection.__init__` | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Valid post collection construction semantics stay green. | `TestForumPostCollectionInit` passed 25 tests and `tests/unit/test_forum_post.py` passed 160 tests after the ownership preflight. | Rejecting valid same-thread explicit collections, valid same-thread inferred collections, empty no-parent collections, or normal thread inference rejects this local completion claim. | Forum post collections | `tests/unit/test_forum_post.py` |
| R4 | Existing source-time mutation validation and adjacent forum workflows remain green. | `TestForumPostCollectionGetSources.test_get_post_sources_rejects_post_from_different_thread_before_fetch` now constructs a valid empty collection and appends the different-thread post after construction; adjacent forum category/thread/post/revision coverage passed 532 tests, and the full unit suite passed 2699 tests. | Losing the post-construction mutation guard, regressing post-list acquisition, parser diagnostics, cached duplicate thread-post reuse, lazy `ForumThread.posts`, source acquisition, edit workflows, forum thread/category behavior, or forum post revision behavior rejects this local completion claim. | Forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | Repository quality gates pass in the local dependency environment. | Full `ruff check`, `ruff format --check`, `mypy`, full `pyright`, and `git diff --check` passed. Full pyright reported 0 errors, 0 warnings, and 0 informations; full format saw 87 files already formatted; full mypy found no issues in 87 source files. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regressions use synthetic valid `ForumThread` and `ForumPost` objects; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page/forum content from real sites, post source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `8d8fbad fix(forum_post): validate post collection thread ownership`.

- RED explicit target-thread ownership: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_init_rejects_post_from_different_thread -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused explicit ownership regression: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_init_rejects_post_from_different_thread -q` passed 1 test.
- RED inferred target-thread ownership: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_init_rejects_mixed_thread_posts_when_thread_is_inferred -q` failed before the inferred-branch fix with `DID NOT RAISE`.
- GREEN focused ownership coverage: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_init_rejects_post_from_different_thread tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_init_rejects_mixed_thread_posts_when_thread_is_inferred -q` passed 2 tests.
- Constructor coverage: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionInit -q` passed 25 tests.
- Forum post module coverage: `uv run pytest tests/unit/test_forum_post.py -q` passed 160 tests.
- Adjacent forum category/thread/post/revision tests: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 532 tests.
- `uv run pytest tests/unit -q` passed 2699 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPostCollection(thread_a, [post_from_thread_b])` raises `ValueError("posts must belong to the collection thread")` before storing collection list state.
- `ForumPostCollection(thread=None, posts=[post_from_thread_a, post_from_thread_b])` raises the same diagnostic after inferring the first post's thread and before storing collection list state.
- `ForumPostCollection(thread=<valid ForumThread>, posts=[])`, `ForumPostCollection(thread=<valid ForumThread>, posts=[same_thread_post])`, `ForumPostCollection(thread=None, posts=[same_thread_post])`, and `ForumPostCollection(thread=None, posts=[])` remain valid.
- Existing source-time mutation validation, `find(...)`, post-list acquisition, parser diagnostics, cached duplicate thread-post reuse, lazy `ForumThread.posts`, source acquisition, edit workflows, and adjacent forum category/thread/revision behavior remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPostCollection.thread` and each retained `ForumPost.thread` should describe the same owning thread for browser-free forum post inventories, generated moderation ledgers, migration audits, cached thread post lists, lazy source capture, edit workflows, and downstream revision traversal. Parser paths already create posts from the owning thread, and same-thread post-list helpers already preserve post ownership; constructor ownership validation keeps mismatched rehydrated records, fixtures, or generated ledgers from silently carrying another thread's posts under the collection thread.

## Local Evidence, Not For Upstream Paste

- The explicit RED failure showed a valid post from another thread could be accepted by `ForumPostCollection(thread, [post])` without ownership rejection.
- The inferred RED failure showed `ForumPostCollection(thread=None, posts=[post_from_thread_a, post_from_thread_b])` could infer a collection thread from the first post while retaining another thread's post.
- Existing local drafts covered post-list acquisition, parser diagnostics, response-body diagnostics, lookup validation, collection posts/entry validation, direct post thread validation, explicit collection-thread validation, empty no-parent handling, source-time retained parent validation, source-time target ownership validation, and mixed-site post-list batching, but did not compare each valid `ForumPost.thread` to the effective collection thread during construction.
- This slice only validates forum-post collection target-thread ownership at collection initialization. It does not change post-list parsing, collection lookup semantics, lazy thread-post cache invalidation, source response parsing, edit behavior, revision acquisition, live site behavior, authentication semantics, or parser selectors.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page/forum source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The ownership check intentionally requires both matching thread ID and the same retained site object. This matches the existing source-time target ownership preflight and allows duplicate thread objects representing the same thread on the same `Site` object, while still rejecting different-thread and different-site posts. It does not coerce thread-like objects, compare by title, infer a collection thread from a later post, validate a thread's cached post collection ownership, verify remote thread membership, or change live client authentication; those are separate parser, lookup, cache, and workflow concerns.
