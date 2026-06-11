# PR Draft: Validate Page Action Response Payload

## Summary

`Page.destroy()` and the shared non-metadata page action status helper now validate that decoded `deletePage` / `renamePage` action responses are dictionaries before reading their `status` fields. Non-mapping payloads such as `["not-ok"]` raise contextual `NoElementException` with site, page, page ID, event, expected type, and actual type context instead of leaking a raw list-index `TypeError`.

The change is intentionally narrow: valid `{"status": "ok"}` actions, missing `status` diagnostics, non-string `status` diagnostics, explicit non-ok string status handling, delete cache invalidation, rename local-state updates, and rename file-cache behavior remain unchanged.

## Problem Statement

The shared non-metadata page action helper treats decoded action responses from `deletePage`, `renamePage`, `saveTags`, and `setParentPage` as status-bearing JSON objects. Earlier local slices covered missing delete/rename action statuses, explicit non-ok string statuses, and present non-string statuses such as `{"status": ["not-ok"]}`. One response-shape gap remained: if `response.json()` returned a non-dictionary payload, `_require_page_action_status(...)` attempted `data["status"]` and leaked a raw `TypeError`.

That failure gives callers neither the page action context nor a stable wikidot.py data-shape exception. Generated fixtures, adapters, recorded traffic, or mocked responses should be classified before field access, and delete failures must not clear page-bound caches.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free page lifecycle, cleanup, rename, metadata, generated-fixture, migration, translation, and publish-support workflows as practical automation surfaces: [247-pr-page-rename-action-status-context.md](247-pr-page-rename-action-status-context.md), [248-pr-page-delete-action-status-context.md](248-pr-page-delete-action-status-context.md), [266-pr-page-rename-file-cache-invalidation.md](266-pr-page-rename-file-cache-invalidation.md), [267-pr-page-destroy-cache-invalidation.md](267-pr-page-destroy-cache-invalidation.md), [352-pr-validate-page-rename-fullname-input.md](352-pr-validate-page-rename-fullname-input.md), [557-pr-validate-page-destroy-site.md](557-pr-validate-page-destroy-site.md), [560-pr-validate-page-rename-site.md](560-pr-validate-page-rename-site.md), [722-pr-validate-page-action-status-type.md](722-pr-validate-page-action-status-type.md), [790-pr-validate-rename-retained-page-id.md](790-pr-validate-rename-retained-page-id.md), and [793-pr-validate-destroy-retained-page-id.md](793-pr-validate-destroy-retained-page-id.md).

This slice is not a duplicate of [247-pr-page-rename-action-status-context.md](247-pr-page-rename-action-status-context.md) or [248-pr-page-delete-action-status-context.md](248-pr-page-delete-action-status-context.md). Those issues covered mapping responses that omitted `status` and explicit non-ok string statuses.

This slice is not a duplicate of [722-pr-validate-page-action-status-type.md](722-pr-validate-page-action-status-type.md). Issue 722 covered a present non-string `status` field inside a mapping, such as `{"status": ["not-ok"]}`. This slice covers the decoded direct page action response payload not being a mapping before `status` lookup starts.

Issue [808-pr-validate-page-save-response-payload.md](808-pr-validate-page-save-response-payload.md) is not a duplicate because it covers `Page.create_or_edit(...)` `savePage` payloads. Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) covers the raw Ajax Module Connector response envelope before module-level action payload handling.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free page deletion through `Page.destroy()`.
- Browser-free page rename through `Page.rename(...)`.
- Shared direct page action response handling used by tag and parent updates.
- Generated-fixture, migration, translation, cleanup, metadata, and recorded-response tests that decode action responses before returning them to wikidot.py module code.

## Proposed Fix

- Change `_require_page_action_status(...)` to accept an object payload.
- Reject non-dictionary payloads with `NoElementException` before field access.
- Include only structural context and type names in the diagnostic, not raw response data.
- Preserve existing missing-status, malformed-status-type, non-ok string, success, cache, and local-state behavior.

## Implementation Notes

Implemented locally in commit `bdeb19f fix(page): validate action response payload`.

The implementation adds one preflight guard in `src/wikidot/module/page.py`:

```python
if not isinstance(data, dict):
    raise exceptions.NoElementException(
        f"Page action response is malformed for site: {site.unix_name}, page: {page.fullname} "
        f"(id={page.id}, event={event}, expected=dict, actual={type(data).__name__})"
    )
```

The RED regression mocked `Page.destroy()`'s `deletePage` response as `["not-ok"]`. Before the fix, the helper leaked `TypeError: list indices must be integers or slices, not str`. After the fix, the same case raises contextual `NoElementException`, decodes the response once, and preserves page-bound caches.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Non-dictionary direct page action payloads fail before `status` lookup. | `test_destroy_malformed_action_response_type_preserves_page_bound_caches` failed RED with raw `TypeError`, then passed GREEN. | Reaching list indexing, leaking `TypeError`, coercing the payload, or treating a list as a status response rejects this claim. |
| Missing `status` in a dictionary keeps the existing Issues 247/248 diagnostics. | Focused GREEN included delete and rename missing-status regressions. | Reclassifying `{}` as the payload-type branch or dropping `field=status` rejects this claim. |
| Present non-string `status` keeps the existing Issue 722 diagnostic. | Focused GREEN included delete and rename malformed status-type regressions. | Reclassifying `{"status": ["not-ok"]}` as a payload-type error or treating the list as a status code rejects this claim. |
| Explicit non-ok string statuses still use `WikidotStatusCodeException`. | Focused GREEN included `test_rename_explicit_non_ok_action_status_preserves_local_name_and_files_cache`. | Reclassifying non-ok strings as malformed response shape rejects this claim. |
| Failed delete action payloads do not clear page-bound caches. | The new regression asserts source, revisions, votes, metas, discussion, discussion flag, and files caches are preserved. | Clearing any page-bound cache before a valid delete status rejects this claim. |
| Adjacent page write behavior remains stable. | `TestPageWriteMethods` passed 128 tests and `tests/unit/test_page.py` passed 480 tests. | Regressing page deletion, rename, tags, parent, metadata, vote, edit, or create/edit behavior rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3906 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `bdeb19f fix(page): validate action response payload`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_destroy_malformed_action_response_type_preserves_page_bound_caches -q --tb=short` failed before the fix with raw `TypeError: list indices must be integers or slices, not str`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_destroy_missing_action_status_includes_site_page_event_and_field_context tests/unit/test_page.py::TestPageWriteMethods::test_destroy_malformed_action_response_type_preserves_page_bound_caches tests/unit/test_page.py::TestPageWriteMethods::test_destroy_malformed_action_status_type_preserves_page_bound_caches tests/unit/test_page.py::TestPageWriteMethods::test_rename_missing_action_status_does_not_update_local_name tests/unit/test_page.py::TestPageWriteMethods::test_rename_malformed_action_status_type_preserves_local_name_and_files_cache tests/unit/test_page.py::TestPageWriteMethods::test_rename_explicit_non_ok_action_status_preserves_local_name_and_files_cache -q --tb=short` passed 6 tests.
- Page write coverage: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q --tb=short` passed 128 tests.
- Page module coverage: `uv run pytest tests/unit/test_page.py -q --tb=short` passed 480 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3906 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Page.destroy()` with `response.json()` returning `["not-ok"]` raises `NoElementException` matching `Page action response is malformed for site: test-site, page: test-page (id=12345, event=deletePage, expected=dict, actual=list)`.
- `{}` still raises the existing missing-status message with `field=status`.
- `{"status": ["not-ok"]}` still raises the existing malformed status-type message with `expected=str, actual=list`.
- `{"status": "not_ok"}` still raises `WikidotStatusCodeException`.
- The malformed payload branch decodes the response JSON once, preserves page-bound caches, and does not include raw response data.
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
- Risk: This could hide raw payload details useful for debugging. Mitigation: the diagnostic includes site, page, page ID, event, expected type, and actual type while avoiding raw response data that could contain private page content or account material.
- Risk: The helper is shared by multiple direct page actions. Mitigation: it only adds a pre-`status` mapping check and preserves the existing action-specific event string in the diagnostic.

## Dependencies

- Direct page action responses remain expected to decode as JSON objects with string `status` fields.
- `WikidotStatusCodeException` remains responsible for explicit non-ok string statuses.
- `NoElementException` remains the parser/data-shape exception for malformed module response payloads.

## Open Questions

None for this local slice. Similar non-mapping action-payload guards may be useful on page rating, page metadata, forum, site-invitation, site-application, and site-member mutation helpers, but each surface should receive its own duplicate check against the existing action-status and status-type issue series before implementation.

## Rationale for Upstream Suitability

The patch is small, local, and consistent with existing wikidot.py response-shape diagnostics. It improves failure classification for malformed direct page action responses without changing successful actions, documented input validation, cache invalidation timing, local page identity updates, or existing status-code behavior.

## Local Evidence

- Local rollout-backed page drafts established delete, rename, metadata, publish support, cleanup, generated-fixture, migration, and translation workflows as practical consumers of direct page action behavior.
- Existing local drafts covered missing action status context, present non-string action status values, raw connector envelope status typing, page save non-mapping payloads, rename input validation, destroy retained-site validation, and retained page-ID validation. They did not cover a decoded direct page action response payload that is not a mapping before `status` lookup.
- This slice only validates direct page action payload shape. It does not change request construction, login checks, retry behavior, page save handling, rating action handling, metadata-specific action handling, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw page content, raw response bodies, private site data, and private source text out of upstream discussion.
