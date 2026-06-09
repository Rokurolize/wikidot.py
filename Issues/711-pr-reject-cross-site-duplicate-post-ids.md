# PR Draft: Reject Cross-Site Duplicate Forum Post IDs

## Summary

`ForumPostRevisionCollection.acquire_all_for_posts(...)` deduplicates forum post revision-list requests by retained `ForumPost.id`, which is correct for duplicate post objects from the same `Site`. One adjacent batch-boundary gap remained: if caller or rehydrated state supplied two valid `ForumPost` objects with the same numeric ID but different retained `Site` objects, the method treated the second post as an ordinary duplicate before same-site validation could see it. The returned `dict[int, ForumPostRevisionCollection]` also cannot represent two different site/post pairs with the same integer key.

This change validates that duplicate retained post IDs in a revision-list batch belong to the same `Site` object before cache maps, ID-only deduplication, request construction, cache reuse, or optional revision HTML acquisition. Same-site duplicate ID dedupe, same-site cached duplicate revision-list reuse, mixed-site different-ID rejection, retained post-ID validation, direct acquisition, parser diagnostics, response diagnostics, retry behavior, and adjacent forum workflows remain unchanged.

## Outcome

Forum post revision-list batches no longer silently collapse cross-site post objects that share the same retained post ID. Valid same-site duplicates are still fetched or cache-reused once, while cross-site ID collisions now fail with `ValueError("posts must belong to the same Site")` before either site's AMC helpers are called.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `ForumPost.revisions`, `ForumPostRevisionCollection.acquire_all(...)`, or `ForumPostRevisionCollection.acquire_all_for_posts(...)` in browser-free forum edit-history inventories, moderation tooling, migration ledgers, translation review scripts, cached revision-list reuse, optional revision HTML capture, or rehydrated forum post records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post revision-list acquisition, duplicate post batching, cached post-revision reuse, retained parent validation, and mixed-site request routing as practical workflow surfaces. Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [580-pr-validate-forum-post-revision-thread.md](580-pr-validate-forum-post-revision-thread.md), [583-pr-reject-mixed-site-forum-post-revision-batches.md](583-pr-reject-mixed-site-forum-post-revision-batches.md), and [679-pr-validate-forum-post-revision-list-acquisition-retained-post-id-state.md](679-pr-validate-forum-post-revision-list-acquisition-retained-post-id-state.md) establish this as an active read boundary.

This slice is not a duplicate of those drafts. Issue 583 rejects mixed-site uncached batches where different retained post IDs would be routed through one request site. Issue 679 validates malformed or negative retained post IDs before grouping, request payloads, result keys, or cache assignment. Issues 056, 135, 142, 143, and 229 intentionally preserve same-site duplicate ID dedupe and cached duplicate reuse. This slice covers the remaining collision case where the ID value is valid but the duplicated ID belongs to a different retained `Site`, making ID-only dedupe unsafe.

No upstream issue was filed from this local workspace.

## Changes

- Add a preflight that scans duplicate retained post IDs and requires every duplicate ID to point at the same retained `Site` object.
- Run that preflight immediately after post input and retained post-ID validation, before cache maps and seen-ID dedupe.
- Preserve same-site duplicate ID dedupe and later cached duplicate collection copying.
- Add a regression for two valid `ForumPost` objects with the same `id` and different `Site` objects.

## Type Of Change

- Batch input validation
- Forum post revision-list cache/dedupe hardening
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection.acquire_all_for_posts([...])` must reject valid duplicate retained post IDs from different `Site` objects with `ValueError("posts must belong to the same Site")` before AMC request work or `_revisions` cache mutation. |
| R2 | Same-site duplicate retained post IDs must continue to deduplicate to one request/result entry. |
| R3 | Same-site cached duplicate revision-list reuse must continue to copy the cached collection for the first-seen post without refetching. |
| R4 | Existing mixed-site different-ID rejection must remain intact. |
| R5 | Direct acquisition, optional `with_html=True`, retry-exhausted diagnostics, response-body diagnostics, parser behavior, source/edit adjacent behavior, and adjacent forum workflows must remain compatible. |
| R6 | Focused RED/GREEN, forum-post-revision module, adjacent forum tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Cross-site duplicate post IDs fail before side effects. | `test_acquire_all_for_posts_rejects_duplicate_post_ids_from_different_sites_before_fetch` failed RED with `DID NOT RAISE`, then passed GREEN with the same-site diagnostic and no AMC calls. | Silently treating the second site post as a duplicate, calling either site's AMC helpers, mutating `_revisions`, or returning a single ID-keyed result rejects this local completion claim. | `ForumPostRevisionCollection.acquire_all_for_posts(...)` duplicate-ID preflight | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Existing same-site duplicate ID dedupe remains unchanged. | Focused GREEN included `test_acquire_all_for_posts_deduplicates_duplicate_post_ids`. | Rejecting valid same-site duplicates, sending duplicate requests, or changing the result key rejects this local completion claim. | Same-site duplicate revision-list batching | `tests/unit/test_forum_post_revision.py` |
| R3 | Existing same-site cached duplicate reuse remains unchanged. | Focused GREEN included `test_acquire_all_for_posts_reuses_later_cached_duplicate_post_revisions`. | Refetching cached duplicates, reusing a cached collection without retargeting revisions, or mutating cached HTML state rejects this local completion claim. | Cached duplicate revision-list reuse | `tests/unit/test_forum_post_revision.py` |
| R4 | Mixed-site different-ID batches still reject before request work. | Focused GREEN included `test_acquire_all_for_posts_rejects_mixed_site_posts_before_fetch` and `test_acquire_all_for_posts_with_html_rejects_mixed_site_cached_revisions_before_fetch`. | Regressing Issue 583 by routing a mixed-site request or HTML request through one site rejects this local completion claim. | Mixed-site revision-list batch preflight | `tests/unit/test_forum_post_revision.py` |
| R5 | Adjacent forum workflows remain green. | `tests/unit/test_forum_post_revision.py` passed 229 tests, adjacent forum tests passed 878 tests, and full unit coverage passed 3561 tests. | Regressing direct acquisition, optional revision HTML acquisition, parser diagnostics, response diagnostics, source/edit adjacent behavior, forum category/thread/post behavior, or site-adjacent behavior rejects this local completion claim. | Forum post revision-list and adjacent forum workflows | `tests/unit` |
| R6 | Repository quality gates pass in the local dependency environment. | Full ruff check passed, full ruff format check passed, full mypy passed with no issues in 87 source files, pyright passed with 0 errors, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live site state or private material is needed to prove the behavior. | The regression uses synthetic valid `Site`, `ForumThread`, and `ForumPost` objects plus unit-level response mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `29848eb fix(forum_post_revision): reject cross-site duplicate post ids`.

- RED: `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_rejects_duplicate_post_ids_from_different_sites_before_fetch -q` failed before the fix with `Failed: DID NOT RAISE <class 'ValueError'>`.
- GREEN focused: `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_rejects_duplicate_post_ids_from_different_sites_before_fetch tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_deduplicates_duplicate_post_ids tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_reuses_later_cached_duplicate_post_revisions tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_rejects_mixed_site_posts_before_fetch tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_with_html_rejects_mixed_site_cached_revisions_before_fetch -q` passed 5 tests.
- `uv run --extra test pytest tests/unit/test_forum_post_revision.py -q` passed 229 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 878 tests.
- `uv run --extra test pytest tests/unit -q` passed 3561 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Cross-site duplicate retained post IDs in `ForumPostRevisionCollection.acquire_all_for_posts(...)` raise `ValueError("posts must belong to the same Site")` before AMC request work or `_revisions` cache mutation.
- Same-site duplicate retained post IDs still deduplicate to one request/result entry.
- Same-site cached duplicate revision-list reuse still avoids request work and returns a collection retargeted to the first-seen post.
- Mixed-site different-ID batches still reject before request work, including cached `with_html=True` batches.
- Direct revision-list acquisition, empty input behavior, cached revision-list skips, optional revision HTML acquisition, retry-exhausted diagnostics, response-body diagnostics, parser behavior, source/edit adjacent behavior, and adjacent forum workflows remain green.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A caller may intentionally batch cached posts from multiple sites. Mitigation: this slice only rejects duplicate numeric post IDs that cannot be represented safely in the ID-keyed result map; different-ID cache-only behavior is left unchanged.
- Risk: The new preflight could interfere with same-site duplicate dedupe. Mitigation: focused coverage proves same-site duplicate IDs and cached duplicate reuse still pass.
- Risk: Cross-site object graphs can share a client while still representing different sites. Mitigation: the check compares retained `Site` object identity through the post's retained thread, matching the existing mixed-site batch guard and avoiding name/id coercion.

## Out Of Scope

Changing result keys, supporting multi-site request routing in one call, rejecting all cached mixed-site batches, changing same-site duplicate behavior, changing optional revision HTML parsing, changing parser selectors, changing forum post source/edit behavior, live Wikidot behavior, pushing changes, opening upstream Issues, and opening upstream PRs are outside this slice.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used forum post revision-list acquisition, duplicate post batching, cached revision-list reuse, forum migration ledgers, moderation/audit workflows, and rehydrated forum records.
- Existing local drafts covered retry behavior, duplicate same-site fetch reduction, cached revision-list skip/reuse, direct acquisition cache population, malformed retained post/thread-site validation, mixed-site different-ID routing rejection, and malformed/negative retained post-ID validation.
- The focused RED failure showed the same numeric post ID from a different `Site` was silently treated as an ordinary duplicate and the second post's site was never consulted.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private forum content, private site data, and source text from real sites out of upstream discussion.
