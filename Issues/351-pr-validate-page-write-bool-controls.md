# PR Draft: Validate Page Write Boolean Controls Before Side Effects

## Summary

`Page.create_or_edit(...)`, `Page.edit(...)`, `Site.page.create(...)`, and `Site.page.publish(...)` document several write-control arguments as booleans, but malformed truthy strings or other non-bool values were not validated at the public API boundary. A caller passing `force_edit="yes"` could reach forced edit-lock behavior or existing-page edit delegation; `raise_on_exists="false"` could be treated as enabled after an edit-lock request; and `verify_source="false"` could trigger source verification after a page save instead of being treated as a malformed configuration.

This change validates page write boolean controls before login checks, existing-page lookup, current-source fetches, edit-lock requests, save requests, post-save page-ID resolution, source verification, metadata writes, result creation, or local cache mutation. Invalid controls now raise `ValueError("<field> must be a boolean")`.

## Outcome

Browser-free page creation, edit, and publish callers now get deterministic preflight validation for malformed boolean controls instead of partial write-side progress, unexpected forced edit behavior, unintended source verification, or raw downstream errors.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use direct page write APIs or `Site.page.publish(...)` for browser-free page publishing, migration scripts, generated page updates, translation workflows, audit ledgers, and cleanup jobs.

## Current Evidence

Local rollout evidence repeatedly uses browser-free page publishing and page edit workflows that coordinate forced edit locks, create-versus-edit branching, source verification, metadata updates, and audit-friendly publish result records. Existing drafts [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md), [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [346-pr-validate-publish-visibility-controls.md](346-pr-validate-publish-visibility-controls.md), [347-pr-validate-publish-source-normalizer.md](347-pr-validate-publish-source-normalizer.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), and [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md) establish page writes and publish controls as practical operational surfaces. Those slices covered publish orchestration, visibility-control numeric validation, source-normalizer callable validation, source/text input validation, metadata ordering, lock diagnostics, and result fields; they did not cover malformed boolean controls.

## Related Issue

Builds directly on [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [346-pr-validate-publish-visibility-controls.md](346-pr-validate-publish-visibility-controls.md), [347-pr-validate-publish-source-normalizer.md](347-pr-validate-publish-source-normalizer.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), and [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a shared page boolean-control validator for documented `bool` page write controls.
- Reject non-bool `force_edit` values with `ValueError("force_edit must be a boolean")`.
- Reject non-bool `raise_on_exists` values with `ValueError("raise_on_exists must be a boolean")`.
- Reject non-bool `verify_source` values with `ValueError("verify_source must be a boolean")`.
- Apply validation to `Page.create_or_edit(...)` before login checks, edit-lock acquisition, forced lock request construction, existing-page branch handling, save requests, post-save lookup, or local cache mutation.
- Apply validation to `Page.edit(force_edit=...)` before login checks, current-source defaulting, page-ID lookup, `Page.create_or_edit(...)` delegation, revision-cache invalidation, or local cache mutation.
- Apply validation to `Site.page.create(force_edit=...)` before login checks, force-edit existing-page lookup, existing-page edit delegation, or create request delegation.
- Apply validation to `Site.page.publish(force_edit=..., verify_source=...)` before login checks, page lookup, create/edit delegation, post-save page-ID resolution, source refresh, source verification, metadata writes, or result creation.
- Preserve valid `True` and `False` behavior for forced edits, create-versus-edit branching, direct `raise_on_exists`, source verification, source normalizers, metadata ordering, visibility controls, local cache sync, revision-cache invalidation, and `PagePublishResult` fields.

## Type Of Change

- Input validation
- Public API behavior hardening
- Write preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.create_or_edit(..., force_edit=..., raise_on_exists=...)` must reject non-bool controls with stable `ValueError` messages before login checks, edit-lock requests, forced-lock payload construction, save requests, post-save lookup, or local cache mutation. |
| R2 | `Page.edit(force_edit=...)` must reject explicit non-bool controls with `ValueError("force_edit must be a boolean")` before login checks, current-source fetches, page-ID reads, create/edit delegation, save requests, revision-cache invalidation, or local cache mutation. |
| R3 | `Site.page.create(force_edit=...)` must reject non-bool controls before login checks, force-edit lookup, existing-page edit delegation, or `Page.create_or_edit(...)` delegation. |
| R4 | `Site.page.publish(force_edit=..., verify_source=...)` must reject non-bool controls before login checks, page lookup, create/edit work, post-save page-ID resolution, source verification, metadata writes, or result creation. |
| R5 | Valid page-write behavior must remain unchanged for `True` and `False` controls, valid source/title/comment strings, forced edits, create/edit branching, source verification, metadata ordering, visibility controls, source normalizers, and publish result fields. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent create/edit/publish tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct create/edit helper fails with stable `ValueError` before any page-write side effect. | `TestPageCreateOrEdit.test_create_or_edit_rejects_non_bool_controls_before_request` failed RED before the fix because malformed controls reached login and edit-lock handling, then passed GREEN after the fix. | Calling login, adding `force_lock=yes`, sending edit-lock or save requests, constructing a local `Page`, assigning `PageSource`, or leaking lock/save errors rejects this local completion claim. | Direct page write preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Instance edit fails for malformed `force_edit` before reads or writes. | `TestPageEdit.test_edit_rejects_non_bool_force_edit_before_request` failed RED before the fix because the invalid value reached login and `Page.create_or_edit(...)` delegation, then passed GREEN after the fix. | Calling login, fetching current source, reading page ID, delegating to `Page.create_or_edit(...)`, sending AMC requests, invalidating revisions, or changing local caches rejects this local completion claim. | Page edit preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | High-level create fails before login or force-edit lookup. | `TestSitePageAccessor.test_create_rejects_non_bool_force_edit_before_login` failed RED before the high-level preflight with `DID NOT RAISE`, then passed GREEN after the fix. | Calling login, looking up an existing page, editing an existing page, or delegating to `Page.create_or_edit(...)` rejects this local completion claim. | Site create preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R4 | High-level publish fails before create/edit work. | `TestSitePageAccessor.test_publish_rejects_non_bool_controls_before_save` failed RED before the high-level preflight with `DID NOT RAISE`, then passed GREEN after the fix. | Calling login, looking up a page, calling `Page.create_or_edit(...)`, editing an existing page, resolving page IDs, refreshing source, writing metadata, or returning a result rejects this local completion claim. | Publish control preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R5 | Existing page write and publish behavior remains green. | Focused boolean-control tests passed 6 tests; adjacent create/edit/publish tests passed 60 tests; full unit passed 950 tests. | Regressing valid `True`/`False` forced edits, direct `raise_on_exists`, publish source verification, source normalizers, metadata ordering, visibility retry, local source sync, revision invalidation, or result exports rejects this local completion claim. | Page write and publish workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent create/edit/publish tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `711576c fix(page): validate write bool controls`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_rejects_non_bool_controls_before_request tests/unit/test_page.py::TestPageEdit::test_edit_rejects_non_bool_force_edit_before_request tests/unit/test_site.py::TestSitePageAccessor::test_create_rejects_non_bool_force_edit_before_login tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_non_bool_controls_before_save -q` failed 6 tests before the fix. Direct `Page.create_or_edit(...)` malformed controls reached login and edit-lock handling; `Page.edit(...)` reached login and downstream delegation; Site create/publish controls produced `DID NOT RAISE` because malformed truthy controls were accepted.
- GREEN: the same focused command passed 6 tests after adding boolean-control preflight.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageEdit tests/unit/test_site.py::TestSitePageAccessor -q` passed 60 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run --extra test pytest tests/unit -q` passed 950 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `Page.create_or_edit(site, "new-page", force_edit="yes")` raises `ValueError("force_edit must be a boolean")` before calling login, edit-lock AMC requests, save AMC requests, post-save lookup, or local cache mutation.
- `Page.create_or_edit(site, "new-page", raise_on_exists="false")` raises `ValueError("raise_on_exists must be a boolean")` before calling login, edit-lock AMC requests, save AMC requests, post-save lookup, or local cache mutation.
- `page.edit(force_edit="yes")` raises `ValueError("force_edit must be a boolean")` before calling login, fetching current source, reading page ID, delegating to `Page.create_or_edit(...)`, sending AMC requests, invalidating cached revisions, or changing local caches.
- `Site.page.create("new-page", force_edit="yes")` raises `ValueError("force_edit must be a boolean")` before login, force-edit lookup, existing-page edit delegation, or `Page.create_or_edit(...)` delegation.
- `Site.page.publish("new-page", force_edit="yes")` raises `ValueError("force_edit must be a boolean")` before login, page lookup, create/edit saves, post-save page-ID resolution, source verification, metadata writes, or result creation.
- `Site.page.publish("new-page", verify_source="false")` raises `ValueError("verify_source must be a boolean")` before login, page lookup, create/edit saves, post-save page-ID resolution, source refresh, metadata writes, or result creation.
- Existing successful create/edit/publish behavior remains green for valid `True` and `False` controls.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Boolean controls decide whether a page write uses forced edit-lock behavior, whether direct create/edit raises on existing pages, and whether publish performs saved-source verification. If caller configuration passes strings from CLI arguments, environment variables, JSON, YAML, or spreadsheets, wikidot.py should reject those values before any write-side progress can occur. Runtime validation keeps the documented `bool` API honest without changing valid page saves or publish behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free publish and edit flows that coordinated forced edit locks, source verification, metadata updates, source caches, and publish result ledgers.
- Existing local drafts covered page publish orchestration, visibility controls, source normalizers, source/text input validation, metadata ordering, edit lock diagnostics, local cache sync, revision cache invalidation, parent input validation, and meta input validation, but did not cover malformed boolean controls.
- The focused RED failures showed malformed boolean controls reaching edit-lock handling, downstream edit delegation, or Site create/publish branches without stable preflight.
- This slice only validates page write boolean-control shape; it does not change fullname validation, source/text input validation, tag/parent/meta validation, valid source serialization, edit lock handling, save response validation, source verification comparison, source normalizers, metadata writes, visibility retry behavior, result fields, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed boolean controls instead of coercing truthy or falsy values. Callers that load these controls from text-based configuration should parse them into real booleans before calling wikidot.py write helpers.
