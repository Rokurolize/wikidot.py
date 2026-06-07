# PR Draft: Validate Page Cancel Vote Site

## Summary

`Page.cancel_vote()` already validates the returned `cancelVote` status, parses returned rating points with page/site context, updates local rating, and invalidates cached vote lists after success. One adjacent action-time state boundary still trusted `page.site` after construction: if a caller, fixture, or rehydrated page object replaced `page.site` with a mock, dictionary-like object, or other non-`Site` value, `cancel_vote()` could reach login checks, AMC request construction, and returned-status diagnostics before reporting the parent-site problem.

This change revalidates `self.site` at the start of `Page.cancel_vote()` before login or request work. Malformed action-time page sites now raise `ValueError("site must be a Site")` before login checks, `cancelVote` AMC requests, response handling, local rating mutation, or vote-cache invalidation. Valid vote cancellation, logged-out behavior, rating response diagnostics, and successful vote-cache invalidation remain unchanged.

## Outcome

`Page.cancel_vote()` now has an explicit action-time parent-site preflight consistent with the page constructor and the adjacent `Page.vote()` action-time site guard.

## Current Evidence

Existing drafts [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), [244-pr-page-rating-points-context.md](244-pr-page-rating-points-context.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), and [561-pr-validate-page-vote-site.md](561-pr-validate-page-vote-site.md) establish page constructor site validation, cancel-vote response validation, vote-cache invalidation, and adjacent vote action-time site validation. This slice covers mutated `Page.site` at `Page.cancel_vote()` time, not direct `Page(site=...)` construction, malformed rating responses, or cache invalidation after valid vote cancellation.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.site` at the start of `Page.cancel_vote()`.
- Use the validated site for `login_check()`, `amc_request(...)`, rating action-status diagnostics, and rating points parsing.
- Add a regression for a mutated non-`Site` `page.site` that asserts no login check or AMC request occurs, local rating remains unchanged, and cached votes are not invalidated.
- Preserve valid vote cancellation, logged-out behavior, rating response diagnostics, and successful vote-cache invalidation.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.cancel_vote()` must reject a mutated non-`Site` `page.site` with `ValueError("site must be a Site")` before login checks, `cancelVote` AMC requests, response handling, local rating mutation, or vote-cache invalidation. |
| R2 | Valid vote cancellation must still return and store the parsed rating. |
| R3 | Valid-site logged-out behavior, malformed points diagnostics, non-`ok` status diagnostics, and successful vote-cache invalidation must remain unchanged. |
| R4 | Focused cancel-vote tests, full page module tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A mutated non-`Site` parent fails before cancel-vote side-effect surfaces. | `TestPageWriteMethods.test_cancel_vote_rejects_malformed_site_before_login` failed RED by reaching mocked login/request/response handling and raising `WikidotStatusCodeException`, then passed GREEN with `ValueError("site must be a Site")`. | Calling `login_check()`, calling `amc_request(...)`, parsing mock response state, accepting dictionaries/mocks as sites, mutating local `rating`, clearing `_votes`, or leaking a mock-derived status message rejects this local completion claim. | `Page.cancel_vote()` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Successful valid cancel-vote remains stable. | `test_cancel_vote_success` passed in the focused GREEN run, the full page module run, and the full unit suite. | Changing request shape, return value, rating parsing, or local rating update rejects this local completion claim. | Valid cancel-vote path | `tests/unit/test_page.py` |
| R3 | Existing valid-site error and cache behavior remain stable. | `test_cancel_vote_success_invalidates_cached_votes`, `test_cancel_vote_malformed_points_includes_site_page_event_field_and_value_context`, and `test_cancel_vote_non_ok_action_status_does_not_update_local_state` passed in the focused GREEN run, the full page module run, and the full unit suite. | Losing site/page/event/field diagnostics, updating rating from malformed responses, clearing vote cache before valid success, or keeping stale vote caches after valid success rejects this local completion claim. | Rating diagnostics and cache consistency | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Existing repository quality gates remain green. | Focused cancel-vote tests passed 5 tests, full page module tests passed 286 tests, full unit passed 2657 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live auth material or private state is needed to prove the behavior. | The regression uses a synthetic mutated site and mocked unit-level page state; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, or live account details. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `27a250a fix(page): validate cancel vote site`.

- RED action-time site validation: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_rejects_malformed_site_before_login -q` failed before the fix because mutated `page.site` reached mocked login/request/response handling and raised `WikidotStatusCodeException` instead of `ValueError("site must be a Site")`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_rejects_malformed_site_before_login tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_success tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_success_invalidates_cached_votes tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_malformed_points_includes_site_page_event_field_and_value_context tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_non_ok_action_status_does_not_update_local_state -q` passed 5 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 286 tests.
- `uv run pytest tests/unit -q` passed 2657 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.cancel_vote()` rejects a mutated malformed `page.site` with `ValueError("site must be a Site")` before login checks, `cancelVote` AMC requests, returned-status handling, local rating mutation, or vote-cache invalidation.
- Valid vote cancellation, rating response diagnostics, and valid vote-cache invalidation remain intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed invalid mutated parent state reaching mocked login/request/response handling before validation.
- This slice only validates mutated `Page.site` before `Page.cancel_vote()`. It does not change page construction, lookup, create/edit behavior, metadata batching, tag saves, set-parent, rename, destroy, voting, vote acquisition, source/revision/file acquisition, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private-message content, and live Wikidot account details out of upstream discussion.
