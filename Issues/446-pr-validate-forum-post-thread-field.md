# PR Draft: Validate Forum Post Thread Field

## Summary

`ForumPost` records carry the owning `ForumThread` used by browser-free post-list reads, lazy `ForumThread.posts`, post source acquisition, edit cache invalidation, duplicate thread-post reuse, and generated forum migration or audit ledgers. Earlier local slices validated forum-post acquisition inputs, post collection entries, collection search keys, collection initialization, source acquisition entries, parser diagnostics, edit cache invalidation, and forum post revision ownership, but the public `ForumPost(...)` constructor still accepted malformed `thread` values such as `None`, booleans, strings, dictionaries, and arbitrary objects.

This change validates `ForumPost.thread` at initialization. Malformed values now raise `ValueError("thread must be a ForumThread")`. Existing post-list parsing, lazy `ForumThread.posts`, duplicate cached post reuse, source acquisition, post editing, revision invalidation, thread post-cache invalidation, and adjacent forum workflows remain unchanged for valid `ForumThread` objects.

## Outcome

Callers cannot silently construct forum post records whose parent thread is not a `ForumThread`, while parser-created, fixture-created, and manually created valid posts continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum thread reads, generated discussion migration ledgers, post source capture, duplicate thread-post cache reuse, direct `ForumPostCollection.acquire_all_in_thread(thread)`, lazy `ForumThread.posts`, multi-thread `ForumPostCollection.acquire_all_in_threads(...)`, post editing, or local tests that construct `ForumPost` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post ownership as a practical workflow surface. Existing drafts [041-pr-retry-forum-post-fetches.md](041-pr-retry-forum-post-fetches.md), [055-pr-deduplicate-thread-post-fetches.md](055-pr-deduplicate-thread-post-fetches.md), [062-pr-reuse-forum-post-source-parsing.md](062-pr-reuse-forum-post-source-parsing.md), [082-pr-skip-empty-forum-post-fetches.md](082-pr-skip-empty-forum-post-fetches.md), [133-pr-reuse-cached-duplicate-thread-posts.md](133-pr-reuse-cached-duplicate-thread-posts.md), [140-pr-reuse-cached-duplicate-forum-post-sources.md](140-pr-reuse-cached-duplicate-forum-post-sources.md), [169-pr-forum-post-list-fetch-failure-context.md](169-pr-forum-post-list-fetch-failure-context.md), [215-pr-forum-post-list-response-body-context.md](215-pr-forum-post-list-response-body-context.md), [269-pr-forum-post-edit-thread-cache-invalidation.md](269-pr-forum-post-edit-thread-cache-invalidation.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [378-pr-validate-forum-post-search-keys.md](378-pr-validate-forum-post-search-keys.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), and [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md) establish thread-owned post-list acquisition, source reads, duplicate cache reuse, edit invalidation, acquisition input validation, collection integrity, lookup validation, and revision ownership as active operational boundaries.

Those prior slices are not duplicates. Issue363 validates `ForumPostCollection.acquire_all_in_thread(thread=...)` and `acquire_all_in_threads(threads=...)` API inputs before post-list acquisition, but explicitly does not validate forum dataclass fields. Issue422 validates `ForumPostCollection(thread, posts=...)` constructor state, not the `ForumPost.thread` field. Issue445 validates `ForumPostRevision.post`, not the post's own parent thread. The remaining prior slices cover fetch, parse, cache, source, edit, lookup, and response-diagnostic behavior after valid post records exist.

## Related Issue

Builds directly on [041-pr-retry-forum-post-fetches.md](041-pr-retry-forum-post-fetches.md), [055-pr-deduplicate-thread-post-fetches.md](055-pr-deduplicate-thread-post-fetches.md), [062-pr-reuse-forum-post-source-parsing.md](062-pr-reuse-forum-post-source-parsing.md), [133-pr-reuse-cached-duplicate-thread-posts.md](133-pr-reuse-cached-duplicate-thread-posts.md), [140-pr-reuse-cached-duplicate-forum-post-sources.md](140-pr-reuse-cached-duplicate-forum-post-sources.md), [169-pr-forum-post-list-fetch-failure-context.md](169-pr-forum-post-list-fetch-failure-context.md), [215-pr-forum-post-list-response-body-context.md](215-pr-forum-post-list-response-body-context.md), [269-pr-forum-post-edit-thread-cache-invalidation.md](269-pr-forum-post-edit-thread-cache-invalidation.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [378-pr-validate-forum-post-search-keys.md](378-pr-validate-forum-post-search-keys.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), and the adjacent constructor parent-field validation pattern from [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md), and [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumPost.thread` validation at dataclass initialization.
- Reject non-`ForumThread` values with `ValueError("thread must be a ForumThread")`.
- Replace a BeautifulSoup `hasattr(..., "get")` narrowing check with `isinstance(..., Tag)` in parent-post parsing so the touched source file is target-pyright-clean without changing valid parser behavior.
- Keep negative test fixtures pyright-clean by typing intentionally malformed values through `Any`.
- Preserve existing post-list parsing, lazy `ForumThread.posts`, duplicate cached post reuse, source acquisition, post editing, revision invalidation, thread post-cache invalidation, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum post parent-thread state integrity
- Test fixture tightening
- Type-narrowing cleanup

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPost(thread=None)`, `True`, `"3001"`, `{"id": 3001}`, and `object()` must raise `ValueError("thread must be a ForumThread")` when every other post field is valid. |
| R2 | Valid `ForumThread` instances must remain valid and preserve existing post fields. |
| R3 | Existing post-list parsing, lazy `ForumThread.posts`, duplicate cached post reuse, source acquisition, post editing, revision invalidation, thread post-cache invalidation, and adjacent forum workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, forum-post tests, adjacent forum tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor threads fail at the public dataclass boundary. | `TestForumPostBasic.test_init_rejects_malformed_threads` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after thread validation was added. | Accepting missing values, booleans, strings, dictionaries, arbitrary objects, or emitting post rows with non-`ForumThread` parent state rejects this local completion claim. | ForumPost constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Valid thread semantics stay green. | Existing forum-post unit tests passed after valid constructor fixtures continued using real `ForumThread` values. | Rejecting valid `ForumThread` instances, coercing thread-like mocks, or changing stored post fields rejects this local completion claim. | Parser-created and manually created posts | `tests/unit/test_forum_post.py` |
| R3 | Existing adjacent forum workflows remain green. | `tests/unit/test_forum_post.py` passed 99 tests, adjacent forum-post-revision/forum-thread/forum-category tests passed 227 tests, and full unit tests passed 1717 tests. | Regressing post-list parsing, direct acquisition, lazy `ForumThread.posts`, multi-thread acquisition, cached duplicate post reuse, source acquisition, post edit cache invalidation, revision invalidation, parser diagnostics, response diagnostics, search lookup, or adjacent forum workflows rejects this local completion claim. | Forum post and adjacent forum workflows | `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum post text, revision HTML, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `1e76982 fix(forum_post): validate post thread`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_threads -q` failed 5 tests before the fix; every malformed `thread` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_threads -q` passed 5 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 99 tests.
- `uv run ruff check src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed.
- `uv run pyright src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run mypy src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_forum_post_revision.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py -q` passed 227 tests.
- `uv run pytest tests/unit -q` passed 1717 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 75 existing full-tree typing errors, including intentional invalid-input test fixtures, fixture `None` mismatches, invalid `test_search_pages_query` parameter calls, requestutil response narrowing issues, and site/application test mock typing issues. The changed source file and changed test file pass pyright together.

## Acceptance Criteria

- `ForumPost(thread=None)`, `True`, `"3001"`, `{"id": 3001}`, and `object()` raise `ValueError("thread must be a ForumThread")`.
- Valid `ForumThread` instances remain valid as `thread`.
- Existing post-list parsing, lazy `ForumThread.posts`, duplicate cached post reuse, `ForumPostCollection.find(...)`, direct and batched acquisition, source acquisition, post editing, revision invalidation, and thread post-cache invalidation remain green.
- Existing forum post revision, thread, and category workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPost.thread` is the parent context behind browser-free forum post reads, duplicate thread post-list reuse, lazy `ForumThread.posts`, source acquisition, post editing, thread post-cache invalidation, and generated moderation or migration ledgers. Constructor validation keeps malformed local parent-thread state out of post rows while preserving parser and caller paths that construct posts from real `ForumThread` objects.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free forum post reads, duplicate thread post-list reuse, source acquisition, post editing, thread post-cache invalidation, and tests that seed post objects directly.
- Existing local drafts covered forum post fetch retry behavior, duplicate thread-post reduction, source parse reuse, response diagnostics, parser field diagnostics, cached duplicate source reuse, acquisition thread input validation, collection initialization validation, loaded-collection mutation validation, search-key validation, edit invalidation, and revision ownership validation, but did not cover direct `ForumPost(thread=...)` construction.
- The focused RED failures showed invalid constructor thread fields were accepted as dataclass state. The GREEN regression covers missing, boolean, string, dictionary, and arbitrary object thread values.
- This slice only validates forum post parent-thread constructor input and preserves a stricter BeautifulSoup type narrowing check in existing parent-post parsing. It does not change post-list request construction, pagination, parser selectors, post ID parsing, parent-post ID parsing, user/timestamp parsing, source/edit behavior, revision behavior, collection lookup semantics, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum post text, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates only that `thread` is a `ForumThread` instance. It does not validate thread IDs, category identity, site identity, post IDs, post text, post source, user shape, timestamp shape, revision cache content, or live client authentication at `ForumPost` construction time; those are separate thread object, parser, cache, and workflow concerns.
