# PR Draft: Validate Forum Post Revision HTML Target Post Thread State

## Summary

`ForumPostRevisionCollection.get_htmls()` validated the collection parent post before revision HTML request work, but each uncached target revision still carried its own retained `revision.post`. If that target revision post's `thread` was mutated to a malformed object after construction while the collection parent stayed valid, `get_htmls()` could reach request plumbing and unrelated response-iteration diagnostics before reporting the invalid retained parent. The same gap existed in `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` for cached revision collections.

This change validates every uncached revision scheduled for HTML acquisition before batch revision-HTML requests. Malformed target `revision.post.thread` state now raises `ValueError("thread must be a ForumThread")` before AMC request work or revision HTML cache mutation. Valid direct `get_htmls()` acquisition, lazy `ForumPostRevision.html`, cached HTML reuse, duplicate revision ID deduplication, revision-list acquisition, cached-list `with_html=True`, adjacent forum workflows, and existing response diagnostics remain unchanged.

## Outcome

Forum post revision HTML acquisition now preflights both the collection-level request parent and each target revision's retained post/thread/site before request routing or HTML cache mutation.

## Current Evidence

Existing drafts [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), [366-pr-validate-forum-post-revisions-before-html-fetch.md](366-pr-validate-forum-post-revisions-before-html-fetch.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), [473-pr-validate-forum-post-revision-collection-post-field.md](473-pr-validate-forum-post-revision-collection-post-field.md), [535-pr-preserve-empty-forum-post-revision-collection-parent.md](535-pr-preserve-empty-forum-post-revision-collection-parent.md), [580-pr-validate-forum-post-revision-thread.md](580-pr-validate-forum-post-revision-thread.md), and [581-pr-validate-forum-post-revision-html-thread.md](581-pr-validate-forum-post-revision-html-thread.md) establish forum post revision acquisition, revision HTML reads, retained parent validation, deduplicated HTML acquisition, and response diagnostics as practical workflow surfaces.

This slice is not a duplicate of those issues. Issue 581 validates the collection/lazy retained post thread before revision HTML acquisition when the request parent itself is malformed. This slice validates each uncached target revision's own retained `revision.post.thread` before the request, including cached revision collections used by `acquire_all_for_posts(..., with_html=True)`.

No upstream issue was filed from this local workspace.

## Changes

- Add a shared revision HTML target preflight that validates each target revision's retained post, thread, and site.
- Apply that preflight before direct `ForumPostRevisionCollection.get_htmls()` revision-HTML requests.
- Apply that preflight before `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` revision-HTML requests.
- Add regressions for malformed target `revision.post.thread` in direct `get_htmls()` and cached-list `with_html=True` acquisition.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection.get_htmls()` must reject a mutated non-`ForumThread` target `revision.post.thread` with `ValueError("thread must be a ForumThread")` before AMC request work or revision HTML cache mutation. |
| R2 | `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` must reject a mutated non-`ForumThread` cached target `revision.post.thread` with `ValueError("thread must be a ForumThread")` before AMC request work or revision HTML cache mutation. |
| R3 | Valid direct revision HTML acquisition, lazy HTML reads, cached HTML reuse, duplicate revision ID handling, exhausted-retry behavior, response-content diagnostics, revision-list acquisition, and constructor validation must remain stable. |
| R4 | Adjacent forum category, forum thread, forum post, and forum post revision workflows must remain stable. |
| R5 | Focused RED/GREEN, full revision module, adjacent forum tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct revision HTML acquisition fails before side-effect surfaces when a target revision's retained post has a malformed thread. | `TestForumPostRevisionCollectionGetHtmls.test_get_htmls_rejects_mutated_target_revision_post_thread_before_fetch` failed RED with an unrelated `zip() argument 2 is shorter than argument 1` diagnostic, then passed GREEN with `ValueError("thread must be a ForumThread")`, no request call, and no HTML cache mutation. | Calling `amc_request_with_retry`, accepting dictionaries or mocks as target revision threads, mutating `_html`, or deferring failure to request/response diagnostics rejects this local completion claim. | `ForumPostRevisionCollection.get_htmls()` | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Cached-list `with_html=True` acquisition fails before side-effect surfaces when a target revision's retained post has a malformed thread. | `TestForumPostRevisionCollectionAcquireAllForPosts.test_acquire_all_for_posts_with_html_rejects_mutated_cached_revision_post_thread_before_fetch` passed and asserts no request call and no HTML cache mutation. | Calling `amc_request_with_retry`, accepting dictionaries or mocks as cached target revision threads, mutating `_html`, or deferring failure to request/response diagnostics rejects this local completion claim. | `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Valid revision HTML behavior remains unchanged. | Full `tests/unit/test_forum_post_revision.py` passed 125 tests. | Regressing lazy HTML reads, direct `get_htmls()`, cached reuse, duplicate revision ID handling, exhausted-retry behavior, response-content diagnostics, revision-list acquisition, cached-list `with_html=True`, or constructor validation rejects this local completion claim. | Forum post revision workflows | `tests/unit/test_forum_post_revision.py` |
| R4 | Adjacent workflows remain stable. | Adjacent forum workflow tests passed 522 tests, and the full unit suite passed 2683 tests. | Regressing forum category, forum thread, forum post, or forum post revision behavior rejects this local completion claim. | Forum and adjacent workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regressions use synthetic mutated post state and local fixtures; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private forum content, post source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `60dcaf1 fix(forum_post_revision): validate revision html target post thread`.

- RED target revision retained-thread validation: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_rejects_mutated_target_revision_post_thread_before_fetch -q` failed before the fix because malformed target `revision.post.thread` state reached mocked request handling and surfaced `zip() argument 2 is shorter than argument 1` instead of `ValueError("thread must be a ForumThread")`.
- GREEN focused regressions: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_with_html_rejects_mutated_cached_revision_post_thread_before_fetch tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_rejects_mutated_target_revision_post_thread_before_fetch -q` passed 2 tests.
- Focused HTML acquisition coverage: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml -q` passed 20 tests.
- Full revision module: `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 125 tests.
- Adjacent forum: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 522 tests.
- `uv run pytest tests/unit -q` passed 2683 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPostRevisionCollection.get_htmls()` rejects mutated malformed target `revision.post.thread` values with `ValueError("thread must be a ForumThread")` before AMC request work or revision HTML cache mutation.
- `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` rejects mutated malformed cached target `revision.post.thread` values with `ValueError("thread must be a ForumThread")` before AMC request work or revision HTML cache mutation.
- Valid direct revision HTML acquisition, lazy HTML reads, cached HTML reuse, duplicate revision ID handling, exhausted-retry behavior, response-content diagnostics, revision-list acquisition, and constructor validation remain unchanged.
- Adjacent forum behavior remains intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed malformed target `revision.post.thread` state reached mocked revision HTML request handling and then raised an unrelated `zip()` length diagnostic instead of the existing thread diagnostic.
- This slice only validates target revision retained parent-thread state before revision HTML acquisition work. It does not change revision-list acquisition, revision constructor validation, revision collection constructor validation, response parsing, revision-list retry behavior, cached collection reuse, source acquisition, edit behavior, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, private forum content, post source text from real sites, and live Wikidot account details out of upstream discussion.
