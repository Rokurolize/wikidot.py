# PR Draft: Validate Page Vote Site

## Summary

`Page.vote()` already validates vote values before request construction, validates the returned `ratePage` status, parses returned rating points with page/site context, updates local rating, and invalidates cached vote lists after success. One adjacent action-time state boundary still trusted `page.site` after construction: if a caller, fixture, or rehydrated page object replaced `page.site` with a mock, dictionary-like object, or other non-`Site` value, `vote()` could reach login checks, AMC request construction, and returned-status diagnostics before reporting the parent-site problem.

This change revalidates `self.site` at the start of `Page.vote()` after vote-value validation and before login or request work. Malformed action-time page sites now raise `ValueError("site must be a Site")` before login checks, `ratePage` AMC requests, response handling, local rating mutation, or vote-cache invalidation. Valid positive/negative votes, invalid vote-value rejection, logged-out behavior, rating response diagnostics, and successful vote-cache invalidation remain unchanged.

## Outcome

`Page.vote()` now has an explicit action-time parent-site preflight consistent with the page constructor and the adjacent `Page.destroy()`, `Page.commit_tags()`, `Page.set_parent()`, and `Page.rename()` action-time site guards.

## Current Evidence

Existing drafts [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [244-pr-page-rating-action-status-context.md](244-pr-page-rating-action-status-context.md), [245-pr-page-rating-points-context.md](245-pr-page-rating-points-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [557-pr-validate-page-destroy-site.md](557-pr-validate-page-destroy-site.md), [558-pr-validate-page-commit-tags-site.md](558-pr-validate-page-commit-tags-site.md), [559-pr-validate-page-set-parent-site.md](559-pr-validate-page-set-parent-site.md), and [560-pr-validate-page-rename-site.md](560-pr-validate-page-rename-site.md) establish page constructor site validation, vote-value validation, rating response validation, vote-cache invalidation, and adjacent page action-time site validation. This slice covers mutated `Page.site` at `Page.vote()` time, not direct `Page(site=...)` construction, malformed vote values, malformed rating responses, or cache invalidation after valid votes.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.site` at the start of `Page.vote()` after vote-value validation.
- Use the validated site for `login_check()`, `amc_request(...)`, rating action-status diagnostics, and rating points parsing.
- Add a regression for a mutated non-`Site` `page.site` that asserts no login check or AMC request occurs, local rating remains unchanged, and cached votes are not invalidated.
- Preserve valid positive/negative votes, invalid vote-value rejection, logged-out behavior, rating response diagnostics, and successful vote-cache invalidation.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.vote()` must reject a mutated non-`Site` `page.site` with `ValueError("site must be a Site")` before login checks, `ratePage` AMC requests, response handling, local rating mutation, or vote-cache invalidation. |
| R2 | Invalid vote-value validation must retain precedence over site validation. |
| R3 | Valid positive and negative votes must still return and store the parsed rating. |
| R4 | Valid-site logged-out behavior, missing status/points diagnostics, and successful vote-cache invalidation must remain unchanged. |
| R5 | Focused vote tests, full page module tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A mutated non-`Site` parent fails before vote side-effect surfaces. | `TestPageWriteMethods.test_vote_rejects_malformed_site_before_login` failed RED by reaching mocked login/request/response handling and raising `WikidotStatusCodeException`, then passed GREEN with `ValueError("site must be a Site")`. | Calling `login_check()`, calling `amc_request(...)`, parsing mock response state, accepting dictionaries/mocks as sites, mutating local `rating`, clearing `_votes`, or leaking a mock-derived status message rejects this local completion claim. | `Page.vote()` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Malformed vote values still fail before parent-site validation. | Existing `test_vote_invalid_value_raises` and `test_vote_rejects_non_integer_vote_values_before_request` stayed green in the focused GREEN run, the full page module run, and the full unit suite. | Checking malformed sites first, accepting invalid vote values, or serializing malformed vote inputs rejects this local completion claim. | Vote-value validation | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Successful valid votes remain stable. | `test_vote_positive` and `test_vote_negative` passed in the focused GREEN run, the full page module run, and the full unit suite. | Changing request shape, return value, rating parsing, or local rating update rejects this local completion claim. | Valid vote paths | `tests/unit/test_page.py` |
| R4 | Existing valid-site error and cache behavior remain stable. | `test_vote_not_logged_in`, `test_vote_missing_points_includes_site_page_event_and_field_context`, `test_vote_missing_action_status_does_not_update_local_state`, and `test_vote_success_invalidates_cached_votes` passed in the focused GREEN run, the full page module run, and the full unit suite. | Bypassing login checks for valid sites, losing site/page/event/field diagnostics, updating rating from malformed responses, clearing vote cache before valid success, or keeping stale vote caches after valid success rejects this local completion claim. | Login preflight, rating diagnostics, and cache consistency | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Existing repository quality gates remain green. | Focused vote tests passed 11 tests, full page module tests passed 285 tests, full unit passed 2656 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regression uses a synthetic mutated site and mocked unit-level page state; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, or live account details. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `587e5f8 fix(page): validate vote site`.

- RED action-time site validation: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_rejects_malformed_site_before_login -q` failed before the fix because mutated `page.site` reached mocked login/request/response handling and raised `WikidotStatusCodeException` instead of `ValueError("site must be a Site")`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_rejects_malformed_site_before_login tests/unit/test_page.py::TestPageWriteMethods::test_vote_positive tests/unit/test_page.py::TestPageWriteMethods::test_vote_success_invalidates_cached_votes tests/unit/test_page.py::TestPageWriteMethods::test_vote_negative tests/unit/test_page.py::TestPageWriteMethods::test_vote_missing_points_includes_site_page_event_and_field_context tests/unit/test_page.py::TestPageWriteMethods::test_vote_missing_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_vote_invalid_value_raises tests/unit/test_page.py::TestPageWriteMethods::test_vote_rejects_non_integer_vote_values_before_request tests/unit/test_page.py::TestPageWriteMethods::test_vote_not_logged_in -q` passed 11 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 285 tests.
- `uv run pytest tests/unit -q` passed 2656 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.vote()` rejects a mutated malformed `page.site` with `ValueError("site must be a Site")` before login checks, `ratePage` AMC requests, returned-status handling, local rating mutation, or vote-cache invalidation.
- Invalid vote values still fail before site validation and before request work.
- Valid positive/negative votes, valid logged-out behavior, rating response diagnostics, and valid vote-cache invalidation remain intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This could be mistaken for vote-value validation. Mitigation: Issue 353 still covers malformed vote values; this slice covers valid vote values with corrupted action-time parent site state.
- Risk: This could be mistaken for rating response validation. Mitigation: Issues 244 and 245 cover response shape/status/points; this slice rejects malformed parent site state before any `ratePage` request or response handling.
- Risk: This could be mistaken for vote-cache invalidation. Mitigation: Issue 261 covers successful vote cache behavior; this slice ensures malformed parent site state does not clear `_votes`.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`Page.vote()` is a write primitive that also mutates local rating state and invalidates cached vote lists. Revalidating mutable parent site state immediately before login and request work gives generated callers, fixtures, and cached page workflows deterministic errors for corrupted parent state without changing vote-value validation, valid login checks, `ratePage` request shape, local rating update timing, vote-cache invalidation after valid votes, or response diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed invalid mutated parent state reaching mocked login/request/response handling before validation.
- This slice only validates mutated `Page.site` before `Page.vote()`. It does not change page construction, lookup, create/edit behavior, metadata batching, tag saves, set-parent, rename, destroy, vote acquisition, source/revision/file acquisition, live site behavior, vote-value validation, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private-message content, and live Wikidot account details out of upstream discussion.
