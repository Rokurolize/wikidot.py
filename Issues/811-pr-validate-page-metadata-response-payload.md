# PR Draft: Validate Page Metadata Response Payload

## Summary

`Page.set_metadata(...)` and the shared page metadata action status helper now validate that decoded metadata action responses are dictionaries before reading their `status` fields. Non-mapping payloads such as `["not-ok"]` raise contextual `NoElementException` with site, page, page ID, event, expected type, and actual type context instead of leaking a raw list-index `TypeError`.

The change is intentionally narrow: valid `{"status": "ok"}` metadata actions, missing `status` diagnostics, non-string `status` diagnostics, explicit non-ok string status handling, tag serialization, parent clearing, meta diffing, local state updates, and metadata batching remain unchanged.

## Problem Statement

Page metadata writes treat decoded `saveTags`, `setParentPage`, `deleteMetaTag`, and `saveMetaTag` responses as status-bearing JSON objects before accepting the action as confirmed and updating local metadata state. Earlier local slices covered missing metadata action statuses, explicit non-ok string statuses, present non-string statuses such as `{"status": ["not-ok"]}`, retained page/site/client boundaries, retained page IDs, and metadata input validation. One response-shape gap remained: if `response.json()` returned a non-dictionary payload, `_require_page_metadata_action_status(...)` attempted `data["status"]` and leaked a raw `TypeError`.

That failure gives callers neither the metadata action context nor a stable wikidot.py data-shape exception. Generated fixtures, response adapters, recorded traffic, or mocked responses should be classified before field access, and failed metadata responses must not update local tags, parent state, or cached metas.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free publishing, metadata cleanup, tag synchronization, parent-page maintenance, generated page ledgers, migration scripts, and local fixtures as practical automation surfaces: [007-pr-batch-meta-tag-updates.md](007-pr-batch-meta-tag-updates.md), [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), [246-pr-page-direct-metadata-action-status-context.md](246-pr-page-direct-metadata-action-status-context.md), [249-pr-page-metas-setter-action-status-context.md](249-pr-page-metas-setter-action-status-context.md), [265-pr-page-empty-parent-clear-normalization.md](265-pr-page-empty-parent-clear-normalization.md), [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), [348-pr-validate-meta-tag-inputs.md](348-pr-validate-meta-tag-inputs.md), [532-pr-validate-commit-tags-state.md](532-pr-validate-commit-tags-state.md), [558-pr-validate-page-commit-tags-site.md](558-pr-validate-page-commit-tags-site.md), [563-pr-validate-page-set-metadata-site.md](563-pr-validate-page-set-metadata-site.md), [565-pr-validate-page-metas-setter-site.md](565-pr-validate-page-metas-setter-site.md), [724-pr-validate-page-metadata-status-type.md](724-pr-validate-page-metadata-status-type.md), [794-pr-validate-set-metadata-retained-page-id.md](794-pr-validate-set-metadata-retained-page-id.md), and [795-pr-validate-metas-setter-retained-page-id.md](795-pr-validate-metas-setter-retained-page-id.md).

This slice is not a duplicate of [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), [246-pr-page-direct-metadata-action-status-context.md](246-pr-page-direct-metadata-action-status-context.md), or [249-pr-page-metas-setter-action-status-context.md](249-pr-page-metas-setter-action-status-context.md). Those issues covered mapping responses that omitted `status` and explicit non-ok string statuses.

This slice is not a duplicate of [724-pr-validate-page-metadata-status-type.md](724-pr-validate-page-metadata-status-type.md). Issue 724 covered a present non-string `status` field inside a mapping, such as `{"status": ["not-ok"]}`. This slice covers the decoded metadata action response payload not being a mapping before `status` lookup starts.

Issue [810-pr-validate-page-rating-response-payload.md](810-pr-validate-page-rating-response-payload.md) covers rating actions; Issue [809-pr-validate-page-action-response-payload.md](809-pr-validate-page-action-response-payload.md) covers non-rating direct page actions such as `deletePage` and `renamePage`; Issue [808-pr-validate-page-save-response-payload.md](808-pr-validate-page-save-response-payload.md) covers `savePage`; Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) covers the raw Ajax Module Connector response envelope before module-level action payload handling.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free metadata writes through `Page.set_metadata(...)`.
- Direct tag, parent, and meta-tag actions that share `_require_page_metadata_action_status(...)`.
- Browser-free publishing flows that apply tags, parent pages, or meta tags after source save.
- Generated page ledgers, migration tooling, metadata cleanup jobs, fixtures, and recorded-response tests that decode action responses before returning them to wikidot.py module code.

## Proposed Fix

- Change `_require_page_metadata_action_status(...)` to accept an object payload.
- Reject non-dictionary payloads with `NoElementException` before field access.
- Include only structural context and type names in the diagnostic, not raw response data.
- Preserve existing missing-status, malformed-status-type, non-ok string, success, request construction, and local metadata update behavior.

## Implementation Notes

Implemented locally in commit `12cc21d fix(page): validate metadata response payload`.

The implementation adds one preflight guard in `src/wikidot/module/page.py`:

```python
if not isinstance(data, dict):
    raise exceptions.NoElementException(
        f"Page metadata action response is malformed for site: {site.unix_name}, page: {page.fullname} "
        f"(id={page.id}, event={event}, expected=dict, actual={type(data).__name__})"
    )
```

The RED regression mocked `Page.set_metadata(...)`'s `saveTags` response as `["not-ok"]`. Before the fix, the helper leaked `TypeError: list indices must be integers or slices, not str`. After the fix, the same case raises contextual `NoElementException`, decodes the response once, and preserves local tags, parent state, and cached metas.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Non-dictionary metadata action payloads fail before `status` lookup. | `test_set_metadata_malformed_action_response_type_does_not_update_local_state` failed RED with raw `TypeError`, then passed GREEN. | Reaching list indexing, leaking `TypeError`, coercing the payload, or treating a list as a status response rejects this claim. |
| Missing `status` in a dictionary keeps the existing Issues 245/246/249 diagnostics. | Focused GREEN included metadata missing-status regressions for tag, parent, meta setter, and batched metadata paths. | Reclassifying `{}` as the payload-type branch or dropping `field=status` rejects this claim. |
| Present non-string `status` keeps the existing Issue 724 diagnostic. | Focused GREEN included `test_metas_setter_malformed_action_status_type_does_not_update_local_state` and `test_set_metadata_malformed_action_status_type_does_not_update_local_state`. | Reclassifying `{"status": ["not-ok"]}` as a payload-type error or treating the list as a status code rejects this claim. |
| Explicit non-ok string statuses still use `WikidotStatusCodeException`. | Source inspection confirms the non-ok branch still follows the string-status guard, and full page write coverage stayed green. | Reclassifying non-ok strings as malformed response shape rejects this claim. |
| Failed metadata action payloads do not update local metadata state. | The new regression asserts unchanged `tags`, `parent_fullname`, and `_metas`. | Updating tags, parent state, or cached metas before confirmed action status rejects this claim. |
| Adjacent page write behavior remains stable. | `TestPageWriteMethods` passed 130 tests and `tests/unit/test_page.py` passed 482 tests. | Regressing page metadata, tags, parent, edit, save, delete, rename, vote, or cancel-vote behavior rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3908 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `12cc21d fix(page): validate metadata response payload`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_malformed_action_response_type_does_not_update_local_state -q --tb=short` failed before the fix with raw `TypeError: list indices must be integers or slices, not str`.
- GREEN focused: the same new regression passed after the helper guard.
- Metadata helper coverage: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_missing_action_status_includes_site_page_event_and_field_context tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_success tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_empty_string_clears_local_parent tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_missing_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_missing_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_malformed_action_status_type_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_batches_tags_parent_and_metas tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_missing_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_malformed_action_response_type_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_malformed_action_status_type_does_not_update_local_state -q --tb=short` passed 10 tests.
- Page write coverage: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q --tb=short` passed 130 tests.
- Page module coverage: `uv run pytest tests/unit/test_page.py -q --tb=short` passed 482 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3908 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Page.set_metadata(...)` with `response.json()` returning `["not-ok"]` raises `NoElementException` matching `Page metadata action response is malformed for site: test-site, page: test-page (id=12345, event=saveTags, expected=dict, actual=list)`.
- `{}` still raises the existing missing-status message with `field=status`.
- `{"status": ["not-ok"]}` still raises the existing malformed status-type message with `expected=str, actual=list`.
- Explicit non-ok string statuses still raise `WikidotStatusCodeException`.
- The malformed payload branch decodes the response JSON once, preserves local tags, parent state, and cached metas, and does not include raw response data.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: A caller may have relied on raw `TypeError` from malformed synthetic responses. Mitigation: the public module expects a status-bearing JSON object, and repo validation style consistently routes malformed generated response shape through contextual `NoElementException`.
- Risk: This could be confused with missing-status or status-type validation. Mitigation: missing `status`, non-string `status`, and non-ok strings are preserved and tested separately.
- Risk: This could hide raw payload details useful for debugging. Mitigation: the diagnostic includes site, page, page ID, event, expected type, and actual type while avoiding raw response data that could contain private page content, metadata values, or account material.

## Dependencies

- Page metadata action responses remain expected to decode as JSON objects with string `status` fields.
- `WikidotStatusCodeException` remains responsible for explicit non-ok string statuses.
- `NoElementException` remains the parser/data-shape exception for malformed module response payloads.

## Open Questions

None for this local slice. Similar non-mapping action-payload guards may be useful on forum, site-invitation, site-application, and site-member mutation helpers, but each surface should receive its own duplicate check against the existing action-status and status-type issue series before implementation.

## Rationale for Upstream Suitability

The patch is small, local, and consistent with existing wikidot.py response-shape diagnostics. It improves failure classification for malformed page metadata action responses without changing successful metadata writes, request bodies, local state update timing, or existing status-code behavior.

## Local Evidence

- Local rollout-backed page drafts established browser-free publishing, metadata batching, direct tag/parent/meta writes, parent clearing, metadata input validation, and page action diagnostics as practical consumers of metadata write behavior.
- Existing local drafts covered missing metadata action status context, present non-string metadata action status values, raw connector envelope status typing, page rating payloads, direct page action payloads, page save payloads, metadata input validation, metadata retained site/client state, and metadata retained page IDs. They did not cover a decoded metadata action response payload that is not a mapping before `status` lookup.
- This slice only validates page metadata action payload shape. It does not change request construction, login checks, retry behavior, page save handling, direct non-metadata page action handling, rating action handling, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw page content, raw response bodies, private metadata values, private site data, and private source text out of upstream discussion.
