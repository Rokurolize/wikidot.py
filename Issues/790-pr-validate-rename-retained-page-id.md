# PR Draft: Validate Rename Retained Page ID

## Summary

`Page.rename()` already validates the requested `new_fullname`, retained `page.site`, returned `renamePage` action status, and successful file-cache invalidation ordering. One retained identity field still crossed the action authentication boundary late: if a valid `Page` was later mutated, fixture-loaded, or rehydrated with a malformed or negative cached `_id`, `rename("...")` called `login_check()` before the retained page-ID error surfaced through `self.id`.

This change validates a present retained `_id` with `_validate_retained_page_id(self)` after rename-target and site validation and before login checks, AMC request construction, response handling, local page identity mutation, or file-cache invalidation. Missing `_id is None` still preserves the existing login-before-lazy-ID-lookup behavior.

## Outcome

Page renames can no longer authenticate or build `renamePage` request work through corrupted retained page-ID state. Valid loaded page IDs still produce the same integer `page_id` payload, and unloaded pages still acquire IDs only after the entry login succeeds.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page rename cleanup, generated page maintenance, migration fixtures, translation workflows, audit ledgers, or serialized and rehydrated `Page` records before calling `Page.rename()`.

## Current Evidence

Local rollout-backed drafts repeatedly identify page rename and retained page identity as practical workflow surfaces. Existing drafts [247-pr-page-rename-action-status-context.md](247-pr-page-rename-action-status-context.md), [266-pr-page-rename-file-cache-invalidation.md](266-pr-page-rename-file-cache-invalidation.md), [352-pr-validate-page-rename-fullname-input.md](352-pr-validate-page-rename-fullname-input.md), [560-pr-validate-page-rename-site.md](560-pr-validate-page-rename-site.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md), [664-pr-validate-page-collection-retained-page-id-state.md](664-pr-validate-page-collection-retained-page-id-state.md), [787-pr-validate-page-edit-retained-page-id.md](787-pr-validate-page-edit-retained-page-id.md), [788-pr-validate-commit-tags-retained-page-id.md](788-pr-validate-commit-tags-retained-page-id.md), and [789-pr-validate-set-parent-retained-page-id.md](789-pr-validate-set-parent-retained-page-id.md) establish rename action-status validation, rename file-cache invalidation, rename target validation, retained rename-site validation, page-ID validation, retained getter validation, collection retained-ID validation, edit-path retained-ID validation, direct tag-save retained-ID validation, and direct parent-update retained-ID validation.

This slice is not a duplicate of those drafts. Issue 352 validates the caller-provided `new_fullname` value. Issue 560 validates retained `page.site` before rename work. Issues 247 and 266 validate remote rename responses and local cache invalidation after a successful response. Issues 413 and 658 validate public setter/getter page-ID behavior, but `Page.rename()` had its own earlier login boundary before reaching the getter. Issue 664 validates retained IDs during collection acquisition. Issues 787, 788, and 789 validate adjacent write paths, not direct `renamePage`.

No upstream issue was filed from this local workspace.

## Changes

- Validate present retained `self._id` at the start of `Page.rename()` with `_validate_retained_page_id(self)`.
- Run retained-ID validation before `login_check()`.
- Preserve missing-ID behavior by calling `self.id` after login only when retained `_id is None`.
- Use the validated or lazily acquired local `page_id` value in the `renamePage` request payload.
- Add focused regressions for malformed and negative retained page IDs that previously reached login before failing.

## Type Of Change

- State validation
- Page rename hardening
- Retained identity integrity
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.rename("...")` must reject retained malformed `_id` values such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("page.id must be an integer")`. |
| R2 | `Page.rename("...")` must reject retained negative `_id=-1` with `ValueError("page.id must be non-negative")`. |
| R3 | Retained-ID rejection must happen before `login_check()`, AMC request construction, response handling, local page identity mutation, or file-cache invalidation. |
| R4 | Missing `_id is None` must preserve the existing login-before-lazy-ID-lookup behavior. |
| R5 | Rename target validation, retained site validation, successful simple renames, category-qualified renames, action-status diagnostics, file-cache invalidation, and existing page-ID boundaries must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, rename coverage, write-method coverage, adjacent page/source/site coverage, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Renames reject malformed retained page IDs before authentication. | `TestPageWriteMethods.test_rename_rejects_malformed_retained_page_ids_before_login` failed RED for five malformed values because `login_check()` had already been called, then passed GREEN after retained-ID validation moved before login. | Accepting booleans/floats, coercing values, authenticating, sending AMC requests, or delaying diagnosis to the public getter rejects this local completion claim. | `Page.rename()` retained page-ID preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Renames reject negative retained page IDs before authentication. | `TestPageWriteMethods.test_rename_rejects_negative_retained_page_id_before_login` failed RED because `login_check()` had already been called, then passed GREEN with the non-negative diagnostic before login. | Treating a negative retained ID as a request ID, authenticating before the local state error, or changing the diagnostic rejects this local completion claim. | `Page.rename()` retained page-ID preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Validation is side-effect free for corrupted retained IDs. | The regressions assert `login_check()` and `site.amc_request(...)` are not called, and that `fullname`, `category`, `name`, and `_files` remain unchanged. | Calling login, constructing or sending `renamePage`, parsing responses, mutating page identity, or clearing `_files` rejects this local completion claim. | Rename preflight | focused tests |
| R4 | Missing IDs still defer lookup until after login. | The implementation stores `page_id = _validate_retained_page_id(self)` and only calls `self.id` after login when `page_id is None`; existing rename success and logged-out paths remain covered by write-method and adjacent suites. | Calling `PageCollection.get_page_ids()` before login for `_id is None` would change the existing authentication boundary. | Rename missing-ID flow | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Existing adjacent validation boundaries remain stable. | Focused rename retained-ID tests passed 6 tests, rename-focused coverage passed 14 tests, `TestPageWriteMethods` passed 89 tests, adjacent page/source/revision/file/votes/site coverage passed 1182 tests, and full unit coverage passed 3832 tests. | Regressing rename target validation, retained site validation, action-status diagnostics, file-cache invalidation, valid rename payloads, page ID setter/getter behavior, or adjacent page workflows rejects this local completion claim. | Page write and adjacent workflows | `tests/unit` |
| R6 | The local proof stays unit-level and private-data-free. | All regressions use synthetic local fixtures and mocks. | Using live Wikidot, credentials, cookies, auth JSON, raw private page source, raw rollout paths, private site names, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `ec4a0ba fix(page): validate rename page id`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_rename_rejects_malformed_retained_page_ids_before_login tests/unit/test_page.py::TestPageWriteMethods::test_rename_rejects_negative_retained_page_id_before_login -q --tb=short` failed six retained page-ID cases before the fix because `login_check.assert_not_called()` observed one login call.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_rename_rejects_malformed_retained_page_ids_before_login tests/unit/test_page.py::TestPageWriteMethods::test_rename_rejects_negative_retained_page_id_before_login -q` passed 6 tests.
- Rename-focused coverage: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -k rename -q` passed 14 tests.
- Write-method coverage: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 89 tests.
- Adjacent page coverage: `uv run pytest tests/unit/test_page.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1182 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3832 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Page.rename("component:new-name")` raises `ValueError("page.id must be an integer")` when retained `_id` is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- The same method raises `ValueError("page.id must be non-negative")` when retained `_id` is `-1`.
- The retained-ID failure occurs before login checks, AMC request construction, response handling, local page identity mutation, or file-cache invalidation.
- Failed retained-ID preflight does not coerce or rewrite the corrupted retained `_id`.
- `_id is None` still follows the existing authenticated lazy lookup path.
- Invalid `new_fullname` still fails before site and ID validation.
- Malformed retained `page.site` still fails before retained ID validation can call login or AMC request work.
- Valid simple renames, category-qualified renames, malformed action-status diagnostics, explicit non-`ok` status diagnostics, and successful `_files` invalidation remain intact.
- Existing page-ID constructor, setter, getter, create/edit argument validation, collection retained-ID validation, edit-path retained-ID validation, commit-tags retained-ID validation, and set-parent retained-ID validation remain unchanged.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Callers with mutated or rehydrated malformed `Page._id` values now fail before rename work. Mitigation: constructor, setter, getter, direct create/edit, collection, edit-path, commit-tags, and set-parent validation already define those values as invalid page identity state.
- Risk: This could regress unloaded pages that need authentication before lazy page-ID lookup. Mitigation: `_id is None` is still not acquired until after `login_check()` succeeds; the preflight only validates present retained state.
- Risk: This could be mistaken for rename-target validation. Mitigation: Issue 352 remains the target fullname input boundary; this slice covers valid rename inputs with corrupted retained page identity.
- Risk: This could be mistaken for response/cache ordering. Mitigation: Issues 247 and 266 remain the action-status and file-cache boundaries; this slice only changes the pre-auth retained-ID boundary.

## Dependencies

- Existing `_validate_retained_page_id(...)` remains the canonical optional retained page-ID validator.
- Existing `Page.id` getter validation remains unchanged.
- Existing `Page.rename()` target validation, retained site validation, request shape, status diagnostics, local identity update timing, and `_files` invalidation remain unchanged for valid values.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, cache ownership boundaries, result ergonomics, or complexity candidates outside this now-covered direct rename retained-page-ID path.

## Upstream-Safe Motivation

`Page.rename()` is the direct low-level rename primitive and also mutates the calling page object's local identity. A present retained page ID should satisfy the same integer and non-negative contract as direct `Page.id`, `Page.edit(...)`, `Page.commit_tags()`, and `Page.set_parent()` before authentication or `renamePage` request work can happen. Validating present retained IDs locally keeps corrupted fixture or rehydrated state from becoming a rename identifier while preserving valid loaded IDs and authenticated lazy lookup for unloaded pages.

## Local Evidence

- Local rollout-backed work established page rename as a practical workflow through rename target validation, action-status diagnostics, local identity preservation on failure, and file-cache invalidation after success.
- Existing local drafts covered direct `Page.rename()` target validation, retained rename site validation, direct `Page.id` setter/getter validation, collection retained page-ID validation, page edit retained page-ID validation, commit-tags retained page-ID validation, and set-parent retained page-ID validation; they did not cover present malformed retained `_id` state used by `Page.rename()` before its entry login.
- The focused RED failure showed malformed and negative retained page-ID state could call `login_check()` before failing.
- This slice only validates present retained page IDs used by `Page.rename()` calls. It does not change rename target syntax, category/name splitting, action-status parsing, `_files` invalidation timing, page-ID acquisition URLs, page-ID parser behavior, source/edit behavior, metadata writes, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw page source text, rendered page content, private page content, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates present retained IDs without calling `Page.id` before login. That preserves the existing unauthenticated rename behavior for missing IDs while making corrupted non-`None` retained identity state fail deterministically at the `rename()` boundary.
