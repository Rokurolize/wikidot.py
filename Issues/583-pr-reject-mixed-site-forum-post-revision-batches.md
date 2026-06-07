# PR Draft: Reject Mixed-Site Forum Post Revision Batches

## Summary

`ForumPostRevisionCollection.acquire_all_for_posts(...)` validated each target post's retained thread/site state, but it still selected `target_sites[0]` as the single request site for every uncached post in the batch. If caller code mixed valid posts from different `Site` objects, the method could route another site's `ForumPostRevisionsModule` request through the first site and then fail with unrelated response-iteration diagnostics, or worse, parse wrong-site data if IDs overlapped.

This change rejects mixed-site forum post revision batches before request work. The same guard covers cached revision collections when `with_html=True`, because eager revision HTML acquisition also uses one request site for every target revision. Same-site batches, duplicate post handling, cached revision-list reuse, cached-list `with_html=True`, duplicate revision HTML deduplication, parser diagnostics, exhausted-retry behavior, and adjacent forum workflows remain unchanged.

## Outcome

Forum post revision batch reads now fail explicitly with `ValueError("posts must belong to the same Site")` before a mixed-site input can send revision-list or revision-HTML requests through the wrong site.

## Current Evidence

Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [580-pr-validate-forum-post-revision-thread.md](580-pr-validate-forum-post-revision-thread.md), [581-pr-validate-forum-post-revision-html-thread.md](581-pr-validate-forum-post-revision-html-thread.md), and [582-pr-validate-forum-post-revision-html-target-post-thread.md](582-pr-validate-forum-post-revision-html-target-post-thread.md) establish retry-aware, cache-aware, duplicate-aware, contextual, and retained-parent-safe forum post revision acquisition.

This slice is not a duplicate of those issues. The earlier retained-parent slices validate malformed local object state. This slice covers a different valid-object routing problem: every post and site is individually valid, but the batch spans more than one `Site` object while the implementation has only one request site and an `id`-keyed result.

No upstream issue was filed from this local workspace.

## Changes

- Add a shared same-site preflight for forum post revision batch request sites.
- Apply it before `ForumPostRevisionCollection.acquire_all_for_posts(...)` revision-list requests.
- Apply it before `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` revision-HTML requests, including all-cached revision-list inputs.
- Add regressions for mixed-site uncached revision-list batches and mixed-site cached revision-list HTML batches.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection.acquire_all_for_posts([...])` must reject valid posts from different `Site` objects with `ValueError("posts must belong to the same Site")` before AMC request work or revision-cache mutation. |
| R2 | `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` must reject valid cached revisions from different `Site` objects with `ValueError("posts must belong to the same Site")` before AMC request work or revision HTML cache mutation. |
| R3 | Valid same-site revision-list acquisition, cached revision-list reuse, duplicate post handling, duplicate revision HTML handling, valid `with_html=True`, response diagnostics, and constructor validation must remain stable. |
| R4 | Adjacent forum category, forum thread, forum post, and forum post revision workflows must remain stable. |
| R5 | Focused RED/GREEN, full revision module, adjacent forum tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Mixed-site uncached revision-list batches fail before side-effect surfaces. | `TestForumPostRevisionCollectionAcquireAllForPosts.test_acquire_all_for_posts_rejects_mixed_site_posts_before_fetch` failed RED by routing through the first site's mocked retry helper and surfacing `zip() argument 2 is shorter than argument 1`, then passed GREEN with `ValueError("posts must belong to the same Site")`, no request call, and no revision-cache mutation. | Calling either site's AMC helpers, accepting mixed valid site objects, mutating `_revisions`, or deferring failure to request/response diagnostics rejects this local completion claim. | `ForumPostRevisionCollection.acquire_all_for_posts(...)` | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Mixed-site cached `with_html=True` batches fail before side-effect surfaces. | `TestForumPostRevisionCollectionAcquireAllForPosts.test_acquire_all_for_posts_with_html_rejects_mixed_site_cached_revisions_before_fetch` passed and asserts no request call and no revision HTML cache mutation. | Calling either site's AMC helpers, accepting mixed valid site objects, mutating `_html`, or routing HTML requests through the first site rejects this local completion claim. | `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Valid same-site revision workflows remain unchanged. | Full `tests/unit/test_forum_post_revision.py` passed 127 tests. | Regressing same-site revision acquisition, cached revision-list reuse, duplicate post handling, duplicate revision HTML deduplication, valid `with_html=True`, response diagnostics, or constructor validation rejects this local completion claim. | Forum post revision workflows | `tests/unit/test_forum_post_revision.py` |
| R4 | Adjacent workflows remain stable. | Adjacent forum workflow tests passed 524 tests, and the full unit suite passed 2685 tests. | Regressing forum category, forum thread, forum post, or forum post revision behavior rejects this local completion claim. | Forum and adjacent workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regressions use synthetic valid `Site`, `ForumThread`, `ForumPost`, and `ForumPostRevision` objects; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private forum content, post source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `c1dfb38 fix(forum_post_revision): reject mixed-site revision batches`.

- RED mixed-site revision-list routing: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_rejects_mixed_site_posts_before_fetch -q` failed before the fix because mixed valid site objects reached the first site's mocked retry helper and surfaced `zip() argument 2 is shorter than argument 1` instead of `ValueError("posts must belong to the same Site")`.
- GREEN focused regressions: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_rejects_mixed_site_posts_before_fetch tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_with_html_rejects_mixed_site_cached_revisions_before_fetch -q` passed 2 tests.
- Full revision module: `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 127 tests.
- Adjacent forum: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 524 tests.
- `uv run pytest tests/unit -q` passed 2685 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Mixed-site `ForumPostRevisionCollection.acquire_all_for_posts([...])` inputs fail with `ValueError("posts must belong to the same Site")` before revision-list request work or cache mutation.
- Mixed-site cached `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` inputs fail with `ValueError("posts must belong to the same Site")` before revision-HTML request work or cache mutation.
- Same-site revision-list acquisition, cached revision-list reuse, duplicate post handling, duplicate revision HTML deduplication, valid `with_html=True`, response diagnostics, and constructor validation remain unchanged.
- Adjacent forum behavior remains intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed mixed valid site objects reached the first site's mocked revision-list request handling and then raised an unrelated `zip()` length diagnostic instead of a same-site batch diagnostic.
- This slice only rejects mixed-site forum post revision batches that the current one-site request implementation cannot route safely. It does not change same-site revision-list acquisition, revision constructor validation, revision collection constructor validation, response parsing, retry behavior, cached collection reuse, revision HTML content handling, source acquisition, edit behavior, live site behavior, or authentication semantics for valid same-site batches.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, private forum content, post source text from real sites, and live Wikidot account details out of upstream discussion.
