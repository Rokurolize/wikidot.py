# PR Draft: Validate Forum Category List Response Bodies

## Summary

`ForumCategoryCollection.acquire_all(site)`, also exposed through `site.forum.categories`, retrieves the forum index with `forum/ForumStartModule` and then parses generated category tables. Earlier local slices made that category-list read retry-aware, rejected nested category-like tables, preserved title and description spacing, and added site/row context to malformed category parser failures. The remaining malformed response-body path still read `response.json()["body"]`, so an AMC response without a `body` field leaked a raw `KeyError` before the parser could report which site produced the malformed category-list response.

This follow-up keeps the request module and payload, retry-exhausted `None` handling, empty forum indexes, nested category-table filtering, site/row parse context, category title and description spacing, category thread access, reload behavior, and thread creation unchanged. It only treats a missing category-list response `body` as a malformed list response and raises `NoElementException` with site context before BeautifulSoup parsing or category row parsing.

## Related Issue

Builds on [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), and [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md). Those drafts established `forum/ForumStartModule` as a practical read-heavy parser boundary and forum category acquisition as retry-aware, parser-scoped, and diagnosable.

No upstream issue was filed from this local workspace.

## Changes

- Add a small forum category list response-body helper that reads `response.json().get("body")`.
- Convert missing category-list response `body` into site-specific `NoElementException`.
- Preserve retry-exhausted `None` response handling as an `UnexpectedException`.
- Preserve successful category parsing, empty result handling, nested category-table filtering, title/description spacing, site/row parser context, category thread access, and thread creation behavior.
- Add a focused regression for missing forum category list response body handling through public `ForumCategoryCollection.acquire_all(site)`.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum category list response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A forum category list response without JSON `body` still fails before HTML parsing or category row parsing. | `TestForumCategoryCollectionAcquireAll.test_acquire_all_missing_response_body_includes_site_context` returns `{}` from the category-list AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, silently returns an empty collection, or starts category parsing rejects this local completion claim. |
| Malformed category-list response errors identify the affected site. | The focused regression asserts `Forum category list response body is not found for site: test-site`. | A generic parser exception without site context rejects this local completion claim. |
| Retry-exhausted `None` category-list responses remain distinct from malformed JSON body responses. | Existing `test_acquire_all_raises_when_retry_is_exhausted` remains green and expects `UnexpectedException`. | A change that turns skipped/exhausted `None` responses into body-validation failures rejects this local completion claim. |
| Existing forum category behavior remains green. | `uv run pytest tests/unit/test_forum_category.py -q` passed 20 tests. | Regressions in successful parsing, empty forums, nested category filtering, title/description spacing, parser context, thread access, or create-thread behavior reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 156 tests. | Regressions in category/thread/post/revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `a707ef9 fix(forum_category): validate list response bodies`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_missing_response_body_includes_site_context -q` failed before the fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_missing_response_body_includes_site_context tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_success tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_empty tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_raises_when_retry_is_exhausted -q` passed 4 tests.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 20 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 156 tests.
- `uv run pytest tests/unit -q` passed 746 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Forum category list requests still use `forum/ForumStartModule` with `hidden=true`.
- Missing category-list response JSON `body` raises `NoElementException` naming the site.
- Missing response-body handling does not convert retry-exhausted `None` responses into malformed-body failures.
- Successful category parsing, empty forum indexes, nested category-table filtering, title and description spacing, site/row parser context, category thread access, reload behavior, and thread creation remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum category inspection depends on Wikidot returning a JSON `body` field for the generated forum index. If that field is missing, wikidot.py should report a structured malformed-response failure with the site name, not a raw dictionary `KeyError`, so caller logs can route the failure without preserving raw response JSON, generated forum HTML, credentials, local rollout paths, or account details.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum category acquisition as retry-aware and parser-scoped, with practical usage through `site.forum.categories`.
- Recent response-body validation slices in private-message and forum-post modules showed the same raw `KeyError` failure mode at AMC response-body boundaries.
- The refreshed complexity memo continues to list raw response-body boundaries in `forum_thread`, `site_member`, `site_application`, `page_file`, `page_revision`, `page`, and `site` as follow-up leads, but this slice only claims forum category list response-body validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated forum HTML, and private deployment details out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, retry-exhausted `None` handling, empty-forum handling, category table selection, title or description extraction, category row parser context, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumCategory.create_thread(...)`, or live Wikidot behavior. It only converts missing forum category list response `body` fields into site-context `NoElementException` failures before parser work.
