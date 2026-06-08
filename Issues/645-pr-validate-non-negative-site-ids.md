# PR Draft: Validate Non-Negative Site IDs

## Summary

`Site.id` and direct `QuickModule` `site_id` request arguments identify concrete Wikidot sites used by browser-free site bootstrap, page, forum, membership, application, recent-change, source, publish, and QuickModule lookup workflows. Existing local drafts validate site IDs as non-boolean integers, but direct `Site(...)` construction and direct `QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` calls still accepted negative integers such as `-1`. Negative QuickModule site IDs could even reach `httpx.get(...)` as `s=-1`.

This change validates stored `Site.id` values and direct QuickModule `site_id` arguments as non-negative integers at their existing validation boundaries. It deliberately preserves `0` because prior identity-field drafts avoid stronger positive-ID requirements unless parser or live evidence proves one.

## Outcome

Directly constructed `Site` records and direct QuickModule lookup calls can no longer store or submit negative site IDs, while zero-ID compatibility, malformed direct type diagnostics, generated site bootstrap parsing, site routing metadata validation, valid QuickModule URL serialization, retry behavior, response diagnostics, and adjacent Site/User/SiteMember workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free site lookup, generated site ledgers, page/forum/member/application workflows, QuickModule member/user/page selection, moderation or migration tooling, local fixtures, or serialized/rehydrated site records.

## Current Evidence

Local rollout-backed drafts repeatedly identify site identity and QuickModule lookup as practical workflow surfaces. [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [310-pr-site-id-context.md](310-pr-site-id-context.md), [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md), [318-pr-quickmodule-row-shape-context.md](318-pr-quickmodule-row-shape-context.md), [319-pr-quickmodule-response-field-context.md](319-pr-quickmodule-response-field-context.md), [320-pr-quickmodule-response-body-context.md](320-pr-quickmodule-response-body-context.md), [339-pr-quickmodule-json-decode-context.md](339-pr-quickmodule-json-decode-context.md), [359-pr-validate-site-lookup-unix-names.md](359-pr-validate-site-lookup-unix-names.md), [480-pr-validate-site-constructor-metadata.md](480-pr-validate-site-constructor-metadata.md), [494-pr-validate-quickmodule-result-text-fields.md](494-pr-validate-quickmodule-result-text-fields.md), [497-pr-validate-quickmodule-request-arguments.md](497-pr-validate-quickmodule-request-arguments.md), [548-pr-validate-site-lookup-client.md](548-pr-validate-site-lookup-client.md), and [629-pr-validate-blank-site-routing-metadata.md](629-pr-validate-blank-site-routing-metadata.md) establish site ID metadata, direct site construction, site lookup validation, QuickModule request validation, QuickModule parser diagnostics, and site routing metadata as operational boundaries.

This slice is not a duplicate of Issues 310, 480, 497, or 629. Issue 310 handles malformed generated `WIKIREQUEST.info.siteId` assignments and already extracts digit-only IDs from site bootstrap HTML. Issue 480 rejects malformed direct `Site.id` types, but still accepts negative integers. Issue 497 rejects malformed direct QuickModule `site_id` types, but still accepts negative integers and serializes them into request URLs. Issue 629 validates blank routing metadata, not site-ID range semantics.

## Related Issue / Non-Duplicate Analysis

Builds directly on [310-pr-site-id-context.md](310-pr-site-id-context.md), [480-pr-validate-site-constructor-metadata.md](480-pr-validate-site-constructor-metadata.md), [497-pr-validate-quickmodule-request-arguments.md](497-pr-validate-quickmodule-request-arguments.md), and [629-pr-validate-blank-site-routing-metadata.md](629-pr-validate-blank-site-routing-metadata.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject direct `Site(id=-1)` and `Site(id=-100)` with `ValueError("id must be non-negative")`.
- Reject direct `QuickModule.member_lookup(-1, "test")`, `QuickModule.user_lookup(-1, "test")`, and `QuickModule.page_lookup(-1, "test")` with `ValueError("site_id must be non-negative")` before `httpx.get(...)`.
- Preserve direct `Site(id=0)` and direct QuickModule request serialization with `site_id=0` as non-negative identity values.
- Preserve existing malformed-ID diagnostics for non-integers and booleans.
- Leave generated site bootstrap parsing, site lookup names, routing metadata validation, QuickModule query validation, response parsing, retry behavior, adjacent Site/User/SiteMember workflows, and live Wikidot behavior unchanged.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- QuickModule request-boundary hardening
- Site identity state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `Site(id=-1)` and `Site(id=-100)` must raise `ValueError("id must be non-negative")` when every other site metadata field is valid. |
| R2 | Direct `QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` calls must reject negative `site_id` values with `ValueError("site_id must be non-negative")` before request construction. |
| R3 | Direct `Site(id=0)` and direct QuickModule `_request(..., site_id=0, ...)` must remain valid. |
| R4 | Existing malformed direct type diagnostics must remain stable. |
| R5 | Generated site bootstrap parsing, site routing metadata validation, valid QuickModule request serialization, retry behavior, response diagnostics, and adjacent Site/User/SiteMember workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site/user/member data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, touched Site/QuickModule tests, adjacent Site/QuickModule consumer tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct site records cannot store negative site IDs. | `TestSiteInit.test_init_rejects_negative_ids` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after `_validate_site_id(...)` rejected values below zero. | Accepting negative site IDs, coercing them to zero, or deferring failure to lookup or QuickModule code rejects this local completion claim. | Site constructor | `src/wikidot/module/site.py`, `tests/unit/test_site_constructor.py` |
| R2 | Direct QuickModule lookups reject negative site IDs before request work. | `TestQuickModuleRequest.test_lookup_rejects_negative_site_ids_before_request` failed RED for member/user/page lookup paths because `httpx.get(...)` was reached with `s=-1` or `s=-100`, then passed GREEN after `_validate_quickmodule_site_id(...)` rejected values below zero. | Calling `httpx.get(...)`, URL-encoding `s=-1`, retrying the invalid request, or relying on remote response handling rejects this local completion claim. | QuickModule request boundary | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R3 | Zero remains valid at both site-ID boundaries. | `TestSiteInit.test_init_accepts_zero_id` and `TestQuickModuleRequest.test_request_allows_zero_site_id` passed in RED and GREEN runs. | Requiring positive-only site IDs without separate evidence rejects this local completion claim. | Constructor and request compatibility | `tests/unit/test_site_constructor.py`, `tests/unit/test_quick_module.py` |
| R4 | Existing malformed direct type diagnostics remain stable. | `TestSiteInit.test_init_rejects_malformed_metadata` and `TestQuickModuleRequest.test_lookup_rejects_malformed_site_ids_before_request` passed in the same focused RED and GREEN commands. | Changing `ValueError("id must be an integer")` or `ValueError("site_id must be an integer")`, accepting booleans, or coercing strings/floats rejects this local completion claim. | Site and QuickModule ID type validation | `tests/unit/test_site_constructor.py`, `tests/unit/test_quick_module.py` |
| R5 | Existing Site and QuickModule workflows remain green. | Touched site-constructor/QuickModule coverage passed 144 tests, adjacent QuickModule/Site/SiteMember/User coverage passed 573 tests, and the full unit suite passed 2925 tests. | Regressing generated site bootstrap, site routing metadata, valid QuickModule URL construction, retry behavior, response parser diagnostics, member lookup, user lookup, page lookup, site member workflows, or user workflows rejects this local completion claim. | Site and QuickModule adjacent workflows | `tests/unit/test_site_constructor.py`, `tests/unit/test_quick_module.py`, `tests/unit/test_site.py`, `tests/unit/test_site_member.py`, `tests/unit/test_user.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw QuickModule response bodies, raw lookup queries from real sites, usernames, or private site/member/page data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, touched tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d32f1b2 fix(site): validate non-negative site ids`.

- RED: `uv run pytest tests/unit/test_site_constructor.py::TestSiteInit::test_init_rejects_malformed_metadata tests/unit/test_site_constructor.py::TestSiteInit::test_init_rejects_negative_ids tests/unit/test_site_constructor.py::TestSiteInit::test_init_accepts_zero_id tests/unit/test_quick_module.py::TestQuickModuleRequest::test_lookup_rejects_malformed_site_ids_before_request tests/unit/test_quick_module.py::TestQuickModuleRequest::test_lookup_rejects_negative_site_ids_before_request tests/unit/test_quick_module.py::TestQuickModuleRequest::test_request_allows_zero_site_id -q` failed 8 negative site-ID cases before the fix; 38 malformed-input and zero-compatibility guards stayed green.
- GREEN: the same focused command passed 46 tests after site-ID range validation was added.
- `uv run ruff format src/wikidot/module/site.py src/wikidot/util/quick_module.py tests/unit/test_site_constructor.py tests/unit/test_quick_module.py` left all 4 files unchanged.
- Re-running the same focused command after formatting passed 46 tests.
- `uv run pytest tests/unit/test_site_constructor.py tests/unit/test_quick_module.py -q` passed 144 tests.
- `uv run pytest tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_user.py -q` passed 573 tests.
- `uv run pytest tests/unit -q` passed 2925 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Site(id=-1)` and `Site(id=-100)` raise `ValueError("id must be non-negative")`.
- `QuickModule.member_lookup(-1, "test")`, `QuickModule.user_lookup(-1, "test")`, and `QuickModule.page_lookup(-1, "test")` raise `ValueError("site_id must be non-negative")` before `httpx.get(...)`.
- `Site(id=0)` remains accepted and stores `0`.
- Direct QuickModule `_request("MemberLookupQModule", 0, "test")` still serializes `s=0` and returns the parsed response.
- `Site(id=None)`, `True`, `"123456"`, and `123456.0` continue to raise `ValueError("id must be an integer")`.
- Direct QuickModule `site_id=None`, `True`, `"123456"`, and `123456.0` continue to raise `ValueError("site_id must be an integer")`.
- Generated site bootstrap parsing, site lookup names, routing metadata validation, QuickModule query validation, retry behavior, response parsing, adjacent Site/User/SiteMember workflows, live Wikidot behavior, pushes, upstream Issues, and upstream PRs remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Site IDs are identity metadata for browser-free site objects and QuickModule lookup requests. Negative IDs can look like valid integers in direct fixtures, generated lookup queues, or rehydrated records, then either become impossible stored site state or get serialized into avoidable remote lookup URLs. Non-negative validation catches that impossible state early while avoiding a stronger positive-only rule.

## Local Evidence

- Local rollout evidence used site lookup, site-scoped page/forum/member/application workflows, QuickModule member/user/page selection, generated ledgers, local fixtures, and records that construct or consume `Site` and direct QuickModule lookup inputs.
- Existing local drafts covered malformed generated site IDs, direct `Site.id` type validation, blank site routing metadata, direct QuickModule request argument types, and QuickModule response/parser diagnostics, but did not cover negative direct site IDs.
- The focused RED failures showed negative direct `Site.id` values were accepted as stored state and negative QuickModule `site_id` values reached the mocked HTTP request path as `s=-1` or `s=-100`. The GREEN regressions cover invalid values, zero compatibility, existing malformed type validation, and adjacent workflow compatibility.
- This slice only validates non-negative direct site-ID semantics. It does not change generated site bootstrap parsing, site lookup names, routing metadata, URL formatting, QuickModule query validation, QuickModule retry behavior, QuickModule response parsing, live site behavior, or upstream actions.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw QuickModule response bodies, raw lookup query text from real sites, private messages, and private site/member/page data out of upstream discussion.

## Additional Notes

This change intentionally validates non-negative direct site IDs only. It does not require positive IDs, coerce numeric strings, or change generated site bootstrap parsing because that path already has contextual malformed-ID diagnostics and digit-only extraction.
