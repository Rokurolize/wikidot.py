# PR Draft: Include Site Context In Page Discussion And Meta Fetch Failures

## Summary

`Page.discussion` and `Page.metas` both lazily retrieve auxiliary page data through AMC modules. Before this local fix, exhausted retry failures raised `UnexpectedException` messages that only named the page fullname: `Cannot retrieve page discussion: <fullname>` and `Cannot retrieve page metas: <fullname>`. In multi-site crawler and publishing workflows, the same page fullname can exist on multiple sites, so page-only failure messages are weaker than the surrounding page fetch diagnostics that include site context.

This follow-up keeps request payloads, retry behavior, successful discussion parsing, missing-discussion `None` behavior, successful meta parsing, meta entity decoding, metadata writes, and exception types unchanged. It only adds the site unix name to the two existing exhausted-retry failure messages.

## Related Issue

Builds on [046-pr-retry-page-meta-fetch.md](046-pr-retry-page-meta-fetch.md), [149-pr-page-source-failure-context.md](149-pr-page-source-failure-context.md), [183-pr-listpages-fetch-failure-context.md](183-pr-listpages-fetch-failure-context.md), and [191-pr-listpages-key-parse-context.md](191-pr-listpages-key-parse-context.md). Those drafts established retry-aware page meta reads, page-level lazy fetch diagnostics, ListPages fetch diagnostics, and parser context as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Include `site.unix_name` and page fullname when `Page.discussion` cannot retrieve `forum/ForumCommentsListModule` after retries.
- Include `site.unix_name` and page fullname when `Page.metas` cannot retrieve `edit/EditMetaModule` after retries.
- Tighten the existing exhausted-retry regressions for both properties to assert the site/page context.

## Type Of Change

- Bug fix / diagnostics improvement
- Lazy auxiliary page fetch context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| `Page.discussion` exhausted retry failures still raise `UnexpectedException`. | `TestPageProperties.test_discussion_raises_when_retry_is_exhausted` configures one retry and a repeated failed AMC request. | A change that caches the failure as checked, returns `None` for exhausted retry, or changes the exception class rejects this local completion claim. |
| `Page.discussion` failure messages identify the site and page. | The focused regression asserts `Cannot retrieve page discussion for site: test-site, page: test-page`. | The RED test failed before the fix because the message only said `Cannot retrieve page discussion: test-page`. |
| `Page.metas` exhausted retry failures still raise `UnexpectedException`. | `TestPageWriteMethods.test_metas_getter_raises_when_retry_is_exhausted` configures one retry and a repeated failed AMC request. | A change that caches an empty dict, returns partial metadata, or changes the exception class rejects this local completion claim. |
| `Page.metas` failure messages identify the site and page. | The focused regression asserts `Cannot retrieve page metas for site: test-site, page: test-page`. | The RED test failed before the fix because the message only said `Cannot retrieve page metas: test-page`. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 182 tests. | Regressions in page source/revision/vote/file access, discussion parsing, meta parsing, metadata writes, page publishing, or site accessors reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `9298a3c fix(page): include site in auxiliary fetch failures`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_discussion_raises_when_retry_is_exhausted -q` failed before the fix because the exception message was `Cannot retrieve page discussion: test-page`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_discussion_raises_when_retry_is_exhausted -q`.
- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_raises_when_retry_is_exhausted -q` failed before the fix because the exception message was `Cannot retrieve page metas: test-page`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_discussion_raises_when_retry_is_exhausted tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_raises_when_retry_is_exhausted -q` passed 2 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 182 tests.
- `uv run pytest tests/unit -q` passed 733 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Page.discussion` still requests `forum/ForumCommentsListModule` with the current page ID.
- `Page.discussion` still returns `None` when the module response succeeds but contains no `WIKIDOT.forumThreadId`.
- `Page.discussion` still resolves an existing thread ID through `ForumThread.get_from_id(...)`.
- `Page.discussion` exhausted retry failures now name both site and page.
- `Page.metas` still requests `edit/EditMetaModule` with the current page ID.
- `Page.metas` still decodes flexible escaped meta markup and caches the parsed dictionary.
- `Page.metas` exhausted retry failures now name both site and page.
- Metadata setter and `set_metadata(...)` behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Auxiliary page data fetches are used by publishing, metadata, and comment-thread inspection workflows. When retries are exhausted, logs should identify both the site and page without requiring raw response bodies or local account context. This keeps the existing retry behavior strict while making multi-site failure routing easier.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established page-level lazy fetch diagnostics and retry-aware auxiliary page reads as practical workflow surfaces.
- The refreshed complexity memo continues to list parser/source collection helpers and direct property failure messages as follow-up leads; this slice only claims `Page.discussion` and `Page.metas` exhausted-retry diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, raw page source text, and account details out of upstream discussion.

## Additional Notes

This slice intentionally does not change discussion module request construction, discussion thread parsing, missing-discussion semantics, meta module request construction, meta parsing, entity decoding, metadata mutation, publish flows, retry policy, or live Wikidot behavior. It only enriches two existing exhausted-retry exception messages.
