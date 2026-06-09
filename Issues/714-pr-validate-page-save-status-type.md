# PR Draft: Validate Page Save Status Type

## Summary

`Page.create_or_edit(...)` decodes the `savePage` response and requires a `status` field before deciding whether the save succeeded. Missing `status` was already handled by Issue 243, and explicit non-ok string statuses still route through `WikidotStatusCodeException`, but present non-string values such as `{"status": ["not-ok"]}` were treated as Wikidot status codes. This change rejects non-string save statuses as malformed generated response data before any post-save `ListPagesModule` lookup or fallback page creation.

## Outcome

Page save workflows now distinguish malformed response shape from real Wikidot status-code failures, preserving existing string-status behavior while surfacing type-corrupt generated responses with site, page, field, and type context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page create, edit, publish, generated fixture, migration, translation, or source-verification workflows where save responses may come from synthetic tests, recorded traffic, adapters, or generated data.

## Current Evidence

Local rollout-backed drafts already identify page save and page publish automation as practical shared workflows. Existing drafts [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), and [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md) cover save response reuse, login-required edit handling, edit lock field validation, and missing save status context. Edit-lock follow-up drafts [653-pr-validate-page-edit-lock-revision-ids.md](653-pr-validate-page-edit-lock-revision-ids.md), [654-pr-validate-page-edit-lock-token-fields.md](654-pr-validate-page-edit-lock-token-fields.md), [655-pr-validate-page-edit-lock-revision-before-page-id.md](655-pr-validate-page-edit-lock-revision-before-page-id.md), and [656-pr-validate-page-edit-lock-locked-field.md](656-pr-validate-page-edit-lock-locked-field.md) further harden the edit boundary.

Adjacent page and publish drafts [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), and [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md) show that page save outcomes feed browser-free publish and verification paths. Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) is not a duplicate: it covers raw Ajax Module Connector response status typing before module-level dispatch, while this slice validates the module-level `savePage` action response consumed by `Page.create_or_edit(...)`. No upstream issue was filed from this local workspace.

## Changes

- Add a type guard in the page save status extractor used by `Page.create_or_edit(...)`.
- Raise `NoElementException` for a present non-string `status` with site, page, field, expected type, and actual type context.
- Preserve the Issue 243 missing-status diagnostic.
- Preserve explicit non-ok string handling through `WikidotStatusCodeException`.
- Add a focused regression proving malformed status types fail before post-save lookup or fallback page creation.

## Type Of Change

- Response-shape validation
- Page save action hardening
- Generated response data diagnostics
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.create_or_edit(...)` must reject a non-string `savePage` response `status` with `NoElementException` containing site, page, `field=status`, `expected=str`, and the actual type. |
| R2 | A missing `status` field must keep the existing Issue 243 missing-status diagnostic. |
| R3 | Explicit non-ok string statuses must still raise `WikidotStatusCodeException` and must not be reclassified as malformed shape. |
| R4 | The save response body must still be decoded once for the relevant create/edit status handling paths. |
| R5 | Adjacent page create/edit behavior must remain green. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `{"status": ["not-ok"]}` fails with malformed save status context before any post-save `ListPagesModule` request. | `test_create_or_edit_malformed_save_status_type_includes_site_page_and_type_context` failed RED with `WikidotStatusCodeException`, then passed GREEN after status typing was added. | Treating a list, dict, number, or object as a Wikidot status code, consuming a post-save lookup, or creating a fallback `Page` rejects this local completion claim. | Page save response shape | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | `{}` still raises the Issue 243 missing-status message with site, page, and field context. | `test_create_or_edit_missing_save_status_includes_site_page_and_field_context` passed unchanged. | Changing the missing-status exception type, dropping context, or masking it behind status-code handling rejects this local completion claim. | Page save missing field handling | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | `{"status": "not_ok"}` still routes through `WikidotStatusCodeException`. | `test_create_or_edit_save_failure_decodes_response_once` passed with the same exception path. | Reclassifying non-ok strings as malformed response shape rejects this local completion claim. | Page save status-code handling | `tests/unit/test_page.py` |
| R4 | The save response JSON is decoded once in the relevant failure path. | `test_create_or_edit_save_failure_decodes_response_once` remained green. | Reintroducing duplicate decode work or hidden side effects rejects this local completion claim. | Page save response decoding | `tests/unit/test_page.py` |
| R5 | Adjacent create/edit tests remain stable. | `TestPageCreateOrEdit` passed 66 tests and `tests/unit/test_page.py` passed 383 tests. | Regressing page creation, edit locks, save failures, fallback lookup, or page module behavior rejects this local completion claim. | Page workflows | `tests/unit/test_page.py` |
| R6 | No live site state or private material is needed to prove the behavior. | The regression uses synthetic unit-level response bodies and mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private content, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `71f5e73 fix(page): validate save status type`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_malformed_save_status_type_includes_site_page_and_type_context -q` failed before the fix with `WikidotStatusCodeException` instead of the expected malformed-shape `NoElementException`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_save_failure_decodes_response_once tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_missing_save_status_includes_site_page_and_field_context tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_malformed_save_status_type_includes_site_page_and_type_context -q` passed 3 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit -q` passed 66 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 383 tests.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page.py` passed.

## Acceptance Criteria

- `{"status": ["not-ok"]}` raises `NoElementException` with site, page, `field=status`, `expected=str`, and `actual=list` context.
- The malformed non-string status path does not run post-save lookup; the existing unit regression keeps `amc_request` at the edit-lock and save calls only.
- `{}` still raises the existing missing-status message from Issue 243.
- `{"status": "not_ok"}` still raises `WikidotStatusCodeException`.
- The non-ok string failure path still decodes the response JSON once.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A caller may have relied on a non-string `status` object being formatted into a `WikidotStatusCodeException`. Mitigation: Wikidot action statuses are strings, Issue 403 already validates raw AMC statuses as strings, and module-level action responses should reject malformed generated data before business handling.
- Risk: This could be confused with raw AMC response typing. Mitigation: Issue 403 covers the raw connector response envelope; this slice covers the `savePage` action payload used by `Page.create_or_edit(...)`.
- Risk: Tightening save response shape could hide legitimate non-ok Wikidot string statuses. Mitigation: non-ok strings are deliberately preserved on the existing `WikidotStatusCodeException` path.
- Risk: The error could become too generic for generated fixtures. Mitigation: the diagnostic names the site, page, field, expected type, and actual type.

## Dependencies

- Existing `Page.create_or_edit(...)` remains responsible for page save orchestration.
- Existing `WikidotStatusCodeException` handling remains responsible for explicit non-ok string statuses.
- Existing `NoElementException` remains the parser/data-shape exception for missing or malformed response fields.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered page save status type path.

## Upstream-Safe Motivation

`Page.create_or_edit(...)` treats `savePage` as an action response with a string status. Rejecting malformed status types at that boundary keeps generated or adapted response data from masquerading as a real Wikidot status code and makes page save failures easier to diagnose.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established page create, edit, publish, source verification, generated-fixture, migration, and translation workflows as practical consumers of page save behavior.
- Existing save and raw AMC drafts covered missing save status context and raw connector envelope status typing; they did not validate the module-level `savePage` action status type.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
