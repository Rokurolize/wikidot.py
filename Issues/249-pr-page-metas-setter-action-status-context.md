# PR Draft: Validate Page.metas Setter Action Status Before Updating Cache

## Summary

`Page.metas = {...}` batches `deleteMetaTag` and `saveMetaTag` actions, but it used to accept any returned response objects and immediately update the local `_metas` cache. That meant a malformed metadata action response without `status`, or an explicit non-`ok` status, could leave callers with optimistic local metadata state that was not confirmed by Wikidot.

This follow-up routes the meta-tag setter responses through the same metadata action status validator now used by `Page.set_metadata(...)`, `Page.commit_tags()`, and `Page.set_parent(...)`. A missing `status` raises `NoElementException` with site, page, page ID, event, and field context. Explicit non-`ok` statuses raise `WikidotStatusCodeException`. Successful `status: ok` meta setter batching, request construction, and cache updates remain unchanged.

## Related Issue

Builds on [007-pr-batch-meta-tag-updates.md](007-pr-batch-meta-tag-updates.md), [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), and [246-pr-page-direct-metadata-action-status-context.md](246-pr-page-direct-metadata-action-status-context.md). Those drafts established batched meta updates and the adjacent metadata action-response diagnostic pattern.

No upstream issue was filed from this local workspace.

## Changes

- Validate every returned `deleteMetaTag` / `saveMetaTag` response from the `Page.metas` setter before updating `_metas`.
- Convert missing meta setter action `status` into `NoElementException` with site, page, page ID, event, and field context.
- Preserve explicit non-`ok` metadata status handling through `WikidotStatusCodeException`.
- Add a focused public-interface regression for malformed meta setter responses.
- Preserve login checks, meta diffing, request ordering, batched request construction, and successful `status: ok` cache updates.

## Type Of Change

- Bug fix / diagnostics improvement
- Page meta setter action response validation
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A meta setter action response missing `status` fails with contextual `NoElementException`. | `TestPageWriteMethods.test_metas_setter_missing_action_status_does_not_update_local_state` returns `{"body": ""}` for the first `deleteMetaTag` response and asserts `NoElementException`. | Returning success, raising a raw `KeyError`, fabricating success, or omitting action context rejects this local completion claim. |
| The malformed meta setter message identifies site, page, page ID, event, and missing field. | The focused regression asserts `Page metadata action response is malformed for site: test-site, page: test-page (id=12345, event=deleteMetaTag, field=status)`. | Omitting site, page fullname, page ID, event, or field context makes the failure ambiguous and rejects this local completion claim. |
| Malformed meta setter responses do not update local `_metas`. | The focused regression asserts the old local meta cache remains unchanged after the exception. | Updating `_metas` before validating all returned action responses rejects this local completion claim. |
| Successful meta setter batching remains unchanged. | `TestPageWriteMethods.test_metas_setter_batches_changes` passes with three `status: ok` responses and the same delete/add/update request bodies. | Regressions in meta diffing, request order, batching, login checks, or successful local cache updates reject this local completion claim. |
| Adjacent metadata write behavior remains unchanged. | `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q` passes. | Regressions in `Page.set_metadata(...)`, direct tag/parent setters, delete, rename, vote, or other page write helpers reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `f5463a6 fix(page): guard meta setter action status`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_missing_action_status_does_not_update_local_state -q` failed before the fix because `Page.metas = {...}` returned without raising and updated `_metas`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_missing_action_status_does_not_update_local_state -q` passed.
- `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_batches_changes tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_missing_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_batches_tags_parent_and_metas tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_missing_action_status_does_not_update_local_state -q` passed 4 tests.
- `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 28 tests.
- `uv run pytest tests/unit -q` passed 799 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Page.metas = {...}` raises `NoElementException` when a returned meta action response lacks `status`.
- The malformed-response message includes site `unix_name`, page fullname, page ID, action event, and missing field.
- Explicit non-`ok` meta action statuses are not treated as successful metadata writes.
- Local `_metas` is updated only after returned action statuses have been validated.
- Successful setter paths keep the existing diffing, request order, batched request body, login check, and cache-update behavior.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

`Page.metas = {...}` remains a valid public metadata API, even though higher-level publish flows now prefer `Page.set_metadata(...)`. Metadata callers should not observe a locally updated meta cache from an unclassified action response. Validating the returned action statuses makes the setter consistent with adjacent metadata write helpers and gives callers an event-specific retry/debug signal when Wikidot omits the required status field.

## Local Evidence, Not For Upstream Paste

- Existing local drafts show meta tags are part of browser-free publish and metadata workflows, and `Page.metas = ...` remains documented as a separate public operation.
- Earlier adjacent slices hardened `Page.set_metadata(...)`, `Page.commit_tags()`, `Page.set_parent(...)`, `Page.rename(...)`, and `Page.destroy()` action responses before local state or success was accepted.
- The immediately related metadata action draft intentionally did not claim `Page.metas` setter behavior; this slice closes that remaining direct setter response boundary.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, page source text, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not retry metadata writes, change meta diffing, change request construction, add per-action result objects, alter `Page.set_metadata(...)`, change `Page.metas` getter parsing, or modify live Wikidot behavior. It only validates the returned meta setter action responses before treating the setter as successful and updating `_metas`.
