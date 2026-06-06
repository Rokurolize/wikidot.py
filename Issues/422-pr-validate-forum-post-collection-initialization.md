# PR Draft: Validate Forum Post Collection Initialization

## Summary

`ForumPostCollection` documents `posts` as `list[ForumPost] | None`, but its constructor accepted malformed containers and arbitrary list entries. A caller could construct `ForumPostCollection(thread, posts=False)`, which silently became an empty collection, or `ForumPostCollection(thread, posts="5001")`, `ForumPostCollection(thread, posts=("5001",))`, and `ForumPostCollection(thread, posts=[None])`, which could store malformed collection entries or raise incidental low-level exceptions.

This change validates constructor input before storing entries. Non-list non-`None` `posts` values now raise `ValueError("posts must be a list or None")`; list entries that are not `ForumPost` now raise `ValueError("posts list entries must be ForumPost")`. `posts=None`, empty collections, valid `ForumPost` lists, thread inference from a valid first post, iteration, `find(...)`, direct post-list acquisition, lazy `ForumThread.posts`, multi-thread post acquisition, cached thread-post reuse, duplicate thread-post reuse, and `get_post_sources()` mutation guarding remain unchanged.

## Outcome

Callers cannot silently create malformed `ForumPostCollection` instances through the public constructor, while existing forum post fetch, parser, cache, search, and source acquisition behavior remains intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum post reads, generated discussion migration ledgers, post source capture, duplicate post-list cache reuse, direct `ForumPostCollection.acquire_all_in_thread(thread)`, lazy `ForumThread.posts`, multi-thread `ForumPostCollection.acquire_all_in_threads(...)`, or local fixtures that construct post collections directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post lists and forum post source reads as practical workflow surfaces. Existing drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), and [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md) establish forum post acquisition, source acquisition, parser diagnostics, response diagnostics, caller-provided thread validation, loaded-collection mutation validation, and search-key validation as active operational boundaries. Adjacent constructor-hardening drafts [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), and [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md) establish the local state-integrity pattern for collection constructors.

Those prior slices are not duplicates. Issues036, 043, 055, 059, 076, 081, 082, 083, 097, 109, 123, 124, 125, 134, 141, 160, 161, 171, 174, 175, 208, 209, and 327 covered fetching, retry behavior, duplicate reuse, cache reuse, parser diagnostics, source diagnostics, and response diagnostics; Issue363 validated caller-provided thread inputs before post-list acquisition; Issue367 validated loaded collection entries before `get_post_sources()` performs cache or network work; Issue378 validated search IDs after a collection already exists. None of them validates the `ForumPostCollection(thread, posts=...)` constructor itself before malformed post entries become stored list state.

## Related Issue

Builds directly on [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), and the adjacent constructor validation pattern from [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), and [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumPostCollection.__init__(..., posts=...)` validation.
- Preserve `posts=None` as an empty collection when a thread is supplied.
- Reject non-list non-`None` `posts` with `ValueError("posts must be a list or None")`.
- Reject non-`ForumPost` list entries with `ValueError("posts list entries must be ForumPost")`.
- Preserve valid empty collections, valid `ForumPost` entries, thread inference from a valid first post, iteration, `find(...)`, direct post-list acquisition, lazy `ForumThread.posts`, multi-thread acquisition, cached thread-post reuse, duplicate thread-post reuse, and `get_post_sources()` mutated-entry validation behavior.

## Type Of Change

- Input validation
- Public constructor behavior hardening
- Forum post collection state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostCollection(thread, posts=True)`, `False`, `"5001"`, `("5001",)`, and `5001` must raise `ValueError("posts must be a list or None")` before storing collection entries. |
| R2 | `ForumPostCollection(thread, posts=[None])`, `[True]`, `["5001"]`, and `[{"id": 5001}]` must raise `ValueError("posts list entries must be ForumPost")` before storing collection entries. |
| R3 | `ForumPostCollection(thread, posts=None)`, `ForumPostCollection(thread, posts=[])`, and `ForumPostCollection(thread, posts=[valid_post])` must remain valid, and `ForumPostCollection(thread=None, posts=[valid_post])` must still infer the thread from that post. |
| R4 | Existing iteration, `find(...)`, direct post-list acquisition, lazy `ForumThread.posts`, multi-thread post acquisition, cached thread-post reuse, duplicate thread-post reuse, source acquisition, forum thread workflows, forum category workflows, and forum post revision workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent forum post/thread/category/revision tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list constructor input fails at the public constructor boundary, while `None` remains valid. | `TestForumPostCollectionInit.test_init_rejects_non_list_posts` failed RED for `True`, `False`, `"5001"`, `("5001",)`, and `5001`, then passed GREEN after constructor validation was added. | Treating `False` as empty, accepting strings or tuples as post lists, surfacing incidental `TypeError`, or deferring failure to iteration rejects this local completion claim. | ForumPostCollection constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Non-`ForumPost` constructor list entries fail at the public constructor boundary. | `TestForumPostCollectionInit.test_init_rejects_non_post_entries` failed RED for `None`, `True`, `"5001"`, and `{"id": 5001}` because the constructor did not raise, then passed GREEN after entry validation was added. | Accepting missing values, booleans, strings, dictionaries, serialized post records, or fixture stand-ins as stored posts rejects this local completion claim. | ForumPostCollection constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Valid constructor inputs remain green. | Existing empty-list, valid-post, and thread-inference initialization tests passed in the focused 15-test run. | Rejecting `None`, empty valid lists, valid post lists, normal thread inference, iteration, or ID lookup rejects this local completion claim. | ForumPostCollection constructor and methods | `tests/unit/test_forum_post.py` |
| R4 | Existing forum post and adjacent workflows remain green. | Focused regressions passed 15 tests, forum post/thread/category/revision tests passed 284 tests, and full unit tests passed 1539 tests. | Regressing direct post-list acquisition, lazy `ForumThread.posts`, multi-thread acquisition, cached thread-post reuse, duplicate post reuse, parser diagnostics, response diagnostics, ID lookup, source acquisition, forum thread workflows, category workflows, or forum post revision behavior rejects this local completion claim. | Forum post and adjacent forum workflows | `tests/unit/test_forum_post.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `0cec732 fix(forum_post): validate post collection initialization`.

- RED: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_init_rejects_non_list_posts -q` failed 5 tests before the container fix; `False`, strings, and tuples were accepted, while `True` and `5001` leaked incidental `TypeError`.
- GREEN: the same focused command passed 5 tests after adding non-list validation.
- RED: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_init_rejects_non_post_entries -q` failed 4 tests before the entry fix because malformed list entries were accepted and stored.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_init_rejects_non_list_posts tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_init_rejects_non_post_entries tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_init_with_thread_and_empty_posts tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_init_with_thread_and_posts tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_init_infers_thread_from_posts tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_rejects_non_post_entries_before_fetch -q` passed 15 tests after adding entry validation and preserving thread inference plus mutated-entry `get_post_sources()` validation.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left 2 files unchanged.
- `uv run --extra test pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py -q` passed 284 tests.
- `uv run --extra test pytest tests/unit -q` passed 1539 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `ForumPostCollection(thread, posts=True)`, `False`, `"5001"`, `("5001",)`, and `5001` raise `ValueError("posts must be a list or None")`.
- `ForumPostCollection(thread, posts=[None])`, `[True]`, `["5001"]`, and `[{"id": 5001}]` raise `ValueError("posts list entries must be ForumPost")`.
- `ForumPostCollection(thread, posts=None)`, `ForumPostCollection(thread, posts=[])`, and `ForumPostCollection(thread, posts=[valid_post])` continue to work.
- `ForumPostCollection(thread=None, posts=[valid_post])` still infers the thread from that post.
- Existing iteration, `find(...)`, direct post-list acquisition, lazy `ForumThread.posts`, multi-thread post acquisition, cached thread-post reuse, duplicate thread-post reuse, `get_post_sources()`, forum thread behavior, category behavior, and forum post revision behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPostCollection` is the stored object shape behind browser-free forum post-list reads, direct post-list acquisition, lazy `ForumThread.posts`, multi-thread post acquisition, post source capture, duplicate thread-post cache reuse, and post ID lookup. Constructor validation keeps malformed local state out of the collection while preserving existing fetch, parser, cache, search, and source acquisition behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free forum post reads, duplicate thread-post reuse, lazy forum thread post reads, forum post source fetches, and tests that seed post collections directly.
- Existing local drafts covered forum post fetch retry behavior, duplicate post and source fetch reduction, parse reuse, response diagnostics, parser field diagnostics, cached direct acquisition, thread input validation, loaded-collection mutation validation, and ID search validation, but did not cover the `ForumPostCollection(thread, posts=...)` constructor itself.
- The focused RED failures showed invalid constructor input either raised incidental exceptions, was treated as empty, was accepted as an iterable, or stored invalid entries. The GREEN regressions cover non-list input, malformed list entries, valid constructor input preservation, and adjacent forum workflows.
- This slice only validates forum post collection constructor input. It does not change direct post-list acquisition, multi-thread post-list acquisition, parser selectors, post ID parsing, title/text parsing, created/edited metadata parsing, source content parsing, cached duplicate behavior, `find(...)`, `get_post_sources()` behavior beyond preserving its mutated-entry guard, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects duck-typed post-like objects and test mocks in `ForumPostCollection`. Callers should construct real `ForumPost` entries before storing them in a post collection.
