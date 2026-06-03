# PR Draft: Preserve Thread Detail Description Text

## Summary

`ForumThreadCollection._parse_thread_page(...)`, used by `ForumThreadCollection.acquire_from_thread_ids(...)`, `Site.get_thread(...)`, `Site.get_threads(...)`, and `ForumThread.get_from_id(...)`, parses thread detail HTML returned by `forum/ForumViewThreadModule`.

Before this fix, the thread detail description was assembled from direct `NavigableString` children of `div.description-block` only. If the description contained Wikidot-rendered formatting markup such as a `span`, `strong`, or other inline element, text inside that element was dropped and adjacent direct text chunks were concatenated without a separating space. The focused regression changed `Test thread description` to `Test <span class="wiki-formatting">thread</span> description`; before the fix, the parsed description became `Testdescription`.

This fix preserves formatted description text while still excluding the structural `div.statistics` metadata block from the description field.

## Related Issue

Builds on [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md) and [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), because those drafts established direct thread detail acquisition as a practical local workflow and the direct `div.description-block` plus structural `div.statistics` as the thread detail boundary.

The parser-boundary failure class is adjacent to [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), and [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), because all of these fixes separate thread/forum authored content from generated structural controls and metadata.

No upstream issue was filed from this local workspace.

## Changes

- Add a small helper that extracts thread detail description text from direct children of `div.description-block`.
- Preserve text inside direct child tags using `get_text(" ", strip=True)`.
- Continue excluding the chosen structural `div.statistics` block from the description field.
- Add a public acquisition regression where inline formatting markup inside the thread description does not drop text.
- Preserve direct thread detail metadata parsing, duplicate-ID output order, retry-aware fetching, exhausted retry errors, category thread lists, forum post fetching, and replies.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Thread detail descriptions should preserve text inside formatted child elements. | `TestForumThreadCollectionAcquireFromIds.test_acquire_from_ids_preserves_formatted_description_text` asserts `description == "Test thread description"` for `Test <span>thread</span> description`. | The RED test failed before the fix because the parsed description was `Testdescription`. |
| Structural thread detail metadata should remain excluded from `ForumThread.description`. | Existing detail parse tests and the neighboring statistics-boundary regression remained green. | If the structural statistics text leaks into the description or metadata parsing is disrupted, the focused neighboring tests reject the local completion claim. |
| Direct thread acquisition and adjacent forum workflows should remain green. | `uv run pytest tests/unit/test_forum_thread.py -q` passed 35 tests, and `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 120 tests. | Regressions in direct thread lookup, category thread lists, post acquisition, revision parsing, retry handling, duplicate IDs, or replies reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `3e8eb86 fix(forum_thread): preserve formatted detail descriptions`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_preserves_formatted_description_text -q` failed before the fix because `description` was `Testdescription`.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_preserves_formatted_description_text -q`
- `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_ignores_description_statistics_markup tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_preserves_formatted_description_text tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_success tests/unit/test_forum_thread.py::TestForumThreadCollectionParseThreadPage::test_parse_fields -q` passed 4 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 35 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 120 tests.
- `uv run pytest tests/unit -q` passed 656 tests.
- `uv run ruff check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py`
- `uv run ruff format --check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py`
- `uv run mypy src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Direct thread detail descriptions preserve text inside inline or formatted child elements.
- The structural `div.statistics` metadata block is not included in `ForumThread.description`.
- Creator, creation time, post count, and thread ID parsing remain unchanged.
- Existing direct thread lookup, duplicate ID behavior, retry-aware fetching, exhausted retry handling, category thread-list parsing, forum post fetching, revision parsing, and reply behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Wikidot thread descriptions can render formatted HTML inside the thread detail `div.description-block`. The parser should preserve the visible description text while still treating Wikidot's generated `div.statistics` block as metadata rather than description content. This keeps direct thread lookup faithful to the rendered description without changing request flow or public object shape.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md) and [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md) established `forum/ForumViewThreadModule` as a practical read-heavy target and the structural statistics block as the metadata boundary.
- Parser-boundary drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), and [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md) established forum authored content as a recurring parser-boundary risk.
- The refreshed complexity scan continues to flag forum thread parsing/acquisition paths as audit-worthy.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and thread contents out of upstream discussion.

## Additional Notes

This slice does not change request payloads, retry policy, direct thread batch deduplication, thread ID extraction from scripts, title parsing, structural statistics selection, category thread-list acquisition, post acquisition, post revision parsing, or reply behavior. It only changes how visible thread detail description text is collected before the structural statistics block is parsed.
