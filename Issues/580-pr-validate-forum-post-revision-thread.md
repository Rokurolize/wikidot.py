# PR Draft: Validate Forum Post Revision Thread State

## Summary

`ForumPostRevisionCollection.acquire_all(...)` and the lazy `ForumPost.revisions` path validated that caller-provided values were `ForumPost` objects, but they still trusted the retained `post.thread` field before revision-list request work. If caller code, a fixture, or rehydrated state replaced a valid post's thread with a malformed object after construction, revision acquisition could reach request plumbing and surface unrelated request or iterator diagnostics before reporting the invalid retained parent.

This change revalidates the retained post thread before uncached forum-post revision-list acquisition. Malformed action-time parent-thread state now raises `ValueError("thread must be a ForumThread")` before AMC request work or revision-cache mutation. Valid direct revision acquisition, lazy `ForumPost.revisions`, cached revision reuse, batch revision-list acquisition, optional revision HTML acquisition, response-body diagnostics, parser diagnostics, and adjacent forum workflows remain unchanged.

## Outcome

Forum post revision acquisition now has explicit retained-thread preflight before malformed local parent-thread state can influence request routing, response parsing, or revision-cache mutation.

## Current Evidence

Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [329-pr-forum-post-revision-list-body-type-context.md](329-pr-forum-post-revision-list-body-type-context.md), [364-pr-validate-forum-post-revision-list-posts.md](364-pr-validate-forum-post-revision-list-posts.md), [366-pr-validate-forum-post-revisions-before-html-fetch.md](366-pr-validate-forum-post-revisions-before-html-fetch.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), [473-pr-validate-forum-post-revision-collection-post-field.md](473-pr-validate-forum-post-revision-collection-post-field.md), [535-pr-preserve-empty-forum-post-revision-collection-parent.md](535-pr-preserve-empty-forum-post-revision-collection-parent.md), [576-pr-validate-forum-post-source-collection-thread.md](576-pr-validate-forum-post-source-collection-thread.md), [577-pr-validate-forum-post-source-thread-site.md](577-pr-validate-forum-post-source-thread-site.md), [578-pr-validate-forum-post-edit-thread.md](578-pr-validate-forum-post-edit-thread.md), and [579-pr-validate-forum-post-edit-thread-site.md](579-pr-validate-forum-post-edit-thread-site.md) establish forum post revision acquisition, retained parent validation, source/edit retained parent validation, and revision-list diagnostics as practical workflow surfaces.

This slice is not a duplicate of those issues. Issue 445 validates constructor-time `ForumPostRevision.post` input. Issue 473 validates constructor-time `ForumPostRevisionCollection.post` input. Issue 364 validates caller-provided `post` and `posts` values before revision acquisition. Issue 366 validates revision entries before HTML acquisition. Issues 576 through 579 cover source/edit retained parent state, not revision-list acquisition. This slice covers a valid retained post whose `post.thread` was mutated before uncached revision-list acquisition or lazy `ForumPost.revisions`.

No upstream issue was filed from this local workspace.

## Changes

- Add forum-post revision helpers for retained `ForumPost.thread` and `ForumThread.site` validation.
- Revalidate the retained post thread before direct uncached `ForumPostRevisionCollection.acquire_all(...)` request work.
- Revalidate retained post threads for uncached target posts before batch `ForumPostRevisionCollection.acquire_all_for_posts(...)` request work.
- Keep cached revision-list reuse behavior intact and avoid mutating `_revisions` when retained-thread validation fails.
- Add regressions for direct revision acquisition and lazy `ForumPost.revisions` with a mutated retained thread.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection.acquire_all(...)` must reject a mutated non-`ForumThread` `post.thread` with `ValueError("thread must be a ForumThread")` before AMC request work or `_revisions` cache mutation. |
| R2 | Lazy `ForumPost.revisions` must reject a mutated non-`ForumThread` `post.thread` with `ValueError("thread must be a ForumThread")` before AMC request work or `_revisions` cache mutation. |
| R3 | Valid direct revision acquisition, valid lazy revision reads, cached revision reuse, duplicate-post handling, optional with-HTML acquisition, response-body diagnostics, parser diagnostics, and collection copying must remain stable. |
| R4 | Adjacent forum category, forum thread, forum post, and forum post revision workflows must remain stable. |
| R5 | Focused RED/GREEN, relevant revision acquisition tests, full revision module, adjacent forum tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct uncached revision acquisition fails before side-effect surfaces. | `TestForumPostRevisionCollectionAcquireAll.test_acquire_all_rejects_mutated_thread_before_fetch` passed after the fix and asserts no request call and no `_revisions` mutation. | Calling `amc_request_with_retry`, accepting dictionaries or mocks as threads, mutating `_revisions`, or deferring failure to request/response diagnostics rejects this local completion claim. | `ForumPostRevisionCollection.acquire_all(...)` | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Lazy uncached revision acquisition fails before side-effect surfaces. | `TestForumPostRevisions.test_revisions_property_rejects_mutated_thread_before_fetch` failed RED by reaching mocked request plumbing and surfacing `zip() argument 2 is shorter than argument 1`, then passed GREEN with `ValueError("thread must be a ForumThread")`. | Calling `amc_request_with_retry`, accepting dictionaries or mocks as threads, mutating `_revisions`, or deferring failure to request/response diagnostics rejects this local completion claim. | `ForumPost.revisions` through `ForumPostRevisionCollection.acquire_all_for_posts(...)` | `src/wikidot/module/forum_post_revision.py`, `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Valid revision behavior remains unchanged. | Full `tests/unit/test_forum_post_revision.py` passed 121 tests. | Regressing direct revision acquisition, lazy revision reads, cached reuse, duplicate-post handling, with-HTML behavior, parser diagnostics, or response diagnostics rejects this local completion claim. | Forum post revision workflows | `tests/unit/test_forum_post_revision.py` |
| R4 | Adjacent workflows remain stable. | Adjacent forum workflow tests passed 518 tests, and the full unit suite passed 2679 tests. | Regressing forum category, forum thread, forum post, or forum post revision behavior rejects this local completion claim. | Forum and adjacent workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regressions use synthetic mutated post state and local fixtures; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private forum content, post source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `3c6aaa4 fix(forum_post_revision): validate revision post thread`.

- RED lazy revision retained-thread validation: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisions::test_revisions_property_rejects_mutated_thread_before_fetch -q` failed before the fix because mutated retained `ForumPost.thread` state reached mocked request plumbing and surfaced `zip() argument 2 is shorter than argument 1` instead of `ValueError("thread must be a ForumThread")`.
- GREEN focused regressions: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_rejects_mutated_thread_before_fetch tests/unit/test_forum_post_revision.py::TestForumPostRevisions::test_revisions_property_rejects_mutated_thread_before_fetch -q` passed 2 tests.
- Relevant acquisition coverage: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts tests/unit/test_forum_post_revision.py::TestForumPostRevisions -q` passed 37 tests.
- Full revision module: `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 121 tests.
- Adjacent forum: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 518 tests.
- `uv run pytest tests/unit -q` passed 2679 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPostRevisionCollection.acquire_all(...)` rejects mutated malformed `post.thread` values with `ValueError("thread must be a ForumThread")` before AMC request work or `_revisions` cache mutation.
- Lazy `ForumPost.revisions` rejects mutated malformed `post.thread` values with `ValueError("thread must be a ForumThread")` before AMC request work or `_revisions` cache mutation.
- Valid direct revision acquisition, valid lazy revision reads, cached revision reuse, duplicate-post handling, optional with-HTML acquisition, response-body diagnostics, parser diagnostics, and collection copying remain unchanged.
- Adjacent forum behavior remains intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed mutated retained `ForumPost.thread` state reached mocked revision-list request handling and then raised an unrelated `zip()` length diagnostic instead of the existing thread diagnostic.
- This slice only validates retained forum-post revision parent-thread state before revision-list acquisition work. It does not change revision constructor validation, revision collection constructor validation, response parsing, revision-list retry behavior, cached collection reuse, revision HTML parsing, source acquisition, edit behavior, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, private forum content, post source text from real sites, and live Wikidot account details out of upstream discussion.
