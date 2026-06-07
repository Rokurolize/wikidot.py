# PR Draft: Validate Page Commit Tags Site

## Summary

`Page.commit_tags()` already validates the current mutable `Page.tags` state before serializing the `saveTags` payload, and it already validates the returned metadata action status before accepting success. One adjacent action-time state boundary still trusted `page.site` after construction: if a caller, fixture, or rehydrated page object replaced `page.site` with a mock, dictionary-like object, or other non-`Site` value, `commit_tags()` could reach login checks, AMC request construction, and returned-status diagnostics before reporting the parent-site problem.

This change revalidates `self.site` at the start of `Page.commit_tags()` after tag-state validation and before login or request work. Malformed action-time page sites now raise `ValueError("site must be a Site")` before login checks, `saveTags` AMC requests, or response handling. Valid tag saves, logged-out behavior, current-tag validation, and `saveTags` action-status diagnostics remain unchanged.

## Outcome

`Page.commit_tags()` now has an explicit action-time parent-site preflight consistent with the page constructor and the adjacent `Page.destroy()` action-time site guard.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who keep mutable `Page` objects in fixtures, generated ledgers, or cache-backed workflows where corrupted parent site state should fail before tag-save request work.

## Current Evidence

Existing drafts [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), [532-pr-validate-commit-tags-state.md](532-pr-validate-commit-tags-state.md), [246-pr-page-metadata-action-status-context.md](246-pr-page-metadata-action-status-context.md), [557-pr-validate-page-destroy-site.md](557-pr-validate-page-destroy-site.md), [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md), and [501-pr-validate-site-member-site-field.md](501-pr-validate-site-member-site-field.md) establish page constructor site validation, tag-state validation, metadata action-status validation, adjacent page action-time site validation, and adjacent site-member/application action-time parent-site revalidation. This slice covers mutated `Page.site` at `Page.commit_tags()` time, not direct `Page(site=...)` construction, malformed current tags, or metadata response shape.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.site` at the start of `Page.commit_tags()` after current tag-state validation.
- Use the validated site for `login_check()`, `amc_request(...)`, and metadata action-status diagnostics.
- Add a regression for a mutated non-`Site` `page.site` that asserts no login check or AMC request occurs.
- Preserve valid tag saves, logged-out behavior for valid sites, current tag-state validation, and `saveTags` response diagnostics.

## Type Of Change

- Input validation
- Mutation action-boundary hardening
- Page parent-state hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.commit_tags()` must reject a mutated non-`Site` `page.site` with `ValueError("site must be a Site")` before login checks, `saveTags` AMC requests, or response handling. |
| R2 | Current `Page.tags` validation must retain precedence over site validation. |
| R3 | Valid `Page.commit_tags()` success must still submit the same `saveTags` request and return the calling page. |
| R4 | Valid-site logged-out behavior and missing `saveTags` action-status diagnostics must remain unchanged. |
| R5 | Focused commit-tags tests, full page module tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A mutated non-`Site` parent fails before tag-save side-effect surfaces. | `TestPageWriteMethods.test_commit_tags_rejects_malformed_site_before_login` failed RED by reaching mocked login/request/response handling and raising `WikidotStatusCodeException`, then passed GREEN with `ValueError("site must be a Site")`. | Calling `login_check()`, calling `amc_request(...)`, parsing mock response state, accepting dictionaries/mocks as sites, or leaking a mock-derived status message rejects this local completion claim. | `Page.commit_tags()` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Malformed current tags still fail before parent-site validation. | Existing `test_commit_tags_rejects_invalid_tags_before_request` stayed green in the focused GREEN run, the full page module run, and the full unit suite. | Checking malformed sites first, accepting non-list tags, accepting non-string tag entries, or serializing malformed current tags rejects this local completion claim. | Current tag-state validation | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Successful valid tag saves remain stable. | `test_commit_tags_success` passed in the focused GREEN run, the full page module run, and the full unit suite. | Changing request shape, tag serialization, return value, or status validation rejects this local completion claim. | Valid direct tag save | `tests/unit/test_page.py` |
| R4 | Existing valid-site error paths remain stable. | `test_commit_tags_not_logged_in` and `test_commit_tags_missing_action_status_includes_site_page_event_and_field_context` passed in the focused GREEN run, the full page module run, and the full unit suite. | Returning a site validation error for a valid logged-out site, bypassing login checks, losing site/page/event/field diagnostics, or accepting malformed `saveTags` responses rejects this local completion claim. | Login preflight and metadata action diagnostics | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Existing repository quality gates remain green. | Focused commit-tags tests passed 8 tests, full page module tests passed 282 tests, full unit passed 2653 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regression uses a synthetic mutated site and mocked unit-level page state; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, or live account details. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `7e87a5a fix(page): validate commit tags site`.

- RED action-time site validation: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_rejects_malformed_site_before_login -q` failed before the fix because mutated `page.site` reached mocked login/request/response handling and raised `WikidotStatusCodeException` instead of `ValueError("site must be a Site")`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_rejects_malformed_site_before_login tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_success tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_not_logged_in tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_rejects_invalid_tags_before_request tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_missing_action_status_includes_site_page_event_and_field_context -q` passed 8 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 282 tests.
- `uv run pytest tests/unit -q` passed 2653 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.commit_tags()` rejects a mutated malformed `page.site` with `ValueError("site must be a Site")` before login checks, `saveTags` AMC requests, or returned-status handling.
- Current malformed tag state still fails before site validation and before request work.
- Valid `Page.commit_tags()` behavior, valid logged-out behavior, and `saveTags` action-status diagnostics remain intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This could be mistaken for current tag-state validation. Mitigation: Issue 532 still covers malformed `Page.tags`; this slice covers valid tags with corrupted action-time parent site state.
- Risk: This could be mistaken for metadata action response validation. Mitigation: Issue 246 covers response shape/status; this slice rejects malformed parent site state before any `saveTags` request or response handling.
- Risk: This could be overgeneralized to every page metadata method. Mitigation: the implementation is deliberately scoped to `Page.commit_tags()`, the direct tag-save primitive with existing focused tests.

## Dependencies

- Existing `Page.__post_init__` validation remains responsible for direct constructor parent-site validation.
- Existing current tag-state validation remains responsible for tag container and tag entry checks before site validation.
- Existing metadata action-status validation remains responsible for response shape/status handling after a valid-site request.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`Page.commit_tags()` is the direct low-level tag-save primitive. Revalidating mutable parent site state immediately before login and request work gives generated callers, fixtures, and cached page workflows deterministic errors for corrupted parent state without changing tag serialization, valid login checks, `saveTags` request shape, or response diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed invalid mutated parent state reaching mocked login/request/response handling before validation.
- This slice only validates mutated `Page.site` before `Page.commit_tags()`. It does not change page construction, lookup, create/edit behavior, metadata batching, parent changes, rename, voting, source/revision/file/vote acquisition, live site behavior, current tag validation, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private-message content, and live Wikidot account details out of upstream discussion.
