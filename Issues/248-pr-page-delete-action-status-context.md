# PR Draft: Validate Page Delete Action Status Before Reporting Success

## Summary

`Page.destroy()` sends a `deletePage` action and used to return after `site.amc_request(...)` produced any response object. That meant a malformed action response without `status`, or an explicit non-`ok` status, could be treated as a successful page deletion by callers and cleanup code.

This follow-up routes `deletePage` through the same generic page action status validator now used by `Page.rename(...)`. A missing `status` raises `NoElementException` with site, page, page ID, event, and field context. Explicit non-`ok` statuses raise `WikidotStatusCodeException`. Successful `status: ok` deletion behavior and request construction remain unchanged.

## Related Issue

Builds on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), [246-pr-page-direct-metadata-action-status-context.md](246-pr-page-direct-metadata-action-status-context.md), and [247-pr-page-rename-action-status-context.md](247-pr-page-rename-action-status-context.md). Those drafts established browser-free page writes as a practical workflow and established the adjacent action-response diagnostic pattern.

No upstream issue was filed from this local workspace.

## Changes

- Validate the single `deletePage` response returned by `Page.destroy(...)` before treating deletion as successful.
- Convert missing delete action `status` into `NoElementException` with site, page, page ID, event, and field context.
- Preserve explicit non-`ok` status handling through `WikidotStatusCodeException`.
- Add a focused public-interface regression for malformed delete responses.
- Preserve login checks, delete request construction, and successful `status: ok` deletion behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Page delete action response validation
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A delete action response missing `status` fails with contextual `NoElementException`. | `TestPageWriteMethods.test_destroy_missing_action_status_includes_site_page_event_and_field_context` returns `{"body": ""}` for the `deletePage` response and asserts `NoElementException`. | Returning success, raising a raw `KeyError`, fabricating success, or omitting action context rejects this local completion claim. |
| The malformed delete action message identifies site, page, page ID, event, and missing field. | The focused regression asserts `Page action response is malformed for site: test-site, page: test-page (id=12345, event=deletePage, field=status)`. | Omitting site, page fullname, page ID, event, or field context makes cleanup/delete failures ambiguous and rejects this local completion claim. |
| Successful deletion remains unchanged. | Existing `test_destroy_success` passes with the `status: ok` delete fixture. | Regressions in delete request construction, login checks, or normal no-return deletion behavior reject this local completion claim. |
| Adjacent page write behavior remains unchanged. | `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q` passes. | Regressions in tag, parent, rename, vote, metadata, or delete write helpers reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `8966a7e fix(page): guard delete action status`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_destroy_missing_action_status_includes_site_page_event_and_field_context -q` failed before the fix because `Page.destroy(...)` returned without raising.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_destroy_missing_action_status_includes_site_page_event_and_field_context -q` passed.
- `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 27 tests.
- `uv run pytest tests/unit -q` passed 798 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Page.destroy(...)` raises `NoElementException` when the `deletePage` response lacks `status`.
- The malformed-response message includes site `unix_name`, page fullname, page ID, action event, and missing field.
- Explicit non-`ok` `deletePage` statuses are not treated as successful deletion.
- Successful delete paths keep the existing request body, login check, and no-return behavior.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Page deletion is used both as an explicit lifecycle operation and as cleanup around created test or publishing pages. Callers should not proceed as if a page was deleted when Wikidot returned a malformed or non-success action result. Validating the action status makes delete behavior consistent with adjacent page write helpers and gives callers a precise retry/debug signal when Wikidot omits the required status field.

## Local Evidence, Not For Upstream Paste

- Existing integration tests exercise page lifecycle delete and cleanup paths, so `Page.destroy(...)` is a real operational surface rather than an unused API.
- Earlier local drafts intentionally left delete actions unchanged while hardening read retries, then later slices hardened page edit locks, save status, rating actions, metadata actions, and rename action status.
- The refreshed complexity memo still lists page action/read boundaries as useful leads; this slice closes the delete action-response boundary outside the already-covered metadata and rename action paths.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, page source text, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not retry delete writes, change delete request construction, add local deleted-state tracking, add per-action result objects, alter `Page.create_or_edit(...)`, touch metadata actions, or modify live Wikidot behavior. It only validates the `deletePage` action response before treating deletion as successful.
