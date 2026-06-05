# PR Draft: Validate Page Title And Comment Inputs Before Page Writes

## Summary

`Page.create_or_edit(...)`, `Page.edit(title=..., comment=...)`, `Site.page.create(title=..., comment=...)`, and `Site.page.publish(title=..., comment=...)` document page title and edit comment inputs as `str`, but malformed non-string values were not validated consistently at the public API boundary. Direct page writes could proceed into login checks, edit-lock acquisition, AMC request construction, current-source reads, or downstream save helpers with non-string title/comment payloads. High-level `Site.page.create(...)` and `Site.page.publish(...)` could pass the malformed values into downstream write helpers before any stable caller-facing validation.

This change validates explicit page title and comment inputs before login checks, existing-page lookup, current-source fetches, page edit-lock requests, save requests, post-save page-ID resolution, source verification, metadata writes, or local title/source cache mutation. Invalid inputs now raise `ValueError("title must be a string")` or `ValueError("comment must be a string")`.

## Outcome

Browser-free page creation, edit, and publish callers now get deterministic preflight validation for malformed title/comment payloads instead of partial write-side progress, remote calls, raw lock/save behavior, or surprising current-source reads.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use direct page write APIs or `Site.page.publish(...)` for browser-free page publishing, migration scripts, generated page updates, translation workflows, audit ledgers, and cleanup jobs.

## Current Evidence

Local rollout evidence repeatedly uses browser-free page publishing and page edit workflows that save titles, source, comments, tags, parents, metas, and audit-friendly publish result records. Existing drafts [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [259-pr-page-edit-local-cache-sync.md](259-pr-page-edit-local-cache-sync.md), [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md), and [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md) establish page writes as a practical operational surface. Related parser/read-side drafts such as [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md) and edit-response drafts such as [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md) are not duplicates because they cover parsed/read or forum-post response behavior, not page write input preflight for title/comment.

## Related Issue

Builds directly on [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [259-pr-page-edit-local-cache-sync.md](259-pr-page-edit-local-cache-sync.md), [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md), and [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md). It also follows the input-boundary pattern from [342-pr-validate-tag-list-inputs.md](342-pr-validate-tag-list-inputs.md), [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), [346-pr-validate-publish-visibility-controls.md](346-pr-validate-publish-visibility-controls.md), [347-pr-validate-publish-source-normalizer.md](347-pr-validate-publish-source-normalizer.md), and [348-pr-validate-meta-tag-inputs.md](348-pr-validate-meta-tag-inputs.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a shared page text-field validator for documented `str` page write inputs.
- Keep `source` validation using the same helper while preserving the existing `ValueError("source must be a string")` diagnostic.
- Reject non-string title values with `ValueError("title must be a string")`.
- Reject non-string comment values with `ValueError("comment must be a string")`.
- Apply validation to `Page.create_or_edit(...)` before login checks, edit-lock acquisition, AMC save requests, post-save ListPages lookup, fallback `Page` construction, or local cache mutation.
- Apply validation to explicit `Page.edit(title=..., comment=...)` values before login checks, current-source defaulting, page-ID lookup, edit-lock acquisition, save requests, revision-cache invalidation, or local title/source-cache mutation.
- Apply validation to `Site.page.create(title=..., comment=...)` before login checks, force-edit existing-page lookup, existing-page edit delegation, or create request delegation.
- Apply validation to `Site.page.publish(title=..., comment=...)` before login checks, page lookup, create/edit delegation, post-save page-ID resolution, source refresh, source verification, metadata writes, or result creation.
- Preserve valid empty-string titles/comments, omitted `Page.edit(title=None, comment=None)` behavior, valid source writes, force-edit behavior, create/edit branching, source verification ordering, metadata gating, local cache sync, revision-cache invalidation, and `PagePublishResult` fields.

## Type Of Change

- Input validation
- Public API behavior hardening
- Write preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.create_or_edit(..., title=..., comment=...)` must reject non-string title/comment values with stable `ValueError` messages before login checks, edit-lock requests, save requests, post-save lookup, or local cache mutation. |
| R2 | `Page.edit(title=..., comment=...)` must reject explicit non-string title/comment values with stable `ValueError` messages before login checks, current-source fetches, page-ID reads, edit-lock requests, save requests, revision-cache invalidation, or local cache mutation. |
| R3 | `Site.page.create(title=..., comment=...)` must reject non-string title/comment values before login checks, force-edit lookup, existing-page edit delegation, or `Page.create_or_edit(...)` delegation. |
| R4 | `Site.page.publish(title=..., comment=...)` must reject non-string title/comment values before login checks, page lookup, create/edit work, post-save page-ID resolution, source verification, metadata writes, or result creation. |
| R5 | Valid page-write behavior must remain unchanged for empty title/comment strings, omitted edit title/comment defaults, valid source strings, force edit, create/edit branching, source verification, metadata ordering, visibility controls, source normalizers, and publish result fields. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent create/edit/publish tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct create/edit helper fails with stable `ValueError` before any page-write side effect. | `TestPageCreateOrEdit.test_create_or_edit_rejects_non_string_text_inputs_before_request` failed RED before the fix because the invalid value reached login and edit-lock handling, then passed GREEN after the fix. | Calling login, sending an edit-lock request, sending a save request, constructing a local `Page`, assigning `PageSource`, or leaking lock/save errors rejects this local completion claim. | Direct page write preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Instance edit fails for explicit non-string title/comment before reads or writes. | `TestPageEdit.test_edit_rejects_non_string_text_inputs_before_request` failed RED before the fix because omitted source caused a current-source fetch and a raw mocked source error before stable validation, then passed GREEN after the fix. | Calling login, fetching current source, reading page ID, sending AMC requests, invalidating revisions, or changing local title/source caches rejects this local completion claim. | Page edit preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | High-level create fails before login or force-edit lookup. | `TestSitePageAccessor.test_create_rejects_non_string_text_inputs_before_login` failed RED before the high-level preflight with `DID NOT RAISE` when downstream `Page.create_or_edit(...)` was patched, then passed GREEN after the fix. | Calling login, looking up an existing page, editing an existing page, or delegating to `Page.create_or_edit(...)` rejects this local completion claim. | Site create preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R4 | High-level publish fails before create/edit work. | `TestSitePageAccessor.test_publish_rejects_non_string_text_inputs_before_save` failed RED before the high-level preflight with `DID NOT RAISE` when downstream `Page.create_or_edit(...)` was patched, then passed GREEN after the fix. | Calling login, looking up a page, calling `Page.create_or_edit(...)`, editing an existing page, resolving page IDs, refreshing source, writing metadata, or returning a result rejects this local completion claim. | Publish text preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R5 | Existing page write and publish behavior remains green. | Focused title/comment tests passed 8 tests; adjacent create/edit/publish tests passed 54 tests; full unit passed 944 tests. | Regressing empty title/comment saves, omitted edit defaults, valid source strings, force edit, create/edit stale lookup fallback, source verification, source normalizers, metadata ordering, visibility retry, local source sync, revision invalidation, or result exports rejects this local completion claim. | Page write and publish workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent create/edit/publish tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `e94954d fix(page): validate page text inputs`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_rejects_non_string_text_inputs_before_request tests/unit/test_page.py::TestPageEdit::test_edit_rejects_non_string_text_inputs_before_request -q` failed before the fix. `Page.create_or_edit(...)` reached login/edit-lock handling and surfaced a mocked lock-path `TargetErrorException`; `Page.edit(...)` fetched current source before validating title/comment and leaked a raw mocked source error.
- GREEN: the same two Page-side focused tests passed 4 tests after adding direct title/comment preflight.
- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_create_rejects_non_string_text_inputs_before_login tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_non_string_text_inputs_before_save -q` failed before the high-level preflight with `DID NOT RAISE`, showing the accessors passed malformed title/comment into downstream write paths.
- GREEN: the same two Site-side focused tests passed 4 tests after adding high-level title/comment preflight.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_rejects_non_string_text_inputs_before_request tests/unit/test_page.py::TestPageEdit::test_edit_rejects_non_string_text_inputs_before_request tests/unit/test_site.py::TestSitePageAccessor::test_create_rejects_non_string_text_inputs_before_login tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_non_string_text_inputs_before_save -q` passed 8 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageEdit tests/unit/test_site.py::TestSitePageAccessor -q` passed 54 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run --extra test pytest tests/unit -q` passed 944 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `Page.create_or_edit(site, "new-page", title=3)` raises `ValueError("title must be a string")` before calling login, edit-lock AMC requests, save AMC requests, post-save lookup, or local cache mutation.
- `Page.create_or_edit(site, "new-page", comment=3)` raises `ValueError("comment must be a string")` before calling login, edit-lock AMC requests, save AMC requests, post-save lookup, or local cache mutation.
- `page.edit(title=3)` and `page.edit(comment=3)` raise stable `ValueError` messages before calling login, fetching current source, reading page ID, sending AMC requests, invalidating cached revisions, or changing local caches.
- `Site.page.create("new-page", title=3)` and `Site.page.create("new-page", comment=3)` raise stable `ValueError` messages before login, force-edit lookup, existing-page edit delegation, or `Page.create_or_edit(...)` delegation.
- `Site.page.publish("new-page", title=3)` and `Site.page.publish("new-page", comment=3)` raise stable `ValueError` messages before login, page lookup, create/edit saves, post-save page-ID resolution, source verification, metadata writes, or result creation.
- Existing successful create/edit/publish behavior remains green, including empty title/comment strings and `Page.edit(title=None, comment=None)` preserving current defaults.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Title and comment are small fields, but they are still part of the page write payload. If caller configuration passes a non-string object, wikidot.py should reject it before any edit lock, save request, source default fetch, source verification, metadata update, or local cache mutation can occur. Runtime validation keeps the documented `str` API honest without changing valid page saves or publish behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free publish and edit flows that saved titles, source, comments, metadata, source caches, and publish result ledgers.
- Existing local drafts covered page publish orchestration, edit login/read ordering, edit lock diagnostics, local cache sync, revision cache invalidation, page source input validation, parent input validation, visibility controls, source normalizers, and meta input validation, but did not cover malformed page title/comment inputs.
- The focused RED failures showed direct Page writes reaching login/edit-lock or current-source behavior, and high-level Site accessors passing invalid title/comment into downstream write paths without stable preflight.
- This slice only validates page title/comment input shape; it does not change fullname validation, page source input validation, valid source serialization, edit lock handling, save response validation, source verification comparison, source normalizers, metadata writes, visibility retry behavior, result fields, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed title/comment inputs instead of coercing them. Callers that load these fields from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should normalize the final page title and edit comment to `str` before calling wikidot.py write helpers.
