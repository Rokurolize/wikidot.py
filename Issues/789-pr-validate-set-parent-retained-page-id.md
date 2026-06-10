# PR Draft: Validate Set Parent Retained Page ID

## Summary

`Page.set_parent()` already validates the requested parent fullname, retained `page.site`, and returned `setParentPage` action status before updating local parent state. One retained identity field still crossed the action authentication boundary late: if a valid `Page` was later mutated, fixture-loaded, or rehydrated with a malformed or negative cached `_id`, `set_parent("...")` called `login_check()` before the retained page-ID error surfaced through `self.id`.

This change validates a present retained `_id` with `_validate_retained_page_id(self)` after parent-fullname normalization and site validation and before login checks, AMC request construction, response handling, or local parent-state mutation. Missing `_id is None` still preserves the existing login-before-lazy-ID-lookup behavior.

## Outcome

Direct parent updates can no longer authenticate or build `setParentPage` request work through corrupted retained page-ID state. Valid loaded page IDs still produce the same string `pageId` payload, and unloaded pages still acquire IDs only after the entry login succeeds.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page parent cleanup, publishing metadata flows, generated page ledgers, migration fixtures, or serialized and rehydrated `Page` records before calling `Page.set_parent()`.

## Current Evidence

Local rollout-backed drafts repeatedly identify direct and batched parent metadata writes as practical workflow surfaces. Existing drafts [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), [246-pr-page-direct-metadata-action-status-context.md](246-pr-page-direct-metadata-action-status-context.md), [265-pr-page-empty-parent-clear-normalization.md](265-pr-page-empty-parent-clear-normalization.md), [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), [559-pr-validate-page-set-parent-site.md](559-pr-validate-page-set-parent-site.md), [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md), [664-pr-validate-page-collection-retained-page-id-state.md](664-pr-validate-page-collection-retained-page-id-state.md), [787-pr-validate-page-edit-retained-page-id.md](787-pr-validate-page-edit-retained-page-id.md), and [788-pr-validate-commit-tags-retained-page-id.md](788-pr-validate-commit-tags-retained-page-id.md) establish parent metadata writes, metadata action-status validation, parent clear normalization, parent-fullname input validation, retained site validation, page-ID validation, collection retained-ID validation, edit-path retained-ID validation, and direct tag-save retained-ID validation.

This slice is not a duplicate of those drafts. Issue 343 validates the caller-provided `parent_fullname` value. Issue 559 validates retained `page.site` before direct parent updates. Issues 413 and 658 validate public setter/getter page-ID behavior, but `Page.set_parent()` had its own earlier login boundary before reaching the getter. Issue 664 validates retained IDs during collection acquisition. Issues 787 and 788 validate adjacent write paths, not direct `setParentPage`.

No upstream issue was filed from this local workspace.

## Changes

- Validate present retained `self._id` at the start of `Page.set_parent()` with `_validate_retained_page_id(self)`.
- Run retained-ID validation before `login_check()`.
- Preserve missing-ID behavior by calling `self.id` after login only when retained `_id is None`.
- Use the validated or lazily acquired local `page_id` value in the string `setParentPage` request payload.
- Add focused regressions for malformed and negative retained page IDs that previously reached login before failing.

## Type Of Change

- State validation
- Direct parent-update hardening
- Retained identity integrity
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.set_parent("...")` must reject retained malformed `_id` values such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("page.id must be an integer")`. |
| R2 | `Page.set_parent("...")` must reject retained negative `_id=-1` with `ValueError("page.id must be non-negative")`. |
| R3 | Retained-ID rejection must happen before `login_check()`, AMC request construction, response handling, or local parent-state mutation. |
| R4 | Missing `_id is None` must preserve the existing login-before-lazy-ID-lookup behavior. |
| R5 | Parent-fullname validation, retained site validation, valid parent sets, parent clears, valid logged-out behavior, metadata action-status diagnostics, and existing page-ID boundaries must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, set-parent coverage, write-method coverage, adjacent page/source/site coverage, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct parent updates reject malformed retained page IDs before authentication. | `TestPageWriteMethods.test_set_parent_rejects_malformed_retained_page_ids_before_login` failed RED for five malformed values because `login_check()` had already been called, then passed GREEN after retained-ID validation moved before login. | Accepting booleans/floats, coercing values, authenticating, sending AMC requests, or delaying diagnosis to the public getter rejects this local completion claim. | `Page.set_parent()` retained page-ID preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Direct parent updates reject negative retained page IDs before authentication. | `TestPageWriteMethods.test_set_parent_rejects_negative_retained_page_id_before_login` failed RED because `login_check()` had already been called, then passed GREEN with the non-negative diagnostic before login. | Treating a negative retained ID as a request ID, authenticating before the local state error, or changing the diagnostic rejects this local completion claim. | `Page.set_parent()` retained page-ID preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Validation is side-effect free for corrupted retained IDs. | The regressions assert `login_check()` and `site.amc_request(...)` are not called, and that the previous `parent_fullname` remains unchanged. | Calling login, constructing or sending `setParentPage`, parsing responses, or mutating parent state rejects this local completion claim. | Direct parent-update preflight | focused tests |
| R4 | Missing IDs still defer lookup until after login. | The implementation stores `page_id = _validate_retained_page_id(self)` and only calls `self.id` after login when `page_id is None`; existing set-parent success and logged-out paths remain covered by write-method and adjacent suites. | Calling `PageCollection.get_page_ids()` before login for `_id is None` would change the existing authentication boundary. | Direct parent-update missing-ID flow | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Existing adjacent validation boundaries remain stable. | Focused set-parent retained-ID tests passed 6 tests, set-parent neighborhood coverage passed 6 tests, `TestPageWriteMethods` passed 83 tests, adjacent page/source/revision/file/vote/site coverage passed 1400 tests, and full unit coverage passed 3826 tests. | Regressing parent-fullname validation, retained site validation, parent clear normalization, valid parent payloads, logged-out behavior, status diagnostics, page ID setter/getter behavior, or adjacent page workflows rejects this local completion claim. | Page write and adjacent workflows | `tests/unit` |
| R6 | The local proof stays unit-level and private-data-free. | All regressions use synthetic local fixtures and mocks. | Using live Wikidot, credentials, cookies, auth JSON, raw private page source, raw rollout paths, private site names, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `0fac08d fix(page): validate set parent page id`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_rejects_malformed_retained_page_ids_before_login tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_rejects_negative_retained_page_id_before_login -q --tb=short` failed six retained page-ID cases before the fix because `login_check.assert_not_called()` observed one login call.
- GREEN focused: the same focused command passed 6 tests after the fix.
- Set-parent neighborhood: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_success tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_clear tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_empty_string_clears_local_parent tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_rejects_non_string_parent_before_request tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_rejects_malformed_site_before_login tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_missing_action_status_does_not_update_local_state -q` passed 6 tests.
- Write-method coverage: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 83 tests.
- Adjacent page coverage: `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1400 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3826 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Page.set_parent("new-parent")` raises `ValueError("page.id must be an integer")` when retained `_id` is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- The same method raises `ValueError("page.id must be non-negative")` when retained `_id` is `-1`.
- The retained-ID failure occurs before login checks, AMC request construction, response handling, or local parent-state mutation.
- Failed retained-ID preflight does not coerce or rewrite the corrupted retained `_id`.
- `_id is None` still follows the existing authenticated lazy lookup path.
- Invalid `parent_fullname` still fails before site and ID validation.
- Malformed retained `page.site` still fails before retained ID validation can call login or AMC request work.
- Valid parent updates, parent clears, valid logged-out behavior, and `setParentPage` action-status diagnostics remain intact.
- Existing page-ID constructor, setter, getter, create/edit argument validation, collection retained-ID validation, edit-path retained-ID validation, and commit-tags retained-ID validation remain unchanged.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Callers with mutated or rehydrated malformed `Page._id` values now fail before parent-update work. Mitigation: constructor, setter, getter, direct create/edit, collection, edit-path, and commit-tags validation already define those values as invalid page identity state.
- Risk: This could regress unloaded pages that need authentication before lazy page-ID lookup. Mitigation: `_id is None` is still not acquired until after `login_check()` succeeds; the preflight only validates present retained state.
- Risk: This could be mistaken for parent-fullname validation. Mitigation: Issue 343 remains the parent input boundary; this slice covers valid parent inputs with corrupted retained page identity.

## Dependencies

- Existing `_validate_retained_page_id(...)` remains the canonical optional retained page-ID validator.
- Existing `Page.id` getter validation remains unchanged.
- Existing `Page.set_parent()` parent-fullname normalization, retained site validation, request shape, status diagnostics, and local parent update timing remain unchanged for valid values.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, cache ownership boundaries, result ergonomics, or complexity candidates outside this now-covered direct parent-update retained-page-ID path.

## Upstream-Safe Motivation

`Page.set_parent()` is the direct low-level parent-change primitive. A present retained page ID should satisfy the same integer and non-negative contract as direct `Page.id`, `Page.edit(...)`, and `Page.commit_tags()` before authentication or `setParentPage` request work can happen. Validating present retained IDs locally keeps corrupted fixture or rehydrated state from becoming a parent-update identifier while preserving valid loaded IDs and authenticated lazy lookup for unloaded pages.

## Local Evidence

- Local rollout-backed work established direct and batched parent metadata writes as practical workflows through metadata batching, direct parent updates, parent clear normalization, response-status diagnostics, retained site validation, and page-ID state validation.
- Existing local drafts covered direct `Page.set_parent()` parent-fullname validation, retained set-parent site validation, direct `Page.id` setter/getter validation, collection retained page-ID validation, page edit retained page-ID validation, and commit-tags retained page-ID validation; they did not cover present malformed retained `_id` state used by `Page.set_parent()` before its entry login.
- The focused RED failure showed malformed and negative retained page-ID state could call `login_check()` before failing.
- This slice only validates present retained page IDs used by `Page.set_parent()` calls. It does not change parent name syntax, empty-string clear behavior, metadata batching, tag saves, meta-tag diffing, page-ID acquisition URLs, page-ID parser behavior, source/edit behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw page source text, rendered page content, private page content, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates present retained IDs without calling `Page.id` before login. That preserves the existing unauthenticated direct parent-update behavior for missing IDs while making corrupted non-`None` retained identity state fail deterministically at the `set_parent()` boundary.
