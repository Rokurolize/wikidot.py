# PR: Validate site application action response counts

## Problem Statement

`SiteApplication.accept()` and `SiteApplication.decline()` share `_process(...)`, which sends one direct `ManageSiteMembershipAction` AMC request and then immediately indexes the first returned response. Before this change, a connector, mock, or adapter that returned zero responses leaked Python's raw `IndexError("list index out of range")` before wikidot.py could explain which site, applicant, and action broke the direct action batch contract.

This was a low-context failure at a membership-moderation mutation boundary. It also bypassed the existing action diagnostics that preserve member caches until the returned action status is confirmed.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free pending-application moderation as practical infrastructure for membership workflows, generated ledgers, local tests, migration checks, and moderation automation. Existing local slices hardened site applications around applicant user IDs, retained site/client state, application-list payloads, action payload shape, missing action status, action status type, explicit non-ok status mapping, and accept-side member-cache invalidation. They did not validate the direct `ManageSiteMembershipAction` response count before indexing the returned response sequence.

The local fix is committed as `0009de4`.

## Affected Workflows

- Browser-free pending application acceptance through `SiteApplication.accept()`.
- Browser-free pending application rejection through `SiteApplication.decline()`.
- Generated membership moderation scripts that wrap or mock `site.amc_request(...)`.
- Fixture-backed tests where a malformed adapter returns the wrong number of direct action responses.
- Debugging malformed connector behavior where response count, not payload shape, is the first broken contract.

## Proposed Fix

Add a small site application action response-count guard. Validate that the direct action response sequence has exactly one entry before indexing and parsing it. Raise `UnexpectedException` with site/applicant/event/type context and expected/actual counts on mismatch.

## Implementation Notes

The change adds `_require_site_application_action_response_count(...)` next to the existing site application action-status helper. `_process(...)` now stores the raw `site.amc_request(...)` result, validates the count, then parses `responses[0].json()` through the existing `_require_site_application_action_status(...)` helper.

The guard intentionally stays local to site application action handling instead of adding a generic `Site.amc_request(...)` response-count policy. Direct action callers already have domain-specific diagnostics, and a broad site-level guard could preempt more useful page/forum/member/application context.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_rejects_action_response_count_mismatch_before_parsing -q --tb=short
uv run pytest tests/unit/test_site_application.py::TestSiteApplicationProcess -q --tb=short
uv run pytest tests/unit/test_site_application.py -q --tb=short
uv run pytest tests/unit/test_site_member.py tests/unit/test_site.py tests/unit/test_user.py -q --tb=short
uv run pytest tests/unit -q --tb=short
uv run ruff check
uv run ruff format --check
uv run mypy src tests
uv run pyright src tests
git diff --check
```

The focused RED run failed before the fix because the new regression leaked raw `IndexError` from indexing the empty response list. The focused GREEN run passed after adding the count guard. Full unit verification passed 3966 tests, ruff and pyright were clean, mypy reported only existing untyped-function notes with no issues, and whitespace checks passed.

## Compatibility And Risk Notes

- Valid application accept/decline calls still send the same `ManageSiteMembershipAction` request body and parse action status before treating the mutation as successful.
- Existing applicant ID, retained site/client, malformed payload, missing action status, malformed status type, explicit non-ok status, and `no_application` mapping diagnostics remain unchanged.
- Mismatched response-count failures preserve the site members cache before accept-side invalidation can run.
- Decline still preserves the members cache on valid success.
- The diagnostic does not include raw generated module bodies, raw response JSON, credentials, cookies, auth JSON, local rollout paths, or account material.

## Rationale For Upstream Suitability

Direct site application actions rely on positional correspondence between the submitted action and returned response. When that correspondence is broken, wikidot.py should report the site application action response-count failure directly instead of leaking a raw Python indexing error.

## Scope

This slice does not change retry policy, direct `site.amc_request(...)` behavior, request construction, applicant validation, action status parsing, `no_application` mapping, cache invalidation on valid accept, live Wikidot behavior, or upstream filing state.
