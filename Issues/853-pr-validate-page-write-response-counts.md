# PR: Validate page write response counts

## Problem Statement

`Page.create_or_edit(...)` sends two direct one-request AMC batches: an `edit/PageEditModule` request to acquire the edit lock and a `savePage` action to write the page. Before this change, either direct call could return zero responses and leak Python's raw `IndexError("list index out of range")` before wikidot.py could explain which site, page, and page-write phase broke the direct response-count contract.

This was a low-context failure at the central browser-free page write boundary. It also bypassed the existing edit-lock and save diagnostics that validate returned payloads, status fields, lock tokens, revision IDs, and local cache updates after a response has already been selected.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free page creation, editing, and publishing as practical infrastructure for page migration, generated maintenance scripts, source verification, metadata updates, local tests, and publish-result ledgers. Existing local slices hardened this workflow around page write inputs, retained page/site/client state, edit-lock payload shape, edit-lock fields, edit-lock revision IDs, save payload shape, save status type, stale post-save search fallback, local source/title synchronization, revision-cache invalidation, and direct metadata response counts. They did not validate the direct edit-lock or save response count before indexing the returned response sequence.

The local fix is committed as `adeffe0`.

## Affected Workflows

- Browser-free page creation through `Page.create_or_edit(...)`.
- Browser-free existing-page edits through `Page.create_or_edit(..., page_id=...)`.
- `Page.edit(...)`, `Site.page.create(...)`, and `Site.page.publish(...)` when they delegate to the shared page write helper.
- Generated publishing, migration, or maintenance scripts that wrap or mock `site.amc_request(...)`.
- Fixture-backed tests where a malformed adapter returns the wrong number of direct page-write responses.
- Debugging malformed connector behavior where response count, not payload shape, is the first broken contract.

## Proposed Fix

Add a small page write response-count guard. Validate that the direct edit-lock and `savePage` response sequences each have exactly one entry before indexing and parsing them. Raise `UnexpectedException` with site/page/write-phase context and expected/actual counts on mismatch.

## Implementation Notes

The change adds `_require_page_write_response_count(...)` next to the existing edit-lock and save-response helpers. `Page.create_or_edit(...)` now stores the raw edit-lock response list, validates the count with `module=edit/PageEditModule` context, then parses the selected response through `_require_page_edit_lock_response_data(...)`. The later save call uses the same helper with `event=savePage` context before parsing `response.json()` and `_require_page_save_status(...)`.

The guard intentionally stays local to page write handling instead of adding a generic `Site.amc_request(...)` response-count policy. Direct action/read callers already have domain-specific diagnostics, and a broad site-level guard could preempt more useful page/forum/member/application context.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_rejects_lock_response_count_mismatch_before_parsing -q --tb=short
uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_rejects_save_response_count_mismatch_before_parsing -q --tb=short
uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_rejects_lock_response_count_mismatch_before_parsing tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_rejects_save_response_count_mismatch_before_parsing -q --tb=short
uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit -q --tb=short
uv run pytest tests/unit/test_page.py -q --tb=short
uv run pytest tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py -q --tb=short
uv run pytest tests/unit -q --tb=short
uv run ruff check
uv run ruff format --check
uv run mypy src tests
uv run pyright src tests
git diff --check
```

The focused RED runs failed before the fix because the new regressions leaked raw `IndexError` from indexing empty edit-lock and save response lists. The focused GREEN run passed after adding the count guard. `TestPageCreateOrEdit` passed 72 tests, `tests/unit/test_page.py` passed 495 tests, adjacent page/site coverage passed 761 tests, full unit verification passed 3969 tests, ruff and pyright were clean, mypy reported only existing untyped-function notes with no issues, and whitespace checks passed.

## Compatibility And Risk Notes

- Valid page writes still send the same edit-lock and `savePage` request bodies and parse the same returned payloads.
- Existing malformed edit-lock payload, lock field, revision ID, save payload, missing save status, malformed save status type, explicit non-ok save status, post-save lookup, and cache update diagnostics remain unchanged.
- Mismatched edit-lock response-count failures occur before lock payload parsing or any save request.
- Mismatched save response-count failures occur after a valid lock response is parsed but before save payload parsing, status handling, post-save lookup, or local page/source/cache updates.
- The diagnostic does not include raw generated module bodies, raw response JSON, credentials, cookies, auth JSON, page lock secrets, private source text, local rollout paths, or account material.

## Rationale For Upstream Suitability

Direct page writes rely on positional correspondence between each submitted one-request batch and its returned response. When that correspondence is broken, wikidot.py should report the page write response-count failure directly instead of leaking a raw Python indexing error.

## Scope

This slice does not change retry policy, direct `site.amc_request(...)` behavior, request construction, edit-lock payload parsing, save status parsing, stale search fallback, local cache synchronization, metadata writes, live Wikidot behavior, or upstream filing state.
