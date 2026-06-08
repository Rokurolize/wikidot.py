# PR Draft: Validate Page Edit-Lock Token Fields

## Summary

`Page.create_or_edit(...)` acquires Wikidot's `edit/PageEditModule` response, requires `lock_id` and `lock_secret`, and forwards those token fields to the later `savePage` request. Existing local drafts already cover browser-free page writes, missing edit-lock token fields, masked lock-secret logging, save-response reuse, save-status diagnostics, and edit-lock `page_revision_id` validation. One token-boundary gap remained: if `lock_id` or `lock_secret` was present but `None`, a boolean, a number, a list, a dictionary, an empty string, or a whitespace-only string, that value was accepted and copied into `savePage`.

This change validates present required edit-lock token fields as non-blank strings before `savePage`. Missing fields keep the same contextual malformed-response diagnostic, malformed present values now use that same site/page/field diagnostic, observed values are not included so `lock_secret` cannot leak through errors, and valid token strings are returned unchanged rather than stripped or normalized.

## Outcome

Malformed or blank edit-lock tokens fail before `savePage`, while valid opaque tokens, missing-field diagnostics, lock-conflict handling, `raise_on_exists`, edit-lock `page_revision_id` validation, save-status diagnostics, stale-search fallback, `Page.edit(...)`, `site.page.publish(...)`, and adjacent page workflows keep their existing behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page creation/editing, page publishing, migration scripts, fixture generators, page-write adapters, or publish ledgers where malformed edit-lock token responses should not become page-write request payloads.

## Current Evidence

Page write drafts [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md), [189-pr-page-create-edit-existing-search-fallback.md](189-pr-page-create-edit-existing-search-fallback.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), and [653-pr-validate-page-edit-lock-revision-ids.md](653-pr-validate-page-edit-lock-revision-ids.md) establish `Page.create_or_edit(...)`, edit locks, save requests, and browser-free publishing as practical mutation boundaries.

This slice is not a duplicate of those drafts. Issue 242 covers missing `lock_id` and `lock_secret` fields, but not present malformed or blank token values. Issue 071 masks `lock_secret` in logs, but does not validate the response value before `savePage`. Issue 080 reuses save-response data, and Issue 243 validates the returned `savePage` status, but both happen after malformed lock tokens could already have been submitted. Issue 351 covers caller boolean controls, not edit-lock response fields. Issue 653 covers the optional edit-lock `page_revision_id`, not the required token fields.

## Related Issue / Non-Duplicate Analysis

Builds directly on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md), [189-pr-page-create-edit-existing-search-fallback.md](189-pr-page-create-edit-existing-search-fallback.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), and [653-pr-validate-page-edit-lock-revision-ids.md](653-pr-validate-page-edit-lock-revision-ids.md).

No upstream issue was filed from this local workspace.

## Changes

- Change `_require_page_edit_lock_field(...)` to return `str`.
- Keep the existing contextual `NoElementException` for missing edit-lock token fields.
- Reject present non-string `lock_id` and `lock_secret` values with the same contextual `NoElementException`.
- Reject present empty-string and whitespace-only `lock_id` and `lock_secret` values with the same contextual `NoElementException`.
- Do not include the observed token value in the exception message, preserving the existing `lock_secret` leak boundary.
- Return valid non-blank strings unchanged so opaque Wikidot tokens are not stripped or normalized.
- Preserve lock acquisition, lock-conflict handling, `raise_on_exists`, edit-lock `page_revision_id` validation, save request shape for valid fields, save-status handling, stale-search fallback, `Page.edit(...)`, `site.page.publish(...)`, live Wikidot behavior, pushes, upstream Issues, and upstream PRs.

## Type Of Change

- Returned response-field validation
- Page mutation-boundary hardening
- Secret-safe diagnostics
- Write-request payload integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A present edit-lock `lock_id` or `lock_secret` with malformed non-string values such as `None`, booleans, numbers, lists, or dictionaries must raise contextual `NoElementException` before `savePage`. |
| R2 | A present edit-lock `lock_id` or `lock_secret` with `""` or whitespace-only string values must raise contextual `NoElementException` before `savePage`. |
| R3 | Missing `lock_id` and `lock_secret` diagnostics must keep the existing site/page/field malformed-response message. |
| R4 | Valid non-blank token strings must still be forwarded to `savePage` unchanged. |
| R5 | Error messages, docs, and tests must not print observed `lock_id` or `lock_secret` values. |
| R6 | Existing lock-conflict handling, `raise_on_exists`, edit-lock `page_revision_id` validation, save-status diagnostics, create/edit behavior, stale-search fallback, `Page.edit(...)`, `site.page.publish(...)`, and adjacent page workflows must remain stable. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source text, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, create/edit tests, adjacent page/site/revision/source tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed non-string token values fail at the response boundary. | `test_create_or_edit_malformed_lock_field_value_fails_before_save` failed RED for `lock_id` and `lock_secret` across `None`, `True`, `False`, `100`, `100.0`, `[]`, and `{}` with `DID NOT RAISE`, then passed GREEN after `_require_page_edit_lock_field(...)` rejected malformed present values. | Accepting non-string values, coercing them to strings, or sending `savePage` rejects this local completion claim. | `Page.create_or_edit` edit-lock response parsing | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Blank and whitespace-only token values fail at the response boundary. | `test_create_or_edit_blank_lock_field_value_fails_before_save` failed RED for `lock_id` and `lock_secret` across `""` and `"   "` with `DID NOT RAISE`, then passed GREEN after blank strings were rejected. | Accepting empty or whitespace-only strings, stripping them to empty payloads, or sending `savePage` rejects this local completion claim. | `Page.create_or_edit` edit-lock response parsing | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Missing-token diagnostics remain unchanged. | `test_create_or_edit_missing_lock_field_includes_site_page_and_field_context` passed in the focused RED and GREEN commands. | Changing the missing-field exception type, removing site/page/field context, or requiring a separate missing-field diagnostic rejects this local completion claim. | Edit-lock response diagnostics | `tests/unit/test_page.py` |
| R4 | Valid token strings remain valid and opaque. | `test_create_new_page` passed in the focused RED and GREEN commands, and the broader create/edit class passed after the fix. The implementation returns the original string rather than `strip()` output. | Trimming, normalizing, replacing, rejecting, or otherwise changing valid non-blank strings rejects this local completion claim. | Save request token payload | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Diagnostics do not leak token values. | The shared malformed-response message includes only site unix name, page fullname, and `field=<name>`; it does not include the observed value. Tests assert that same contextual pattern. | Printing a `lock_secret` value in an exception, draft, report, log, or test output rejects this local completion claim. | Secret-safe diagnostics | `src/wikidot/module/page.py`, `tests/unit/test_page.py`, this draft |
| R6 | Adjacent page workflows stay green. | The create/edit class passed 51 tests, `TestPageEdit` passed 13 tests, `TestSitePageAccessor` passed 92 tests, `tests/unit/test_page.py` passed 336 tests, adjacent page/site/page-revision/page-source suites passed 763 tests, and full unit passed 2975 tests. | Regressing lock conflicts, valid saves, edit-lock `page_revision_id`, `Page.edit`, publish helpers, page accessors, page revision/source behavior, save-status diagnostics, or any existing unit test rejects this local completion claim. | Page workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_source.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic edit-lock responses and mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, create/edit tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `efa5a83 fix(page): validate edit lock token fields`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_missing_lock_field_includes_site_page_and_field_context tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_malformed_lock_field_value_fails_before_save tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_blank_lock_field_value_fails_before_save tests/unit/test_page.py::TestPageCreateOrEdit::test_create_new_page -q` failed 18 malformed/blank edit-lock token cases before the fix; 3 missing-field and valid-create guards stayed green.
- GREEN: the same focused command passed 21 tests after the edit-lock token guard was added.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left both files unchanged.
- `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit -q` passed 51 tests.
- `uv run pytest tests/unit/test_page.py::TestPageEdit -q` passed 13 tests.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed 92 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 336 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_revision.py tests/unit/test_page_source.py -q` passed 763 tests.
- `uv run pytest tests/unit -q` passed 2975 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.create_or_edit(...)` rejects present edit-lock `lock_id` and `lock_secret` values of `None`, `True`, `False`, `100`, `100.0`, `[]`, and `{}` with `NoElementException`.
- `Page.create_or_edit(...)` rejects present edit-lock `lock_id` and `lock_secret` values of `""` and `"   "` with `NoElementException`.
- Malformed and blank edit-lock token values fail before `savePage`; tests assert only the edit-lock AMC request was made.
- The malformed-value exception message includes the site unix name, page fullname, and `field=lock_id` or `field=lock_secret`.
- The malformed-value exception message does not include the observed token value.
- Missing `lock_id` and `lock_secret` fields keep the same contextual diagnostic.
- Valid non-blank token strings remain forwarded unchanged to `savePage`.
- Existing edit-lock `page_revision_id` validation, save-status diagnostics, create/edit behavior, `Page.edit(...)`, and page-accessor workflows remain unchanged.
- Live Wikidot behavior, pushes, upstream Issues, and upstream PRs remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

The edit-lock response is the source of truth for the token pair required by `savePage`. Rejecting malformed or blank present `lock_id` and `lock_secret` values at that boundary prevents invalid token state from becoming a page-write request payload, while avoiding diagnostics that could leak a secret token and avoiding normalization of valid opaque token strings.

## Local Evidence

- Local rollout-backed drafts repeatedly use browser-free page creation/editing, publishing, post-save lookup, source verification, metadata updates, and page-write audit ledgers.
- Existing local drafts covered missing edit-lock fields, lock-secret masking, save-response reuse, save-status diagnostics, and edit-lock `page_revision_id` validation, but did not cover present malformed or blank required edit-lock token values.
- The focused RED failure showed malformed and blank present edit-lock token values were accepted into `savePage` before this slice.
- This slice only validates present required edit-lock token fields. It does not change login behavior, edit-lock request construction, lock conflict handling, `raise_on_exists`, `page_revision_id` validation, save status parsing, post-save search fallback, page URL construction, direct page or revision constructors, publish result construction, live site behavior, or parser behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

This change intentionally validates the required token field values without printing them. `lock_id` is less sensitive than `lock_secret`, but the helper handles both fields uniformly so future diagnostics cannot accidentally expose one token path differently from the other.
