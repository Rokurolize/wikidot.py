# PR Draft: Ignore Forum Content Pager Markup

## Summary

`ForumPostCollection.acquire_all_in_threads(...)` fetches the first forum post-list page for each thread, parses posts from that response, and then inspects `div.pager` to determine whether additional post-list pages should be requested.

Before this fix, pagination discovery used response-wide `html.select_one("div.pager")`. If an authored forum post body contained pager-like markup, the acquisition path treated that content markup as structural pagination. The focused regression inserted a content `div.pager` with targets `1` and `2`; before the fix the collection fetched a phantom second page and returned four posts instead of the two posts actually present on the first response.

This fix keeps target parsing and real paginated request behavior unchanged, but ignores pager elements whose ancestors are authored post content containers, specifically `div.content` elements whose IDs start with `post-content-`.

## Related Issue

Builds on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), because that draft established forum post-list acquisition as a practical read-heavy workflow rather than speculative code. It is adjacent to [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md) and [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), which harden forum post source acquisition after post-list discovery.

The parser-boundary motivation follows [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), and the later structural selector fixes through [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumPostCollection._pager_from_html(...)` to return the first structural pager while skipping pager elements inside authored post content.
- Use `_pager_from_html(...)` in `ForumPostCollection.acquire_all_in_threads(...)` before deriving the last page.
- Add a regression where a content `div.pager` inside the first post body does not trigger an additional `ForumViewThreadPostsModule` request.
- Preserve normal single-page acquisition, real pagination, non-numeric pager handling, first-page retry behavior, exhausted page errors, duplicate thread ID deduplication, post parsing, source fetching, edit behavior, and reply behavior.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Pager-like markup in authored forum post content should not be treated as post-list pagination. | `TestForumPostCollectionAcquireAll.test_acquire_all_ignores_content_pager_markup` inserts a content `div.pager` with targets `1` and `2`, asserts two posts are returned, and asserts only the first AMC request is made. | The RED test failed before the fix because four posts were returned after a phantom second-page fetch. |
| Real structural forum post-list pagination should continue to request additional pages. | `TestForumPostCollectionAcquireAll.test_acquire_all_pagination` remained green with the focused pager regression and nearby pager tests. | If a real structural pager stops queuing page 2, the existing pagination test rejects the local completion claim. |
| Existing forum post acquisition and mutation workflows should remain green. | `uv run pytest tests/unit/test_forum_post.py -q` passed 37 tests, and `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py -q` passed 118 tests. | Regressions in post parsing, pagination, retry exhaustion, source fetching, edit behavior, reply behavior, thread parsing, category parsing, or revision parsing reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `399a05c fix(forum_post): ignore content pager markup`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_ignores_content_pager_markup -q` failed before the fix because `len(collection)` was `4` after a content pager triggered an extra page fetch.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_ignores_content_pager_markup -q`
- `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_pagination tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_ignores_non_numeric_pager_targets tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_ignores_content_pager_markup -q` passed 4 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 37 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py -q` passed 118 tests.
- `uv run pytest tests/unit -q` passed 649 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- Content `div.pager` markup inside `div.content[id^='post-content-']` is treated as authored post content only.
- Content pager markup cannot queue additional `ForumViewThreadPostsModule` requests.
- Real structural forum post-list pagination still queues additional pages.
- Non-numeric pager target handling remains unchanged.
- Existing single-page, paginated, retry, exhausted-page, duplicate-thread, post parsing, source, edit, reply, thread, category, and revision workflows remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum bodies can render interface-like authored fragments, while post-list pagination is generated by the surrounding module structure. `ForumPostCollection.acquire_all_in_threads(...)` should use structural pager markup to decide additional page requests and ignore pager-like markup that is part of a post body.

## Local Evidence, Not For Upstream Paste

- Earlier local draft [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md) established forum post-list acquisition as a repeatedly hardened forum workflow.
- Forum post source drafts [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md) and [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md) show the same operational area has been used and improved in local rollout-backed work.
- Parser-boundary drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), and [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md) established the concrete failure class for authored forum content.
- Later parser-boundary drafts through [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md) show the same selector-scoping pattern across generated Wikidot module structures.
- The refreshed complexity scan continues to flag `src/wikidot/module/forum_post.py` as an audit-worthy read-heavy parser and acquisition surface.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, forum content, and site-specific thread details out of upstream discussion.

## Additional Notes

This slice does not change post candidate parsing, parent-post detection, source fetching, edit-form fetching, reply submission, retry policy, request payloads, or target extraction for real structural pagers. It only narrows pager discovery before additional post-list page requests are queued.
