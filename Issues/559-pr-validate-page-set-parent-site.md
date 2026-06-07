# PR Draft: Validate Page Set Parent Site

## Summary

`Page.set_parent()` already normalizes and validates the requested parent fullname before request construction, and it already validates the returned metadata action status before updating local state. One adjacent action-time state boundary still trusted `page.site` after construction: if a caller, fixture, or rehydrated page object replaced `page.site` with a mock, dictionary-like object, or other non-`Site` value, `set_parent()` could reach login checks, AMC request construction, and returned-status diagnostics before reporting the parent-site problem.

This change revalidates `self.site` at the start of `Page.set_parent()` after parent-fullname normalization and before login or request work. Malformed action-time page sites now raise `ValueError("site must be a Site")` before login checks, `setParentPage` AMC requests, or response handling. Valid parent updates, parent clears, invalid parent-name rejection, logged-out behavior, and `setParentPage` action-status diagnostics remain unchanged.

## Outcome

`Page.set_parent()` now has an explicit action-time parent-site preflight consistent with the page constructor and the adjacent `Page.destroy()` and `Page.commit_tags()` action-time site guards.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who keep mutable `Page` objects in fixtures, generated ledgers, or cache-backed workflows where corrupted parent site state should fail before parent-change request work.

## Current Evidence

Existing drafts [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), [343-pr-validate-page-parent-fullname-fields.md](343-pr-validate-page-parent-fullname-fields.md), [246-pr-page-metadata-action-status-context.md](246-pr-page-metadata-action-status-context.md), [557-pr-validate-page-destroy-site.md](557-pr-validate-page-destroy-site.md), [558-pr-validate-page-commit-tags-site.md](558-pr-validate-page-commit-tags-site.md), [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md), and [501-pr-validate-site-member-site-field.md](501-pr-validate-site-member-site-field.md) establish page constructor site validation, parent-fullname validation, metadata action-status validation, adjacent page action-time site validation, and adjacent site-member/application action-time parent-site revalidation. This slice covers mutated `Page.site` at `Page.set_parent()` time, not direct `Page(site=...)` construction, malformed parent-fullname inputs, or metadata response shape.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.site` at the start of `Page.set_parent()` after parent-fullname normalization.
- Use the validated site for `login_check()`, `amc_request(...)`, and metadata action-status diagnostics.
- Add a regression for a mutated non-`Site` `page.site` that asserts no login check or AMC request occurs and local `parent_fullname` remains unchanged.
- Preserve valid parent updates, valid parent clears, invalid parent-name rejection, and `setParentPage` response diagnostics.

## Type Of Change

- Input validation
- Mutation action-boundary hardening
- Page parent-state hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.set_parent()` must reject a mutated non-`Site` `page.site` with `ValueError("site must be a Site")` before login checks, `setParentPage` AMC requests, or response handling. |
| R2 | Parent-fullname normalization and invalid parent-name validation must retain precedence over site validation. |
| R3 | Valid `Page.set_parent("parent-page")`, `Page.set_parent(None)`, and `Page.set_parent("")` behavior must remain stable. |
| R4 | Valid-site logged-out behavior and missing `setParentPage` action-status diagnostics must remain unchanged. |
| R5 | Focused set-parent tests, full page module tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A mutated non-`Site` parent fails before parent-change side-effect surfaces. | `TestPageWriteMethods.test_set_parent_rejects_malformed_site_before_login` failed RED by reaching mocked login/request/response handling and raising `WikidotStatusCodeException`, then passed GREEN with `ValueError("site must be a Site")`. | Calling `login_check()`, calling `amc_request(...)`, parsing mock response state, accepting dictionaries/mocks as sites, mutating local `parent_fullname`, or leaking a mock-derived status message rejects this local completion claim. | `Page.set_parent()` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Malformed parent-fullname input still fails before parent-site validation. | Existing `test_set_parent_rejects_non_string_parent_before_request` stayed green in the focused GREEN run, the full page module run, and the full unit suite. | Checking malformed sites first, accepting non-string parent values, or serializing malformed parent inputs rejects this local completion claim. | Parent-fullname validation | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Successful valid parent updates and clears remain stable. | `test_set_parent_success`, `test_set_parent_clear`, and `test_set_parent_empty_string_clears_local_parent` passed in the focused GREEN run, the full page module run, and the full unit suite. | Changing request shape, parent clear normalization, return value, or local parent update timing rejects this local completion claim. | Valid direct parent update | `tests/unit/test_page.py` |
| R4 | Existing valid-site error paths remain stable. | `test_set_parent_missing_action_status_does_not_update_local_state` passed in the focused GREEN run, the full page module run, and the full unit suite; existing valid-site login behavior stayed covered by the page module and full unit runs. | Returning a site validation error for a valid logged-out site, bypassing login checks, losing site/page/event/field diagnostics, updating local parent state on malformed response, or accepting malformed `setParentPage` responses rejects this local completion claim. | Login preflight and metadata action diagnostics | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Existing repository quality gates remain green. | Focused set-parent tests passed 6 tests, full page module tests passed 283 tests, full unit passed 2654 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regression uses a synthetic mutated site and mocked unit-level page state; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, or live account details. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `fa51d12 fix(page): validate set parent site`.

- RED action-time site validation: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_rejects_malformed_site_before_login -q` failed before the fix because mutated `page.site` reached mocked login/request/response handling and raised `WikidotStatusCodeException` instead of `ValueError("site must be a Site")`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_rejects_malformed_site_before_login tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_success tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_clear tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_empty_string_clears_local_parent tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_rejects_non_string_parent_before_request tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_missing_action_status_does_not_update_local_state -q` passed 6 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 283 tests.
- `uv run pytest tests/unit -q` passed 2654 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.set_parent()` rejects a mutated malformed `page.site` with `ValueError("site must be a Site")` before login checks, `setParentPage` AMC requests, or returned-status handling.
- Invalid parent-fullname input still fails before site validation and before request work.
- Valid `Page.set_parent()` parent updates, parent clears, and `setParentPage` action-status diagnostics remain intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This could be mistaken for parent-fullname validation. Mitigation: Issue 343 still covers malformed parent fullname state; this slice covers valid parent inputs with corrupted action-time parent site state.
- Risk: This could be mistaken for metadata action response validation. Mitigation: Issue 246 covers response shape/status; this slice rejects malformed parent site state before any `setParentPage` request or response handling.
- Risk: This could be overgeneralized to every page metadata method. Mitigation: the implementation is deliberately scoped to `Page.set_parent()`, the direct parent-change primitive with existing focused tests.

## Dependencies

- Existing `Page.__post_init__` validation remains responsible for direct constructor parent-site validation.
- Existing parent-fullname normalization remains responsible for input validation before site validation.
- Existing metadata action-status validation remains responsible for response shape/status handling after a valid-site request.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`Page.set_parent()` is the direct low-level parent-change primitive. Revalidating mutable parent site state immediately before login and request work gives generated callers, fixtures, and cached page workflows deterministic errors for corrupted parent state without changing parent normalization, valid login checks, `setParentPage` request shape, local update timing, or response diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed invalid mutated parent state reaching mocked login/request/response handling before validation.
- This slice only validates mutated `Page.site` before `Page.set_parent()`. It does not change page construction, lookup, create/edit behavior, metadata batching, tag saves, destroy, rename, voting, source/revision/file/vote acquisition, live site behavior, parent fullname validation, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private-message content, and live Wikidot account details out of upstream discussion.
