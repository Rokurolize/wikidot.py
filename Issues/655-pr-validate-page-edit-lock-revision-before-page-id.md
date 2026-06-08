# PR Draft: Validate Page Edit-Lock Revision Before Page-ID Preconditions

## Summary

`Page.create_or_edit(...)` uses Wikidot's `edit/PageEditModule` response to decide whether a save is creating a new page or editing an existing page. Issue 653 added validation for present `page_revision_id` values before building the later `savePage` request, but one precedence gap remained: `Page.create_or_edit(...)` still used `"page_revision_id" in data` to decide that the page exists before validating the returned value. If Wikidot returned `page_revision_id=None`, a boolean, a string, a float, or a negative integer and the caller did not pass `page_id`, wikidot.py raised the caller precondition `ValueError("page_id must be specified when editing existing page")` before reporting the malformed edit-lock response.

This change validates a present edit-lock `page_revision_id` once immediately after lock-conflict handling and uses the validated value to derive the existing-page branch. Malformed or negative present values now raise the same contextual `NoElementException` regardless of whether the caller supplied `page_id`. A missing `page_revision_id` key still means the new-page path, and valid existing-page responses without `page_id` still raise the existing caller precondition.

## Outcome

Malformed returned edit-lock revision IDs no longer get masked by a missing caller `page_id`. Valid existing-page edit preconditions, new-page saves, zero-ID compatibility, valid existing-page saves, edit-lock token validation, save-status diagnostics, stale-search fallback, `Page.edit(...)`, `site.page.publish(...)`, and adjacent page workflows keep their existing behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page creation/editing, page publishing, migration scripts, fixture generators, page-write adapters, or publish ledgers where malformed edit-lock response identity metadata should be diagnosed before caller precondition checks that depend on that metadata.

## Current Evidence

Page write drafts [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [653-pr-validate-page-edit-lock-revision-ids.md](653-pr-validate-page-edit-lock-revision-ids.md), and [654-pr-validate-page-edit-lock-token-fields.md](654-pr-validate-page-edit-lock-token-fields.md) establish `Page.create_or_edit(...)`, edit locks, save requests, caller page IDs, returned revision IDs, and browser-free publishing as practical mutation boundaries.

This slice is not a duplicate of those drafts. Issue 412 preserves the valid existing-page behavior where a caller must supply `page_id` after a valid edit-lock response reports an existing page. Issue 653 validates returned `page_revision_id` values before `savePage` when `page_id` is supplied, but it did not cover the branch where a malformed returned revision ID was interpreted as page existence before validation. Issue 654 validates required edit-lock token values, not revision-ID branch precedence.

## Related Issue / Non-Duplicate Analysis

Builds directly on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [653-pr-validate-page-edit-lock-revision-ids.md](653-pr-validate-page-edit-lock-revision-ids.md), and [654-pr-validate-page-edit-lock-token-fields.md](654-pr-validate-page-edit-lock-token-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate the optional returned edit-lock `page_revision_id` before deriving `is_exist`.
- Use `page_revision_id is not None` as the existing-page branch signal after validation.
- Preserve missing `page_revision_id` as the new-page path.
- Preserve valid existing-page responses without caller `page_id` as `ValueError("page_id must be specified when editing existing page")`.
- Preserve edit-lock `lock_id` and `lock_secret` validation, save request shape, `raise_on_exists`, lock-conflict handling, save-status handling, stale search fallback, `Page.edit(...)`, `site.page.publish(...)`, live Wikidot behavior, pushes, upstream Issues, and upstream PRs.

## Type Of Change

- Response validation order
- Page mutation-boundary hardening
- Diagnostic precedence fix
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A present edit-lock `page_revision_id` with malformed values such as `None`, booleans, strings, or floats must raise contextual `NoElementException` before the missing-`page_id` caller precondition. |
| R2 | A present negative edit-lock `page_revision_id` such as `-1` or `-100` must raise contextual `NoElementException` before the missing-`page_id` caller precondition. |
| R3 | A valid existing-page edit-lock response with no caller `page_id` must still raise `ValueError("page_id must be specified when editing existing page")`. |
| R4 | A missing `page_revision_id` key must keep the new-page save path and send an empty `revision_id` value. |
| R5 | `page_revision_id=0` and valid positive integer revision IDs must remain accepted and forwarded as `revision_id` when caller `page_id` is supplied. |
| R6 | Existing edit-lock token validation, missing lock-field diagnostics, save-status diagnostics, create/edit behavior, stale-search fallback, `Page.edit(...)`, `site.page.publish(...)`, and adjacent page workflows must remain stable. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source text, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, create/edit tests, adjacent page/site/revision/source tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed present edit-lock revision IDs fail at the response boundary even when `page_id` is omitted. | `test_create_or_edit_malformed_page_revision_id_fails_before_missing_page_id` failed RED for `None`, `True`, `False`, `"100"`, and `100.0` with the caller `ValueError`, then passed GREEN after validation moved before the existence branch. | Raising `ValueError("page_id must be specified when editing existing page")`, coercing malformed values, or sending `savePage` rejects this local completion claim. | `Page.create_or_edit` edit-lock response parsing | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Negative present edit-lock revision IDs fail at the response boundary even when `page_id` is omitted. | `test_create_or_edit_negative_page_revision_id_fails_before_missing_page_id` failed RED for `-1` and `-100` with the caller `ValueError`, then passed GREEN after the non-negative guard ran first. | Raising the caller missing-`page_id` error, accepting negative values, treating them as new-page state, or sending `savePage` rejects this local completion claim. | `Page.create_or_edit` edit-lock response parsing | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Valid existing-page `page_id` precondition stays stable. | `test_edit_without_page_id` passed in the focused RED and GREEN commands. | Allowing a valid existing-page edit without caller `page_id`, changing the exception type/message, or checking token fields first for the valid precondition rejects this local completion claim. | Page edit caller precondition | `tests/unit/test_page.py` |
| R4 | Missing `page_revision_id` remains the new-page path. | `test_create_new_page` and the broader create/edit class passed after the validation-order change. | Requiring `page_revision_id` for new pages or changing the new-page save payload rejects this local completion claim. | Page create path | `tests/unit/test_page.py` |
| R5 | Zero and positive existing-page revision IDs remain valid. | Existing `page_revision_id` zero/positive coverage and the broader create/edit class passed after the reorder. | Rejecting zero, rejecting valid positive integers, or changing existing-page request payloads rejects this local completion claim. | Page edit path | `tests/unit/test_page.py` |
| R6 | Adjacent page workflows stay green. | The create/edit class passed 58 tests, `TestPageEdit` passed 13 tests, `TestSitePageAccessor` passed 92 tests, `tests/unit/test_page.py` passed 343 tests, adjacent page/site/page-revision/page-source suites passed 770 tests, and full unit passed 2982 tests. | Regressing lock conflicts, token validation, valid saves, edit-lock `page_revision_id`, `Page.edit`, publish helpers, page accessors, page revision/source behavior, save-status diagnostics, or any existing unit test rejects this local completion claim. | Page workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_source.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic edit-lock responses and mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, create/edit tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `1b60730 fix(page): validate edit lock revision before page id`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_malformed_page_revision_id_fails_before_missing_page_id tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_negative_page_revision_id_fails_before_missing_page_id tests/unit/test_page.py::TestPageCreateOrEdit::test_edit_without_page_id -q` failed 7 malformed/negative edit-lock revision-ID precedence cases before the fix; the valid existing-page missing-`page_id` guard passed.
- GREEN: the same focused command passed 8 tests after the edit-lock revision-ID validation moved before the existence/precondition branch.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left both files unchanged.
- `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit -q` passed 58 tests.
- `uv run pytest tests/unit/test_page.py::TestPageEdit -q` passed 13 tests.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed 92 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 343 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_revision.py tests/unit/test_page_source.py -q` passed 770 tests.
- `uv run pytest tests/unit -q` passed 2982 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.create_or_edit(...)` rejects present edit-lock `page_revision_id=None`, booleans, strings, and floats with `NoElementException` even when caller `page_id` is omitted.
- `Page.create_or_edit(...)` rejects present edit-lock `page_revision_id=-1` and `page_revision_id=-100` with `NoElementException` even when caller `page_id` is omitted.
- Malformed and negative returned revision IDs fail before `savePage`; tests assert only the edit-lock AMC request was made.
- A valid existing-page edit-lock response with omitted caller `page_id` still raises `ValueError("page_id must be specified when editing existing page")`.
- A missing `page_revision_id` key remains the new-page path and sends an empty `revision_id`.
- `page_revision_id=0` remains valid and is forwarded as `revision_id=0` when caller `page_id` is supplied.
- Valid positive existing-page revision IDs remain valid.
- Existing edit-lock token validation, missing lock-field diagnostics, save-status diagnostics, create/edit behavior, `Page.edit(...)`, and page-accessor workflows remain unchanged.
- Live Wikidot behavior, pushes, upstream Issues, and upstream PRs remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

The edit-lock response is the source of truth for whether a page save is an existing-page update. A caller should only receive the missing-`page_id` precondition after wikidot.py has confirmed that the returned revision identity is well-formed enough to prove the existing-page branch. Validating the returned `page_revision_id` first keeps malformed response data from being misreported as caller misuse.

## Local Evidence

- Local rollout-backed drafts repeatedly use browser-free page creation/editing, publishing, post-save lookup, source verification, metadata updates, and page-write audit ledgers.
- Existing local drafts covered malformed `page_revision_id` values with caller `page_id` supplied, caller-provided page-ID validation, missing edit-lock fields, token value validation, save-response reuse, and save-status diagnostics, but did not cover malformed returned revision IDs being masked by the missing caller page-ID precondition.
- The focused RED failure showed malformed and negative present edit-lock revision IDs raised the caller precondition before the response-boundary validator ran.
- This slice only changes validation order for returned edit-lock `page_revision_id`. It does not change login behavior, edit-lock request construction, lock conflict handling, `raise_on_exists`, token validation, save status parsing, post-save search fallback, page URL construction, direct page or revision constructors, publish result construction, live site behavior, or parser behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally treats a missing `page_revision_id` key differently from a present malformed value. Missing remains the documented new-page signal, while present values must be plausible existing-page revision IDs before caller edit preconditions are evaluated.
