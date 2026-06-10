# PR Draft: Validate Page Edit Retained Fullname

## Summary

`Page.edit(...)` already validates explicit `title`, `source`, `comment`, `force_edit`, retained `page.site`, and retained omitted-title state before save delegation. One adjacent retained identity field still crossed the edit boundary unvalidated: if a valid `Page` was later mutated, fixture-loaded, or rehydrated with a non-string `fullname`, `Page.edit(title="...", source="...")` could call `login_check()` and continue toward `Page.create_or_edit(...)` before the malformed retained page fullname was diagnosed.

This change validates retained `self.fullname` with `_validate_page_text_field("fullname", self.fullname)` after retained site validation and before `login_check()`, current-source reads, `Page.create_or_edit(...)` delegation, local title/source mutation, revision-count sync, or revision-cache invalidation. Malformed retained fullnames now raise `ValueError("fullname must be a string")` locally and side-effect free.

## Outcome

Page edits can no longer authenticate or delegate write work when the page object's retained fullname has been corrupted after construction. Valid page edits continue to use the current retained string fullname unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page editing, generated fixtures, migration ledgers, publication tooling, local tests, or serialized and rehydrated `Page` records before calling `Page.edit(...)`.

## Current Evidence

Local rollout-backed drafts repeatedly identify page editing and page identity state as practical workflow surfaces. Existing drafts [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [259-pr-page-edit-local-cache-sync.md](259-pr-page-edit-local-cache-sync.md), [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md), [564-pr-validate-page-edit-site.md](564-pr-validate-page-edit-site.md), and [785-pr-validate-page-edit-retained-title.md](785-pr-validate-page-edit-retained-title.md) establish page edit defaulting, local cache sync, revision invalidation, direct create/edit input validation, constructor identity validation, edit-time retained site validation, and adjacent retained-title validation.

This slice is not a duplicate of those drafts. Issue 481 validates `Page(fullname=...)` at construction, but it cannot cover post-construction mutation, fixture mutation, or rehydrated state before a later edit call. The direct `Page.create_or_edit(...)` tests validate `fullname=` before that helper's own login check, but `Page.edit(...)` performs its own login before delegating to the helper. Issue 564 validates retained `page.site` at edit time, and Issue 785 validates retained `page.title`; neither validates the retained page fullname used to address the edit target.

The focused RED test demonstrated the gap: `mock_page_with_id.fullname = 3` followed by `mock_page_with_id.edit(title="Updated Title", source="Updated source")` raised only after `login_check()` had already been called, causing the side-effect assertion `login_check.assert_not_called()` to fail.

## Related Issue / Non-Duplicate Analysis

Builds directly on [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md), [564-pr-validate-page-edit-site.md](564-pr-validate-page-edit-site.md), and [785-pr-validate-page-edit-retained-title.md](785-pr-validate-page-edit-retained-title.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `self.fullname` at the start of `Page.edit(...)` after retained site validation.
- Run the retained-fullname validation before `login_check()`.
- Pass the validated local `fullname` value into `Page.create_or_edit(...)`.
- Preserve explicit edit input validation, retained-title validation, source defaulting, page-ID resolution, create/edit delegation, and post-success local cache sync.
- Add a focused regression for a mutated retained fullname that previously reached login before failing.

## Type Of Change

- State validation
- Page edit-path hardening
- Retained identity integrity
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.edit(title=..., source=...)` must reject a retained `page.fullname` that is not a string with `ValueError("fullname must be a string")`. |
| R2 | The retained-fullname rejection must happen before `login_check()`, current-source reads, `Page.create_or_edit(...)`, local title/source mutation, revision-count sync, or revision-cache invalidation. |
| R3 | Constructor-time `Page.fullname` validation, direct `Page.create_or_edit(fullname=...)` validation, retained site validation, and retained title validation must remain unchanged. |
| R4 | Valid page edits, edit lock/save behavior, local source sync, revision-cache invalidation, and adjacent page/site workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, edit coverage, adjacent page/source/site coverage, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Edit rejects malformed retained fullname state. | `TestPageEdit.test_edit_rejects_malformed_retained_fullname_before_login_or_delegation` failed RED because `login_check()` had already been called, then passed GREEN after retained-fullname validation was added. | Accepting an integer or other non-string retained fullname, coercing it, or deferring diagnosis past authentication rejects this local completion claim. | `Page.edit(...)` retained fullname preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Validation is side-effect free. | The regression asserts `login_check` and `Page.create_or_edit(...)` are not called, and that retained fullname, title, `revisions_count`, `_source`, and `_revisions` remain unchanged. | Authenticating, delegating to `Page.create_or_edit(...)`, fetching current source, updating `title`, updating `_source`, changing `revisions_count`, or clearing `_revisions` rejects this local completion claim. | Page edit preflight | focused test |
| R3 | Existing adjacent validation boundaries remain stable. | `TestPageEdit` passed 15 tests after the fix, including retained site/title and explicit input validation coverage. | Regressing constructor identity validation, direct create/edit fullname validation, retained site validation, retained title validation, or explicit edit input diagnostics rejects this local completion claim. | Public edit inputs and retained state | `tests/unit/test_page.py` |
| R4 | Valid edit behavior and adjacent page workflows remain green. | Adjacent page/source/revision/file/vote/site coverage passed 1382 tests; full unit passed 3808 tests. | Regressing valid edits, edit-lock/save behavior, local source sync, revision-cache invalidation, page source/revision/file/vote workflows, site workflows, or full unit coverage rejects this local completion claim. | Page edit and adjacent workflows | `tests/unit` |
| R5 | The local proof stays unit-level and private-data-free. | All regressions use synthetic local fixtures and mocks. | Using live Wikidot, credentials, cookies, auth JSON, raw private page source, raw rollout paths, private site names, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `e2b929d fix(page): validate retained edit fullname`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageEdit::test_edit_rejects_malformed_retained_fullname_before_login_or_delegation -q --tb=short` failed before the fix because `login_check.assert_not_called()` observed one login call.
- GREEN focused: the same focused command passed 1 test after the fix.
- Edit coverage: `uv run pytest tests/unit/test_page.py::TestPageEdit -q` passed 15 tests after formatting.
- Adjacent page coverage: `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1382 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3808 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted after formatting the edited test file.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Page.edit(title=..., source=...)` raises `ValueError("fullname must be a string")` when the edited page's retained `fullname` is an integer or other non-string.
- The retained-fullname failure occurs before login checks, current-source reads, `Page.create_or_edit(...)`, local title/source mutation, revision-count sync, or revision-cache invalidation.
- The retained-fullname failure does not coerce or rewrite the corrupted retained `fullname`.
- Explicit invalid `title`, `comment`, `source`, and `force_edit` inputs still raise the same diagnostics before request work.
- Malformed retained `page.site` and omitted-title retained `page.title` still fail at their existing boundaries.
- Valid page edits still delegate the current retained string fullname.
- Valid explicit-title edits still update local state from the returned edited page after confirmed successful delegation.
- Existing edit lock/save behavior, local source sync, revision-cache invalidation, page source/revision/file/vote workflows, and site workflows remain green.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Callers with mutated or rehydrated malformed `Page.fullname` values now fail before edit work. Mitigation: constructor validation already requires strings, and corrupted retained identity state should be fixed before request construction rather than coerced into a page save target.
- Risk: This could be mistaken for direct `Page.create_or_edit(fullname=...)` validation. Mitigation: that boundary already validates before its own login; this slice only covers `Page.edit(...)` performing an earlier login before delegation.
- Risk: This could be mistaken for constructor identity validation. Mitigation: Issue 481 remains the constructor boundary; this slice covers post-construction mutation, fixture mutation, or rehydrated state before a later edit call.

## Dependencies

- Existing `_validate_page_text_field(...)` remains the canonical page text-field validator.
- Existing `Page(fullname=...)` constructor validation remains unchanged.
- Existing direct `Page.create_or_edit(fullname=...)` validation remains unchanged.
- Existing `Page.edit(...)` source defaulting, `Page.create_or_edit(...)` delegation, local state sync, revision-count handling, revision-cache invalidation, and source-cache update behavior remains unchanged for valid values.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, cache ownership boundaries, result ergonomics, or complexity candidates outside this now-covered edit retained-fullname path.

## Upstream-Safe Motivation

`Page.edit(...)` addresses the write target through the page object's retained `fullname`. That retained identity should satisfy the same string contract as direct `Page.create_or_edit(fullname=...)` before authentication, current-source reads, save delegation, or local cache mutation can happen. Validating it locally keeps corrupted fixture or rehydrated state from becoming an edit target while preserving valid edit behavior.

## Local Evidence

- Local rollout-backed work established page editing as a practical workflow through login/source ordering, local title/source cache sync, revision-cache invalidation, page source input validation, explicit page title/comment validation, constructor identity validation, retained edit-site validation, and retained edit-title validation.
- Existing local drafts covered direct `Page.create_or_edit(fullname=...)` input validation, constructor-time `Page.fullname` validation, retained edit parent site validation, retained edit title validation, source defaulting, edit-lock/save behavior, and cache invalidation; they did not cover post-construction malformed retained `self.fullname` state used by the `Page.edit(...)` path before its entry login.
- The focused RED failure showed malformed retained fullname state could call `login_check()` before failing.
- This slice only validates the retained fullname used by `Page.edit(...)` calls. It does not change parser field extraction, fullname normalization, URL construction, page-ID acquisition, source text contents, source acquisition internals, edit-lock handling, save response handling, metadata writes, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw page source text, rendered page content, private page content, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates type only. It does not reject empty fullnames, trim fullnames, coerce non-string values, reassign `self.fullname` during preflight, or change the local title/source update rule after successful edit delegation.
