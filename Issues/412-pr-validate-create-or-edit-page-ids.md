# PR Draft: Validate Create Or Edit Page IDs

## Summary

`Page.create_or_edit(...)` documents `page_id` as an optional integer used when editing an existing page, but malformed non-`None` values were not validated at the public API boundary. Because Python treats `bool` as an `int` subclass, `page_id=True` or `page_id=False` could enter the edit path as numeric-looking identifiers, while strings and floats could reach login, edit-lock acquisition, forced lock handling, save request construction, stale search fallback, or downstream lock response errors before callers got a stable diagnostic.

This change validates the optional `page_id` before login checks, edit-lock requests, save requests, post-save lookup, stale search fallback, or local cache mutation. Invalid non-`None` values now raise `ValueError("page_id must be an integer or None")`.

## Outcome

Browser-free page creation and edit callers now get deterministic preflight validation for malformed edit identifiers instead of partial write-side progress or downstream lock/save errors.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use direct page write APIs or `Site.page.publish(...)` for browser-free page publishing, migration scripts, generated page updates, translation workflows, audit ledgers, and cleanup jobs.

## Current Evidence

Local rollout evidence repeatedly uses browser-free page lookup, creation, edit, publish, source verification, and audit-friendly publish result workflows. Existing drafts [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), [259-pr-page-edit-local-cache-sync.md](259-pr-page-edit-local-cache-sync.md), [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md), [262-pr-page-edit-revision-count-sync.md](262-pr-page-edit-revision-count-sync.md), [347-pr-validate-publish-source-normalizer.md](347-pr-validate-publish-source-normalizer.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), and [408-pr-reject-boolean-publish-visibility-controls.md](408-pr-reject-boolean-publish-visibility-controls.md) establish page writes and publish controls as practical operational surfaces.

Those prior slices are not duplicates. Issues349 and 350 validate page source and text fields, Issue351 validates page write boolean controls, Issue353 validates page vote values, and Issue408 rejects boolean publish visibility controls. None of them validates the optional create/edit `page_id` identifier.

## Related Issue

Builds directly on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), [259-pr-page-edit-local-cache-sync.md](259-pr-page-edit-local-cache-sync.md), [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md), [262-pr-page-edit-revision-count-sync.md](262-pr-page-edit-revision-count-sync.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), and [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a shared optional page-ID validator for `Page.create_or_edit(...)`.
- Reject `page_id=True` and `page_id=False` with `ValueError("page_id must be an integer or None")`.
- Reject string, float, and other non-integer non-`None` page IDs with the same stable diagnostic.
- Apply validation before login checks, edit-lock acquisition, forced lock request construction, existing-page branch handling, save requests, post-save lookup, stale search fallback, or local cache mutation.
- Preserve `page_id=None` create behavior, including the existing "page_id must be specified when editing existing page" error when a lock response reports that the page already exists.
- Preserve valid non-boolean integer `page_id` edit behavior and stale ListPages fallback behavior.

## Type Of Change

- Input validation
- Public API behavior hardening
- Write preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.create_or_edit(..., page_id=True or False)` must reject the value with `ValueError("page_id must be an integer or None")` before login checks, edit-lock requests, forced-lock payload construction, save requests, stale search fallback, post-save lookup, or local cache mutation. |
| R2 | `Page.create_or_edit(..., page_id="12345" or 12345.0)` must reject the value with the same stable diagnostic before login checks or write-side requests. |
| R3 | `page_id=None` must remain allowed for create attempts and must preserve the existing downstream error when a reported existing page cannot be edited without a concrete page ID. |
| R4 | Valid non-boolean integer page IDs must remain allowed and must preserve existing edit and stale ListPages fallback behavior. |
| R5 | Existing page write, source/text validation, boolean-control validation, edit-lock diagnostics, save status diagnostics, publish helper behavior, local source sync, revision-cache invalidation, and Site page accessor behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent create/edit/site tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Boolean page IDs fail before any page-write side effect. | New `TestPageCreateOrEdit.test_create_or_edit_rejects_invalid_page_id_before_login` failed RED because booleans reached login and edit-lock handling, then passed GREEN after the validator was added. | Treating `True` or `False` as edit identifiers, calling login, sending edit-lock or save requests, constructing a local `Page`, assigning `PageSource`, or leaking lock/save errors rejects this local completion claim. | Direct page write preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | String and float page IDs fail with the same stable diagnostic before login. | The same focused regression failed RED because malformed non-integer page IDs reached login and lock handling, then passed GREEN after the validator was added. | Calling login, sending edit-lock or save requests, reaching stale search fallback, mutating caches, or leaking downstream lock/save errors rejects this local completion claim. | Direct page write preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Create attempts without an edit page ID keep their existing behavior. | `TestPageCreateOrEdit` passed 20 tests after the validation change, preserving the existing create and missing-ID branches. | Rejecting `None` at the API boundary, changing the existing missing-ID diagnostic, changing create behavior, or changing lock handling rejects this local completion claim. | Page create/edit branch behavior | `tests/unit/test_page.py` |
| R4 | Real integer page IDs keep existing edit behavior and stale ListPages fallback behavior. | `TestPageCreateOrEdit` passed 20 tests, including the existing stale search fallback coverage that preserves `page_id=12345`. | Rejecting non-bool integers, dropping the requested page ID, changing stale search fallback, or changing saved `Page` identity rejects this local completion claim. | Existing page edit path | `tests/unit/test_page.py` |
| R5 | Existing page and site write behavior remains green. | Adjacent create/edit/site tests passed 72 tests; page and site unit tests passed 371 tests; full unit tests passed 1458 tests. | Regressing source/text validation, boolean-control validation, edit-lock diagnostics, save status diagnostics, publish behavior, local cache sync, revision invalidation, or Site page accessor behavior rejects this local completion claim. | Page write and site workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent page/site tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `bc40a80 fix(page): validate create_or_edit page ids`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_rejects_invalid_page_id_before_login -q` failed 4 tests before the fix. `page_id=True`, `page_id=False`, `page_id="12345"`, and `page_id=12345.0` reached login and edit-lock handling, then raised `TargetErrorException("Page existing-page is locked or other locks exist")` from mocked lock response handling instead of a stable preflight error.
- GREEN: the same focused command passed 4 tests after adding optional page-ID preflight.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left both files unchanged.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCreateOrEdit -q` passed 20 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageEdit tests/unit/test_site.py::TestSitePageAccessor -q` passed 72 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 371 tests.
- `uv run --extra test pytest tests/unit -q` passed 1458 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `Page.create_or_edit(site, "existing-page", page_id=True)` and `Page.create_or_edit(site, "existing-page", page_id=False)` raise `ValueError("page_id must be an integer or None")` before calling login, edit-lock AMC requests, save AMC requests, stale search fallback, post-save lookup, or local cache mutation.
- `Page.create_or_edit(site, "existing-page", page_id="12345")` and `Page.create_or_edit(site, "existing-page", page_id=12345.0)` raise `ValueError("page_id must be an integer or None")` before calling login, edit-lock AMC requests, save AMC requests, stale search fallback, post-save lookup, or local cache mutation.
- `Page.create_or_edit(site, "new-page", page_id=None)` keeps the existing create path behavior.
- `Page.create_or_edit(site, "existing-page", page_id=12345)` keeps the existing edit path behavior and preserves the provided page ID through stale search fallback.
- Existing page write and publish behavior remains green for valid sources, text fields, boolean controls, source normalizers, edit-lock responses, save responses, local cache sync, revision-cache invalidation, and Site page accessors.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`page_id` is a write-path identifier that decides whether `Page.create_or_edit(...)` can edit an existing page after the edit-lock response. Callers that load values from JSON, YAML, CLI flags, spreadsheets, generated structures, or audit ledgers should get a stable boundary error for malformed identifiers instead of reaching login, lock, save, fallback, or cache mutation work.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free publish and edit flows that coordinated direct page lookup, forced edit locks, source verification, metadata updates, source caches, and publish result ledgers.
- Existing local drafts covered page lookup/create/edit hardening, browser-free publish orchestration, edit-lock diagnostics, save diagnostics, local cache sync, revision cache invalidation, source/text input validation, page write boolean controls, page vote validation, source normalizers, and publish visibility controls, but did not cover malformed optional `page_id`.
- The focused RED failures showed malformed page IDs reaching login and edit-lock handling before the fix. The GREEN regression covers booleans, strings, and floats before any mocked login or AMC request can run.
- This slice only validates optional page-ID shape; it does not change fullname validation, source/text input validation, tag/parent/meta validation, valid source serialization, edit lock handling, save response validation, source verification comparison, source normalizers, metadata writes, visibility retry behavior, result fields, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed page IDs instead of coercing values. Callers that load page identifiers from text-based configuration should parse and validate those values into real integers before calling wikidot.py write helpers.
