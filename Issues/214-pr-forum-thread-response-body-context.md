# PR Draft: Validate Forum Thread Response Bodies

## Summary

`ForumThreadCollection.acquire_all_in_category(category)` retrieves generated category thread-list pages, while `ForumThreadCollection.acquire_from_thread_ids(site, thread_ids, category)` retrieves direct forum thread detail pages. These public flows are also reached through `ForumCategory.threads`, `ForumCategory.reload_threads()`, `Site.get_thread(...)`, `Site.get_threads(...)`, and `ForumThread.get_from_id(...)`. Earlier local slices made the same flows retry-aware, cached/reload-aware, parser-scoped, pager-filtered, duplicate-ID-aware, and context-rich. The remaining malformed response-body paths still read `response.json()["body"]`, so an AMC response without a `body` field leaked a raw `KeyError` before the parser could report which site, category, page, or thread produced the malformed response.

This follow-up keeps retry-exhausted `None` response handling, request payloads, pagination, cached category thread reuse/reload, duplicate thread-ID dedupe, input order restoration, requested/parsed thread-ID mismatch handling, parser contexts, nested table filtering, description pager filtering, title and description spacing, post access, and replies unchanged. It only treats missing category thread-list and direct thread-detail response `body` fields as malformed forum thread responses and raises `NoElementException` with site/category/page or site/thread context before BeautifulSoup parsing or thread parsing.

## Related Issue

Builds on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), and [170-pr-forum-thread-detail-fetch-failure-context.md](170-pr-forum-thread-detail-fetch-failure-context.md). Those drafts established forum thread acquisition as a practical retry-aware workflow with parser boundaries, cache behavior, deduplication, text preservation, and site/category/page or site/thread diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Add small forum thread response-body helpers that read `response.json().get("body")` for thread-list and thread-detail responses.
- Convert missing first-page category thread-list response `body` fields into `NoElementException` with site, category, and page context.
- Convert missing paginated category thread-list response `body` fields into `NoElementException` with site, category, and page context.
- Convert missing direct thread-detail response `body` fields into `NoElementException` with site and thread context.
- Preserve retry-exhausted `None` response handling as `UnexpectedException`.
- Preserve successful thread-list parsing, direct thread parsing, pagination, category cache reuse/reload, direct thread-ID dedupe, input order restoration, parser contexts, nested table filtering, pager filtering, title/description spacing, post access, and replies.
- Add focused regressions for missing first-page, paginated, and direct thread-detail response-body handling through public collection APIs.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum thread response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A first-page category thread-list response without JSON `body` still fails before HTML parsing or thread parsing. | `TestForumThreadCollectionAcquireAll.test_acquire_all_missing_first_page_response_body_includes_context` returns `{}` from the first AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, silently returns an empty thread collection, or enters thread parsing rejects this local completion claim. |
| A paginated category thread-list response without JSON `body` still fails with the affected page number. | `TestForumThreadCollectionAcquireAll.test_acquire_all_missing_paginated_response_body_includes_context` returns a valid page 1 with pager and `{}` for page 2, then expects page-2 `NoElementException`. | A change that raises raw `KeyError`, fabricates an empty page 2, returns page-1 threads as partial success, or parses page 2 rejects this local completion claim. |
| A direct thread-detail response without JSON `body` still fails before thread parsing. | `TestForumThreadCollectionAcquireFromIds.test_acquire_from_ids_missing_response_body_includes_thread_context` returns `{}` from the direct detail response and expects `NoElementException`. | A change that raises raw `KeyError`, returns no thread, fabricates a thread, or enters thread-detail parsing rejects this local completion claim. |
| Malformed thread-list response errors identify site, category, and page. | The focused regressions assert `Forum thread list response body is not found for site: test-site, category: 1001, page: 1` and page `2`. | A generic parser exception without site/category/page context rejects this local completion claim. |
| Malformed thread-detail response errors identify site and thread ID. | The focused direct-detail regression asserts `Forum thread detail response body is not found for site: test-site, thread: 3001`. | A generic parser exception without site/thread context rejects this local completion claim. |
| Retry-exhausted `None` thread responses remain distinct from malformed JSON body responses. | Existing category thread-list and direct thread-detail retry-exhausted tests remain green and expect `UnexpectedException`. | A change that turns skipped/exhausted `None` responses into body-validation failures rejects this local completion claim. |
| Existing forum thread behavior remains green. | `uv run pytest tests/unit/test_forum_thread.py -q` passed 45 tests. | Regressions in pagination, cache reuse/reload, duplicate IDs, requested/parsed thread mismatch, parser context, text spacing, nested tables, pager filtering, post access, or replies reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 159 tests. | Regressions in category lists, post lists, post sources, post edit forms, or post revisions reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `ebe9b4c fix(forum_thread): validate thread response bodies`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_missing_first_page_response_body_includes_context -q` failed before the fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_missing_first_page_response_body_includes_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_raises_when_paginated_retry_is_exhausted -q` passed 3 tests.
- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_missing_paginated_response_body_includes_context -q` failed before the fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_missing_first_page_response_body_includes_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_missing_paginated_response_body_includes_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_pagination tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_raises_when_paginated_retry_is_exhausted -q` passed 4 tests.
- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_missing_response_body_includes_thread_context -q` failed before the fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_missing_first_page_response_body_includes_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_missing_paginated_response_body_includes_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_pagination tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_missing_response_body_includes_thread_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_success tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_raises_when_retry_is_exhausted -q` passed 6 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 45 tests.
- `uv run pytest tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 159 tests.
- `uv run pytest tests/unit -q` passed 752 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Category thread-list requests still use `forum/ForumViewCategoryModule` with the same category, page, and options payloads.
- Direct thread-detail requests still use `forum/ForumViewThreadModule` with the same thread ID payloads.
- Missing first-page or paginated category thread-list response JSON `body` raises `NoElementException` naming the site, category, and page number.
- Missing direct thread-detail response JSON `body` raises `NoElementException` naming the site and thread ID.
- Missing response-body handling does not convert retry-exhausted `None` responses into malformed-body failures.
- Successful thread parsing, response-level pagination, cached category thread reuse/reload, duplicate direct thread-ID handling, input order restoration, requested/parsed thread-ID mismatch handling, parser-context diagnostics, nested table filtering, description pager filtering, title/description spacing, post access, and reply access remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum category thread-list and direct thread-detail acquisition depend on Wikidot returning a JSON `body` field for each generated module response. If that field is missing, wikidot.py should report a structured malformed-response failure with the site/category/page or site/thread, not a raw dictionary `KeyError`, so caller logs can route the failure without preserving raw response JSON, generated forum HTML, credentials, local rollout paths, or private forum content.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum thread acquisition as retry-aware, parser-scoped, cache-aware, duplicate-ID-aware, and used through both collection APIs and `Site` / `ForumCategory` / `ForumThread` convenience methods.
- Recent response-body validation slices in private-message, forum-post, forum-category, site-application, and site-member modules showed the same raw `KeyError` failure mode at AMC response-body boundaries.
- The refreshed complexity memo continues to list raw response-body boundaries in `page_file`, `page_revision`, `forum_post_revision`, `page`, and `site` as follow-up leads, but this slice only claims forum thread response-body validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated forum HTML, and private forum content out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, retry-exhausted `None` handling, pagination calculation, cached category thread behavior, direct thread-ID dedupe, input order restoration, thread-list parser, thread-detail parser, parser-context diagnostics, spacing preservation, post/reply accessors, or live Wikidot behavior. It only converts missing forum thread list/detail response `body` fields into context-rich `NoElementException` failures before parser work.
