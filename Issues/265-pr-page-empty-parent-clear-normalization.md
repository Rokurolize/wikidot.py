# PR Draft: Normalize Empty Parent Clears To None Locally

## Summary

`Page.set_parent(...)` documents that both `None` and an empty string clear a page's parent, and it already sends an empty `parentName` for both values. One local-state gap remained: after a successful `set_parent("")`, the calling `Page` object kept `parent_fullname == ""` even though the remote operation is a parent clear.

This follow-up normalizes successful empty-string parent clears to `None` locally. The same normalization is applied to `Page.set_metadata(parent_fullname="")`, because that batched metadata path also sends an empty `parentName` and should leave the original page object in the same no-parent state as `set_parent(None)`.

## Related Issue

Builds on [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), [246-pr-page-direct-metadata-action-status-context.md](246-pr-page-direct-metadata-action-status-context.md), [249-pr-page-metas-setter-action-status-context.md](249-pr-page-metas-setter-action-status-context.md), [257-pr-publish-source-verification-status.md](257-pr-publish-source-verification-status.md), and [258-pr-publish-metadata-update-count.md](258-pr-publish-metadata-update-count.md). Those drafts established browser-free page metadata writes as a practical workflow surface, hardened action status handling, and improved publish metadata result ergonomics.

No upstream issue was filed from this local workspace.

## Changes

- Normalize `Page.set_parent("")` to `parent_fullname is None` after successful action status validation.
- Normalize `Page.set_metadata(parent_fullname="")` to `parent_fullname is None` after successful batched metadata status validation.
- Preserve request payloads: both empty-string and `None` clears continue to submit `parentName: ""`.
- Preserve failed-action behavior: local `parent_fullname` is still not updated before the existing status gate succeeds.
- Add focused regressions for direct and batched parent-clear paths.

## Type Of Change

- Page metadata local-state consistency
- Parent-clear normalization
- Browser-free page mutation ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| `Page.set_parent("")` clears the local parent state to `None` after a successful response. | `TestPageWriteMethods.test_set_parent_empty_string_clears_local_parent` starts from an old parent, calls `set_parent("")`, and asserts `parent_fullname is None`. | Leaving `parent_fullname == ""` after success rejects this local completion claim. |
| Direct parent clears still send the same remote clear payload. | The focused `set_parent("")` regression asserts the submitted `parentName` is `""`. | Changing the remote payload rejects this local completion claim. |
| `Page.set_metadata(parent_fullname="")` applies the same local clear semantics after successful batched metadata validation. | `TestPageWriteMethods.test_set_metadata_empty_parent_string_clears_local_parent` starts from an old parent, calls the batched metadata path, and asserts `parent_fullname is None`. | Leaving the batched path with an empty string local parent rejects this local completion claim. |
| Failed metadata actions still do not mutate local parent state. | Existing missing-status tests for `set_parent(...)` and `set_metadata(...)` continue to pass, and normalization remains after the existing status gates. | Updating parent state before action status validation rejects this local completion claim. |
| Existing page write and metadata behavior remains intact. | `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 32 tests. | Regressions in page write methods reject this local completion claim. |
| Adjacent page and publish behavior remains unchanged. | `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 225 tests. | Regressions in page or site publish tests reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `2d1b5ba fix(page): normalize empty parent clears`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_empty_string_clears_local_parent tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_empty_parent_string_clears_local_parent -q` failed before the fix because both paths left `parent_fullname == ""`.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_empty_string_clears_local_parent tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_empty_parent_string_clears_local_parent -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 32 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 225 tests.
- `uv run --extra test pytest tests/unit -q` passed 818 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Successful `Page.set_parent("")` calls leave the calling page object's `parent_fullname` as `None`.
- Successful `Page.set_metadata(parent_fullname="")` calls leave the calling page object's `parent_fullname` as `None`.
- Direct and batched parent-clear requests still submit `parentName: ""`.
- Missing or non-`ok` action statuses still prevent local parent mutation.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Empty-string parent names are already treated as remote parent clears by the request payload. Keeping an empty string in the original `Page` object after a successful clear creates an avoidable local inconsistency: callers that check `page.parent_fullname is None` see a different state depending on whether they cleared with `None` or `""`. Normalizing the local value after successful status validation keeps the API contract coherent without changing requests, server behavior, or failure handling.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established page metadata writes, publish metadata updates, action status validation, and publish metadata result fields as practical workflow surfaces.
- This slice intentionally targets only local parent-clear normalization; metadata batching, tag updates, meta-tag diffing, page lookup, publish sequencing, and live Wikidot behavior remain separate boundaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved page contents, source text from real pages, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This is a local-state consistency fix. It does not alter how parent clears are submitted remotely; it only makes the original `Page` instance reflect the same no-parent state for both supported clear spellings.
