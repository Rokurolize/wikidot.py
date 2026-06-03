# PR Draft: Ignore Content Edit Metadata

## Summary

`ForumPostCollection._parse(...)` already scopes the main forum post wrapper, head, title, info, and content lookups to direct structural children. The edit metadata lookup used descendant `div.changes`, so rendered post body markup that happened to contain `div.changes`, `span.printuser`, and `span.odate` could be treated as real forum edit metadata.

This fix narrows edit metadata parsing to a direct `div.changes` child of the post wrapper. Content `div.changes` markup no longer sets `edited_by` or `edited_at`, while real top-level edit metadata remains parseable.

## Related Issue

Builds on [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), which keeps forum content pseudo-post markup out of the post candidate set. It is also adjacent to the forum post-list read surface in [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md).

No upstream issue was filed from this local workspace.

## Changes

- Change the edit metadata lookup from descendant `div.changes` to direct `:scope > div.changes` under the real post wrapper.
- Add a regression test where the post body contains content `div.changes` markup with a `content_user` and `odate`.
- Add a preservation test proving a direct top-level `div.changes` still populates `edited_by` and `edited_at`.
- Preserve normal post parsing, pseudo-post filtering, nested reply-parent detection, pagination, retry behavior, source fetching, edit behavior, and reply behavior.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Content `div.changes` markup should not set forum edit metadata. | `TestForumPostCollectionParse.test_parse_ignores_content_changes_metadata` asserts `edited_by is None` and `edited_at is None`. | The RED test failed before the fix because `edited_by` was parsed as `content_user` with ID `54321`. |
| Real top-level edit metadata should remain parseable. | `TestForumPostCollectionParse.test_parse_preserves_top_level_changes_metadata` asserts `edited_by.name == "edit_user"`, `edited_by.id == 54322`, and `edited_at is not None`. | A selector that ignored direct top-level changes would fail this preservation test. |
| Forum post workflows stay green. | `uv run pytest tests/unit/test_forum_post.py` passed 35 tests. | Regressions in post parsing, pseudo-post filtering, pagination, source fetch, lazy source, edit, or parent handling reject the local completion claim. |
| Adjacent forum workflows stay green. | `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py` passed 111 tests. | Forum category/thread/post/revision regressions reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `690eecb fix(forum_post): scope edit metadata parsing`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_ignores_content_changes_metadata` failed before the fix because `edited_by` was parsed as `content_user` with ID `54321`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_ignores_content_changes_metadata tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_preserves_top_level_changes_metadata`
- `uv run pytest tests/unit/test_forum_post.py` passed 35 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py` passed 111 tests.
- `uv run pytest tests/unit` passed 634 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Direct top-level `div.changes` metadata under a real forum post wrapper is parsed into `edited_by` and `edited_at`.
- `div.changes` markup inside the post body is treated as post content only.
- Content users and odates do not contaminate real forum post edit metadata.
- Existing direct-child parsing for wrapper, head, title, info, and content remains unchanged.
- Existing pseudo-post filtering, nested reply-parent detection, pagination, retry-aware post-list fetching, source fetching, edit behavior, and reply behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post bodies can render user content that resembles Wikidot forum UI fragments. The parser should read edit metadata from the structural forum post wrapper, not from arbitrary descendants inside the authored content. Scoping the `div.changes` lookup to a direct child matches the surrounding parser structure and avoids false edit attribution.

## Local Evidence, Not For Upstream Paste

- The previous parser robustness draft [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md) established that forum post bodies can contain post-like UI markup that must not contaminate real post parsing.
- The refreshed complexity scan continued to flag `src/wikidot/module/forum_post.py` as a parser/source hot path worth auditing.
- Local forum inspection drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), and [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md) established forum post inspection as an active read-heavy surface.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and saved page/forum contents out of upstream discussion.

## Additional Notes

This slice does not change forum post candidate selection, field extraction for authorship and creation time, nested reply parent detection, pagination, retry policy, source retrieval, edit actions, or reply actions. It only narrows edit metadata lookup to the direct structural location where Wikidot emits it.

Follow-up [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md) keeps this metadata guard and also prevents complete `post-container` fragments inside authored post content from becoming false forum posts.
