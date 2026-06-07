# PR Draft: Validate Forum Post Source Target Thread Ownership

## Summary

`ForumPostCollection.get_post_sources()` validates the retained collection thread and its site before source-form acquisition, but it still trusted every `ForumPost` entry to belong to that collection thread. A caller could construct or rehydrate `ForumPostCollection(collection_thread, [post_from_other_thread])`; the source helper would then route `ForumEditPostFormModule` through `collection_thread.site` with `threadId=collection_thread.id` and `postId=post_from_other_thread.id`, deferring failure to unrelated response-iteration diagnostics or risking wrong-thread source assignment if IDs overlapped.

This change validates target post ownership before cache reuse, duplicate grouping, request construction, response parsing, or `_source` mutation. Posts whose retained thread ID/site do not match the collection thread now raise `ValueError("posts must belong to the collection thread")`. Valid same-thread source reads, cached-source no-ops, duplicate/cache reuse, response diagnostics, lazy `ForumPost.source`, edit workflows, and adjacent forum workflows remain unchanged.

## Outcome

Forum post source acquisition now rejects different-thread target posts before a collection-level thread can be used to fetch or assign source for a post that belongs elsewhere.

## Current Evidence

Existing drafts [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [506-pr-validate-forum-post-source-cache.md](506-pr-validate-forum-post-source-cache.md), [576-pr-validate-forum-post-source-collection-thread.md](576-pr-validate-forum-post-source-collection-thread.md), and [577-pr-validate-forum-post-source-thread-site.md](577-pr-validate-forum-post-source-thread-site.md) establish forum post source reads, retained parent state, and source cache behavior as practical workflow surfaces.

This slice is not a duplicate of those issues. Issue 576 validates the collection's retained parent thread, Issue 577 validates that parent thread's site, Issue 367 validates non-post entries, and Issue 506 validates cached source values. This slice covers a valid `ForumPost` entry whose retained `post.thread` is individually valid but does not belong to the collection thread used for the source-form request. It is also separate from Issues 583 and 584, which reject mixed-site batch routing in revision and post-list acquisition rather than target-post ownership inside source acquisition.

No upstream issue was filed from this local workspace.

## Changes

- Add a source-acquisition ownership preflight for target posts.
- Validate each target post's retained thread and site before cache reuse or `ForumEditPostFormModule` request construction.
- Add a public regression for a collection containing a valid post from a different same-site thread.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostCollection.get_post_sources()` must reject valid `ForumPost` entries from a different retained thread with `ValueError("posts must belong to the collection thread")` before AMC request work or source-cache mutation. |
| R2 | Existing retained collection-thread, retained thread-site, collection-entry, and source-cache validations must remain stable. |
| R3 | Valid source acquisition, cached-source no-ops, duplicate/cache reuse, retry diagnostics, response diagnostics, lazy `ForumPost.source`, edit workflows, and adjacent forum behavior must remain stable. |
| R4 | Focused RED/GREEN, source-acquisition tests, source/edit adjacency, full forum-post module, adjacent forum tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Different-thread target posts fail before source request work. | `TestForumPostCollectionGetSources.test_get_post_sources_rejects_post_from_different_thread_before_fetch` failed RED by routing through the collection thread's mocked retry helper and surfacing `zip() argument 2 is shorter than argument 1`, then passed GREEN with `ValueError("posts must belong to the collection thread")`, no request call, and no `_source` mutation. | Calling AMC helpers, accepting a different-thread target post, assigning `_source`, or deferring failure to request/response diagnostics rejects this local completion claim. | `ForumPostCollection.get_post_sources()` | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Existing source preflights remain stable. | Focused source-acquisition coverage passed 18 tests, including non-post entries, mutated collection thread, mutated thread site, cached-source no-op, duplicate source reuse, retry, and response-body diagnostics. | Reordering validation so malformed parents, malformed sites, malformed entries, or invalid cached source values can reach request work rejects this local completion claim. | Forum post source preflight | `tests/unit/test_forum_post.py` |
| R3 | Adjacent workflows remain stable. | `tests/unit/test_forum_post.py` passed 158 tests, adjacent forum workflow tests passed 526 tests, and the full unit suite passed 2687 tests. | Regressing source-form fetches, transient retry handling, response-body diagnostics, direct source textarea scoping, duplicate source reuse, lazy `ForumPost.source`, post editing, post-list reads, forum thread behavior, forum category behavior, or forum post revision behavior rejects this local completion claim. | Forum post and adjacent forum workflows | `tests/unit` |
| R4 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live auth material or private state is needed to prove the behavior. | The regression uses synthetic valid `ForumThread` and `ForumPost` objects; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private forum content, post source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `0c23d7f fix(forum_post): validate source post thread ownership`.

- RED target-thread ownership: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_rejects_post_from_different_thread_before_fetch -q` failed before the fix with `ValueError("zip() argument 2 is shorter than argument 1")` after the different-thread post reached mocked source-form retry handling.
- GREEN focused regression: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_rejects_post_from_different_thread_before_fetch -q` passed 1 test.
- Focused source-acquisition coverage: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources -q` passed 18 tests.
- Source/lazy/edit adjacency: `uv run pytest tests/unit/test_forum_post.py::TestForumPostSource tests/unit/test_forum_post.py::TestForumPostEdit -q` passed 21 tests.
- Full forum-post module: `uv run pytest tests/unit/test_forum_post.py -q` passed 158 tests.
- Adjacent forum: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 526 tests.
- `uv run pytest tests/unit -q` passed 2687 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPostCollection(collection_thread, [post_from_other_thread]).get_post_sources()` raises `ValueError("posts must belong to the collection thread")` before source-form request work or `_source` mutation.
- Existing retained collection-thread, retained site, non-post entry, and cached-source validations remain unchanged.
- Valid source acquisition, cached-source no-ops, duplicate/cache behavior, retry diagnostics, response diagnostics, lazy source reads, and edit workflows remain unchanged.
- Adjacent forum behavior remains intact.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed a valid post from another same-site thread reaching the collection thread's source-form request handling and then raising an unrelated `zip()` length diagnostic instead of a source-target ownership diagnostic.
- This slice only validates source target post ownership relative to the collection thread. It does not change source response parsing, source textarea parsing, lazy source cache semantics, post-list acquisition, revision acquisition, post editing, reply actions, forum category behavior, live site behavior, or authentication semantics for valid same-thread posts.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, private forum content, post source text from real sites, and live Wikidot account details out of upstream discussion.
