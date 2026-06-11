# PR Draft: Validate Page Save Response Payload

## Summary

`Page.create_or_edit(...)` now validates that the decoded `savePage` response is a dictionary before reading its `status` field. Non-mapping payloads such as `["not-ok"]` raise contextual `NoElementException` with site, page, event, expected type, and actual type context instead of leaking a raw list-index `TypeError`.

The change is intentionally narrow: valid `{"status": "ok"}` saves, missing `status` diagnostics, non-string `status` diagnostics, explicit non-ok string status handling, post-save lookup behavior, and fallback page construction remain unchanged.

## Problem Statement

`Page.create_or_edit(...)` treats the response from Wikidot's `savePage` action as a status-bearing JSON object. Earlier local slices covered missing `status`, explicit non-ok string statuses, present non-string `status` values, edit-lock fields, input validation, retained page identity, and site/client boundary checks. One response-shape gap remained: if `response.json()` returned a non-dictionary payload, `_require_page_save_status(...)` attempted `data["status"]` and leaked a raw `TypeError`.

That failure gives callers neither the page-save context nor a stable wikidot.py data-shape exception. Generated fixtures, adapters, recorded traffic, or mocked responses should be classified before field access.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free page save, edit, publish, generated-fixture, migration, translation, and source-verification workflows as practical automation surfaces: [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [714-pr-validate-page-save-status-type.md](714-pr-validate-page-save-status-type.md), [799-pr-validate-page-write-site-boundaries.md](799-pr-validate-page-write-site-boundaries.md), and [800-pr-validate-page-save-site-clients.md](800-pr-validate-page-save-site-clients.md).

This slice is not a duplicate of [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md). Issue 243 covered a mapping response that omitted `status`.

This slice is not a duplicate of [714-pr-validate-page-save-status-type.md](714-pr-validate-page-save-status-type.md). Issue 714 covered a present non-string `status` field inside a mapping, such as `{"status": ["not-ok"]}`. This slice covers the decoded `savePage` action response payload not being a mapping before `status` lookup starts.

Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) is not a duplicate because it covers the raw Ajax Module Connector response envelope before module-level action payload handling.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free page creation and editing through `Page.create_or_edit(...)`.
- `Page.edit(...)` and `site.page.publish(...)` workflows that rely on create/edit behavior.
- Generated-fixture, migration, translation, source-verification, and recorded-response tests that decode action responses before returning them to wikidot.py module code.

## Proposed Fix

- Change `_require_page_save_status(...)` to accept an object payload.
- Reject non-dictionary payloads with `NoElementException` before field access.
- Include only structural context and type names in the diagnostic, not raw response data.
- Preserve existing missing-status, malformed-status-type, non-ok string, success, and post-save lookup behavior.

## Implementation Notes

Implemented locally in commit `5999930 fix(page): validate save response payload`.

The implementation adds one preflight guard in `src/wikidot/module/page.py`:

```python
if not isinstance(data, dict):
    raise exceptions.NoElementException(
        f"Page save response is malformed for site: {site.unix_name}, page: {fullname} "
        f"(event=savePage, expected=dict, actual={type(data).__name__})"
    )
```

The RED regression mocked `response.json()` as `["not-ok"]`. Before the fix, the helper leaked `TypeError: list indices must be integers or slices, not str`. After the fix, the same case raises contextual `NoElementException`, decodes the save response once, and stops before post-save `ListPagesModule` lookup or fallback page construction.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Non-dictionary page save action payloads fail before `status` lookup. | `test_create_or_edit_malformed_save_response_type_includes_site_page_event_and_type_context` failed RED with raw `TypeError`, then passed GREEN. | Reaching list indexing, leaking `TypeError`, coercing the payload, or treating a list as a status response rejects this claim. |
| Missing `status` in a dictionary keeps the existing Issue 243 diagnostic. | Focused GREEN included `test_create_or_edit_missing_save_status_includes_site_page_and_field_context`. | Reclassifying `{}` as the payload-type branch or dropping `field=status` rejects this claim. |
| Present non-string `status` keeps the existing Issue 714 diagnostic. | Focused GREEN included `test_create_or_edit_malformed_save_status_type_includes_site_page_and_type_context`. | Reclassifying `{"status": ["not-ok"]}` as a payload-type error or treating the list as a status code rejects this claim. |
| Explicit non-ok string statuses still use `WikidotStatusCodeException`. | Focused GREEN included `test_create_or_edit_save_failure_decodes_response_once`. | Reclassifying non-ok strings as malformed response shape rejects this claim. |
| Adjacent page create/edit behavior remains stable. | `TestPageCreateOrEdit` passed 69 tests and `tests/unit/test_page.py` passed 479 tests. | Regressing page creation, edit locks, save failures, fallback lookup, page editing, or page module behavior rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3905 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `5999930 fix(page): validate save response payload`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_malformed_save_response_type_includes_site_page_event_and_type_context -q --tb=short` failed before the fix with raw `TypeError: list indices must be integers or slices, not str`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_save_failure_decodes_response_once tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_missing_save_status_includes_site_page_and_field_context tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_malformed_save_response_type_includes_site_page_event_and_type_context tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_malformed_save_status_type_includes_site_page_and_type_context -q --tb=short` passed 4 tests.
- Page create/edit coverage: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit -q --tb=short` passed 69 tests.
- Page module coverage: `uv run pytest tests/unit/test_page.py -q --tb=short` passed 479 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3905 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Page.create_or_edit(...)` with `response.json()` returning `["not-ok"]` raises `NoElementException` matching `Page save response is malformed for site: test-site, page: new-page (event=savePage, expected=dict, actual=list)`.
- `{}` still raises the existing missing-status message with `field=status`.
- `{"status": ["not-ok"]}` still raises the existing malformed status-type message with `expected=str, actual=list`.
- `{"status": "not_ok"}` still raises `WikidotStatusCodeException`.
- The malformed payload branch decodes the response JSON once, does not run post-save lookup, does not fabricate a fallback returned page, and does not include raw response data.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: A caller may have relied on raw `TypeError` from malformed synthetic responses. Mitigation: the public module expects a status-bearing JSON object, and repo validation style consistently routes malformed generated response shape through contextual `NoElementException`.
- Risk: This could be confused with status-field validation. Mitigation: missing and non-string `status` branches are preserved and tested separately.
- Risk: This could hide raw payload details useful for debugging. Mitigation: the diagnostic includes site, page, event, expected type, and actual type while avoiding raw response data that could contain private page content or account material.

## Dependencies

- Page save responses remain expected to decode as JSON objects with string `status` fields.
- `WikidotStatusCodeException` remains responsible for explicit non-ok string statuses.
- `NoElementException` remains the parser/data-shape exception for malformed module response payloads.

## Open Questions

None for this local slice. Similar non-mapping action-payload guards may be useful on other mutation helpers, but each surface should receive its own duplicate check against the existing action-status and status-type issue series before implementation.

## Rationale for Upstream Suitability

The patch is small, local, and consistent with existing wikidot.py response-shape diagnostics. It improves failure classification for malformed page save responses without changing successful saves, documented input validation, post-save lookup behavior, fallback page construction, or existing status-code behavior.

## Local Evidence

- Local rollout-backed page drafts established create, edit, publish, source verification, generated-fixture, migration, and translation workflows as practical consumers of page save behavior.
- Existing local drafts covered missing save status context, present non-string save status values, raw connector envelope status typing, edit-lock validation, page input validation, retained page identity, and save client validation. They did not cover a decoded `savePage` action response payload that is not a mapping before `status` lookup.
- This slice only validates page save action payload shape. It does not change request construction, login checks, retry behavior, edit-lock response parsing, page ID handling, source verification, post-save visibility polling, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw page content, raw response bodies, private site data, and private source text out of upstream discussion.
