# PR Draft: Include Context In Forum Post List Parse Errors

## Summary

`ForumPostCollection.acquire_all_in_thread(...)` and `ForumPostCollection.acquire_all_in_threads(...)` parse post-list HTML returned by `forum/ForumViewThreadPostsModule`. The parser already fails when generated post-list markup is missing required post ID, wrapper, head, title, content, info, user, or date elements, but those failures only named the missing element. A plain log line such as `Post title element is not found.` did not identify which site, thread, page, or post candidate produced the malformed shape.

This follow-up keeps the existing `NoElementException` failure behavior and successful post output shape, but includes the affected site `unix_name`, thread ID, page number when known, parsed post position, and post ID when available in required-element parser failures. That makes malformed forum post-list responses diagnosable from logs without saving raw forum HTML or post bodies.

## Related Issue

Builds on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), and [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), because those drafts established thread post-list acquisition as a practical read-heavy workflow and repeatedly hardened the parser boundary.

This is the forum post-list companion to [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md) and [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), which added site/category/thread context to adjacent forum parser failures.

No upstream issue was filed from this local workspace.

## Changes

- Add a small forum post-list parse-context helper for site name, thread ID, optional page number, parsed post position, and parsed post ID.
- Pass page numbers from `ForumPostCollection.acquire_all_in_threads(...)` into `ForumPostCollection._parse(...)` for both first-page and additional-page responses.
- Include the context in missing post ID, wrapper, head, title, content, info, user, and odate `NoElementException` messages.
- Count only real top-level post candidates after existing content-pseudo-post filtering, so authored pseudo-post markup does not skew the reported post position.
- Add a focused malformed post-list regression through `ForumPostCollection.acquire_all_in_thread(...)` that asserts `Post title element is not found for site: test-site (thread=3001, page=1, post=1, post_id=5001)`.
- Preserve request payloads, retry handling, pagination discovery, duplicate-thread deduplication, cached thread-post reuse, content pseudo-post filtering, title text spacing, metadata scoping, source fetching, and edit behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post-list parser error-context ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed forum post-list markup still fails when a required structural post field is missing. | `TestForumPostCollectionAcquireAll.test_acquire_all_missing_post_title_includes_thread_page_and_post_context` still expects `NoElementException` when the first post title element is removed. | A change that silently accepts the malformed post, fabricates an empty title, or shifts parser output rejects this local completion claim. |
| The malformed post-list error identifies the affected site, thread, page, post position, and parsed post ID. | The focused test asserts `Post title element is not found for site: test-site (thread=3001, page=1, post=1, post_id=5001)`. | The RED test failed before the fix because the exception message was only `Post title element is not found.` |
| Related required-element parser failures use the same context helper. | Source inspection of `src/wikidot/module/forum_post.py` shows missing post ID, wrapper, head, title, content, info, user, and odate `NoElementException` messages all append the parse context. | A future partial context change that only updates the title failure would leave other malformed post-list parser failures as generic log lines. |
| Authored pseudo-post markup does not distort the reported real post position. | Source inspection shows the parser increments the reported `post=` counter only after `_is_inside_post_content(...)` filtering. | A future change that enumerates all selected markup before filtering could report misleading post positions when post bodies contain post-like markup. |
| Forum post-list workflows remain green. | `uv run pytest tests/unit/test_forum_post.py -q` passed 47 tests. | Regressions in normal parsing, pagination, duplicate-thread handling, cached thread-post reuse, pseudo-post filtering, title spacing, source fetching, or edit behavior reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py -q` passed 89 tests. | Regressions in thread list/detail parsing, thread post access, and adjacent forum APIs reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `536220b fix(forum_post): include context in post list parse errors`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_missing_post_title_includes_thread_page_and_post_context -q` failed before the fix because the parser raised `Post title element is not found.` without site, thread, page, or post context.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_missing_post_title_includes_thread_page_and_post_context -q`
- `uv run pytest tests/unit/test_forum_post.py -q` passed 47 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py -q` passed 89 tests.
- `uv run pytest tests/unit -q` passed 719 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A thread post-list response whose structural post title is missing still raises `NoElementException`.
- The raised malformed-post-list message includes the site `unix_name`, thread ID, page number, post position, and parsed post ID when available.
- Other malformed required-element failures in the post-list parser also include the same context shape.
- Successful post-list parsing, pagination, duplicate-thread deduplication, cached thread-post reuse, content pseudo-post filtering, parent-post detection, title text spacing, metadata scoping, source fetching, and edit behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post-list acquisition is a read-heavy prerequisite for discussion inspection and tooling built on `thread.posts`. When Wikidot returns malformed generated post-list markup, wikidot.py should still fail instead of inventing post data, but the failure should identify the affected site, thread, page, and post candidate so maintainers can triage from logs without storing raw forum HTML or post bodies.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established `forum/ForumViewThreadPostsModule` as a practical parser and acquisition boundary, including retry-aware reads, duplicate request avoidance, pseudo-post filtering, content pager filtering, title text fidelity, metadata scoping, cached post-list reuse, and later duplicate cache reuse.
- The preceding forum parse-context slices showed that target-specific parser errors improve plain-text logs and resumable ledgers without changing successful behavior.
- The refreshed complexity memo continues to list `src/wikidot/module/forum_post.py` as an audit-worthy parser/acquisition surface.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw forum HTML, and post contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `ForumPostCollection.acquire_all_in_thread(...)` request construction, `ForumPostCollection.acquire_all_in_threads(...)` retry behavior, first-page/additional-page pagination rules, duplicate-thread handling, cached collection behavior, successful parser output, parent-post detection, title extraction, content HTML preservation, author/date parsing, edit metadata parsing, `ForumPost.source`, `ForumPost.edit(...)`, or live Wikidot behavior. It only adds site/thread/page/post context to existing malformed forum post-list parse failures.
