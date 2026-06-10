# PR Draft: Validate Page Edit Retained Page ID

## Summary

`Page.edit(...)` already validates explicit edit inputs, retained `page.site`, retained `page.fullname`, and omitted-title retained `page.title` before save delegation. One retained identity field still crossed the edit authentication boundary late: if a valid `Page` was later mutated, fixture-loaded, or rehydrated with a malformed or negative cached `_id`, `Page.edit(title="...", source="...")` called `login_check()` before the public `Page.id` getter diagnosed the corrupted retained ID.

This change validates a present retained `_id` with `_validate_retained_page_id(self)` after retained site/fullname validation and before `login_check()`, current-source reads, `Page.create_or_edit(...)` delegation, local title/source mutation, revision-count sync, or revision-cache invalidation. Missing `_id is None` still preserves the existing login-before-lazy-ID-lookup behavior.

## Outcome

Page edits can no longer authenticate or delegate write work through corrupted retained page-ID state. Valid loaded page IDs still pass through, and unloaded pages still acquire IDs only after the entry login succeeds.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page editing, generated fixtures, migration ledgers, publication tooling, local tests, or serialized and rehydrated `Page` records before calling `Page.edit(...)`.

## Current Evidence

Local rollout-backed drafts repeatedly identify page editing and page identity state as practical workflow surfaces. Existing drafts [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), [489-pr-validate-page-constructor-id-field.md](489-pr-validate-page-constructor-id-field.md), [639-pr-validate-non-negative-page-ids.md](639-pr-validate-non-negative-page-ids.md), [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md), [664-pr-validate-page-collection-retained-page-id-state.md](664-pr-validate-page-collection-retained-page-id-state.md), [785-pr-validate-page-edit-retained-title.md](785-pr-validate-page-edit-retained-title.md), and [786-pr-validate-page-edit-retained-fullname.md](786-pr-validate-page-edit-retained-fullname.md) establish direct write-argument page-ID validation, setter/constructor/getter page-ID validation, collection retained-ID validation, edit-time retained title validation, and edit-time retained fullname validation.

This slice is not a duplicate of those drafts. Issue 412 validates direct `Page.create_or_edit(page_id=...)` arguments before that helper's own login. Issues 413, 489, 639, and 658 validate direct assignment, construction, non-negative range, and public getter behavior for `Page.id`, but `Page.edit(...)` had its own earlier login boundary before reaching the getter. Issue 664 validates retained IDs during collection acquisition, not write delegation. Issues 785 and 786 cover retained edit title and fullname, not retained page IDs.

The focused RED test demonstrated the gap: malformed retained `_id` values `True`, `False`, `"12345"`, `12345.0`, and `[]`, plus negative `_id=-1`, all raised only after `login_check()` had already been called, causing `login_check.assert_not_called()` to fail.

## Related Issue / Non-Duplicate Analysis

Builds directly on [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), [489-pr-validate-page-constructor-id-field.md](489-pr-validate-page-constructor-id-field.md), [639-pr-validate-non-negative-page-ids.md](639-pr-validate-non-negative-page-ids.md), [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md), [785-pr-validate-page-edit-retained-title.md](785-pr-validate-page-edit-retained-title.md), and [786-pr-validate-page-edit-retained-fullname.md](786-pr-validate-page-edit-retained-fullname.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate present retained `self._id` at the start of `Page.edit(...)` with `_validate_retained_page_id(self)`.
- Run the retained-ID validation before `login_check()`.
- Preserve missing-ID behavior by calling `self.id` after login only when retained `_id is None`.
- Pass the validated or lazily acquired local `page_id` value into `Page.create_or_edit(...)`.
- Add focused regressions for malformed and negative retained page IDs that previously reached login before failing.

## Type Of Change

- State validation
- Page edit-path hardening
- Retained identity integrity
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.edit(title=..., source=...)` must reject retained malformed `_id` values such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("page.id must be an integer")`. |
| R2 | `Page.edit(title=..., source=...)` must reject retained negative `_id=-1` with `ValueError("page.id must be non-negative")`. |
| R3 | The retained-ID rejection must happen before `login_check()`, current-source reads, `Page.create_or_edit(...)`, local title/source mutation, revision-count sync, or revision-cache invalidation. |
| R4 | Missing `_id is None` must preserve the existing login-before-lazy-ID-lookup behavior. |
| R5 | Constructor-time `_id`, direct `Page.id` setter/getter, direct `Page.create_or_edit(page_id=...)`, retained site/title/fullname validation, and valid edit behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, edit coverage, adjacent page/source/site coverage, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Edit rejects malformed retained page IDs before authentication. | `TestPageEdit.test_edit_rejects_malformed_retained_page_ids_before_login_or_delegation` failed RED for five malformed values because `login_check()` had already been called, then passed GREEN after retained-ID validation moved before login. | Accepting booleans/floats, coercing values, authenticating, delegating to `Page.create_or_edit(...)`, or delaying diagnosis to the public getter rejects this local completion claim. | `Page.edit(...)` retained page-ID preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Edit rejects negative retained page IDs before authentication. | `TestPageEdit.test_edit_rejects_negative_retained_page_id_before_login_or_delegation` failed RED because `login_check()` had already been called, then passed GREEN with the non-negative diagnostic before login. | Treating a negative retained ID as a request ID, authenticating before the local state error, or changing the diagnostic rejects this local completion claim. | `Page.edit(...)` retained page-ID preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Validation is side-effect free. | The regressions assert `login_check` and `Page.create_or_edit(...)` are not called, and that retained `_id`, title, `revisions_count`, `_source`, and `_revisions` remain unchanged. | Authenticating, delegating, fetching current source, mutating title/source/revision state, or clearing caches rejects this local completion claim. | Page edit preflight | focused tests |
| R4 | Missing IDs still defer lookup until after login. | The implementation stores `page_id = _validate_retained_page_id(self)` and only calls `self.id` after login when `page_id is None`; existing edit/login/source tests remain green. | Calling `PageCollection.get_page_ids()` before login for `_id is None` would regress Issue 189's unauthenticated edit guard. | Page edit missing-ID flow | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Existing adjacent validation boundaries remain stable. | `TestPageEdit` passed 21 tests, including retained site/title/fullname and explicit input validation coverage. | Regressing constructor ID validation, setter/getter diagnostics, direct create/edit page-ID validation, retained site/title/fullname validation, or valid edit behavior rejects this local completion claim. | Public edit inputs and retained state | `tests/unit/test_page.py` |
| R6 | The local proof stays unit-level and private-data-free. | All regressions use synthetic local fixtures and mocks. | Using live Wikidot, credentials, cookies, auth JSON, raw private page source, raw rollout paths, private site names, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `5d903b7 fix(page): validate retained edit page id`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageEdit::test_edit_rejects_malformed_retained_page_ids_before_login_or_delegation tests/unit/test_page.py::TestPageEdit::test_edit_rejects_negative_retained_page_id_before_login_or_delegation -q --tb=short` failed six retained page-ID cases before the fix because `login_check.assert_not_called()` observed one login call.
- GREEN focused: the same focused command passed 6 tests after the fix.
- Edit coverage: `uv run pytest tests/unit/test_page.py::TestPageEdit -q` passed 21 tests after formatting.
- Adjacent page coverage: `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1388 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3814 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted after formatting the edited test file.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Page.edit(title=..., source=...)` raises `ValueError("page.id must be an integer")` when retained `_id` is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- The same method raises `ValueError("page.id must be non-negative")` when retained `_id` is `-1`.
- The retained-ID failure occurs before login checks, current-source reads, `Page.create_or_edit(...)`, local title/source mutation, revision-count sync, or revision-cache invalidation.
- Failed retained-ID preflight does not coerce or rewrite the corrupted retained `_id`.
- `_id is None` still follows the existing authenticated lazy lookup path.
- Explicit invalid `title`, `comment`, `source`, and `force_edit` inputs still raise the same diagnostics before request work.
- Malformed retained `page.site`, retained `page.fullname`, and omitted-title retained `page.title` still fail at their existing boundaries.
- Existing edit lock/save behavior, local source sync, revision-cache invalidation, page source/revision/file/vote workflows, and site workflows remain green.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Callers with mutated or rehydrated malformed `Page._id` values now fail before edit work. Mitigation: constructor, setter, getter, and direct create/edit validation already define those values as invalid page identity state.
- Risk: This could regress unauthenticated edits that need to fail before page-ID lookup. Mitigation: `_id is None` is still not acquired until after `login_check()` succeeds; the preflight only validates present retained state.
- Risk: This could be mistaken for direct `Page.create_or_edit(page_id=...)` validation. Mitigation: Issue 412 remains the direct argument boundary; this slice covers `Page.edit(...)` performing an earlier login before reaching `self.id`.

## Dependencies

- Existing `_validate_retained_page_id(...)` remains the canonical optional retained page-ID validator.
- Existing `Page.id` getter validation remains unchanged.
- Existing direct `Page.create_or_edit(page_id=...)` validation remains unchanged.
- Existing `Page.edit(...)` source defaulting, `Page.create_or_edit(...)` delegation, local state sync, revision-count handling, revision-cache invalidation, and source-cache update behavior remains unchanged for valid values.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, cache ownership boundaries, result ergonomics, or complexity candidates outside this now-covered edit retained-page-ID path.

## Upstream-Safe Motivation

`Page.edit(...)` uses the page object's retained ID to edit an existing page after authentication. A present retained ID should satisfy the same integer and non-negative contract as direct `Page.id` and `Page.create_or_edit(page_id=...)` before authentication, current-source reads, save delegation, or local cache mutation can happen. Validating present retained IDs locally keeps corrupted fixture or rehydrated state from becoming an edit identifier while preserving valid loaded IDs and authenticated lazy lookup for unloaded pages.

## Local Evidence

- Local rollout-backed work established page editing as a practical workflow through login/source ordering, local title/source cache sync, revision-cache invalidation, page source input validation, explicit page title/comment validation, constructor/setter/getter page-ID validation, direct create/edit page-ID validation, retained edit-site validation, retained edit-title validation, and retained edit-fullname validation.
- Existing local drafts covered direct `Page.create_or_edit(page_id=...)` input validation, constructor/setter/getter page-ID validation, retained collection page-ID validation, retained edit parent site validation, retained edit title validation, retained edit fullname validation, source defaulting, edit-lock/save behavior, and cache invalidation; they did not cover present malformed retained `_id` state used by `Page.edit(...)` before its entry login.
- The focused RED failure showed malformed and negative retained page-ID state could call `login_check()` before failing.
- This slice only validates present retained page IDs used by `Page.edit(...)` calls. It does not change parser field extraction, page-ID acquisition URLs, batch grouping, source text contents, source acquisition internals, edit-lock handling, save response handling, metadata writes, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw page source text, rendered page content, private page content, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates present retained IDs without calling `Page.id` before login. That preserves the existing unauthenticated edit behavior for missing IDs while making corrupted non-`None` retained identity state fail deterministically at the edit boundary.
