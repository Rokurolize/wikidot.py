# PR Draft: Validate Site Application List Response Payload

## Summary

`SiteApplication.acquire_all(site)` now validates that decoded `ManageSiteMembersApplicationsModule` list responses are dictionaries before reading `body`. Non-mapping payloads such as `["not", "a", "mapping"]` raise contextual `NoElementException` with site, expected type, and actual type context instead of leaking raw `AttributeError` from `.get("body")`.

The change is intentionally narrow: valid application-list parsing, forbidden-page detection, empty-list handling, missing `body` diagnostics, present non-string `body` diagnostics, application parser structure checks, user parsing, and accept/decline action handling remain unchanged.

## Problem Statement

`SiteApplication.acquire_all(site)`, also exposed through `site.applications`, fetches pending join applications from `managesite/ManageSiteMembersApplicationsModule`, decodes the AMC response, extracts `body`, checks forbidden markup, and parses generated application HTML. Earlier local slices covered retry-aware list fetches, successful body reuse, nested body markup filtering, text spacing, malformed application structure context, missing response `body`, present non-string response `body`, applicant user parsing, direct site validation, and accept/decline action response shape. One adjacent response-boundary gap remained: if `response.json()` returned a non-dictionary payload, `_application_list_response_body(...)` attempted `.get("body")` and leaked raw `AttributeError`.

That failure gives callers neither the affected site nor a stable wikidot.py data-shape exception. Generated fixtures, response adapters, recorded traffic, or mocked responses should be classified before field access, and malformed list payloads must not enter forbidden-page detection or application parsing.

## Rollout Evidence

Local rollout-backed drafts identify pending application list reads and application moderation as practical browser-free site-management workflows: [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), [177-pr-site-application-fetch-failure-context.md](177-pr-site-application-fetch-failure-context.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [308-pr-site-application-user-context.md](308-pr-site-application-user-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [556-pr-validate-site-application-acquire-site.md](556-pr-validate-site-application-acquire-site.md), [716-pr-validate-site-application-action-status-type.md](716-pr-validate-site-application-action-status-type.md), and [816-pr-validate-site-application-response-payload.md](816-pr-validate-site-application-response-payload.md).

This slice is not a duplicate of [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md). Issue 212 covered mapping responses with a missing `body` field.

This slice is not a duplicate of [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md). Issue 324 covered a present non-string `body` field inside a mapping, such as `{"body": ["not", "html"]}`.

This slice is not a duplicate of [716-pr-validate-site-application-action-status-type.md](716-pr-validate-site-application-action-status-type.md) or [816-pr-validate-site-application-response-payload.md](816-pr-validate-site-application-response-payload.md). Those drafts cover accept/decline action responses consumed by `_process(...)`, not the application-list response consumed by `acquire_all(...)`.

Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) covers the raw Ajax Module Connector response envelope before module-level response-body extraction. This slice covers the decoded module payload handed to site-application list parsing.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free pending site application listing through `SiteApplication.acquire_all(site)` and `site.applications`.
- Site administration tools that review pending join applications before accepting or declining them.
- Generated fixtures and recorded-response tests that decode list responses before returning them to wikidot.py module code.

## Proposed Fix

- Decode the application-list response once in `_application_list_response_body(...)`.
- Validate the decoded payload is a dictionary before reading `body`.
- Reject non-dictionary payloads with contextual `NoElementException`.
- Include only structural context and type names in the diagnostic, not raw response data.
- Preserve existing missing-body, body-type, forbidden-page, empty-list, parser, and action-response behavior.

## Implementation Notes

Implemented locally in commit `a1870ef fix(site_application): validate list response payload`.

The implementation adds one preflight guard before `body` lookup:

```python
data = response.json()
if not isinstance(data, dict):
    raise exceptions.NoElementException(
        "Site application list response payload is malformed "
        f"for site: {_site_name(site)} (expected=dict, actual={type(data).__name__})"
    )

body = data.get("body")
```

The RED regression mocked `SiteApplication.acquire_all(site)`'s list response as `["not", "a", "mapping"]`. Before the fix, the helper leaked `AttributeError: 'list' object has no attribute 'get'`. After the fix, the same case raises contextual `NoElementException`, decodes the response once, and does not call `user_parser`.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Non-dictionary site-application list payloads fail before `body` lookup. | `test_acquire_all_malformed_response_payload_type_includes_site_context` failed RED with raw `AttributeError`, then passed GREEN. | Reaching `.get("body")`, leaking `AttributeError`, coercing the payload, or treating a list as an application-list response rejects this claim. |
| Missing `body` in a dictionary keeps the existing Issue 212 diagnostic. | Focused GREEN included `test_acquire_all_missing_response_body_includes_site_context`. | Reclassifying `{}` as the payload-type branch or changing the missing-body message rejects this claim. |
| Present non-string `body` keeps the existing Issue 324 diagnostic. | Focused GREEN included `test_acquire_all_malformed_response_body_type_includes_site_context`. | Reclassifying `{"body": ["not", "html"]}` as a payload-type error or dropping `field=body` rejects this claim. |
| Malformed payloads do not enter application parsing. | The new regression patches `user_parser` and asserts it is not called. | Calling `user_parser`, entering BeautifulSoup application extraction, or returning an empty list rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3915 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, complexity scan, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, complexity, provenance, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `a1870ef fix(site_application): validate list response payload`.

- RED: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_malformed_response_payload_type_includes_site_context -q` failed before the fix with raw `AttributeError: 'list' object has no attribute 'get'`.
- GREEN focused: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_missing_response_body_includes_site_context tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_malformed_response_payload_type_includes_site_context tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_malformed_response_body_type_includes_site_context -q` passed 3 tests.
- Site application module coverage: `uv run pytest tests/unit/test_site_application.py -q` passed 73 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3915 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused complexity scan of `src/wikidot/module/site_application.py` reported no obvious complexity hotspots.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `SiteApplication.acquire_all(site)` with `response.json()` returning `["not", "a", "mapping"]` raises `NoElementException` matching `Site application list response payload is malformed for site: test-site (expected=dict, actual=list)`.
- `{}` still raises the existing missing-body message.
- `{"body": ["not", "html"]}` still raises the existing malformed body-type message with `field=body`, `expected=str`, and `actual=list`.
- The malformed payload branch decodes the response JSON once, does not call `user_parser`, and does not include raw response data.
- Valid pending-application parsing, forbidden-page handling, empty-list handling, retry exhaustion, direct site validation, application structure diagnostics, and accept/decline action behavior remain unchanged.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: A caller may have relied on raw `AttributeError` from malformed synthetic list responses. Mitigation: the public module expects a body-bearing result object, and repo validation style consistently routes malformed generated response shape through contextual `NoElementException`.
- Risk: This could be confused with application accept/decline response payload validation. Mitigation: Issues 716 and 816 cover `_process(...)`; this slice only covers the list payload consumed by `SiteApplication.acquire_all(...)`.
- Risk: This could hide raw payload details useful for debugging. Mitigation: the diagnostic includes site, expected type, and actual type while avoiding raw response data that could contain private pending-application content.

## Dependencies

- Site application list responses remain expected to decode as JSON objects with string `body`.
- `NoElementException` remains the parser/data-shape exception for malformed module response payloads.
- `BeautifulSoup` remains responsible only after a validated string response body is available.

## Open Questions

None for this local slice. Similar non-mapping list-payload guards may be useful on other `.json().get("body")` read helpers, but each surface should receive its own duplicate check against the existing missing-body and body-type issue series before implementation.

## Rationale for Upstream Suitability

The patch is small, local, and consistent with existing wikidot.py response-shape diagnostics. It improves failure classification for malformed site application list responses without changing successful list parsing, request construction, login checks, forbidden handling, parser behavior, or application moderation actions.

## Local Evidence

- Local rollout-backed application drafts established pending application listing, body parsing, forbidden handling, user parsing, and application moderation as practical workflow surfaces.
- Existing local drafts covered missing application-list body context, present non-string application-list body values, malformed action statuses, non-mapping action payloads, and raw connector envelope status typing. They did not cover a decoded application-list payload that is not a mapping before `body` lookup.
- This slice only validates site application list payload shape. It does not change request construction, login checks, retry behavior, application parser structure, site invitation handling, site member role changes, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw pending-application content, raw response bodies, private site data, and private source text out of upstream discussion.
