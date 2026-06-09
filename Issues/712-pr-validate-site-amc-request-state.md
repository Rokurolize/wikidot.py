# PR Draft: Validate Site AMC Request State

## Summary

`Site.amc_request(...)` and `Site.amc_request_with_retry(...)` are the site-scoped Ajax Module Connector helpers beneath page, forum, member, application, recent-change, ListPages, and source workflows. Adjacent local slices validate constructor-time `Site.client`, constructor and URL-time site metadata, empty AMC batches, `return_exceptions`, retry controls, and retry config objects, but one retained-state gap remained: after a valid `Site` object was created, callers or rehydrated fixtures could replace `site.client`, `site.unix_name`, or `site.ssl_supported` before a non-empty AMC request. The raw helper would either leak an incidental `AttributeError` for malformed clients or pass malformed routing fields to `client.amc_client.request(...)`.

This change validates non-empty Site AMC request state before request delegation. Mutated `site.client` now raises `ValueError("client must be a Client")`; mutated `site.unix_name` raises `ValueError("unix_name must be a string")` or `ValueError("unix_name must not be empty")`; mutated `site.ssl_supported` raises `ValueError("ssl_supported must be a boolean")`. Empty batch behavior, explicit option validation, retry config validation, valid routing delegation, partial-success retries, and adjacent workflows remain unchanged.

## Outcome

Non-empty Site AMC requests now have deterministic retained-state validation at the wrapper boundary before raw AMC request work starts.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free site helpers, page publishing, source/file/revision/vote acquisition, forum reads, site member/application listing, recent changes, ListPages pagination, generated local fixtures, serialized site records, migration ledgers, moderation tools, or rehydrated `Site` objects.

## Current Evidence

Local rollout-backed drafts repeatedly identify `Site.amc_request(...)` and `Site.amc_request_with_retry(...)` as shared infrastructure. Existing drafts [139-pr-skip-empty-amc-retry-batches.md](139-pr-skip-empty-amc-retry-batches.md), [140-pr-skip-empty-site-amc-request-batches.md](140-pr-skip-empty-site-amc-request-batches.md), [387-pr-validate-site-amc-return-exceptions-flag.md](387-pr-validate-site-amc-return-exceptions-flag.md), [394-pr-validate-site-amc-retry-controls.md](394-pr-validate-site-amc-retry-controls.md), [526-pr-validate-site-amc-retry-config-object.md](526-pr-validate-site-amc-retry-config-object.md), [571-pr-validate-site-url-metadata-state.md](571-pr-validate-site-url-metadata-state.md), [629-pr-validate-blank-site-routing-metadata.md](629-pr-validate-blank-site-routing-metadata.md), and [701-pr-validate-site-constructor-client.md](701-pr-validate-site-constructor-client.md) establish empty-batch behavior, option validation, retry setup, retained URL metadata, blank routing metadata, and constructor client validation as active boundaries.

Those prior slices are not duplicates. Issues 139 and 140 cover empty body lists, not non-empty retained-state validation. Issue 387 validates the `return_exceptions` control before branching. Issue 394 validates retry batch and retry count values, and Issue 526 validates the retry config object. Issues 571 and 629 validate URL-generation and constructor/lookup routing metadata, not the AMC wrapper's retained request state. Issue 701 validates direct `Site(client=...)` construction, but it cannot cover a valid `Site` whose public fields are later replaced. No upstream issue was filed from this local workspace.

## Changes

- Add a Site AMC request-state validator that checks retained `client`, `unix_name`, and `ssl_supported` before non-empty raw request delegation.
- Use validated local client/routing values when delegating to `client.amc_client.request(...)`.
- Validate retained `client` in `Site.amc_request_with_retry(...)` before reading retry config, while leaving empty retry batches as no-config no-ops.
- Add regressions for mutated retained `client`, `unix_name`, blank `unix_name`, and `ssl_supported` in both raw and retry-aware Site AMC helpers.

## Type Of Change

- Retained-state validation
- Site AMC request-boundary hardening
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Non-empty `Site.amc_request(...)` must reject mutated non-`Client` retained clients with `ValueError("client must be a Client")` before AMC request delegation. |
| R2 | Non-empty `Site.amc_request(...)` must reject mutated malformed retained `unix_name` values with existing routing diagnostics before AMC request delegation. |
| R3 | Non-empty `Site.amc_request(...)` must reject mutated non-boolean retained `ssl_supported` values with `ValueError("ssl_supported must be a boolean")` before AMC request delegation. |
| R4 | `Site.amc_request_with_retry(...)` must enforce the same retained request-state preflight before non-empty retry request work. |
| R5 | Empty body lists must still return `()` without reading `client.amc_client`, while explicit invalid retry controls and malformed `return_exceptions` values keep their existing precedence. |
| R6 | Valid Site AMC request delegation, retry batching, partial-success handling, retry config validation, page/forum/member/application/raw AMC/RequestUtil workflows, and adjacent site behavior must remain compatible. |
| R7 | Focused RED/GREEN, affected and adjacent tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming local implementation complete. |
| R8 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Mutated retained clients fail with the shared client diagnostic. | `test_amc_request_rejects_mutated_request_state_before_client_request` and `test_amc_request_with_retry_rejects_mutated_request_state_before_client_request` failed RED with raw `AttributeError`, then passed GREEN with `ValueError("client must be a Client")`. | Leaking `AttributeError`, accepting duck-typed objects, reading retry config from a malformed client, or calling the original AMC mock rejects this local completion claim. | Site AMC retained client state | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Mutated non-string and blank retained UNIX names fail before request delegation. | The same focused tests failed RED with `DID NOT RAISE`, then passed GREEN for `unix_name=True` and `unix_name=" "`. | Passing malformed UNIX names into `client.amc_client.request(...)`, coercing values, or relying on lower-level site-name diagnostics rejects this local completion claim. | Site AMC retained routing text | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Mutated retained SSL flags fail before request delegation. | The same focused tests failed RED with `DID NOT RAISE`, then passed GREEN for `ssl_supported="true"`. | Treating truthy or falsy non-booleans as scheme controls, calling AMC request work, or deferring to URL formatting rejects this local completion claim. | Site AMC retained scheme flag | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R4 | Retry-aware Site AMC uses the same retained-state protection for non-empty batches. | The retry focused regression passed after `Site.amc_request_with_retry(...)` validates retained client before config access and delegates through the validated raw helper for routing state. | Reading malformed client config, sending a retry batch with malformed routing state, or mutating retry result shape rejects this local completion claim. | Site AMC retry wrapper | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R5 | Empty-batch and option-precedence behavior remains stable. | `tests/unit/test_site.py` passed 350 tests after the change, including empty-batch, `return_exceptions`, retry-control, and retry-config coverage. | Reading `amc_client` for empty body lists, accepting explicit invalid retry controls on empty batches, or changing empty return shape rejects this local completion claim. | Site AMC public boundary | `tests/unit/test_site.py` |
| R6 | Adjacent request workflows remain green. | Adjacent Site/Page/Forum/SiteMember/SiteApplication/AMC/RequestUtil suites passed 2100 tests, and full unit coverage passed 3569 tests. | Regressing valid batch delegation, retry batching, partial-success preservation, raw AMC behavior, RequestUtil, page reads/writes, forum reads, member/application reads, or site workflows rejects this local completion claim. | Site and request workflows | `tests/unit` |
| R7 | Repository quality gates pass in the local dependency environment. | Full ruff check passed, full ruff format check passed, full mypy passed with no issues in 87 source files, pyright passed with 0 errors, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R8 | No live site state or private material is needed to prove the behavior. | The regressions use synthetic mutated state on valid unit-level `Site` objects and local mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private content, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `ef0cec9 fix(site): validate amc request state`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteAmcRequest::test_amc_request_rejects_mutated_request_state_before_client_request tests/unit/test_site.py::TestSiteAmcRequest::test_amc_request_with_retry_rejects_mutated_request_state_before_client_request -q` failed 8 cases before the fix with `AttributeError` for mutated clients and `DID NOT RAISE` for mutated routing fields.
- GREEN focused: the same focused command passed 8 tests after request-state validation was added.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` passed with 2 files left unchanged.
- `uv run pytest tests/unit/test_site.py -q` passed 350 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_amc_client.py tests/unit/test_requestutil.py -q` passed 2100 tests.
- `uv run pytest tests/unit -q` passed 3569 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Non-empty `Site.amc_request(...)` rejects mutated retained `client`, `unix_name`, blank `unix_name`, and `ssl_supported` state before `client.amc_client.request(...)` is called.
- Non-empty `Site.amc_request_with_retry(...)` rejects the same mutated retained state before request work.
- Empty `Site.amc_request([])` and `Site.amc_request_with_retry([])` behavior remains a no-request `()`.
- Malformed `return_exceptions`, explicit retry controls, retry config objects, constructor metadata, URL-time metadata, and valid request delegation remain covered by their existing tests.
- Adjacent page, forum, site member/application, raw AMC, RequestUtil, and full unit workflows remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Downstream tests may mutate `Site` public fields and expect low-level mocks to accept them. Mitigation: a `Site` is the routing record for site-scoped AMC work, and malformed retained fields should be repaired before non-empty request calls.
- Risk: This could be confused with lower-level raw AMC override validation. Mitigation: this slice covers the Site wrapper's retained state; direct `AjaxModuleConnectorClient.request(..., site_ssl_supported=...)` validation remains a separate possible slice.
- Risk: This could change empty-batch behavior if validation were moved too early. Mitigation: the guard runs only after the existing empty-batch shortcut, and focused Site AMC tests prove empty batches still avoid `amc_client`.

## Out Of Scope

Validating raw `AjaxModuleConnectorClient.request(...)` `site_ssl_supported` override values, validating raw request body shapes at the Site wrapper, changing lower-level site-name validation, changing retry semantics, changing batch splitting, changing partial-success behavior, changing URL generation, changing live Wikidot behavior, pushing changes, opening upstream Issues, and opening upstream PRs are outside this slice.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used Site AMC helpers through page publishing, source/revision/file/vote reads, forum traversal, member/application inventories, recent changes, ListPages pagination, generated fixtures, and mocked retry workflows.
- Existing local drafts covered empty Site AMC batches, Site AMC exception controls, retry controls, retry config object state, constructor client validation, constructor and URL-time metadata validation, and blank routing metadata.
- The focused RED failures showed that a valid `Site` object corrupted after construction could still reach the raw AMC mock or leak an incidental attribute error instead of using established Site diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
