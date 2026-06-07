# PR Draft: Validate Forum Post Revisions Cache Ownership

## Summary

`ForumPost._revisions` is the optional cached `ForumPostRevisionCollection` behind the public `ForumPost.revisions` property. Issue 507 validated the direct cache shape and non-revision entries, and Issue 593 validated that `ForumPostRevisionCollection` constructor entries belong to the collection post. One direct cache ownership gap remained: a caller could construct `ForumPost(..., _revisions=ForumPostRevisionCollection(other_post, []))`, or mutate a valid same-post collection to contain a `ForumPostRevision` retained from another post before passing it into the `ForumPost` constructor. The constructed post then returned a cached revision collection whose parent state or entries described a different post.

This change validates cached revision ownership during `ForumPost.__post_init__` after the existing `_revisions` type and entry checks. Non-null cached collections now compare the collection parent post, when present, and every cached revision's retained post against the constructing post by post ID, thread ID, and the same retained `Site` object. Mismatches raise `ValueError("post.revisions must belong to the post")` before the malformed cache is stored. Valid same-post cached collections, `_revisions=None`, existing cache type diagnostics, malformed cache-entry diagnostics, lazy `ForumPost.revisions`, direct and batched revision acquisition, duplicate cached revision reuse, revision HTML acquisition, and adjacent forum workflows remain unchanged.

## Outcome

Directly constructed `ForumPost` objects reject cached revision collections that belong to another post before the public `post.revisions` property can return cross-post cached state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free forum edit-history inventories, generated discussion migration ledgers, moderation tooling, translation review tooling, cached forum records, local fixtures, generated adapters, or serialized and rehydrated `ForumPost` objects.

## Current Evidence

Prior cache and ownership drafts establish the surrounding behavior. [507-pr-validate-forum-post-revisions-cache.md](507-pr-validate-forum-post-revisions-cache.md) validates the optional `_revisions` cache object shape and non-revision entries. [593-pr-validate-forum-post-revision-collection-post-ownership.md](593-pr-validate-forum-post-revision-collection-post-ownership.md) validates the public `ForumPostRevisionCollection(post, revisions=...)` constructor's own post/revision ownership. [580-pr-validate-forum-post-revision-thread.md](580-pr-validate-forum-post-revision-thread.md), [581-pr-validate-forum-post-revision-html-thread.md](581-pr-validate-forum-post-revision-html-thread.md), [582-pr-validate-forum-post-revision-html-target-post-thread.md](582-pr-validate-forum-post-revision-html-target-post-thread.md), and [583-pr-reject-mixed-site-forum-post-revision-batches.md](583-pr-reject-mixed-site-forum-post-revision-batches.md) establish retained-parent and target-site validation before later revision-list or HTML request work. The remaining gap was direct `ForumPost(_revisions=...)` construction with a valid `ForumPostRevisionCollection` object whose retained parent state did not match the constructed post.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 507. Issue 507 rejects malformed `_revisions` values and collections containing non-`ForumPostRevision` entries; it does not compare a cached collection's parent post or cached revision parent posts with the `ForumPost` being constructed.

This is not a duplicate of Issue 593. Issue 593 validates `ForumPostRevisionCollection.__init__` before a collection stores mismatched entries. This slice covers a separate parent cache slot: a valid collection built for another post can still be passed as `ForumPost._revisions`, and a valid collection can be mutated after construction before direct `ForumPost` construction.

This is not a duplicate of Issues 580 through 583. Those issues validate later acquisition and HTML request boundaries. This slice rejects cross-post cached revision state at the `ForumPost` constructor boundary before lazy access can expose it.

No upstream issue was filed from this local workspace.

## Changes

- Add cached revision ownership validation for direct `ForumPost(...)` construction.
- Reject cached `ForumPostRevisionCollection` objects whose own `post` belongs to a different post, thread, or site.
- Reject cached revision entries whose retained `revision.post` belongs to a different post, thread, or site, including post-construction collection mutations.
- Preserve `_revisions=None`, valid same-post cached collections, existing malformed-cache diagnostics, lazy revision acquisition, direct and batched revision acquisition, cached duplicate revision reuse, revision HTML acquisition, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached forum-post revision ownership integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPost(_revisions=ForumPostRevisionCollection(other_post, []))` must reject the different cached collection parent with `ValueError("post.revisions must belong to the post")` before storing cached state. |
| R2 | `ForumPost(_revisions=collection_mutated_with_revision_from_other_post)` must reject the different retained revision parent with the same diagnostic before storing cached state. |
| R3 | Valid same-post cached revision collections must remain accepted and `post.revisions` must return the cached collection without triggering acquisition. |
| R4 | Existing malformed `_revisions` value and non-revision entry diagnostics from Issue 507 must remain unchanged. |
| R5 | Existing lazy revision acquisition, direct and batched `ForumPostRevisionCollection` acquisition, duplicate cached revision reuse, revision HTML acquisition, forum post source/edit behavior, and adjacent forum category/thread/post/revision workflows must remain unchanged. |
| R6 | Focused RED/GREEN, forum-post constructor coverage, forum-post module coverage, adjacent forum module coverage, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Cached collection parent posts from another logical post fail at the constructor boundary. | `TestForumPostBasic.test_init_rejects_revisions_cache_from_different_post` failed RED with `DID NOT RAISE`, then passed GREEN after `ForumPost.__post_init__` called the ownership preflight. | Accepting `ForumPostRevisionCollection(other_post, [])`, storing the mismatched cache, or deferring the failure to `post.revisions` rejects this local completion claim. | `ForumPost._revisions` cache parent state | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Valid cached collections that are mutated with another post's revision fail at the same constructor boundary. | `TestForumPostBasic.test_init_rejects_revisions_cache_entry_from_different_post` failed RED with `DID NOT RAISE`, then passed GREEN after each cached revision's retained post was checked. | Accepting a same-parent collection with a different-post revision entry, returning it through `post.revisions`, or relying only on later HTML/read-time guards rejects this local completion claim. | `ForumPost._revisions` cache entry ownership | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Valid same-post caches remain a cache hit. | `TestForumPostBasic.test_init_accepts_valid_revisions_cache` passed in the focused cache group and asserts `post.revisions is revisions`. | Triggering revision acquisition, replacing the cached object, or rejecting a valid same-post empty collection rejects this local completion claim. | `ForumPost.revisions` cache access | `tests/unit/test_forum_post.py` |
| R4 | Existing malformed-cache diagnostics remain stable. | The focused cache group also passed `test_init_rejects_malformed_revisions_cache` and `test_init_rejects_malformed_revisions_cache_entries`. | Changing Issue 507 diagnostics, accepting non-collection values, or accepting non-revision cache entries rejects this local completion claim. | `ForumPost` constructor cache shape validation | `tests/unit/test_forum_post.py` |
| R5 | Adjacent forum workflows remain green. | `tests/unit/test_forum_post.py` passed 162 tests, adjacent forum category/thread/post/revision coverage passed 536 tests, and full unit coverage passed 2703 tests. | Regressing lazy `ForumPost.revisions`, revision-list acquisition, duplicate cached revision reuse, revision HTML acquisition, forum post source/edit workflows, parser-created posts, forum thread behavior, or forum category behavior rejects this local completion claim. | Forum workflows | `tests/unit` |
| R6 | Repository quality gates pass in the local dependency environment. | Full `ruff check`, `ruff format --check`, `mypy`, `pyright`, and `git diff --check` passed after formatting. Full mypy found no issues in 87 source files; full pyright reported 0 errors, 0 warnings, and 0 informations; full format saw 87 files already formatted. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live auth material or private site state is needed to prove the behavior. | The regressions use synthetic valid `ForumPost` and `ForumPostRevision` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page/forum content from real sites, forum post source text from real sites, revision HTML from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `05855a4 fix(forum_post): validate revisions cache ownership`.

- RED cached collection parent ownership: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_revisions_cache_from_different_post -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused parent ownership regression: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_revisions_cache_from_different_post tests/unit/test_forum_post.py::TestForumPostBasic::test_init_accepts_valid_revisions_cache -q` passed 2 tests after the collection-parent branch fix.
- RED cached revision entry ownership: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_revisions_cache_entry_from_different_post -q` failed before the entry branch fix with `DID NOT RAISE`.
- GREEN focused cache coverage: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_revisions_cache_from_different_post tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_revisions_cache_entry_from_different_post tests/unit/test_forum_post.py::TestForumPostBasic::test_init_accepts_valid_revisions_cache tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_revisions_cache tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_revisions_cache_entries -q` passed 9 tests.
- Constructor coverage: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic -q` passed 56 tests.
- Forum post module coverage: `uv run pytest tests/unit/test_forum_post.py -q` passed 162 tests.
- Adjacent forum category/thread/post/revision tests: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 536 tests.
- `uv run pytest tests/unit -q` passed 2703 tests.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` reformatted the two touched files before final gates.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPost(_revisions=ForumPostRevisionCollection(other_post, []))` raises `ValueError("post.revisions must belong to the post")` before storing cached state.
- `ForumPost(_revisions=same_post_collection_mutated_with_other_post_revision)` raises the same diagnostic before storing cached state.
- `ForumPost(_revisions=ForumPostRevisionCollection(same_post, []))` remains valid and `post.revisions` returns that cached object without a lookup.
- Existing `_revisions=None`, malformed `_revisions` object rejection, non-revision cache-entry rejection, lazy revision acquisition, direct and batched revision-list acquisition, cached duplicate revision reuse, revision HTML acquisition, forum post source/edit behavior, and adjacent forum category/thread/post/revision behavior remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPost._revisions` is a direct cache slot for browser-free edit-history reads and generated forum ledgers. If the cached collection or one of its retained revision entries belongs to another post, callers can read coherent-looking but cross-post revision state through `post.revisions`. Constructor-time ownership validation keeps direct fixtures, rehydrated records, and generated caches from silently storing another post's revision history under the current post.

## Local Evidence, Not For Upstream Paste

- The first RED failure showed `ForumPost` could accept an empty `ForumPostRevisionCollection` whose collection parent was another post.
- The second RED failure showed a same-post collection mutated after construction with another post's valid revision could still be stored as `ForumPost._revisions`.
- Existing local drafts covered revision-list acquisition, parser diagnostics, response diagnostics, optional `_revisions` cache shape, collection constructor ownership, retained thread/site validation, target revision thread validation, and mixed-site revision batches, but did not validate that the cached revision collection stored on a `ForumPost` belongs to that `ForumPost`.
- This slice only validates direct cached revision ownership during `ForumPost` construction. It does not change revision-list parsing, collection constructor semantics, public revision lookup, lazy cache invalidation, revision HTML response parsing, forum post source/edit behavior, live site behavior, authentication semantics, or parser selectors.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page/forum source text from real sites, revision HTML from real sites, and private site data out of upstream discussion.

## Additional Notes

The ownership check intentionally matches the adjacent collection ownership style: post ID, thread ID, and the same retained `Site` object must match. This allows duplicate `ForumPost` objects representing the same post on the same thread/site, while rejecting different-post, different-thread, and different-site cached revision state. Empty no-parent revision collections remain valid collection objects; direct constructor cache validation rejects only ownership evidence that points away from the constructing post.
