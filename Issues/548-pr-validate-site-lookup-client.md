# PR Draft: Validate Site Lookup Client Input

## Summary

`Site.from_unix_name(client, unix_name)` is the direct browser-free site discovery boundary behind `client.site.get(...)`. Earlier local slices validated site UNIX-name inputs, site lookup config-object state, client accessor parent state, parsed site metadata, site constructor metadata, and site-scoped downstream workflows. One adjacent public lookup-input gap remained: direct calls such as `Site.from_unix_name(None, "test-site")`, booleans, strings, dictionaries, or arbitrary objects reached `client.amc_client.config` and leaked raw `AttributeError`.

This change validates the caller-provided `client` object after UNIX-name validation, but before site lookup config access, HTTP GET setup, redirect handling, or site metadata parsing. Malformed direct site lookup clients now raise `ValueError("client must be a Client")` deterministically, while existing UNIX-name validation precedence, valid SSL and non-SSL lookup behavior, not-found handling, config-object state validation, and malformed site metadata diagnostics remain unchanged.

## Outcome

Direct site lookup callers now get deterministic client validation before config reads or HTTP work instead of incidental attribute errors from malformed client-like values.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call site lookup directly, use client site accessors for browser-free page/site workflows, or load lookup inputs from generated local fixtures where a malformed client should fail before request setup.

## Current Evidence

Local rollout-backed drafts repeatedly identify site lookup and site identity as practical workflow surfaces. Existing drafts [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [310-pr-site-id-context.md](310-pr-site-id-context.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [359-pr-validate-site-lookup-unix-names.md](359-pr-validate-site-lookup-unix-names.md), [394-pr-validate-site-amc-retry-controls.md](394-pr-validate-site-amc-retry-controls.md), [479-pr-validate-client-accessor-parent-clients.md](479-pr-validate-client-accessor-parent-clients.md), [480-pr-validate-site-constructor-metadata.md](480-pr-validate-site-constructor-metadata.md), [525-pr-validate-site-lookup-config-object.md](525-pr-validate-site-lookup-config-object.md), and [526-pr-validate-site-amc-retry-config-object.md](526-pr-validate-site-amc-retry-config-object.md) establish site discovery, site identity, direct site construction, client accessors, site lookup config state, and retry-aware site AMC config state as active operational boundaries.

This is not a duplicate of Issue 359. Issue 359 validates caller-provided `unix_name` values before host construction. This slice validates the separate caller-provided `client` object after the site name is known valid.

This is not a duplicate of Issue 525. Issue 525 validates replaced `client.amc_client.config` state after a usable client reaches request setup. This slice validates the parent client object before `amc_client` or `config` is read.

This is not a duplicate of Issue 479. Issue 479 validates client accessor construction for `client.site`, `client.user`, and `client.private_message`; this slice covers direct static lookup calls to `Site.from_unix_name(...)`.

No upstream issue was filed from this local workspace.

## Changes

- Add a focused regression for malformed direct `Site.from_unix_name(client=...)` inputs with an otherwise valid site UNIX name.
- Add `_validate_site_lookup_client(...)` and call it before site lookup config access.
- Update direct site lookup tests to use the existing autospecced `Client` helper at the stricter public boundary.
- Preserve UNIX-name validation, config-object validation, valid SSL and non-SSL lookup, not-found behavior, and malformed site metadata diagnostics.

## Type Of Change

- Input validation
- Public read-boundary hardening
- Site lookup preflight
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.from_unix_name(None, "test-site")`, `True`, `"test-client"`, `{"site": "test-site"}`, and `object()` must raise `ValueError("client must be a Client")` before config access or HTTP requests. |
| R2 | Existing malformed UNIX-name validation must remain earlier than client validation and request work. |
| R3 | Existing config-object state validation must remain after valid client validation and before HTTP request setup. |
| R4 | Valid SSL lookup, non-SSL lookup, not-found handling, and malformed site metadata diagnostics must remain unchanged. |
| R5 | Site, adjacent client/accessor/user, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct site lookup clients fail at the public lookup boundary. | `TestSiteFromUnixName.test_from_unix_name_rejects_malformed_client_before_config` failed RED for all 5 malformed values with raw `AttributeError`, then passed GREEN after validation was added. | Reaching `client.amc_client.config`, accepting client-like dictionaries, preparing HTTP requests, or leaking raw attribute errors rejects this local completion claim. | `Site.from_unix_name(...)` | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Existing site-name validation remains the first lookup preflight. | Focused GREEN included invalid string and non-string UNIX-name tests, and both assert no HTTP requests were recorded. | Shifting malformed site names into client validation, host construction, redirects, or HTTP requests rejects this local completion claim. | Site lookup names | `tests/unit/test_site.py` |
| R3 | Replaced config-object state remains a separate request-setup validation after a valid client is supplied. | Focused GREEN included `test_from_unix_name_rejects_invalid_config_object_before_request` for five malformed config replacements. | Treating malformed config state as malformed client state, reading config fields before validation, or issuing HTTP requests rejects this local completion claim. | Site lookup config state | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R4 | Valid site lookup and parse diagnostics remain stable. | Focused GREEN included SSL lookup, non-SSL lookup, and not-found tests; the full site suite passed 282 tests. | Regressing redirects, parsed site ID/title/unix name/domain, not-found behavior, missing metadata diagnostics, malformed site ID diagnostics, or adjacent site workflows rejects this local completion claim. | Site lookup and site workflows | `tests/unit/test_site.py` |
| R5 | Existing repository quality gates remain green. | Focused lookup tests passed 15 tests, site tests passed 282 tests, adjacent client/accessor/user tests passed 100 tests, full unit tests passed 2598 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic state; this draft contains no credentials, cookies, auth JSON, raw account data, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private usernames, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `d218eba fix(site): validate lookup client`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_rejects_malformed_client_before_config -q` failed 5 tests before the fix because malformed clients reached `client.amc_client.config` and leaked raw `AttributeError`.
- GREEN focused: `uv run pytest tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_rejects_malformed_client_before_config tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_rejects_invalid_config_object_before_request tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_invalid_name_rejected_before_request tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_non_string_name_rejected_before_request tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_ssl_site tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_non_ssl_site tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_not_found -q` passed 15 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 282 tests.
- `uv run pytest tests/unit/test_client.py tests/unit/test_client_accessors.py tests/unit/test_user.py -q` passed 100 tests.
- `uv run pytest tests/unit -q` passed 2598 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy .` passed with no issues in 87 source files.
- `uv run pyright .` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Malformed direct `Site.from_unix_name(client=...)` inputs raise `ValueError("client must be a Client")`.
- Existing malformed UNIX-name validation remains an earlier preflight.
- Existing replaced config-object validation remains a separate valid-client request setup preflight.
- Valid SSL/non-SSL site lookup, not-found handling, and malformed metadata diagnostics remain unchanged.
- Adjacent client, accessor, and user workflows stay green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Client validation could accidentally change UNIX-name validation precedence. Mitigation: validation runs after existing `StringUtil.validate_site_unix_name(...)`, and focused GREEN includes malformed site-name tests.
- Risk: This could be confused with site lookup config validation. Mitigation: Issue 525 covers replaced config objects after a valid client reaches request setup; this draft explicitly covers the parent client object before `amc_client` is read.
- Risk: Existing tests used plain mocks for direct site lookup. Mitigation: only the `Site.from_unix_name(...)` tests were moved to the existing autospecced `Client` helper that passes `isinstance(client, Client)`.

## Dependencies

- Existing `Client` remains the canonical parent type for direct site lookup.
- Existing site UNIX-name validation remains responsible for site selector input before client validation.
- Existing config-object validation remains responsible for request setup state after a valid client is supplied.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`Site.from_unix_name(...)` is the direct site discovery entry point for browser-free workflows. Validating the supplied client object before config reads and HTTP work gives generated callers and tests deterministic errors for malformed inputs without changing valid site lookup semantics, site-name validation, config-object validation, redirect handling, or parsed metadata diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed malformed direct `client` arguments crossing the public static site lookup boundary and leaking `AttributeError` from `client.amc_client.config`.
- This slice only validates the `Site.from_unix_name(...)` caller-provided parent client. It does not change site UNIX-name syntax, HTTP retry policy, SSL redirect handling, site metadata parsing, site constructor validation, site accessors, site AMC retry behavior, live site behavior, or authentication semantics for valid clients.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private site data, and live Wikidot account details out of upstream discussion.
