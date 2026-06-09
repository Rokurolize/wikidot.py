# PR Draft: Validate Page Metadata Action Status Type

## Summary

`Page.commit_tags()`, `Page.set_parent(...)`, `Page.set_metadata(...)`, and the direct `Page.metas = ...` setter all share the page metadata action status helper after Wikidot returns `saveTags`, `setParentPage`, `deleteMetaTag`, or `saveMetaTag` action data. Issues [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), [246-pr-page-direct-metadata-action-status-context.md](246-pr-page-direct-metadata-action-status-context.md), and [249-pr-page-metas-setter-action-status-context.md](249-pr-page-metas-setter-action-status-context.md) covered missing metadata action `status` fields and explicit non-ok string statuses, but present non-string values such as `{"status": ["not-ok"]}` were still routed into `WikidotStatusCodeException` as if they were real Wikidot status codes. This change rejects malformed generated metadata action data before updating tags, parent state, or cached meta tags.

## Outcome

Page metadata actions now distinguish malformed action-response shape from real Wikidot status-code failures, preserving existing string-status behavior while surfacing type-corrupt generated responses with site, page, page ID, event, field, and type context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page publishing, metadata cleanup, tag synchronization, parent-page maintenance, generated page ledgers, migration scripts, or local fixtures where malformed metadata action responses must not be mistaken for confirmed Wikidot action results.

## Current Evidence

Local rollout-backed drafts already identify browser-free page metadata writes as practical shared workflows. Existing drafts [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), [246-pr-page-direct-metadata-action-status-context.md](246-pr-page-direct-metadata-action-status-context.md), [249-pr-page-metas-setter-action-status-context.md](249-pr-page-metas-setter-action-status-context.md), [265-pr-page-empty-parent-clear-normalization.md](265-pr-page-empty-parent-clear-normalization.md), [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), [348-pr-validate-meta-tag-inputs.md](348-pr-validate-meta-tag-inputs.md), [532-pr-validate-commit-tags-state.md](532-pr-validate-commit-tags-state.md), and [558-pr-validate-page-commit-tags-site.md](558-pr-validate-page-commit-tags-site.md) cover batched metadata writes, direct metadata action status presence/non-ok strings, local parent-clear normalization, input validation, mutable tag-state validation, action-time site validation, and local state preservation on malformed metadata responses.

Adjacent action-status type drafts [714-pr-validate-page-save-status-type.md](714-pr-validate-page-save-status-type.md), [715-pr-validate-private-message-send-status-type.md](715-pr-validate-private-message-send-status-type.md), [716-pr-validate-site-application-action-status-type.md](716-pr-validate-site-application-action-status-type.md), [717-pr-validate-site-member-action-status-type.md](717-pr-validate-site-member-action-status-type.md), [718-pr-validate-site-invite-action-status-type.md](718-pr-validate-site-invite-action-status-type.md), [719-pr-validate-forum-category-create-thread-status-type.md](719-pr-validate-forum-category-create-thread-status-type.md), [720-pr-validate-forum-thread-reply-status-type.md](720-pr-validate-forum-thread-reply-status-type.md), [721-pr-validate-forum-post-edit-status-type.md](721-pr-validate-forum-post-edit-status-type.md), [722-pr-validate-page-action-status-type.md](722-pr-validate-page-action-status-type.md), and [723-pr-validate-page-rating-status-type.md](723-pr-validate-page-rating-status-type.md) establish the same module-level response-shape pattern on other mutation actions. Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) is not a duplicate: it covers raw Ajax Module Connector response envelope status typing before module-level action payload handling. This slice validates the metadata action payload consumed by page metadata writes. No upstream issue was filed from this local workspace.

## Changes

- Add a type guard in the shared page metadata action status extractor.
- Raise `NoElementException` for a present non-string `status` with site, page fullname, page ID, event, field, expected type, and actual type context.
- Preserve Issues 245, 246, and 249 missing-status diagnostics.
- Preserve explicit non-ok string handling through `WikidotStatusCodeException`.
- Preserve request construction, tag serialization, parent clear semantics, meta diffing, and local metadata updates after confirmed `status: ok`.
- Add a `Page.set_metadata(...)` regression proving malformed `saveTags` status types preserve local tags, parent state, and cached metas.
- Add a direct `Page.metas = ...` regression proving malformed `deleteMetaTag` status types preserve cached metas.

## Type Of Change

- Response-shape validation
- Page metadata action hardening
- Generated response data diagnostics
- Cache/state consistency preservation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.set_metadata(...)` must reject a non-string `saveTags` response `status` with `NoElementException` containing site, page fullname, page ID, event, `field=status`, `expected=str`, and the actual type. |
| R2 | The direct `Page.metas = ...` setter must reject a non-string `deleteMetaTag` response `status` with the same malformed metadata action status context. |
| R3 | Missing `status` fields must keep the existing Issues 245, 246, and 249 missing-status diagnostics. |
| R4 | Explicit non-ok string statuses must still raise `WikidotStatusCodeException`. |
| R5 | Malformed, missing, and explicit non-ok metadata action statuses must not update local tags, parent state, or cached metas before a confirmed successful metadata action. |
| R6 | Valid successful `commit_tags()`, `set_parent(...)`, `set_metadata(...)`, and `Page.metas = ...` behavior must remain unchanged. |
| R7 | Adjacent page/site workflows and repository quality gates must remain green. |
| R8 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page data, private metadata values, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `{"status": ["not-ok"]}` from `saveTags` fails with malformed metadata action status context. | `test_set_metadata_malformed_action_status_type_does_not_update_local_state` failed RED with `WikidotStatusCodeException`, then passed GREEN after status typing was added. | Treating a list, dict, number, or object as a Wikidot status code rejects this local completion claim. | Batched page metadata action response shape | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | `{"status": ["not-ok"]}` from `deleteMetaTag` fails with malformed metadata action status context. | `test_metas_setter_malformed_action_status_type_does_not_update_local_state` failed RED with `WikidotStatusCodeException`, then passed GREEN after the shared helper guard. | Updating cached metas or treating malformed status as a meta-setter status-code failure rejects this local completion claim. | Direct page meta setter response shape | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Missing status fields still raise the existing metadata missing-status messages. | `test_commit_tags_missing_action_status_includes_site_page_event_and_field_context`, `test_set_parent_missing_action_status_does_not_update_local_state`, `test_metas_setter_missing_action_status_does_not_update_local_state`, and `test_set_metadata_missing_action_status_does_not_update_local_state` passed unchanged in focused GREEN. | Changing missing-status exception type, dropping context, or masking it behind type/status-code handling rejects this local completion claim. | Page metadata missing status | `tests/unit/test_page.py` |
| R4 | Non-ok string statuses keep the status-code path. | Source inspection shows the non-ok branch still runs after the new `isinstance(status, str)` guard; `TestPageWriteMethods` and page module coverage remained green. | Reclassifying non-ok strings as malformed response shape rejects this local completion claim. | Page metadata status-code handling | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Malformed and missing statuses preserve local metadata state. | The new and existing regressions assert unchanged `tags`, `parent_fullname`, and/or `_metas` after malformed responses. | Updating tags, parent state, or cached metas before confirmed action status rejects this local completion claim. | Page metadata mutation/cache boundary | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R6 | Successful valid metadata behavior remains stable. | Focused GREEN covered `test_set_metadata_batches_tags_parent_and_metas`, `test_set_parent_success`, and `test_set_parent_empty_string_clears_local_parent`; `TestPageWriteMethods` passed 69 tests. | Regressing login checks, request payloads, tag serialization, parent clear semantics, meta diffing, or local updates after confirmed success rejects this local completion claim. | Metadata write workflows | `tests/unit/test_page.py` |
| R7 | Adjacent page behavior and repo quality gates remain green. | Page module passed 390 tests, adjacent page/site coverage passed 1107 tests, full unit passed 3597 tests, ruff, mypy, pyright, and `git diff --check` passed. | Any test, lint, format, type, or whitespace failure rejects this local completion claim. | Repository quality gates | `tests/unit`, `src`, `tests` |
| R8 | No live site state or private material is needed to prove the behavior. | The regressions use synthetic unit-level response bodies and mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private metadata values, private page content, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `0e744d0 fix(page): validate metadata status type`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_malformed_action_status_type_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_malformed_action_status_type_does_not_update_local_state -q` failed before the fix with `WikidotStatusCodeException` instead of the expected malformed-shape `NoElementException`.
- GREEN focused: the same RED command passed 2 tests after the shared metadata action status guard.
- Metadata helper coverage: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_missing_action_status_includes_site_page_event_and_field_context tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_missing_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_missing_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_malformed_action_status_type_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_batches_tags_parent_and_metas tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_missing_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_malformed_action_status_type_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_success tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_empty_string_clears_local_parent -q` passed 9 tests.
- `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 69 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 390 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_source.py tests/unit/test_page_votes.py -q` passed 1107 tests.
- `uv run pytest tests/unit -q` passed 3597 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left both files unchanged.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `{"status": ["not-ok"]}` from `saveTags` raises `NoElementException` with site, page fullname, page ID, event, `field=status`, `expected=str`, and `actual=list` context.
- `{"status": ["not-ok"]}` from `deleteMetaTag` raises the same malformed status type context.
- Missing `status` values still raise the existing missing-status messages from Issues 245, 246, and 249.
- Explicit non-ok string statuses still raise `WikidotStatusCodeException`.
- Malformed and missing statuses do not update local tags, parent state, or cached metas before confirmed success.
- Successful metadata writes keep existing login checks, request payloads, tag serialization, parent clear semantics, meta diffing, local metadata updates, and method return behavior.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private metadata values, private page data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A caller may have relied on a non-string `status` object being formatted into a `WikidotStatusCodeException`. Mitigation: Wikidot action statuses are strings, Issue 403 already validates raw AMC statuses as strings, and module-level action responses should reject malformed generated data before business handling.
- Risk: This could be confused with metadata missing-status handling. Mitigation: Issues 245, 246, and 249 cover missing status and non-ok string status; this slice covers a present status with malformed type.
- Risk: This could be confused with page save, non-metadata page action, or page rating status typing. Mitigation: Issue 714 covers `savePage`, Issue 722 covers `deletePage`/`renamePage`, and Issue 723 covers `ratePage`/`cancelVote`; this slice covers metadata events.
- Risk: Tightening action response shape could hide legitimate non-ok Wikidot string statuses. Mitigation: non-ok strings are deliberately preserved on the existing `WikidotStatusCodeException` path.
- Risk: The error could become too generic for generated fixtures. Mitigation: the diagnostic names the site, page fullname, page ID, event, field, expected type, and actual type.

## Dependencies

- Existing `Page.commit_tags()` remains responsible for tag serialization only after current tag-state validation and a valid parent site.
- Existing `Page.set_parent(...)` remains responsible for parent normalization and local parent mutation only after confirmed successful metadata status.
- Existing `Page.set_metadata(...)` remains responsible for batching tags, parent, and metas and updating local state only after every returned metadata action status is confirmed successful.
- Existing direct `Page.metas = ...` remains responsible for meta diffing and cache updates only after confirmed successful metadata status.
- Existing `WikidotStatusCodeException` handling remains responsible for explicit non-ok string statuses.
- Existing `NoElementException` remains the parser/data-shape exception for missing or malformed response fields.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, complexity candidates, or response-shape candidates outside this now-covered page metadata action status type path.

## Upstream-Safe Motivation

Page metadata writes treat `saveTags`, `setParentPage`, `deleteMetaTag`, and `saveMetaTag` responses as status-bearing action payloads before updating local metadata state. Rejecting malformed status types at that boundary keeps generated or adapted response data from masquerading as a real Wikidot status code and makes metadata mutation failures easier to diagnose without changing successful actions or valid string status handling.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established browser-free page publishing, metadata batching, direct tag/parent/meta writes, parent clearing, metadata input validation, and page action diagnostics as practical consumers of metadata write behavior.
- Existing page metadata and raw AMC drafts covered missing action status context, explicit non-ok action strings, current tag-state validation, parent and meta input validation, action-time site validation, successful local metadata state updates, and raw connector envelope status typing; they did not validate the shared page metadata action status type.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, raw action response bodies, private metadata values, private page content, private site data, and source text from real sites out of upstream discussion.
