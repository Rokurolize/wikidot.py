# PR Draft: Validate Site Member List Response Payload

## Summary

`SiteMember.get(site, group)` now validates that decoded `membership/MembersListModule` list responses are dictionaries before reading `body`. Non-mapping payloads such as `["not", "a", "mapping"]` raise contextual `NoElementException` with site, group, page, expected type, and actual type context instead of leaking raw `AttributeError` from `.get("body")`.

The change is intentionally narrow: valid member-list parsing, group validation, pagination, retry exhaustion, missing `body` diagnostics, present non-string `body` diagnostics, member row parsing, row-local pager filtering, site accessors, and role-change action handling remain unchanged.

## Problem Statement

`SiteMember.get(site, group)`, also exposed through `site.members`, `site.admins`, and `site.moderators`, fetches member-list pages from `membership/MembersListModule`, decodes each AMC response, extracts `body`, and parses generated member rows. Earlier local slices covered retry-aware member-list reads, scoped member row parsing, row-local pager filtering, retry-exhausted context, missing response `body`, present non-string response `body`, member user and joined-at parser context, direct site validation, lookup validation, retained user IDs, retained site/client state, and role-change response shape. One adjacent response-boundary gap remained: if `response.json()` returned a non-dictionary payload, `_member_list_response_body(...)` attempted `.get("body")` and leaked raw `AttributeError`.

That failure gives callers neither the affected group/page nor a stable wikidot.py data-shape exception. Generated fixtures, response adapters, recorded traffic, or mocked responses should be classified before field access, and malformed list payloads must not enter BeautifulSoup parsing or member row parsing.

## Rollout Evidence

Local rollout-backed drafts identify member-list reads and membership moderation as practical browser-free workflows: [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [541-pr-validate-site-member-get-site.md](541-pr-validate-site-member-get-site.md), [717-pr-validate-site-member-action-status-type.md](717-pr-validate-site-member-action-status-type.md), and [817-pr-validate-site-member-response-payload.md](817-pr-validate-site-member-response-payload.md).

This slice is not a duplicate of [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md). Issue 213 covered mapping responses with a missing `body` field.

This slice is not a duplicate of [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md). Issue 323 covered a present non-string `body` field inside a mapping, such as `{"body": ["not", "html"]}`.

This slice is not a duplicate of [717-pr-validate-site-member-action-status-type.md](717-pr-validate-site-member-action-status-type.md) or [817-pr-validate-site-member-response-payload.md](817-pr-validate-site-member-response-payload.md). Those drafts cover role-change action responses consumed by `_change_group(...)`, not the member-list response consumed by `SiteMember.get(site, group)`.

Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) covers the raw Ajax Module Connector response envelope before module-level response-body extraction. This slice covers the decoded module payload handed to site-member list parsing.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free site member listing through `SiteMember.get(site, group)`, `site.members`, `site.admins`, and `site.moderators`.
- Membership tooling that lists members before role changes or audits.
- Generated fixtures and recorded-response tests that decode member-list responses before returning them to wikidot.py module code.

## Proposed Fix

- Decode the member-list response once in `_member_list_response_body(...)`.
- Validate the decoded payload is a dictionary before reading `body`.
- Reject non-dictionary payloads with contextual `NoElementException`.
- Include only structural context and type names in the diagnostic, not raw response data.
- Preserve existing missing-body, body-type, parser, pagination, accessor, and role-change behavior.

## Implementation Notes

Implemented locally in commit `7dce039 fix(site_member): validate list response payload`.

The implementation adds one preflight guard before `body` lookup:

```python
data = response.json()
if not isinstance(data, dict):
    raise NoElementException(
        "Site member list response payload is malformed "
        f"for site: {site.unix_name}, group: {group_label}, page: {page} "
        f"(expected=dict, actual={type(data).__name__})"
    )

body = data.get("body")
```

The RED regression mocked `SiteMember.get(site, "")`'s first page response as `["not", "a", "mapping"]`. Before the fix, the helper leaked `AttributeError: 'list' object has no attribute 'get'`. After the fix, the same case raises contextual `NoElementException` before member parsing.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Non-dictionary site-member list payloads fail before `body` lookup. | `test_get_members_malformed_response_payload_type_includes_context` failed RED with raw `AttributeError`, then passed GREEN. | Reaching `.get("body")`, leaking `AttributeError`, coercing the payload, or treating a list as a member-list response rejects this claim. |
| Missing `body` in a dictionary keeps the existing Issue 213 diagnostic. | Focused GREEN included `test_get_members_missing_first_page_response_body_includes_context`. | Reclassifying `{}` as the payload-type branch or changing the missing-body message rejects this claim. |
| Present non-string `body` keeps the existing Issue 323 diagnostic. | Focused GREEN included `test_get_members_malformed_response_body_type_includes_context`. | Reclassifying `{"body": ["not", "html"]}` as a payload-type error or dropping `field=body` rejects this claim. |
| Malformed payloads do not enter member parsing. | The new regression patches `user_parser` and asserts it is not called. | Calling `user_parser`, entering BeautifulSoup row parsing, or returning an empty member list rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3917 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, complexity scan, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, complexity, provenance, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `7dce039 fix(site_member): validate list response payload`.

- RED: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_malformed_response_payload_type_includes_context -q` failed before the fix with raw `AttributeError: 'list' object has no attribute 'get'`.
- GREEN focused: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_missing_first_page_response_body_includes_context tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_malformed_response_payload_type_includes_context tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_malformed_response_body_type_includes_context -q` passed 3 tests.
- Site member module coverage: `uv run pytest tests/unit/test_site_member.py -q` passed 91 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3917 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused complexity scan of `src/wikidot/module/site_member.py` reported no obvious complexity hotspots.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `SiteMember.get(site, "")` with `response.json()` returning `["not", "a", "mapping"]` raises `NoElementException` matching `Site member list response payload is malformed for site: test-site, group: members, page: 1 (expected=dict, actual=list)`.
- `{}` still raises the existing missing-body message.
- `{"body": ["not", "html"]}` still raises the existing malformed body-type message with `field=body`, `expected=str`, and `actual=list`.
- The malformed payload branch decodes the response JSON once, does not call `user_parser`, and does not include raw response data.
- Valid member-list parsing, group validation, pagination, retry exhaustion, row-local pager filtering, direct site validation, accessors, and role-change action behavior remain unchanged.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private member data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: A caller may have relied on raw `AttributeError` from malformed synthetic list responses. Mitigation: the public module expects a body-bearing result object, and repo validation style consistently routes malformed generated response shape through contextual `NoElementException`.
- Risk: This could be confused with role-change response payload validation. Mitigation: Issues 717 and 817 cover `SiteMember._change_group(...)`; this slice only covers the list payload consumed by `SiteMember.get(site, group)`.
- Risk: This could hide raw payload details useful for debugging. Mitigation: the diagnostic includes site, group, page, expected type, and actual type while avoiding raw response data that could contain private membership content.

## Dependencies

- Site member list responses remain expected to decode as JSON objects with string `body`.
- `NoElementException` remains the parser/data-shape exception for malformed module response payloads.
- `BeautifulSoup` remains responsible only after a validated string response body is available.

## Open Questions

None for this local slice. Similar non-mapping list-payload guards may be useful on other `.json().get("body")` read helpers, but each surface should receive its own duplicate check against the existing missing-body and body-type issue series before implementation.

## Rationale for Upstream Suitability

The patch is small, local, and consistent with existing wikidot.py response-shape diagnostics. It improves failure classification for malformed site member list responses without changing successful list parsing, request construction, login checks, pagination, parser behavior, site accessors, or role-change actions.

## Local Evidence

- Local rollout-backed member-list drafts established member listing, body parsing, row context, row-local pager filtering, user and joined-at parsing, direct acquire validation, and membership moderation as practical workflow surfaces.
- Existing local drafts covered missing site-member list body context, present non-string site-member list body values, malformed role-change statuses, non-mapping role-change payloads, and raw connector envelope status typing. They did not cover a decoded site-member list payload that is not a mapping before `body` lookup.
- This slice only validates site-member list payload shape. It does not change request construction, login checks, retry behavior, member parser structure, site invitation handling, site application moderation, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw member content, raw response bodies, private site data, and private source text out of upstream discussion.
