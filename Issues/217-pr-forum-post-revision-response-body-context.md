# PR Draft: Validate Forum Post Revision List Response Bodies

## Summary

`ForumPostRevisionCollection.acquire_all()` and `ForumPostRevisionCollection.acquire_all_for_posts()` retrieve generated `forum/sub/ForumPostRevisionsModule` response bodies before parsing forum post edit-history rows. Earlier local slices made this workflow retry-aware, duplicate-post-aware, duplicate-revision-aware for optional HTML acquisition, cached-revision-aware, and site/post-context-rich for exhausted fetches and lazy HTML failures. The remaining malformed response-body path still read `response.json()["body"]`, so an AMC response without a `body` field leaked a raw `KeyError` before the revision-list boundary could report which site and post produced the malformed response.

This follow-up keeps request payloads, retry-exhausted `None` handling, cached direct revision-list reuse, duplicate post-ID grouping, successful revision-list parsing, optional `with_html` HTML acquisition, duplicate revision-ID HTML grouping, lazy `ForumPostRevision.html`, and existing parser behavior unchanged. It only treats revision-list responses without JSON `body` fields as malformed generated-module responses and raises `NoElementException` with site and post context before HTML parsing.

## Related Issue

Builds on [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), and [180-pr-forum-post-revision-lazy-html-context.md](180-pr-forum-post-revision-lazy-html-context.md). Those drafts established forum post revision acquisition as a practical retry-aware workflow with parser scoping, duplicate handling, cached reuse, optional HTML acquisition, and site/post/revision diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Read direct forum post revision-list response bodies with `response.json().get("body")`.
- Read batched forum post revision-list response bodies with `response.json().get("body")`.
- Convert missing `forum/sub/ForumPostRevisionsModule` response `body` fields into `NoElementException` with site and post context.
- Preserve retry-exhausted `None` handling as `UnexpectedException`.
- Preserve cached direct revision-list reuse, duplicate post-ID deduplication, duplicate cached post revision copying, optional `with_html` behavior, duplicate revision-ID HTML grouping, successful row parsing, and lazy revision HTML behavior.
- Add focused regressions for missing direct and batched forum post revision-list response bodies through public collection APIs.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post revision response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A direct forum post revision-list response without JSON `body` fails before BeautifulSoup parsing. | `TestForumPostRevisionCollectionAcquireAll.test_acquire_all_missing_response_body_includes_site_and_post_context` returns `{}` from the AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, fabricates an empty revision list from missing `body`, or enters parser work rejects this local completion claim. |
| A batched forum post revision-list response without JSON `body` identifies the affected post. | `TestForumPostRevisionCollectionAcquireAllForPosts.test_acquire_all_for_posts_missing_response_body_includes_site_and_post_context` returns a valid first response and `{}` for post `5002`, then expects `NoElementException`. | A generic batch failure, raw `KeyError`, wrong post ID, or silent partial success rejects this local completion claim. |
| Malformed revision-list response errors identify the site and post ID. | The focused regressions assert `Forum post revision list response body is not found for site: test-site, post: 5001` and `Forum post revision list response body is not found for site: test-site, post: 5002`. | An exception without site/post context rejects this local completion claim. |
| Retry-exhausted `None` responses remain distinct from malformed response bodies. | Existing direct and batched retry-exhausted tests remain green and preserve `UnexpectedException`. | A change that turns retry exhaustion into body-validation failure rejects this local completion claim. |
| Existing forum post revision behavior remains green. | `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 41 tests. | Regressions in successful revision parsing, cached revision-list reuse, duplicate post handling, optional HTML acquisition, duplicate revision HTML grouping, or lazy HTML access reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 161 tests. | Regressions in category/thread/post/revision public flows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `aaa341f fix(forum_post_revision): validate revision list response bodies`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_missing_response_body_includes_site_and_post_context -q` failed before the direct-body fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_missing_response_body_includes_site_and_post_context -q` passed after the direct-body fix.
- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_missing_response_body_includes_site_and_post_context -q` failed before the batched-body fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_missing_response_body_includes_site_and_post_context -q` passed after the batched-body fix.
- `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_missing_response_body_includes_site_and_post_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_raises_when_retry_is_exhausted tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_missing_response_body_includes_site_and_post_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_retries_transient_fetch_failures tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_deduplicates_duplicate_post_ids tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_raises_when_retry_is_exhausted tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_with_html_deduplicates_duplicate_revision_ids -q` passed 8 tests.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 41 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 161 tests.
- `uv run pytest tests/unit -q` passed 757 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `ForumPostRevisionCollection.acquire_all()` still uses retry-aware AMC and the same `forum/sub/ForumPostRevisionsModule` request payload.
- `ForumPostRevisionCollection.acquire_all_for_posts()` still uses retry-aware AMC and the same per-post `forum/sub/ForumPostRevisionsModule` request payloads.
- A missing direct revision-list response JSON `body` raises `NoElementException` naming the site and post ID.
- A missing batched revision-list response JSON `body` raises `NoElementException` naming the site and affected post ID.
- Missing response-body handling does not convert retry-exhausted `None` responses into malformed-body failures.
- Cached direct revision-list reuse, duplicate post-ID deduplication, duplicate cached post revision copying, optional `with_html` behavior, duplicate revision-ID HTML grouping, successful row parsing, and lazy `ForumPostRevision.html` behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, non-goals, verification, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Forum post edit-history inspection depends on Wikidot returning a generated module response with a `body` field. If that response is malformed, wikidot.py should report a structured failure with the site and post ID, not a raw dictionary `KeyError`, so caller logs can route the failure without preserving raw response JSON, generated HTML, credentials, local rollout paths, or private forum content.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum post revision-list acquisition as retry-aware, deduplicated, cached, parser-scoped, and used through both direct post access and batched collection APIs.
- Recent response-body validation slices in private-message, forum-post, forum-category, forum-thread, site-application, site-member, page-file, and page-revision modules showed the same raw `KeyError` failure mode at AMC response-body boundaries.
- The refreshed complexity memo continues to list raw response-body boundaries in `page` and `site` as follow-up leads after this slice removes the remaining `forum_post_revision` direct `response.json()["body"]` reads.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated revision-list HTML, and private forum content out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, retry-exhausted `None` handling, cached direct revision-list reuse, duplicate post-ID grouping, duplicate cached post revision copying, optional `with_html` HTML retrieval, duplicate revision-ID HTML grouping, revision-list row parsing, lazy `ForumPostRevision.html`, or live Wikidot behavior. It only converts missing forum post revision-list response `body` fields into site/post-context `NoElementException` failures before parser work.
