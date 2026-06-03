# PR Draft: Ignore Forum Content Pseudo Posts

## Summary

`ForumPostCollection._parse(...)` is meant to parse real Wikidot forum posts from `forum/ForumViewThreadPostsModule` responses. The implementation selected every `div.post[id^='post-']` in the response, which admits post-like markup embedded inside a post body if user content happens to include a `post-*` id.

This fix narrows the selector to real Wikidot forum post structure: direct `div.post` children of `div.post-container`. That keeps normal top-level posts and nested reply posts, while ignoring content pseudo-posts before the existing field parser runs.

## Related Issue

Builds on the forum post-list read surface documented in [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md). It is adjacent to forum post source/read work in [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md) and [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md).

No upstream issue was filed from this local workspace.

## Changes

- Change the forum post parser selector from all `div.post[id^='post-']` descendants to direct `div.post-container > div.post[id^='post-']` forum post elements.
- Add a regression test where content contains a pseudo-post with `id="post-9999"`.
- Preserve normal post parsing, existing pseudo-post user isolation, nested reply-parent detection, pagination, retry behavior, source fetching, edit behavior, and reply behavior.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Performance improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Content pseudo-post markup with a `post-*` id should not become a `ForumPost`. | `TestForumPostCollectionParse.test_parse_ignores_pseudo_posts_with_post_id` asserts parsed IDs are `[5001, 5002]`. | The RED test failed before the fix with parsed IDs `[5001, 9999, 5002]`. |
| Existing pseudo-post user isolation should remain intact. | Existing `test_parse_ignores_pseudo_posts` and `test_parse_pseudo_post_user_not_mixed` still pass. | Parsing content users as real post users would fail the existing pseudo-post tests. |
| Forum post workflows stay green. | `uv run pytest tests/unit/test_forum_post.py` passed 33 tests. | Regressions in post parsing, pagination, source fetch, lazy source, edit, or parent handling reject the local completion claim. |
| Adjacent forum workflows stay green. | `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py` passed 109 tests. | Forum category/thread/post/revision regressions reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `bbdb088 fix(forum_post): ignore content pseudo posts`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_ignores_pseudo_posts_with_post_id` failed before the fix with parsed IDs `[5001, 9999, 5002]`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_ignores_pseudo_posts_with_post_id`
- `uv run pytest tests/unit/test_forum_post.py` passed 33 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py` passed 109 tests.
- `uv run pytest tests/unit` passed 632 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Real forum posts remain parsed from direct `div.post-container > div.post[id^='post-']` nodes.
- Nested reply posts remain parsed because each reply is still inside its own `post-container`.
- Content pseudo-post markup, even with `id="post-..."`, is ignored.
- Pseudo-post user and odate elements do not contaminate real post authorship.
- Existing pagination, retry-aware post-list fetching, source fetching, lazy source behavior, edit behavior, and reply behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post bodies can contain arbitrary HTML-like or Wikidot-rendered structures that resemble forum UI markup. The parser should select the structural nodes emitted by Wikidot's forum module, not every descendant that happens to share `post` class and `post-*` id conventions. Narrowing the selector avoids false forum posts and reduces unnecessary parsing of content markup.

## Local Evidence, Not For Upstream Paste

- Existing tests already documented a real pseudo-post risk in forum content: [tests/unit/test_forum_post.py](../tests/unit/test_forum_post.py) includes pseudo-post fixtures to ensure content users are not mixed into real forum post parsing.
- The refreshed complexity scan continued to flag `src/wikidot/module/forum_post.py` as a parser/source hot path worth auditing.
- Local forum inspection drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), and [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md) established forum post inspection as an active read-heavy surface.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and saved page/forum contents out of upstream discussion.

## Additional Notes

This slice does not change forum post field extraction, nested reply parent detection, pagination, retry policy, source retrieval, edit actions, or reply actions. It only narrows the parser's candidate post elements before the existing parse logic runs.

Follow-up [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md) keeps the real post candidate selector but also scopes edit metadata to the direct `div.changes` emitted by the forum post wrapper, so content `div.changes` markup cannot create false edit attribution. Follow-up [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md) also rejects candidate post containers nested inside real post content bodies.
