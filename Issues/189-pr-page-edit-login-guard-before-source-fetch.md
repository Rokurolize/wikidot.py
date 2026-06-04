# PR Draft: Guard Page Edit Before Current Source Fetch

## Summary

`Page.edit(...)` fills omitted edit fields from the current page state. In particular, callers may pass `source=None` to reuse the current page source. Before this local fix, an unauthenticated `Page.edit(title=...)` call could attempt to acquire the current source before the mutation path reached `Page.create_or_edit(...)` and its `login_check()`.

This follow-up adds an explicit `login_check()` at the entry of `Page.edit(...)`. Unauthenticated edit attempts now fail before current-source fetches, page-ID lookup, edit-lock acquisition, or save requests. Direct `Page.create_or_edit(...)` calls keep their existing login guard.

## Related Issue

Builds on the browser-free page lookup/create/edit and publishing drafts such as [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [013-pr-refresh-cached-page-source.md](013-pr-refresh-cached-page-source.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [046-pr-retry-page-meta-fetch.md](046-pr-retry-page-meta-fetch.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md), and [185-pr-forum-post-edit-revision-site-context.md](185-pr-forum-post-edit-revision-site-context.md). Those drafts established page edit/source handling, write-result handling, edit-lock sensitivity, and read-before-mutation boundaries as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Add an entry login guard to `Page.edit(...)` before defaulting `title`, resolving current `source`, resolving `self.id`, acquiring an edit lock, or saving.
- Add a focused regression that patches `login_check()` to raise `LoginRequiredException`.
- Assert that the unauthenticated `Page.edit(title=...)` path does not call `amc_request` or `amc_request_with_retry`.
- Preserve the direct `Page.create_or_edit(...)` login guard and create/edit request behavior.

## Type Of Change

- Bug fix / write-boundary hardening
- Page edit authorization ordering
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| `Page.edit(...)` fails unauthenticated callers with `LoginRequiredException`. | `TestPageEdit.test_edit_not_logged_in_does_not_fetch_current_source` patches `login_check()` to raise and expects that exception. | A change that reaches current-source acquisition, page-ID lookup, edit-lock acquisition, or save before login rejects this local completion claim. |
| `Page.edit(source=None, ...)` does not fetch current source when the caller is not logged in. | The focused regression asserts no `site.amc_request` or `site.amc_request_with_retry` call is made. | Any unauthenticated AMC read/write request rejects this local completion claim. |
| Existing page edit/create/write behavior remains green. | `uv run pytest tests/unit/test_page.py::TestPageEdit tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageWriteMethods -q` passed 31 tests. | Regressions in successful edit defaults, create/edit requests, write wrappers, `force_edit`, empty source handling, save payloads, edit-lock payloads, or stale ListPages fallback reject this local completion claim. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 179 tests. | Regressions in page source/id/search helpers or site publishing helpers reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `81ed463 fix(page): guard edit before source fetch`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageEdit::test_edit_not_logged_in_does_not_fetch_current_source -q` failed before the fix by entering page source acquisition instead of raising the patched login exception.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageEdit::test_edit_not_logged_in_does_not_fetch_current_source -q`.
- `uv run pytest tests/unit/test_page.py::TestPageEdit tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageWriteMethods -q` passed 31 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 112 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 179 tests.
- `uv run pytest tests/unit -q` passed 730 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Page.edit(...)` calls `login_check()` before reading current source, reading current title, resolving page ID, acquiring the edit lock, or saving.
- Unauthenticated `Page.edit(...)` makes no AMC read or write request when the login guard fails.
- Direct `Page.create_or_edit(...)` still performs its own login check.
- Successful edit behavior still preserves current title/source defaulting, explicit empty source, `force_edit`, save and lock payloads, stale ListPages fallback, and create/edit write-wrapper behavior.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Write helpers should fail authorization before doing read work or acquiring edit state. This keeps unauthorized edit attempts side-effect-light, avoids unnecessary current-source reads, and keeps write-boundary behavior consistent with the rest of the page publishing and edit helpers.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established browser-free page publishing, current-source refresh, edit-lock masking, save-response reuse, and forum edit read-before-mutation handling as practical local surfaces.
- The refreshed complexity memo continues to list action/read boundaries and page/source collection helpers as follow-up leads; this slice only claims the `Page.edit(...)` login-before-default-resolution fix.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, raw page source text, and account details out of upstream discussion.

## Additional Notes

This slice intentionally does not change `Page.create_or_edit(...)`, request payload shape, retry policy, page ID acquisition internals, edit-lock handling, save-response parsing, source normalization, page search behavior, site publish behavior, or live Wikidot behavior. It only prevents unauthenticated `Page.edit(...)` calls from performing source/default-resolution reads before the existing mutation guard can raise.
