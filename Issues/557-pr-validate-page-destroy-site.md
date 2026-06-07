# PR Draft: Validate Page Destroy Site

## Summary

`Page(site=...)` already validates constructor parent sites, and several page write methods already validate their own direct inputs before login checks or request work. One destructive action boundary still trusted mutable public state after construction: if `page.site` was replaced with a mock, dictionary-like object, or other non-`Site` value, `Page.destroy()` could reach login checks, AMC request construction, returned-status diagnostics, or successful cache clearing before reporting the parent-site problem.

This change revalidates `self.site` at the start of `Page.destroy()`, then uses the validated `Site` for login, delete-page AMC work, and action-status diagnostics. Malformed action-time page sites now raise `ValueError("site must be a Site")` before login checks, delete requests, response parsing, or page-bound cache clearing. Valid page deletion, logged-out behavior, delete action-status diagnostics, and successful cache invalidation remain unchanged.

## Outcome

`Page.destroy()` now has the same explicit parent-site preflight at action time that the page constructor applies at initialization.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who keep mutable `Page` objects in caches, generated fixtures, or test harnesses where a malformed parent site should fail before destructive request work.

## Current Evidence

Existing drafts [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), [248-pr-page-delete-action-status-context.md](248-pr-page-delete-action-status-context.md), [267-pr-page-destroy-cache-invalidation.md](267-pr-page-destroy-cache-invalidation.md), [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md), and [501-pr-validate-site-member-site-field.md](501-pr-validate-site-member-site-field.md) establish page constructor site validation, delete response validation, delete cache invalidation, and adjacent action-time parent-site revalidation. This slice covers mutated `Page.site` at `Page.destroy()` time, not direct `Page(site=...)` construction, delete action response shape, or every page write method.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.site` at the start of `Page.destroy()`.
- Use the validated site for `login_check()`, `amc_request(...)`, and delete action-status diagnostics.
- Add a regression for a mutated non-`Site` `page.site` that asserts no login check, no AMC request, and no cache clearing occurs.
- Preserve valid deletion, logged-out behavior for valid sites, delete action-status diagnostics, and successful delete cache invalidation.

## Type Of Change

- Input validation
- Destructive action-boundary hardening
- Page parent-state hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.destroy()` must reject a mutated non-`Site` `page.site` with `ValueError("site must be a Site")` before login checks, delete AMC requests, response handling, or cache clearing. |
| R2 | Valid `Page.destroy()` success must still submit the same delete request and clear page-bound caches after a confirmed ok action response. |
| R3 | Valid-site logged-out behavior must still raise `LoginRequiredException`. |
| R4 | Missing or non-ok delete action-status diagnostics must remain unchanged for valid sites. |
| R5 | Focused delete tests, full page module tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A mutated non-`Site` parent fails before any destructive side-effect surface. | `TestPageWriteMethods.test_destroy_rejects_malformed_site_before_login_or_cache_clear` failed RED by reaching mocked login/request/response handling and raising `WikidotStatusCodeException`, then passed GREEN with `ValueError("site must be a Site")`. | Calling `login_check()`, calling `amc_request(...)`, parsing mock response state, clearing `_source`, `_revisions`, `_votes`, `_metas`, `_discussion`, `_discussion_checked`, or `_files`, or leaking a mock-derived status message rejects this local completion claim. | `Page.destroy()` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Successful valid deletion remains stable. | `test_destroy_success` and `test_destroy_success_clears_page_bound_caches` passed in the focused GREEN run, the full page module run, and the full unit suite. | Changing request shape, skipping action-status validation, or failing to clear page-bound caches after a confirmed delete rejects this local completion claim. | Valid page deletion | `tests/unit/test_page.py` |
| R3 | Valid-site logged-out behavior remains stable. | `test_destroy_not_logged_in` passed in the focused GREEN run, the full page module run, and the full unit suite. | Returning a site validation error for a valid logged-out site, bypassing login checks, or issuing delete request work while logged out rejects this local completion claim. | Login preflight for valid sites | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Existing delete action response diagnostics remain stable. | `test_destroy_missing_action_status_includes_site_page_event_and_field_context` passed in the focused GREEN run, the full page module run, and the full unit suite. | Losing site/page/event/field context or accepting malformed delete responses rejects this local completion claim. | Delete action-status validation | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Existing repository quality gates remain green. | Focused delete tests passed 5 tests, full page module tests passed 281 tests, full unit passed 2652 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regression uses a synthetic mutated site and mocked unit-level caches; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, or live account details. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `1e5112e fix(page): validate destroy site`.

- RED action-time site validation: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_destroy_rejects_malformed_site_before_login_or_cache_clear -q` failed before the fix because mutated `page.site` reached mocked login/request/response handling and raised `WikidotStatusCodeException` instead of `ValueError("site must be a Site")`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_destroy_rejects_malformed_site_before_login_or_cache_clear tests/unit/test_page.py::TestPageWriteMethods::test_destroy_success tests/unit/test_page.py::TestPageWriteMethods::test_destroy_success_clears_page_bound_caches tests/unit/test_page.py::TestPageWriteMethods::test_destroy_not_logged_in tests/unit/test_page.py::TestPageWriteMethods::test_destroy_missing_action_status_includes_site_page_event_and_field_context -q` passed 5 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 281 tests.
- `uv run pytest tests/unit -q` passed 2652 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.destroy()` rejects a mutated malformed `page.site` with `ValueError("site must be a Site")` before login checks, delete AMC requests, returned-status handling, or page-bound cache clearing.
- Valid delete success still clears `_source`, `_revisions`, `_votes`, `_metas`, `_discussion`, `_discussion_checked`, and `_files` only after a confirmed ok action response.
- Valid logged-out sites still raise `LoginRequiredException`.
- Delete action-status diagnostics remain intact for valid sites.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This could be mistaken for constructor validation. Mitigation: Issue 486 still covers `Page(site=...)`; this slice covers post-construction mutation immediately before destructive action work.
- Risk: This could be mistaken for delete action-response validation. Mitigation: Issue 248 still covers delete response shape/status; this slice rejects malformed parent site state before any delete request or response handling.
- Risk: This could be overgeneralized to every page write method. Mitigation: the implementation is deliberately scoped to `Page.destroy()`, the destructive path with cache invalidation and existing page-delete tests.

## Dependencies

- Existing `Page.__post_init__` validation remains responsible for direct constructor parent-site validation.
- Existing delete action-status validation remains responsible for response shape/status handling after a valid-site request.
- Existing delete cache invalidation remains responsible for clearing page-bound caches only after confirmed delete success.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`Page.destroy()` is a destructive public action. Revalidating mutable parent site state immediately before login and request work gives generated callers, fixtures, and cached page workflows deterministic errors for malformed state without changing valid delete requests, login checks, action-status diagnostics, or successful cache invalidation.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed invalid mutated parent state reaching mocked login/request/response handling before validation.
- This slice only validates mutated `Page.site` before `Page.destroy()`. It does not change page construction, lookup, create/edit behavior, delete response parsing, metadata writes, tag writes, parent changes, voting, source/revision/file/vote acquisition, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private-message content, and live Wikidot account details out of upstream discussion.
