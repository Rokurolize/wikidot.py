# PR Draft: Ignore Thread Description Pager Markup

## Summary

`ForumThreadCollection.acquire_all_in_category(...)` fetches the first `forum/ForumViewCategoryModule` page, parses category thread-list rows, and then inspects `div.pager` to decide whether additional category thread-list pages should be requested.

Before this fix, pagination discovery used response-wide `first_html.select_one("div.pager")`. If a thread description contained pager-like markup, the acquisition path treated that description markup as structural pagination. The focused regression inserted a description `div.pager` with links `1` and `2`; before the fix the collection fetched a phantom second page and returned four threads instead of the two threads actually present on the first response.

This fix keeps real category thread-list pagination unchanged, but ignores pager elements nested under structural thread description cells, specifically `td.name > div.description`.

## Related Issue

Builds on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), because that draft established category thread-list acquisition as a practical read-heavy forum workflow rather than speculative code. It also builds on [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md) and [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), which established thread descriptions as an authored-markup parser boundary for the same `ForumViewCategoryModule` response.

The pagination failure class is adjacent to [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md): both fixes prevent authored forum markup from queueing extra AMC page requests while preserving structural pagers.

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumThreadCollection._pager_from_html(...)` to return the first structural category thread-list pager while skipping pager elements inside thread description cells.
- Add `ForumThreadCollection._is_inside_thread_description(...)` to identify pager elements nested under `td.name > div.description`.
- Use `_pager_from_html(...)` in `ForumThreadCollection.acquire_all_in_category(...)` before deriving the last page.
- Add a regression where a description `div.pager` inside the first thread row does not trigger an additional `ForumViewCategoryModule` request.
- Preserve normal single-page acquisition, real pagination, non-numeric pager handling, exhausted page errors, category association, direct thread lookup, post-list fetching, and reply behavior.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Pager-like markup in a thread description should not be treated as category thread-list pagination. | `TestForumThreadCollectionAcquireAll.test_acquire_all_ignores_description_pager_markup` inserts a description `div.pager` with links `1` and `2`, asserts two threads are returned, and asserts only the first AMC retry batch is made. | The RED test failed before the fix because four threads were returned after a phantom second-page fetch. |
| Real structural category thread-list pagination should continue to request additional pages. | `TestForumThreadCollectionAcquireAll.test_acquire_all_pagination` remained green with the focused pager regression and nearby pager tests. | If a real structural pager stops queuing page 2, the existing pagination test rejects the local completion claim. |
| Existing forum thread acquisition and mutation workflows should remain green. | `uv run pytest tests/unit/test_forum_thread.py -q` passed 34 tests, and `uv run pytest tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 119 tests. | Regressions in thread parsing, category association, pagination, retry exhaustion, direct thread lookup, post fetching, reply behavior, category parsing, post parsing, or revision parsing reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `9c74116 fix(forum_thread): ignore description pager markup`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_ignores_description_pager_markup -q` failed before the fix because `len(collection)` was `4` after a description pager triggered an extra category page fetch.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_ignores_description_pager_markup -q`
- `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_pagination tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_ignores_non_numeric_pager_links tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_ignores_description_pager_markup -q` passed 4 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 34 tests.
- `uv run pytest tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 119 tests.
- `uv run pytest tests/unit -q` passed 650 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- Description `div.pager` markup inside `td.name > div.description` is treated as thread description content only.
- Description pager markup cannot queue additional `ForumViewCategoryModule` requests.
- Real structural category thread-list pagination still queues additional pages.
- Non-numeric pager link handling remains unchanged.
- Existing single-page, paginated, exhausted-page, thread parsing, category association, direct thread detail, post-list fetching, reply, category, post, and revision workflows remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Wikidot forum thread descriptions can render interface-like authored fragments, while category thread-list pagination is generated by the surrounding module structure. `ForumThreadCollection.acquire_all_in_category(...)` should use structural pager markup to decide additional page requests and ignore pager-like markup that is part of a thread description.

## Local Evidence, Not For Upstream Paste

- Earlier local draft [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md) established category thread-list acquisition as a repeatedly hardened forum workflow.
- Thread-list parser-boundary drafts [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md) and [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md) established that rendered thread descriptions can contain forum-like markup that must not contaminate generated thread-list structure.
- Forum content pager draft [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md) established the adjacent pagination failure class: authored forum markup can otherwise queue phantom page requests.
- The refreshed complexity scan continues to flag `src/wikidot/module/forum_thread.py` as an audit-worthy read-heavy parser and acquisition surface.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, forum content, and site-specific category/thread details out of upstream discussion.

## Additional Notes

This slice does not change thread-list row parsing, direct thread-detail parsing, category association, retry policy, request payloads, post-list fetching, reply submission, or target extraction for real structural pagers. It only narrows pager discovery before additional category thread-list page requests are queued.
