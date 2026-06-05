# PR Draft: Validate Page Source Inputs Before Page Writes

## Summary

`Page.create_or_edit(...)`, `Page.edit(source=...)`, `Site.page.create(source=...)`, and `Site.page.publish(source=...)` all document page source as `str`, but malformed non-string values were not validated consistently at the public API boundary. Direct page writes could proceed into login, edit-lock acquisition, AMC request construction, or local `PageSource` cache updates with non-string source payloads. High-level `Site.page.create(...)` and `Site.page.publish(...)` could pass the malformed value into downstream write helpers before any stable caller-facing validation.

This change validates explicit page source input before login checks, existing-page lookup, page edit-lock requests, save requests, post-save page-ID resolution, source verification, metadata writes, or local source-cache mutation. Invalid source input now raises `ValueError("source must be a string")`.

## Outcome

Browser-free page creation, edit, and publish callers now get deterministic preflight validation for malformed source payloads instead of partial write-side progress, remote calls, raw lock/save behavior, or invalid local source state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use direct page write APIs or `Site.page.publish(...)` for browser-free page publishing, migration scripts, generated page updates, translation workflows, audit ledgers, and cleanup jobs.

## Current Evidence

Local rollout evidence repeatedly uses browser-free page publishing and page edit workflows that save source, verify saved source, update tags/parents/metas, refresh source caches, and persist audit-friendly result records. Existing drafts [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [259-pr-page-edit-local-cache-sync.md](259-pr-page-edit-local-cache-sync.md), [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md), [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), [346-pr-validate-publish-visibility-controls.md](346-pr-validate-publish-visibility-controls.md), [347-pr-validate-publish-source-normalizer.md](347-pr-validate-publish-source-normalizer.md), and [348-pr-validate-meta-tag-inputs.md](348-pr-validate-meta-tag-inputs.md) establish page source writes as a practical operational surface. Those slices covered publish orchestration, source verification, source-normalizer validation, metadata ordering, edit login/read ordering, edit lock diagnostics, local cache sync, visibility controls, parent input validation, and meta input validation; they did not cover malformed page source payloads.

## Related Issue

Builds directly on [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), and [259-pr-page-edit-local-cache-sync.md](259-pr-page-edit-local-cache-sync.md). It also follows the input-boundary pattern from [342-pr-validate-tag-list-inputs.md](342-pr-validate-tag-list-inputs.md), [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), [346-pr-validate-publish-visibility-controls.md](346-pr-validate-publish-visibility-controls.md), [347-pr-validate-publish-source-normalizer.md](347-pr-validate-publish-source-normalizer.md), and [348-pr-validate-meta-tag-inputs.md](348-pr-validate-meta-tag-inputs.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a shared source input validator for the documented `str` page source shape.
- Reject non-string source values with `ValueError("source must be a string")`.
- Apply validation to `Page.create_or_edit(...)` before login checks, edit-lock acquisition, AMC save requests, post-save ListPages lookup, fallback `Page` construction, or local `PageSource` assignment.
- Apply validation to `Page.edit(source=...)` before login checks, current-source defaulting, page-ID lookup, edit-lock acquisition, save requests, revision-cache invalidation, or local source-cache mutation.
- Apply validation to `Site.page.create(source=...)` before login checks, force-edit existing-page lookup, existing-page edit delegation, or create request delegation.
- Apply validation to `Site.page.publish(source=...)` before login checks, page lookup, create/edit delegation, post-save page-ID resolution, source refresh, source verification, metadata writes, or result creation.
- Preserve valid empty-string source writes, omitted `Page.edit(source=None)` behavior, force-edit behavior, create/edit branching, source verification ordering, metadata gating, local cache sync, revision-cache invalidation, and `PagePublishResult` fields.

## Type Of Change

- Input validation
- Public API behavior hardening
- Write preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.create_or_edit(..., source=...)` must reject non-string source values with `ValueError("source must be a string")` before login checks, edit-lock requests, save requests, post-save lookup, or local source-cache mutation. |
| R2 | `Page.edit(source=...)` must reject explicit non-string source values with `ValueError("source must be a string")` before login checks, current-source fetches, page-ID reads, edit-lock requests, save requests, or local cache mutation. |
| R3 | `Site.page.create(source=...)` must reject non-string source values before login checks, force-edit lookup, existing-page edit delegation, or `Page.create_or_edit(...)` delegation. |
| R4 | `Site.page.publish(source=...)` must reject non-string source values before login checks, page lookup, create/edit work, post-save page-ID resolution, source verification, metadata writes, or result creation. |
| R5 | Valid page-write behavior must remain unchanged for empty source strings, omitted edit source, force edit, create/edit branching, source verification, metadata ordering, visibility controls, source normalizers, and publish result fields. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent create/edit/publish tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct create/edit helper fails with a stable `ValueError` before any page-write side effect. | `TestPageCreateOrEdit.test_create_or_edit_rejects_non_string_source_before_request` failed RED before the fix because the invalid value reached login and edit-lock handling, then passed GREEN after the fix. | Calling login, sending an edit-lock request, sending a save request, constructing a local `PageSource`, or leaking lock/save errors rejects this local completion claim. | Direct page write preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Instance edit fails for explicit non-string source before reads or writes. | `TestPageEdit.test_edit_rejects_non_string_source_before_request` failed RED before the fix because the invalid value delegated into `Page.create_or_edit(...)` and reached edit-lock handling, then passed GREEN after the fix. | Calling login, fetching current source, reading page ID, sending AMC requests, invalidating revisions, or changing `_source` rejects this local completion claim. | Page edit preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | High-level create fails before login or force-edit lookup. | `TestSitePageAccessor.test_create_rejects_non_string_source_before_login` failed RED before the high-level preflight because no `ValueError` was raised when downstream `Page.create_or_edit(...)` was patched, then passed GREEN after the fix. | Calling login, looking up an existing page, editing an existing page, or delegating to `Page.create_or_edit(...)` rejects this local completion claim. | Site create preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R4 | High-level publish fails before create/edit work. | `TestSitePageAccessor.test_publish_rejects_non_string_source_before_save` failed RED before the high-level preflight because no `ValueError` was raised when downstream `Page.create_or_edit(...)` was patched, then passed GREEN after the fix. | Calling login, looking up a page, calling `Page.create_or_edit(...)`, editing an existing page, resolving page IDs, refreshing source, writing metadata, or returning a result rejects this local completion claim. | Publish source preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R5 | Existing page write and publish behavior remains green. | Focused source-input tests passed 4 tests; adjacent create/edit/publish tests passed 46 tests; full unit passed 936 tests. | Regressing empty-source saves, omitted edit source defaulting, force edit, create/edit stale lookup fallback, source verification, source normalizers, metadata ordering, visibility retry, local source sync, revision invalidation, or result exports rejects this local completion claim. | Page write and publish workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent create/edit/publish tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `b18362b fix(page): validate page source inputs`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_rejects_non_string_source_before_request tests/unit/test_page.py::TestPageEdit::test_edit_rejects_non_string_source_before_request -q` failed before the fix because non-string source values reached login and edit-lock handling, surfacing `TargetErrorException` from the mocked lock path instead of stable input validation.
- GREEN: the same two Page-side focused tests passed after adding the direct source preflight.
- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_create_rejects_non_string_source_before_login tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_non_string_source_before_save -q` failed before the high-level preflight with `DID NOT RAISE`, showing the accessors passed malformed source into downstream write paths.
- GREEN: the same two Site-side focused tests passed after adding high-level source preflight.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_rejects_non_string_source_before_request tests/unit/test_page.py::TestPageEdit::test_edit_rejects_non_string_source_before_request tests/unit/test_site.py::TestSitePageAccessor::test_create_rejects_non_string_source_before_login tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_non_string_source_before_save -q` passed 4 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageEdit tests/unit/test_site.py::TestSitePageAccessor -q` passed 46 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run --extra test pytest tests/unit -q` passed 936 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `Page.create_or_edit(site, "new-page", source=3)` raises `ValueError("source must be a string")` before calling login, edit-lock AMC requests, save AMC requests, post-save lookup, or local `PageSource` assignment.
- `page.edit(source=3)` raises `ValueError("source must be a string")` before calling login, fetching current source, reading page ID, sending AMC requests, invalidating cached revisions, or changing `_source`.
- `Site.page.create("new-page", source=3)` raises `ValueError("source must be a string")` before login, force-edit lookup, existing-page edit delegation, or `Page.create_or_edit(...)` delegation.
- `Site.page.publish("new-page", source=3)` raises `ValueError("source must be a string")` before login, page lookup, create/edit saves, post-save page-ID resolution, source verification, metadata writes, or result creation.
- Existing successful create/edit/publish behavior remains green, including empty source strings and `Page.edit(source=None)` preserving current source behavior.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Page source is the main write payload for browser-free Wikidot automation. If caller configuration passes a non-string object, wikidot.py should reject it before any edit lock, save request, source verification, metadata update, or local source cache mutation can occur. Runtime validation keeps the documented `str` API honest without changing valid source saves or publish behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free publish and edit flows that saved source, verified source, updated metadata, refreshed source caches, and wrote audit ledgers.
- Existing local drafts covered page publish orchestration, source verification, source normalizer hooks, edit login/read ordering, edit lock diagnostics, local source cache sync, revision cache invalidation, parent input validation, visibility controls, and meta input validation, but did not cover malformed page source inputs.
- The focused RED failures showed direct Page writes reaching edit-lock handling and high-level Site accessors passing invalid source into downstream write paths without stable preflight.
- This slice only validates page source input shape; it does not change title or comment validation, valid source serialization, edit lock handling, save response validation, source verification comparison, source normalizers, metadata writes, visibility retry behavior, result fields, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed source inputs instead of coercing them. Callers that load source from files, generated structures, JSON, YAML, CLI flags, or environment variables should normalize the final page body to `str` before calling wikidot.py write helpers.
