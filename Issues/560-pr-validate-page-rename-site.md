# PR Draft: Validate Page Rename Site

## Summary

`Page.rename()` already validates the requested new fullname before request construction, validates the returned `renamePage` action status before local identity mutation, and invalidates cached file metadata after a successful rename. One adjacent action-time state boundary still trusted `page.site` after construction: if a caller, fixture, or rehydrated page object replaced `page.site` with a mock, dictionary-like object, or other non-`Site` value, `rename()` could reach login checks, AMC request construction, and returned-status diagnostics before reporting the parent-site problem.

This change revalidates `self.site` at the start of `Page.rename()` after new-fullname validation and before login or request work. Malformed action-time page sites now raise `ValueError("site must be a Site")` before login checks, `renamePage` AMC requests, response handling, local identity mutation, or file-cache invalidation. Valid simple renames, category-qualified renames, invalid rename-target rejection, missing-status diagnostics, and successful file-cache invalidation remain unchanged.

## Outcome

`Page.rename()` now has an explicit action-time parent-site preflight consistent with the page constructor and the adjacent `Page.destroy()`, `Page.commit_tags()`, and `Page.set_parent()` action-time site guards.

## Current Evidence

Existing drafts [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), [352-pr-validate-page-rename-fullname-input.md](352-pr-validate-page-rename-fullname-input.md), [247-pr-page-rename-action-status-context.md](247-pr-page-rename-action-status-context.md), [266-pr-page-rename-file-cache-invalidation.md](266-pr-page-rename-file-cache-invalidation.md), [557-pr-validate-page-destroy-site.md](557-pr-validate-page-destroy-site.md), [558-pr-validate-page-commit-tags-site.md](558-pr-validate-page-commit-tags-site.md), and [559-pr-validate-page-set-parent-site.md](559-pr-validate-page-set-parent-site.md) establish page constructor site validation, rename target validation, rename response validation, rename cache invalidation, and adjacent page action-time site validation. This slice covers mutated `Page.site` at `Page.rename()` time, not direct `Page(site=...)` construction, malformed rename targets, malformed rename responses, or cache invalidation after valid renames.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.site` at the start of `Page.rename()` after new-fullname validation.
- Use the validated site for `login_check()`, `amc_request(...)`, and action-status diagnostics.
- Add a regression for a mutated non-`Site` `page.site` that asserts no login check or AMC request occurs, local identity remains unchanged, and cached files are not invalidated.
- Preserve valid simple renames, category-qualified renames, invalid rename-target rejection, missing-status diagnostics, and successful file-cache invalidation.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.rename()` must reject a mutated non-`Site` `page.site` with `ValueError("site must be a Site")` before login checks, `renamePage` AMC requests, response handling, local identity mutation, or file-cache invalidation. |
| R2 | Invalid new-fullname validation must retain precedence over site validation. |
| R3 | Valid simple and category-qualified renames must still update local identity correctly. |
| R4 | Missing `renamePage` status diagnostics and successful file-cache invalidation must remain unchanged. |
| R5 | Focused rename tests, full page module tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A mutated non-`Site` parent fails before rename side-effect surfaces. | `TestPageWriteMethods.test_rename_rejects_malformed_site_before_login` failed RED by reaching mocked login/request/response handling and raising `WikidotStatusCodeException`, then passed GREEN with `ValueError("site must be a Site")`. | Calling `login_check()`, calling `amc_request(...)`, parsing mock response state, accepting dictionaries/mocks as sites, mutating local `fullname`/`category`/`name`, clearing `_files`, or leaking a mock-derived status message rejects this local completion claim. | `Page.rename()` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Malformed rename targets still fail before parent-site validation. | Existing `test_rename_rejects_non_string_fullname_before_request` stayed green in the focused GREEN run, the full page module run, and the full unit suite. | Checking malformed sites first, accepting non-string rename targets, or serializing malformed target names rejects this local completion claim. | Rename target validation | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Successful valid renames remain stable. | `test_rename_success` and `test_rename_with_category` passed in the focused GREEN run, the full page module run, and the full unit suite. | Changing request shape, return value, default category handling, or category/name splitting rejects this local completion claim. | Valid rename paths | `tests/unit/test_page.py` |
| R4 | Existing valid-site response and cache behavior remain stable. | `test_rename_missing_action_status_does_not_update_local_name` and `test_rename_success_invalidates_cached_files` passed in the focused GREEN run, the full page module run, and the full unit suite. | Updating local identity from malformed responses, losing site/page/event/field diagnostics, keeping stale file caches after valid rename, or clearing file caches before a valid response rejects this local completion claim. | Rename response and cache consistency | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Existing repository quality gates remain green. | Focused rename tests passed 6 tests, full page module tests passed 284 tests, full unit passed 2655 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regression uses a synthetic mutated site and mocked unit-level page state; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, or live account details. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `93b7f0a fix(page): validate rename site`.

- RED action-time site validation: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_rename_rejects_malformed_site_before_login -q` failed before the fix because mutated `page.site` reached mocked login/request/response handling and raised `WikidotStatusCodeException` instead of `ValueError("site must be a Site")`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_rename_rejects_malformed_site_before_login tests/unit/test_page.py::TestPageWriteMethods::test_rename_success tests/unit/test_page.py::TestPageWriteMethods::test_rename_with_category tests/unit/test_page.py::TestPageWriteMethods::test_rename_success_invalidates_cached_files tests/unit/test_page.py::TestPageWriteMethods::test_rename_missing_action_status_does_not_update_local_name tests/unit/test_page.py::TestPageWriteMethods::test_rename_rejects_non_string_fullname_before_request -q` passed 6 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 284 tests.
- `uv run pytest tests/unit -q` passed 2655 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.rename()` rejects a mutated malformed `page.site` with `ValueError("site must be a Site")` before login checks, `renamePage` AMC requests, returned-status handling, local identity mutation, or file-cache invalidation.
- Invalid rename-target input still fails before site validation and before request work.
- Valid simple renames, category-qualified renames, malformed-response diagnostics, and valid rename file-cache invalidation remain intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This could be mistaken for rename target validation. Mitigation: Issue 352 still covers malformed `new_fullname`; this slice covers valid rename targets with corrupted action-time parent site state.
- Risk: This could be mistaken for rename response validation. Mitigation: Issue 247 covers response shape/status; this slice rejects malformed parent site state before any `renamePage` request or response handling.
- Risk: This could be mistaken for rename cache invalidation. Mitigation: Issue 266 covers successful rename cache behavior; this slice ensures malformed parent site state does not clear `_files`.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`Page.rename()` is a write primitive that also mutates local page identity. Revalidating mutable parent site state immediately before login and request work gives generated callers, fixtures, and cached page workflows deterministic errors for corrupted parent state without changing rename target validation, valid login checks, `renamePage` request shape, local identity update timing, file-cache invalidation after valid renames, or response diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed invalid mutated parent state reaching mocked login/request/response handling before validation.
- This slice only validates mutated `Page.site` before `Page.rename()`. It does not change page construction, lookup, create/edit behavior, metadata batching, tag saves, set-parent, destroy, voting, source/revision/file/vote acquisition, live site behavior, rename target validation, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private-message content, and live Wikidot account details out of upstream discussion.
