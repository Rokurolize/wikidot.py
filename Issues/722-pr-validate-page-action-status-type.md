# PR Draft: Validate Page Action Status Type

## Summary

`Page.destroy()` and `Page.rename(...)` both use the shared non-metadata page action status helper after Wikidot returns `deletePage` or `renamePage` action data. Issues [247-pr-page-rename-action-status-context.md](247-pr-page-rename-action-status-context.md) and [248-pr-page-delete-action-status-context.md](248-pr-page-delete-action-status-context.md) covered missing action `status` and explicit non-ok string statuses, but present non-string values such as `{"status": ["not-ok"]}` were still routed into `WikidotStatusCodeException` as if they were real Wikidot status codes. This change rejects malformed generated action data before treating delete/rename results as status-code failures or successful local mutations.

## Outcome

Non-metadata page actions now distinguish malformed action-response shape from real Wikidot status-code failures, preserving existing string-status behavior while surfacing type-corrupt generated responses with site, page, page ID, event, field, and type context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page lifecycle actions, publishing cleanup, migration scripts, generated page maintenance workflows, cached page-file ledgers, or local fixtures where malformed delete/rename action responses must not be mistaken for confirmed Wikidot action results.

## Current Evidence

Local rollout-backed drafts already identify browser-free page writes and page lifecycle operations as practical shared workflows. Existing drafts [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), [247-pr-page-rename-action-status-context.md](247-pr-page-rename-action-status-context.md), [248-pr-page-delete-action-status-context.md](248-pr-page-delete-action-status-context.md), [266-pr-page-rename-file-cache-invalidation.md](266-pr-page-rename-file-cache-invalidation.md), [352-pr-validate-page-rename-fullname-input.md](352-pr-validate-page-rename-fullname-input.md), and [557-pr-validate-page-destroy-site.md](557-pr-validate-page-destroy-site.md) cover page save status, missing/non-ok rename/delete action status, file-cache invalidation after confirmed rename, rename input validation, and destroy-time parent-site validation.

Adjacent action-status type drafts [714-pr-validate-page-save-status-type.md](714-pr-validate-page-save-status-type.md), [715-pr-validate-private-message-send-status-type.md](715-pr-validate-private-message-send-status-type.md), [716-pr-validate-site-application-action-status-type.md](716-pr-validate-site-application-action-status-type.md), [717-pr-validate-site-member-action-status-type.md](717-pr-validate-site-member-action-status-type.md), [718-pr-validate-site-invite-action-status-type.md](718-pr-validate-site-invite-action-status-type.md), [719-pr-validate-forum-category-create-thread-status-type.md](719-pr-validate-forum-category-create-thread-status-type.md), [720-pr-validate-forum-thread-reply-status-type.md](720-pr-validate-forum-thread-reply-status-type.md), and [721-pr-validate-forum-post-edit-status-type.md](721-pr-validate-forum-post-edit-status-type.md) establish the same module-level response-shape pattern on other mutation actions. Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) is not a duplicate: it covers raw Ajax Module Connector response envelope status typing before module-level action payload handling. This slice validates the non-metadata page action payload consumed by `Page.destroy()` and `Page.rename(...)`. No upstream issue was filed from this local workspace.

## Changes

- Add a type guard in the shared non-metadata page action status extractor.
- Raise `NoElementException` for a present non-string `status` with site, page fullname, page ID, event, field, expected type, and actual type context.
- Preserve Issues 247 and 248 missing-status diagnostics.
- Preserve explicit non-ok string handling through `WikidotStatusCodeException`.
- Add a focused RED/GREEN regression proving malformed `renamePage` status types preserve local page identity and cached files.
- Add a delete-path regression proving malformed `deletePage` status types preserve page-bound caches.
- Add a compatibility regression proving explicit non-ok string rename statuses remain status-code failures and preserve the same local state.

## Type Of Change

- Response-shape validation
- Page delete/rename action hardening
- Generated response data diagnostics
- Cache/state consistency preservation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.rename(...)` must reject a non-string `renamePage` response `status` with `NoElementException` containing site, page fullname, page ID, event, `field=status`, `expected=str`, and the actual type. |
| R2 | `Page.destroy()` must reject a non-string `deletePage` response `status` with the same malformed action status context. |
| R3 | Missing `status` fields must keep the existing Issues 247 and 248 missing-status diagnostics. |
| R4 | Explicit non-ok string statuses must still raise `WikidotStatusCodeException`. |
| R5 | Malformed and explicit non-ok action statuses must not update rename identity, clear rename file caches, or clear destroy page-bound caches. |
| R6 | Valid successful delete and rename behavior must remain unchanged. |
| R7 | Adjacent page/site workflows and repository quality gates must remain green. |
| R8 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `{"status": ["not-ok"]}` from `renamePage` fails with malformed action status context. | `test_rename_malformed_action_status_type_preserves_local_name_and_files_cache` failed RED with `WikidotStatusCodeException`, then passed GREEN after status typing was added. | Treating a list, dict, number, or object as a Wikidot status code rejects this local completion claim. | Page rename action response shape | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | `{"status": ["not-ok"]}` from `deletePage` fails with malformed action status context. | `test_destroy_malformed_action_status_type_preserves_page_bound_caches` passed after the shared helper guard and asserts the delete caches remain intact. | Clearing page-bound caches or treating malformed status as a delete status-code failure rejects this local completion claim. | Page delete action response shape | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Missing status fields still raise the Issues 247/248 missing-status messages. | `test_rename_missing_action_status_does_not_update_local_name` and `test_destroy_missing_action_status_includes_site_page_event_and_field_context` passed unchanged in focused GREEN. | Changing missing-status exception type, dropping context, or masking it behind type/status-code handling rejects this local completion claim. | Page action missing status | `tests/unit/test_page.py` |
| R4 | `{"status": "not_ok"}` keeps the status-code path. | `test_rename_explicit_non_ok_action_status_preserves_local_name_and_files_cache` passed and asserts `status_code == "not_ok"`. | Reclassifying non-ok strings as malformed response shape rejects this local completion claim. | Page action status-code handling | `tests/unit/test_page.py` |
| R5 | Malformed and explicit non-ok statuses preserve local page state and caches. | The new regressions assert unchanged `fullname`, `category`, `name`, cached `_files`, cached `_source`, cached `_revisions`, cached `_votes`, cached `_metas`, cached `_discussion`, and `_discussion_checked`. | Updating identity, clearing file caches, clearing page-bound caches, or decoding repeatedly rejects this local completion claim. | Page mutation/cache boundary | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R6 | Successful valid delete/rename behavior remains stable. | Focused GREEN covered `test_destroy_success`, `test_destroy_success_clears_page_bound_caches`, `test_rename_success`, `test_rename_with_category`, and `test_rename_success_invalidates_cached_files`; `TestPageWriteMethods` passed 65 tests. | Regressing login, request payloads, successful cache clearing after confirmed delete, category/name splitting, file-cache invalidation after confirmed rename, or method chaining rejects this local completion claim. | Delete/rename workflows | `tests/unit/test_page.py` |
| R7 | Adjacent page behavior and repo quality gates remain green. | Page module passed 386 tests, adjacent page/site coverage passed 1103 tests, full unit passed 3593 tests, ruff, mypy, pyright, and `git diff --check` passed. | Any test, lint, format, type, or whitespace failure rejects this local completion claim. | Repository quality gates | `tests/unit`, `src`, `tests` |
| R8 | No live site state or private material is needed to prove the behavior. | The regressions use synthetic unit-level response bodies and mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private page content, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `0c01961 fix(page): validate action status type`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_rename_malformed_action_status_type_preserves_local_name_and_files_cache -q` failed before the fix with `WikidotStatusCodeException` instead of the expected malformed-shape `NoElementException`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_destroy_success tests/unit/test_page.py::TestPageWriteMethods::test_destroy_success_clears_page_bound_caches tests/unit/test_page.py::TestPageWriteMethods::test_destroy_rejects_malformed_site_before_login_or_cache_clear tests/unit/test_page.py::TestPageWriteMethods::test_destroy_missing_action_status_includes_site_page_event_and_field_context tests/unit/test_page.py::TestPageWriteMethods::test_destroy_malformed_action_status_type_preserves_page_bound_caches tests/unit/test_page.py::TestPageWriteMethods::test_rename_success tests/unit/test_page.py::TestPageWriteMethods::test_rename_with_category tests/unit/test_page.py::TestPageWriteMethods::test_rename_success_invalidates_cached_files tests/unit/test_page.py::TestPageWriteMethods::test_rename_missing_action_status_does_not_update_local_name tests/unit/test_page.py::TestPageWriteMethods::test_rename_malformed_action_status_type_preserves_local_name_and_files_cache tests/unit/test_page.py::TestPageWriteMethods::test_rename_explicit_non_ok_action_status_preserves_local_name_and_files_cache tests/unit/test_page.py::TestPageWriteMethods::test_rename_rejects_non_string_fullname_before_request tests/unit/test_page.py::TestPageWriteMethods::test_rename_rejects_malformed_site_before_login -q` passed 13 tests.
- `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 65 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 386 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_source.py tests/unit/test_page_votes.py -q` passed 1103 tests.
- `uv run pytest tests/unit -q` passed 3593 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left both files unchanged.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `{"status": ["not-ok"]}` from `renamePage` raises `NoElementException` with site, page fullname, page ID, event, `field=status`, `expected=str`, and `actual=list` context.
- `{"status": ["not-ok"]}` from `deletePage` raises the same malformed status type context.
- Missing `status` values still raise the existing missing-status messages from Issues 247 and 248.
- `{"status": "not_ok"}` still raises `WikidotStatusCodeException`.
- Malformed and explicit non-ok statuses do not update local page identity.
- Malformed and explicit non-ok statuses do not clear cached page files before a confirmed rename.
- Malformed delete statuses do not clear page-bound caches before a confirmed delete.
- Successful valid deletes and renames keep the existing login checks, request payloads, successful cache updates, category/name splitting, and method return behavior.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private page data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A caller may have relied on a non-string `status` object being formatted into a `WikidotStatusCodeException`. Mitigation: Wikidot action statuses are strings, Issue 403 already validates raw AMC statuses as strings, and module-level action responses should reject malformed generated data before business handling.
- Risk: This could be confused with rename/delete missing-status handling. Mitigation: Issues 247 and 248 cover missing status and non-ok string status; this slice covers a present status with malformed type.
- Risk: This could be confused with page save status typing. Mitigation: Issue 714 covers `Page.create_or_edit(...)` `savePage`; this slice covers the shared non-metadata page action helper for `deletePage` and `renamePage`.
- Risk: This could be confused with page metadata or rating action responses. Mitigation: metadata and rating helpers are separate response surfaces and should only be changed after their own duplicate check.
- Risk: Tightening action response shape could hide legitimate non-ok Wikidot string statuses. Mitigation: non-ok strings are deliberately preserved on the existing `WikidotStatusCodeException` path.
- Risk: The error could become too generic for generated fixtures. Mitigation: the diagnostic names the site, page fullname, page ID, event, field, expected type, and actual type.

## Dependencies

- Existing `Page.destroy()` remains responsible for delete request construction and cache clearing only after confirmed successful delete status.
- Existing `Page.rename(...)` remains responsible for rename request construction, local identity updates, and file-cache invalidation only after confirmed successful rename status.
- Existing `WikidotStatusCodeException` handling remains responsible for explicit non-ok string statuses.
- Existing `NoElementException` remains the parser/data-shape exception for missing or malformed response fields.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, complexity candidates, page metadata/rating action status type guards, or other response-shape candidates outside this now-covered non-metadata page action status type path.

## Upstream-Safe Motivation

`Page.destroy()` and `Page.rename(...)` treat `deletePage` and `renamePage` responses as status-bearing action payloads before clearing page caches or mutating local page identity. Rejecting malformed status types at that boundary keeps generated or adapted response data from masquerading as a real Wikidot status code and makes page lifecycle failures easier to diagnose without changing successful actions or valid string status handling.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established browser-free page writes, page lifecycle cleanup, publish workflows, rename cache invalidation, and page action diagnostics as practical consumers of delete/rename behavior.
- Existing page-action and raw AMC drafts covered missing action status context, explicit non-ok action strings, page save status typing, rename input validation, destroy parent-site validation, and raw connector envelope status typing; they did not validate the shared non-metadata page action status type.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private page content, private site data, page source text from real sites, and source text from real sites out of upstream discussion.
