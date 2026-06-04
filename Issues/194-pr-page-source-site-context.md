# PR Draft: Include Site Context In Direct Page Source Failures

## Summary

`Page.source` and `Page.refresh_source()` are the direct single-page source-read paths used by callers that inspect one page and by browser-free publishing code that verifies saved source through `ViewSourceModule`. Earlier local slices made both paths fail with the page fullname when retry-aware acquisition exhausted, but multi-site crawler and publishing workflows can inspect the same page fullname across several Wikidot sites. A page-only message such as `Cannot find page source: scp-001` is still ambiguous in those logs.

This follow-up keeps automatic source acquisition, explicit refresh cache clearing, retry-aware `ViewSourceModule` request payloads, successful source parsing, source iterator behavior, publish source verification, and exception type unchanged. It only adds the site unix name to direct source-not-found messages: `Cannot find page source for site: <site>, page: <fullname>`.

## Related Issue

Builds on [013-pr-refresh-cached-page-source.md](013-pr-refresh-cached-page-source.md), [014-pr-preserve-viewsource-text.md](014-pr-preserve-viewsource-text.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [025-pr-source-result-error-page-context.md](025-pr-source-result-error-page-context.md), [149-pr-page-source-failure-context.md](149-pr-page-source-failure-context.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), and [192-pr-page-auxiliary-fetch-site-context.md](192-pr-page-auxiliary-fetch-site-context.md). Those drafts established explicit source refresh, source text fidelity, publish source verification, page-context source failures, login-before-read boundaries, and site-context auxiliary page fetch failures as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Include `self.site.unix_name` and page fullname in the shared `Page._source_not_found_exception()` message.
- Tighten the existing `Page.source` exhausted-retry regression to assert site/page context.
- Tighten the existing `Page.refresh_source()` exhausted-retry regression to assert site/page context.
- Preserve request payloads, retry behavior, successful source parsing, explicit refresh cache clearing, source iterator errors, publish source verification behavior, and exception type.

## Type Of Change

- Bug fix / diagnostics improvement
- Direct page source failure context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Lazy `Page.source` failures still raise `NotFoundException` when retry acquisition leaves `_source` unset. | `TestPageProperties.test_source_property_includes_site_page_context_when_retry_is_exhausted` returns `(None,)` from retry fetches and expects `NotFoundException`. | Returning an empty `PageSource`, caching placeholder source, changing the request module, or changing the exception class rejects this local completion claim. |
| Lazy `Page.source` failures identify both site and page. | The focused regression asserts `Cannot find page source for site: test-site, page: test-page`. | The RED test failed before the fix because the message only said `Cannot find page source: test-page`. |
| Explicit `Page.refresh_source()` failures still clear stale cached source before failing. | `TestPageProperties.test_refresh_source_includes_site_page_context_when_retry_is_exhausted` starts from cached source, exhausts retry, and asserts `_source is None`. | Leaving stale cached source after a failed refresh, returning the old cache, or changing the exception class rejects this local completion claim. |
| Explicit `Page.refresh_source()` failures identify both site and page. | The focused regression asserts the same site/page message for refresh failures. | A page-only refresh failure rejects this local completion claim. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 182 tests. | Regressions in source acquisition, source refresh, source iterator fallback, publish source verification, page metadata, or site accessors reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `20d8e13 fix(page): include site in source failures`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_source_property_includes_site_page_context_when_retry_is_exhausted -q` failed before the fix because the exception message was `Cannot find page source: test-page`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_source_property_includes_site_page_context_when_retry_is_exhausted -q`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_source_property_includes_site_page_context_when_retry_is_exhausted tests/unit/test_page.py::TestPageProperties::test_refresh_source_includes_site_page_context_when_retry_is_exhausted -q` passed 2 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 182 tests.
- `uv run pytest tests/unit -q` passed 733 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Page.source` still uses retry-aware source acquisition through `PageCollection.get_page_sources()`.
- `Page.source` still raises `NotFoundException` if source remains unset after acquisition.
- `Page.refresh_source()` still clears cached source before forcing a fresh remote source fetch.
- `Page.refresh_source()` still raises `NotFoundException` if source remains unset after refresh.
- Both direct source failure paths now name both site unix name and page fullname.
- Successful source acquisition, source parsing, source iterator fallback behavior, and publish source verification remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Source inspection and post-save source verification are high-traffic read paths in browser-free publishing and large corpus workflows. When source acquisition exhausts retry, logs should identify both the site and page without requiring raw response bodies, account context, local rollout paths, or saved page contents. This keeps the existing strict failure behavior while making multi-site source failures easier to route.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified direct page source reads and `Page.refresh_source()` as practical workflow surfaces for browser-free publishing, source verification, source iterator fallback, and ledger-friendly failures.
- Recent site-context slices showed that compact site/object identifiers improve resumable ledgers without changing successful behavior.
- This slice only claims direct page source failure diagnostics. It does not claim any live Wikidot behavior change.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change source request module names, retry policy, source parser selectors, source iterator fallback messages, page publishing logic, metadata writes, or live Wikidot behavior. It only adds site unix name context to the existing direct page source-not-found helper.
