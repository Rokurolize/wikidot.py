# PR Draft: Reuse Page Save Response Data

## Summary

`Page.create_or_edit(...)` already receives a single `savePage` response after acquiring the edit lock. On a non-`ok` save status, the implementation decoded that same response JSON once to check the status and again to pass the status into `WikidotStatusCodeException`.

This fix stores the save response data once and reuses it for both the status check and the exception argument. Login checks, lock acquisition, page ID handling, `savePage` request construction, success-path stale-search fallback, edit behavior, publish behavior, and exception type/message/status remain unchanged.

## Related Issue

Builds on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), which covered create/edit save result behavior, and is adjacent to [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), which covered sensitive-data handling for the same edit-lock and `savePage` workflow.

This also supports browser-free publish flows built on [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md) and [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md).

No upstream issue was filed from this local workspace.

## Changes

- Decode the `savePage` response JSON once in `Page.create_or_edit(...)`.
- Reuse `response_data["status"]` for the non-`ok` check and the raised `WikidotStatusCodeException`.
- Add a negative-path regression test asserting one save-response JSON decode on save failure.
- Preserve login enforcement, edit-lock acquisition, lock error handling, `raise_on_exists` behavior, missing `page_id` behavior, `savePage` request fields, exception class/message/status, stale ListPages fallback, edit workflow, and publish helpers.

## Type Of Change

- Performance improvement
- Refactoring
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A failed `savePage` response should be decoded once. | `TestPageCreateOrEdit.test_create_or_edit_save_failure_decodes_response_once` asserts `mock_save_response.json.call_count == 1`. | The RED test failed before the fix with `assert 2 == 1`. |
| A non-`ok` save status should still raise the existing exception with the same status. | The focused test still expects `WikidotStatusCodeException` with `Failed to create or edit page`. | Returning success, changing exception type, or dropping the status would fail the regression test or existing create/edit tests. |
| Page create/edit behavior stays green. | `uv run pytest tests/unit/test_page.py` passed 94 tests. | Regressions in lock handling, create, edit, source, metadata, revisions, files, votes, or stale-search behavior reject the local completion claim. |
| Adjacent page and site workflows stay green. | `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py` passed 214 tests. | Publish, page accessor, revision, file, vote, or related page workflow regressions reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `c3caa08 perf(page): reuse save response data`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_save_failure_decodes_response_once` failed before the fix with `assert 2 == 1`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_save_failure_decodes_response_once`
- `uv run pytest tests/unit/test_page.py` passed 94 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py` passed 214 tests.
- `uv run pytest tests/unit` passed 631 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- `Page.create_or_edit(...)` still acquires a page edit lock before saving.
- `savePage` request construction remains unchanged, including `lock_secret`, `page_id`, `title`, `source`, `comment`, `force_edit`, and metadata fields.
- A failed `savePage` response's JSON body is decoded once.
- A non-`ok` save status still raises `WikidotStatusCodeException("Failed to create or edit page: ...", status)`.
- A successful `savePage` response still returns the page from normal lookup when available.
- The stale-search fallback after successful save still returns a usable `Page`.
- Existing create, edit, publish, source, metadata, revision, file, and vote tests continue to pass.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

`Page.create_or_edit(...)` is the core low-level write path used directly by callers and indirectly by browser-free publishing helpers. Once the save response body has been decoded to inspect status, decoding it again for the same status does not add information. Reusing the parsed data removes avoidable response work while keeping the public create/edit behavior unchanged.

## Local Evidence, Not For Upstream Paste

- [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md) established the local create/edit save-result behavior and fallback expectations.
- [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md) covered the same edit-lock and `savePage` request path from the logging/privacy side.
- The focused RED test demonstrated the remaining avoidable work: a failed `savePage` response was decoded twice.
- Keep private rollout paths, account names, sandbox details, raw command transcripts, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not change write retry policy. `savePage` remains a single write request after lock acquisition, and failed save responses still raise immediately through the existing exception path.
