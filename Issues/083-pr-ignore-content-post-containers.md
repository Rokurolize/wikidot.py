# PR Draft: Ignore Content Post Containers

## Summary

`ForumPostCollection._parse(...)` selects forum posts from `forum/ForumViewThreadPostsModule` responses. The previous parser hardening narrowed candidates to `div.post-container > div.post[id^='post-']`, but authored post content can still render a complete `post-container`-like fragment inside the real post body.

This fix keeps the structural post-container selector, then rejects candidate posts whose ancestors include the real post body container `div.content[id^='post-content-']`. A content-embedded fake `post-container` no longer becomes a `ForumPost`, while normal top-level posts and existing forum workflows remain unchanged.

## Related Issue

Builds on [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), which narrowed forum post candidates to direct post-container children. It is adjacent to [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), which scopes edit metadata so content `div.changes` markup does not contaminate real post metadata.

No upstream issue was filed from this local workspace.

## Changes

- Add a candidate guard that skips `div.post-container > div.post[id^='post-']` elements nested under a real post body `div.content[id^='post-content-']`.
- Add a regression test where the post body contains a complete fake `post-container` with post-like head, title, user, odate, and content.
- Preserve normal post parsing, pseudo-post filtering, edit metadata parsing, nested reply-parent detection, pagination, retry behavior, source fetching, edit behavior, and reply behavior.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A complete `post-container` fragment inside authored post content should not become a `ForumPost`. | `TestForumPostCollectionParse.test_parse_ignores_content_post_containers` asserts parsed IDs are `[5001, 5002]`. | The RED test failed before the fix with parsed IDs `[5001, 9999, 5002]`. |
| Existing pseudo-post and edit-metadata protections should remain intact. | Existing parser-boundary tests for pseudo-post IDs, content `div.changes`, and top-level `div.changes` still pass. | Regressions in either prior parser guard reject the local completion claim. |
| Forum post workflows stay green. | `uv run pytest tests/unit/test_forum_post.py` passed 36 tests. | Regressions in post parsing, pagination, source fetch, lazy source, edit, or parent handling reject the local completion claim. |
| Adjacent forum workflows stay green. | `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py` passed 112 tests. | Forum category/thread/post/revision regressions reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `48a4bd7 fix(forum_post): ignore content post containers`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_ignores_content_post_containers` failed before the fix with parsed IDs `[5001, 9999, 5002]`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_ignores_content_post_containers tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_ignores_pseudo_posts_with_post_id tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_ignores_content_changes_metadata tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_preserves_top_level_changes_metadata`
- `uv run pytest tests/unit/test_forum_post.py` passed 36 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py` passed 112 tests.
- `uv run pytest tests/unit` passed 635 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Real forum posts continue to be parsed from structural forum post containers.
- Complete `post-container` fragments inside `div.content[id^='post-content-']` are ignored.
- Content users and odates from fake post containers do not become real post authorship, creation time, or result entries.
- Existing content pseudo-post filtering and content edit-metadata filtering remain green.
- Existing nested reply-parent detection, pagination, retry-aware post-list fetching, source fetching, edit behavior, and reply behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post bodies can render authored markup that resembles Wikidot forum UI fragments. Selecting every descendant structural-looking `post-container` can turn content into false forum posts. Skipping candidates inside the real post body keeps the parser focused on Wikidot-emitted forum structure while preserving the existing post-list API.

## Local Evidence, Not For Upstream Paste

- The previous parser robustness drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md) and [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md) established that forum post bodies can contain forum-like UI markup that must not contaminate real post parsing.
- The refreshed complexity scan continued to flag `src/wikidot/module/forum_post.py` as a parser/source hot path worth auditing.
- Local forum inspection drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), and [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md) established forum post inspection as an active read-heavy surface.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and saved page/forum contents out of upstream discussion.

## Additional Notes

This slice does not change field extraction for real posts, nested reply parent detection, pagination, retry policy, source retrieval, edit actions, or reply actions. It only rejects post candidates that are nested inside the authored content body of another post.

Adjacent follow-up [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md) applies the same authored-content versus structural-metadata boundary to category thread-list rows, so description-rendered user/date markup cannot override thread creator/date fields.
