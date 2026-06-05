# PR Draft: Validate Page Rename Fullname Before Requests

## Summary

`Page.rename(new_fullname=...)` documents the new page fullname as `str`, but it did not validate the value before the rename request. A malformed non-string value could be sent as the `new_name` action payload. If the action response was treated as successful, the method assigned the non-string value to `self.fullname` and then failed while checking `":" in new_fullname`, leaving local page identity partially corrupted after remote write-side work had already happened.

This change validates `new_fullname` before login checks, AMC request construction, `renamePage` submission, action status parsing, local fullname/category/name updates, or file-cache invalidation. Invalid values now raise `ValueError("new_fullname must be a string")`.

## Outcome

Page rename callers now get deterministic preflight validation for malformed rename targets instead of partial write-side progress, non-string request payloads, or local page identity corruption after a successful action response.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use page rename workflows during browser-free cleanup jobs, migration scripts, generated page maintenance, translation workflows, and audit-ledger reconciliation.

## Current Evidence

Local rollout evidence repeatedly uses browser-free page publishing, source inspection, metadata updates, and cleanup-style page operations where local object identity must remain coherent after writes. Existing drafts [247-pr-page-rename-action-status-context.md](247-pr-page-rename-action-status-context.md) and [266-pr-page-rename-file-cache-invalidation.md](266-pr-page-rename-file-cache-invalidation.md) establish `Page.rename(...)` as a practical write/local-state surface. Those slices validate action responses and invalidate stale file metadata after a successful rename; they did not cover malformed rename target inputs before the write request.

Adjacent input-boundary drafts [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), and [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md) establish the current local pattern: documented page-write inputs should fail before login checks, request construction, remote writes, result creation, or local cache mutation.

## Related Issue

Builds directly on [247-pr-page-rename-action-status-context.md](247-pr-page-rename-action-status-context.md), [266-pr-page-rename-file-cache-invalidation.md](266-pr-page-rename-file-cache-invalidation.md), [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), and [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md).

No upstream issue was filed from this local workspace.

## Changes

- Reuse the existing page text-field validator for `Page.rename(new_fullname=...)`.
- Reject non-string rename targets with `ValueError("new_fullname must be a string")`.
- Run the validation before login checks, `renamePage` request construction, action status handling, local page identity mutation, or `_files` cache invalidation.
- Preserve valid simple and category-qualified rename behavior.
- Preserve existing action-status validation and file-cache invalidation behavior after successful renames.

## Type Of Change

- Input validation
- Public API behavior hardening
- Page rename local-state safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.rename(new_fullname=...)` must reject non-string values with `ValueError("new_fullname must be a string")` before login checks, AMC requests, action status parsing, local identity mutation, or file-cache invalidation. |
| R2 | Valid simple rename targets such as `"new-page-name"` must preserve existing request construction, action-status validation, local fullname/name/category updates, and method chaining. |
| R3 | Valid category-qualified rename targets such as `"component:new-name"` must preserve existing category/name splitting. |
| R4 | Existing malformed action-response behavior must remain unchanged: missing `status` fails before local identity mutation. |
| R5 | Existing successful rename file-cache invalidation must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent rename/page-write tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-string rename targets fail with stable `ValueError` before any page-write side effect. | `TestPageWriteMethods.test_rename_rejects_non_string_fullname_before_request` failed RED before the fix because the invalid value reached the action-status path, then passed GREEN after the fix. | Calling login, sending `renamePage`, assigning `self.fullname`, changing `category` or `name`, clearing `_files`, leaking status errors, or raising `TypeError` rejects this local completion claim. | Page rename preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Simple successful rename remains unchanged. | `TestPageWriteMethods.test_rename_success` passed after the fix. | Changing the request body, return value, local fullname, local name, or default category rejects this local completion claim. | Page rename success path | `tests/unit/test_page.py` |
| R3 | Category-qualified successful rename remains unchanged. | `TestPageWriteMethods.test_rename_with_category` passed after the fix. | Regressing category/name splitting rejects this local completion claim. | Page rename category path | `tests/unit/test_page.py` |
| R4 | Malformed rename action responses still fail before local mutation. | `TestPageWriteMethods.test_rename_missing_action_status_does_not_update_local_name` passed after the fix. | Updating local identity from a malformed response or dropping site/page/event context rejects this local completion claim. | Page rename action response boundary | `tests/unit/test_page.py` |
| R5 | Successful rename still invalidates cached files. | `TestPageWriteMethods.test_rename_success_invalidates_cached_files` passed after the fix. | Reusing cached file metadata derived from the old page path after a successful rename rejects this local completion claim. | Page rename local cache consistency | `tests/unit/test_page.py` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, rename-focused tests passed, `TestPageWriteMethods` passed, adjacent page/site write tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `1f486ea fix(page): validate rename fullname input`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_rename_rejects_non_string_fullname_before_request -q` failed before the fix because the invalid value reached `renamePage` action-status handling instead of failing at the input boundary.
- GREEN: the same focused command passed 1 test after adding `new_fullname` preflight.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_rename_success tests/unit/test_page.py::TestPageWriteMethods::test_rename_with_category tests/unit/test_page.py::TestPageWriteMethods::test_rename_success_invalidates_cached_files tests/unit/test_page.py::TestPageWriteMethods::test_rename_missing_action_status_does_not_update_local_name tests/unit/test_page.py::TestPageWriteMethods::test_rename_rejects_non_string_fullname_before_request -q` passed 5 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 42 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageEdit tests/unit/test_site.py::TestSitePageAccessor -q` passed 102 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run --extra test pytest tests/unit -q` passed 951 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `page.rename(3)` raises `ValueError("new_fullname must be a string")` before calling `login_check()`, constructing or sending a `renamePage` request, parsing action status, mutating `fullname`, `category`, or `name`, or clearing `_files`.
- `page.rename("new-page-name")` keeps the existing successful simple rename behavior.
- `page.rename("component:new-name")` keeps the existing category-qualified rename behavior.
- Missing `renamePage` action `status` still fails before local identity mutation.
- Successful renames still clear cached file metadata.
- The new test uses unit-level code only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Rename targets determine both the remote `renamePage` payload and the local `Page` identity after success. Runtime validation keeps the documented `str` API honest and prevents malformed caller configuration from reaching write-side work or leaving the object in a partially invalid state. The change is narrow: it rejects malformed values instead of coercing them and does not change valid rename semantics.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used page write, publish, source collection, and cleanup-style workflows where local page identity and audit records matter.
- Existing local drafts covered rename action-status validation and post-rename file-cache invalidation, but did not cover malformed rename target inputs.
- Adjacent page input-boundary drafts covered parent names, source, title/comment, metadata, and boolean controls; `new_fullname` was the remaining page rename target input in this write surface.
- This slice only validates rename target input type; it does not change page-name syntax, category parsing, remote rename request shape for valid strings, action-status validation, file-cache invalidation, source/revision/vote caches, live Wikidot behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw action response bodies, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed rename targets instead of coercing them with `str(...)`. Callers that load page names from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should normalize the final target page fullname to `str` before calling `Page.rename(...)`.
