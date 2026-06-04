# PR Draft: Validate Page Rename Action Status Before Local Name Updates

## Summary

`Page.rename(...)` sends a `renamePage` action and then updates local `fullname`, `category`, and `name`. Adjacent local slices now validate page edit locks, save status, rating action points, batched metadata action status, and direct metadata action status before treating write actions as successful. Rename still had the same response-boundary gap: any returned response object was treated as success, so a malformed response without `status` could update local page identity from an unclassified mutation result.

This follow-up validates the `renamePage` action response before local page identity is changed. A missing `status` now raises `NoElementException` with site, page, page ID, event, and field context. Explicit non-`ok` statuses raise `WikidotStatusCodeException`. Successful `status: ok` rename behavior, request construction, category splitting, and method chaining remain unchanged.

## Related Issue

Builds on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), and [246-pr-page-direct-metadata-action-status-context.md](246-pr-page-direct-metadata-action-status-context.md). Those drafts established browser-free page writes as a practical workflow and established the adjacent action-response diagnostic pattern.

No upstream issue was filed from this local workspace.

## Changes

- Add a small generic page action status validator for non-metadata page actions.
- Validate the single `renamePage` response returned by `Page.rename(...)` before updating local page identity.
- Convert missing rename action `status` into `NoElementException` with site, page, page ID, event, and field context.
- Preserve explicit non-`ok` status handling through `WikidotStatusCodeException`.
- Add a focused public-interface regression proving malformed rename responses do not update local page names.
- Preserve login checks, request construction, successful simple rename, category-qualified rename, category/name splitting, and method chaining.

## Type Of Change

- Bug fix / diagnostics improvement
- Page rename action response validation
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A rename action response missing `status` fails with contextual `NoElementException`. | `TestPageWriteMethods.test_rename_missing_action_status_does_not_update_local_name` returns `{"body": ""}` for the `renamePage` response and asserts `NoElementException`. | Returning success, raising a raw `KeyError`, fabricating success, or omitting action context rejects this local completion claim. |
| The malformed rename action message identifies site, page, page ID, event, and missing field. | The focused regression asserts `Page action response is malformed for site: test-site, page: test-page (id=12345, event=renamePage, field=status)`. | Omitting site, page fullname, page ID, event, or field context makes the failure ambiguous and rejects this local completion claim. |
| A malformed rename action does not update local page identity. | The focused regression asserts `fullname`, `category`, and `name` remain unchanged after the exception. | Updating any local identity field before validating the response rejects this local completion claim. |
| Successful rename behavior remains unchanged. | Existing `test_rename_success` and `test_rename_with_category` pass with `status: ok` fixtures. | Regressions in request bodies, category splitting, simple rename, category-qualified rename, or method chaining reject this local completion claim. |
| Adjacent page write and publish behavior remains unchanged. | `uv run pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_site.py::TestSitePageAccessor -q` passes. | Regressions in page write helpers, metadata delegation, source verification, publish result fields, or visibility handling reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `627dbf3 fix(page): guard rename action status`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_rename_missing_action_status_does_not_update_local_name -q` failed before the fix because `Page.rename(...)` returned without raising.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_rename_missing_action_status_does_not_update_local_name tests/unit/test_page.py::TestPageWriteMethods::test_rename_success tests/unit/test_page.py::TestPageWriteMethods::test_rename_with_category -q` passed 3 tests.
- `uv run pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_site.py::TestSitePageAccessor -q` passed 44 tests.
- `uv run pytest tests/unit -q` passed 797 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Page.rename(...)` raises `NoElementException` when the `renamePage` response lacks `status`.
- The malformed-response message includes site `unix_name`, page fullname, page ID, action event, and missing field.
- `Page.rename(...)` does not update `fullname`, `category`, or `name` after a malformed action response.
- Successful simple and category-qualified rename paths keep the existing request body and local name/category behavior.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Page rename is a write operation that also mutates the in-memory `Page` identity. Callers should not observe a local page object renamed from a malformed or unclassified action response. Validating the action status before local mutation makes rename consistent with adjacent page write helpers and gives callers a precise retry/debug signal when Wikidot omits the required status field.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established browser-free page write and publish workflows as practical local surfaces, not speculative features.
- Recent adjacent slices hardened edit locks, save status, rating actions, batched metadata actions, and direct metadata actions before local state updates.
- The refreshed complexity memo still lists action/read boundaries and remaining parser messages as useful leads; this slice closes the rename action-response boundary outside the already-covered metadata action paths.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, page source text, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not retry rename writes, change rename request construction, change category parsing, add per-action result objects, alter `Page.create_or_edit(...)`, touch metadata actions, or modify live Wikidot behavior. It only validates the `renamePage` action response before treating the rename as successful and updating local page identity.
