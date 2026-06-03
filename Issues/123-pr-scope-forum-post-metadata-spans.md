# PR Draft: Scope Forum Post Metadata Spans

## Summary

`ForumPostCollection._parse(...)` parses generated forum post metadata from `div.info` for the post creator/date and from top-level `div.changes` for edit metadata. Before this fix, those metadata lookups used descendant selectors inside each metadata container. If nested user/date-like markup appeared before the direct generated spans, the parser could read the nested `printuser` or `odate` as the real post author, creation date, editor, or edited date.

This fix keeps the existing post container, title, content, parent-post, and edit-metadata boundaries, but scopes metadata span discovery to direct children of the generated metadata containers. Nested `printuser`/`odate` fragments inside the metadata block no longer override the structural spans Wikidot emits for the post.

## Related Issue

Builds on forum post parser-boundary drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), and [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), because those drafts established authored forum content and forum-like markup as a repeated parser contamination risk.

It also remains adjacent to forum post acquisition/source drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), and title text-fidelity draft [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), which make forum post lists a practical rollout-backed read surface rather than a speculative parser.

No upstream issue was filed from this local workspace.

## Changes

- Change post creator lookup from descendant `span.printuser` to direct `:scope > span.printuser` under `div.info`.
- Change post creation-date lookup from descendant `span.odate` to direct `:scope > span.odate` under `div.info`.
- Change edit creator/date lookups under top-level `div.changes` to direct child spans.
- Add focused regressions for nested fake creator/date metadata inside `div.info` and nested fake editor/date metadata inside `div.changes`.
- Preserve normal post parsing, top-level edit metadata, authored-content edit-metadata filtering, content post-container filtering, pagination, retry behavior, source fetching, edit behavior, and reply behavior.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Nested `printuser`/`odate` markup inside `div.info` must not override direct post creator/date metadata. | `TestForumPostCollectionParse.test_parse_scopes_post_info_metadata_to_direct_children` asserts the parsed creator remains `test_user` with ID `12345` and timestamp `1700000000`. | The RED test failed before the fix because the parsed creator was `fake_user`. |
| Nested `printuser`/`odate` markup inside top-level `div.changes` must not override direct edit metadata. | `TestForumPostCollectionParse.test_parse_scopes_post_edit_metadata_to_direct_children` asserts the parsed editor remains `edit_user` with ID `54322` and timestamp `1700000500`. | The RED test failed before the fix because the parsed editor was `fake_editor`. |
| Existing forum post parser-boundary behavior remains intact. | The focused neighboring parser tests for content post containers, content edit metadata, and top-level edit metadata passed with the new tests. | Regressions in authored-content filtering, top-level edit metadata, or post-container filtering reject the local completion claim. |
| Forum post and adjacent forum workflows stay green. | `uv run --extra test pytest tests/unit/test_forum_post.py -q` passed 40 tests, and `uv run --extra test pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py -q` passed 128 tests. | Regressions in post parsing, pagination, retry exhaustion, source fetching, edit behavior, reply behavior, thread parsing, category parsing, or revision parsing reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `19e1caa fix(forum_post): scope post metadata spans`.

- RED: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_scopes_post_info_metadata_to_direct_children -q` failed before the fix because the parsed creator was `fake_user`.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_scopes_post_info_metadata_to_direct_children -q`
- RED: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_scopes_post_edit_metadata_to_direct_children -q` failed before the fix because the parsed editor was `fake_editor`.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_scopes_post_info_metadata_to_direct_children tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_scopes_post_edit_metadata_to_direct_children tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_preserves_top_level_changes_metadata tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_ignores_content_changes_metadata tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_ignores_content_post_containers -q` passed 5 tests.
- `uv run --extra test pytest tests/unit/test_forum_post.py -q` passed 40 tests.
- `uv run --extra test pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py -q` passed 128 tests.
- `uv run --extra test pytest tests/unit -q` passed 676 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Post creator and creation date are parsed only from direct generated spans under `div.info`.
- Post edit creator and edited date are parsed only from direct generated spans under the top-level `div.changes` block.
- Nested user/date-like markup inside those metadata containers cannot override the generated metadata spans.
- Existing authored-content `div.changes` filtering remains intact.
- Existing content post-container filtering, title parsing, post body retention, parent-post detection, pagination, retry-aware acquisition, source fetching, edit behavior, and reply behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post metadata is generated structure, while forum content and copied UI fragments can contain user/date-like spans. A parser should treat the direct generated metadata spans as the boundary for authorship and timestamps. Direct-child scoping prevents nested fragments from changing post identity or edit metadata without changing the public forum post API.

## Local Evidence, Not For Upstream Paste

- Earlier forum post drafts established post-list acquisition, forum post source reads, edit-form reads, and authored-content parser boundaries as practical rollout-backed surfaces.
- The parser-boundary draft series repeatedly found that Wikidot-rendered authored content can resemble generated forum controls and metadata.
- The refreshed complexity scan continues to flag `src/wikidot/module/forum_post.py` as an audit-worthy read-heavy parser/acquisition path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page/forum contents out of upstream discussion.

## Additional Notes

This slice does not change post candidate selection, title/body parsing, parent-post detection, edit action behavior, reply behavior, post source acquisition, retry policy, request payloads, or result object shape. It only narrows the metadata span selectors inside the generated post info and edit metadata containers.
