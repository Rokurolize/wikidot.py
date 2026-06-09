# PR Draft: Validate Forum Post Revision Collection Retained Owner ID State

## Summary

`ForumPostRevisionCollection.__init__` validates that explicit or inferred collection entries belong to one forum post, but the collection ownership helper compared retained `ForumPost.id` and `ForumThread.id` values directly. After local fixture, serialized, or rehydrated state has been mutated incorrectly, booleans and floats could satisfy Python equality against integer post/thread IDs, strings and lists could be reported as generic collection ownership mismatches, and inferred-parent collections could accept corrupted retained IDs when the inferred parent and first revision entry were the same object.

This change validates the collection parent `ForumPost.id`, each revision-entry `ForumPost.id`, the collection parent `ForumThread.id`, and each revision-entry `ForumThread.id` before comparing collection ownership. Malformed retained post IDs now raise `ValueError("id must be an integer")`, negative retained post IDs now raise `ValueError("id must be non-negative")`, malformed retained thread IDs now raise `ValueError("thread_id must be an integer")`, negative retained thread IDs now raise `ValueError("thread_id must be non-negative")`, valid different-post collections still raise `ValueError("revisions must belong to the collection post")`, valid same-post explicit and inferred collections including zero-ID state remain accepted, and no forum fetch or live Wikidot behavior changes.

## Outcome

Direct `ForumPostRevisionCollection(...)` construction can no longer accept or misclassify revision collections whose retained parent or entry post/thread IDs are corrupted.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum edit-history reads, generated discussion migration ledgers, moderation exports, cached forum records, local fixtures, generated adapters, or serialized and rehydrated `ForumPostRevisionCollection` records.

## Current Evidence

Local rollout-backed drafts already established forum post revision collections as a practical boundary. [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [507-pr-validate-forum-post-revisions-cache.md](507-pr-validate-forum-post-revisions-cache.md), [593-pr-validate-forum-post-revision-collection-post-ownership.md](593-pr-validate-forum-post-revision-collection-post-ownership.md), [594-pr-validate-forum-post-revisions-cache-ownership.md](594-pr-validate-forum-post-revisions-cache-ownership.md), and [666-pr-validate-forum-post-revisions-cache-retained-id-state.md](666-pr-validate-forum-post-revisions-cache-retained-id-state.md) cover cached post revision reuse, direct cached revision-list skip behavior, optional `_revisions` cache shape, collection constructor ownership, direct post revisions-cache ownership for valid comparable IDs, and direct post revisions-cache retained-ID hardening. [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md) covers direct revision row IDs, and [665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md](665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md) covers the analogous retained-ID gap for `ForumThread._posts`.

This slice is not a duplicate of those drafts. Issue 593 validates that a `ForumPostRevisionCollection` parent and entries point at the same logical post/thread/site when retained IDs are valid comparable integers, but it does not reject corrupted retained `ForumPost.id` or `ForumThread.id` values before comparison. Issue 594 validates direct `ForumPost._revisions` cache ownership, not collection constructor retained-ID integrity. Issue 666 validates retained IDs at the direct `ForumPost._revisions` cache boundary, not `ForumPostRevisionCollection.__init__`. Issue 638 validates `PageRevision.id` and `ForumPostRevision.id` range semantics, not revision collection owner `ForumPost.id` or `ForumThread.id` state.

## Related Issue / Non-Duplicate Analysis

Builds directly on [507-pr-validate-forum-post-revisions-cache.md](507-pr-validate-forum-post-revisions-cache.md), [593-pr-validate-forum-post-revision-collection-post-ownership.md](593-pr-validate-forum-post-revision-collection-post-ownership.md), [594-pr-validate-forum-post-revisions-cache-ownership.md](594-pr-validate-forum-post-revisions-cache-ownership.md), [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md), [665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md](665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md), and [666-pr-validate-forum-post-revisions-cache-retained-id-state.md](666-pr-validate-forum-post-revisions-cache-retained-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate the explicit or inferred collection parent `ForumPost.id` before comparing collection ownership.
- Validate each revision-entry `ForumPost.id` before comparing collection ownership.
- Validate the explicit or inferred collection parent `ForumThread.id` before comparing collection ownership.
- Validate each revision-entry `ForumThread.id` before comparing collection ownership.
- Reject malformed retained post IDs such as `True`, `False`, `"5001"`, `5001.0`, and `[]` with `ValueError("id must be an integer")`.
- Reject negative retained post IDs such as `-1` with `ValueError("id must be non-negative")`.
- Reject malformed retained thread IDs such as `True`, `False`, `"3001"`, `3001.0`, and `[]` with `ValueError("thread_id must be an integer")`.
- Reject negative retained thread IDs such as `-1` with `ValueError("thread_id must be non-negative")`.
- Preserve valid same-post explicit collections, valid same-post inferred collections, valid zero-ID collections, valid different-post ownership diagnostics, malformed post/revision collection diagnostics, lazy revision acquisition, cached duplicate revision reuse, forum post source/edit behavior, and adjacent forum workflows.

## Type Of Change

- Input validation
- Retained forum-post ID hardening
- Retained forum-thread ID hardening
- Forum post revision collection ownership integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection(post, [revision])` must reject malformed retained explicit parent `post.id` values such as `True`, `False`, `"5001"`, `5001.0`, and `[]` with `ValueError("id must be an integer")` before collection ownership comparison. |
| R2 | The same constructor must reject negative retained explicit parent `post.id` values such as `-1` with `ValueError("id must be non-negative")` before collection ownership comparison. |
| R3 | `ForumPostRevisionCollection(post, [revision])` must reject malformed retained revision-entry `revision.post.id` values with `ValueError("id must be an integer")` before collection ownership comparison. |
| R4 | The same constructor must reject negative retained revision-entry `revision.post.id` values with `ValueError("id must be non-negative")` before collection ownership comparison. |
| R5 | `ForumPostRevisionCollection(post, [revision])` must reject malformed retained explicit parent `post.thread.id` and revision-entry `revision.post.thread.id` values with `ValueError("thread_id must be an integer")` before collection ownership comparison. |
| R6 | The same constructor must reject negative retained explicit parent `post.thread.id` and revision-entry `revision.post.thread.id` values with `ValueError("thread_id must be non-negative")` before collection ownership comparison. |
| R7 | `ForumPostRevisionCollection(post=None, revisions=[revision])` must reject malformed and negative retained inferred parent `revision.post.id` and `revision.post.thread.id` values with the same retained-ID diagnostics. |
| R8 | Valid same-post explicit and inferred collections, valid zero-ID collections, valid different-post ownership mismatches, malformed collection shape diagnostics, and adjacent forum workflows must remain green. |
| R9 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R10 | Focused RED/GREEN, forum-post-revision module coverage, adjacent forum/site coverage, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed explicit collection parent post IDs fail before ownership comparison. | `test_init_rejects_explicit_parent_with_malformed_retained_post_ids` failed RED for five malformed values: booleans and `5001.0` were accepted, while `"5001"` and `[]` raised generic collection ownership mismatch. The test passed GREEN after retained post ID validation. | Accepting booleans or floats, returning generic ownership mismatch for corrupted retained parent post IDs, coercing strings/lists, or storing the collection rejects this local completion claim. | `ForumPostRevisionCollection` explicit parent post state | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Negative explicit collection parent post IDs fail before ownership comparison. | `test_init_rejects_explicit_parent_with_negative_retained_post_id` failed RED with generic ownership mismatch, then passed GREEN after retained post ID validation. | Treating negative post IDs as ordinary wrong-post ownership, accepting them, or coercing them rejects this local completion claim. | `ForumPostRevisionCollection` explicit parent post state | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Malformed explicit revision-entry post IDs fail before ownership comparison. | `test_init_rejects_explicit_entry_with_malformed_retained_post_ids` failed RED for five malformed values with the same accepted or generic-mismatch behavior, then passed GREEN after retained entry post ID validation. | Accepting malformed entry post IDs, relying on Python equality to prove ownership, coercing strings/lists, or storing the entry rejects this local completion claim. | `ForumPostRevisionCollection` entry post state | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R4 | Negative explicit revision-entry post IDs fail before ownership comparison. | `test_init_rejects_explicit_entry_with_negative_retained_post_id` failed RED with generic ownership mismatch, then passed GREEN after retained entry post ID validation. | Accepting negative entry post IDs, coercing them, or classifying them as ordinary collection ownership mismatch rejects this local completion claim. | `ForumPostRevisionCollection` entry post state | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R5 | Malformed explicit parent and entry thread IDs fail before ownership comparison. | `test_init_rejects_explicit_parent_with_malformed_retained_thread_ids` and `test_init_rejects_explicit_entry_with_malformed_retained_thread_ids` failed RED for five malformed values each with accepted or generic-mismatch behavior, then passed GREEN after retained thread ID validation. | Accepting malformed parent or entry thread IDs, relying on Python numeric equality, coercing strings/lists, or returning generic ownership mismatch rejects this local completion claim. | `ForumPostRevisionCollection` parent and entry thread state | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R6 | Negative explicit parent and entry thread IDs fail before ownership comparison. | `test_init_rejects_explicit_parent_with_negative_retained_thread_id` and `test_init_rejects_explicit_entry_with_negative_retained_thread_id` failed RED with generic ownership mismatch, then passed GREEN after retained thread ID validation. | Treating negative thread IDs as ordinary wrong-post ownership, accepting them, or coercing them rejects this local completion claim. | `ForumPostRevisionCollection` parent and entry thread state | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R7 | Malformed and negative inferred parent post/thread IDs fail even when the inferred parent and first entry are the same object. | `test_init_rejects_inferred_parent_with_malformed_retained_post_ids`, `test_init_rejects_inferred_parent_with_negative_retained_post_id`, `test_init_rejects_inferred_parent_with_malformed_retained_thread_ids`, and `test_init_rejects_inferred_parent_with_negative_retained_thread_id` failed RED because corrupted same-object state was accepted, then passed GREEN after retained parent post/thread ID validation. | Accepting inferred same-object corrupted IDs, relying on object identity to bypass retained-ID validation, or coercing malformed values rejects this local completion claim. | `ForumPostRevisionCollection` inferred parent state | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R8 | Existing collection ownership behavior remains compatible. | Focused GREEN coverage passed 55 tests, `tests/unit/test_forum_post_revision.py` passed 171 tests, adjacent forum/category/thread/post/revision/site coverage passed 988 tests, and full unit passed 3145 tests. | Regressing valid same-post explicit/inferred collections, zero IDs, different-post diagnostics, malformed shape diagnostics, lazy revision acquisition, cached duplicate revision reuse, forum post source/edit behavior, or any unit test rejects this local completion claim. | Forum post revision collection and adjacent forum workflows | `tests/unit/test_forum_post_revision.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_site.py`, `tests/unit` |
| R9 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic objects and local unit helpers only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, revision HTML from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R10 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, temporary pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `61f6450 fix(forum_post_revision): validate collection retained owner ids`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit -q` failed 36 retained parent/entry post/thread-ID cases before the fix; 19 valid collection, zero-ID, malformed shape, and valid different-post ownership guards passed.
- GREEN: the same focused command passed 55 tests after validating explicit/inferred parent and revision-entry post/thread IDs before collection ownership comparison.
- `uv run ruff format src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 171 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_site.py -q` passed 988 tests.
- `uv run pytest tests/unit -q` passed 3145 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPostRevisionCollection(post, [revision])` raises `ValueError("id must be an integer")` when the explicit collection parent post's retained `id` is `True`, `False`, `"5001"`, `5001.0`, or `[]`.
- The same constructor raises `ValueError("id must be non-negative")` when the explicit collection parent post's retained `id` is `-1`.
- The same constructor raises `ValueError("id must be an integer")` when a revision entry's retained `revision.post.id` is `True`, `False`, `"5001"`, `5001.0`, or `[]`.
- The same constructor raises `ValueError("id must be non-negative")` when a revision entry's retained `revision.post.id` is `-1`.
- The same constructor raises `ValueError("thread_id must be an integer")` when the explicit collection parent post's retained `thread.id` or a revision entry's retained `revision.post.thread.id` is `True`, `False`, `"3001"`, `3001.0`, or `[]`.
- The same constructor raises `ValueError("thread_id must be non-negative")` when the explicit collection parent post's retained `thread.id` or a revision entry's retained `revision.post.thread.id` is `-1`.
- `ForumPostRevisionCollection(post=None, revisions=[revision])` raises the same malformed and negative retained-ID diagnostics when the inferred parent post's retained post/thread IDs are corrupted.
- Valid same-post explicit and inferred collections still initialize.
- Valid same-post collections with retained post ID `0` and thread ID `0` remain accepted.
- Valid different-post collections still raise `ValueError("revisions must belong to the collection post")`.
- Existing malformed `post`, malformed `revisions`, and malformed revision-entry diagnostics remain unchanged.
- Existing forum category, thread, post, revision, and site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPostRevisionCollection` is the canonical container for browser-free forum edit-history reads, cached direct revision-list skips, duplicate cached post-revision reuse, generated moderation ledgers, discussion migration audits, and local fixture reconstruction. Ownership validation already protects against one post's revisions being stored under another post, but corrupted retained post/thread IDs should fail as corrupted identity state before Python equality can accept booleans/floats or generic ownership mismatch can hide strings/lists/negative IDs. Validating retained post and thread IDs before comparison keeps the existing ownership contract precise without changing network behavior or parser selectors.

## Local Evidence

- Existing local drafts covered forum post revision-list retry behavior, cached direct revision-list skips, duplicate post-revision request reduction, cached duplicate post-revision reuse, optional `_revisions` cache shape, collection constructor ownership for valid comparable IDs, direct `_revisions` ownership, direct `_revisions` retained-ID hardening, direct revision ID range validation, and analogous retained-ID hardening for `ForumThread._posts`.
- None of those drafts covered malformed retained `ForumPost.id` or `ForumThread.id` values inside `ForumPostRevisionCollection.__init__` because the helper compared `revision_post.id != post.id` and `revision_thread.id != post_thread.id` directly.
- The focused RED failure showed booleans and floats could be accepted as retained parent/entry post or thread IDs when they compared equal to explicit integers, strings, lists, and negative IDs could be misreported as ordinary collection ownership mismatches, and inferred-parent same-object collections could accept corrupted retained IDs. The GREEN regressions cover malformed rejection, negative rejection, zero-ID compatibility, valid same-post explicit/inferred compatibility, valid cross-post mismatch diagnostics, adjacent forum workflows, and full unit compatibility.
- This slice only validates retained post/thread IDs at the `ForumPostRevisionCollection` constructor ownership boundary. It does not change forum post parsing, revision-list fetching, direct `_revisions` cache semantics, public revision lookup, lazy cache invalidation, forum post source/edit behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, revision HTML from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally reuses the existing `_validate_post_id(...)` and `_validate_thread_id(...)` semantics. That preserves zero as valid non-negative identity state and keeps invalid retained IDs on the same diagnostic paths as malformed direct `ForumPost.id` and `ForumThread.id` constructor input.
