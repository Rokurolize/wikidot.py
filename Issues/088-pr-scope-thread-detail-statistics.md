# PR Draft: Scope Thread Detail Statistics Parsing

## Summary

`ForumThreadCollection._parse_thread_page(...)`, used by `ForumThreadCollection.acquire_from_thread_ids(...)`, `Site.get_thread(...)`, `Site.get_threads(...)`, and `ForumThread.get_from_id(...)`, parses thread detail HTML returned by `forum/ForumViewThreadModule`.

Before this fix, thread detail metadata was selected with response-wide descendants such as `div.statistics span.printuser`, `div.statistics span.odate`, and `div.statistics br`. If the thread description rendered a `div.statistics`-like block before the structural metadata block, direct thread lookup could parse the description block as the thread creator, creation time, and post count.

This fix first locates the structural statistics block as a direct child of the thread detail `div.description-block`, then parses direct metadata children from that block. Description markup that resembles Wikidot statistics no longer overrides thread detail metadata, while normal direct thread lookup, retry-aware acquisition, duplicate-ID handling, category thread lists, post fetching, and replies remain unchanged.

## Related Issue

Builds on [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), because direct thread detail acquisition is the public fetch path affected by this parser. It also applies the same parser-boundary lesson as [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), and [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md).

No upstream issue was filed from this local workspace.

## Changes

- Parse thread detail metadata from the structural statistics block attached to the direct thread detail description block.
- Use the last direct `div.statistics` child of `div.description-block`, matching the fixture shape where the structural statistics block follows the description text.
- Read creator, creation time, and post-count separators from direct children of that structural statistics block.
- Add a public acquisition regression test where thread description content contains a fake earlier `div.statistics` block with a fake user, fake timestamp, and fake post count.
- Preserve normal direct thread detail lookup, retry-aware acquisition, duplicate-ID output order, category thread-list parsing, thread posts, and replies.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Thread detail creator/date/post-count metadata should come from the structural statistics block, not description content. | `TestForumThreadCollectionAcquireFromIds.test_acquire_from_ids_ignores_description_statistics_markup` asserts `created_by.name == "test_user"`, timestamp `1700000000`, and `post_count == 5`. | The RED test failed before the fix because `created_by.name` was parsed as `content_user` from the description block. |
| Public direct thread acquisition should preserve normal behavior. | `uv run pytest tests/unit/test_forum_thread.py -q` passed 33 tests. | Regressions in success parsing, empty input, retry behavior, duplicate ID handling, exhausted retry handling, post fetching, or replies reject the local completion claim. |
| Adjacent forum workflows stay green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 117 tests. | Forum category, thread-list, post, or revision regressions reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `2820eea fix(forum_thread): scope thread detail statistics parsing`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_ignores_description_statistics_markup -q` failed before the fix because `created_by.name` was `content_user` instead of `test_user`.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_ignores_description_statistics_markup -q`
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 33 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 117 tests.
- `uv run pytest tests/unit -q` passed 640 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- Direct thread detail parsing locates the metadata statistics block from the thread detail description block, not from response-wide descendant selectors.
- Creator, creation time, and post count are parsed from direct structural statistics children.
- A description-rendered `div.statistics` block with fake user/date/count metadata does not override the parsed thread detail fields.
- Existing direct thread lookup, duplicate ID behavior, retry-aware fetching, exhausted retry handling, category thread-list parsing, forum post fetching, and reply behavior remain unchanged.
- Existing forum category, post, and revision workflows remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Thread detail descriptions can render HTML before Wikidot's own metadata block. The parser should treat the thread detail module's structural statistics block as the metadata boundary instead of selecting the first `div.statistics` descendant in the whole response. Scoping metadata extraction to that structural block prevents authored description markup from changing thread creator/date/count values while preserving the public API and acquisition flow.

## Local Evidence, Not For Upstream Paste

- The rollout ledger for this research run records broad practical `wikidot.py` usage and a high candidate-thread count, including forum detail inspection as an active surface.
- Earlier direct thread detail draft [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md) established `ForumViewThreadModule` as a read-heavy public acquisition path.
- Parser-boundary drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), and [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md) established the concrete failure pattern: authored forum-like markup can collide with structural parser selectors.
- The refreshed complexity scan continues to flag `src/wikidot/module/forum_thread.py` around thread parsing and acquisition as an audit-worthy forum path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and saved page/forum contents out of upstream discussion.

## Additional Notes

This slice does not change the script-based thread ID extraction, category thread-list acquisition, direct thread fetch batching, exhausted retry behavior, post acquisition, reply behavior, or forum post/revision parser rules. It only narrows thread detail statistics parsing to the structural statistics block under the thread detail description block.
