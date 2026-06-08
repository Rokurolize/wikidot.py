# PR Draft: Validate Non-Negative QuickModule User IDs

## Summary

`QMCUser.id` and QuickModule member/user lookup row `user_id` values represent concrete Wikidot user identities used by browser-free member resolution, user lookup, moderation tooling, migration ledgers, and local fixtures. Existing local drafts validate malformed returned `user_id` conversion, direct `QMCUser.id` types, QuickModule text fields, and request argument types, but negative integers still passed as valid direct user IDs or parsed returned row user IDs.

This change validates QuickModule user IDs as non-negative integers at both relevant boundaries: direct `QMCUser(...)` construction and returned member/user QuickModule rows. It deliberately preserves `0` because prior identity-field drafts avoid stronger positive-ID requirements unless parser or live evidence proves one.

## Outcome

Direct QuickModule user result records and parsed member/user lookup rows can no longer carry negative user IDs, while zero-ID compatibility, malformed direct type diagnostics, contextual malformed returned-ID diagnostics, valid member/user lookups, blank-name validation, text-field validation, request validation, URL encoding, retry behavior, and adjacent Site/User/SiteMember workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use QuickModule member lookup or user lookup for browser-free member selection, user resolution, moderation or migration tools, attribution reports, local fixtures, or serialized/rehydrated QuickModule result records.

## Current Evidence

QuickModule-related drafts [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md), [318-pr-quickmodule-row-shape-context.md](318-pr-quickmodule-row-shape-context.md), [319-pr-quickmodule-response-field-context.md](319-pr-quickmodule-response-field-context.md), [320-pr-quickmodule-response-body-context.md](320-pr-quickmodule-response-body-context.md), [339-pr-quickmodule-json-decode-context.md](339-pr-quickmodule-json-decode-context.md), [494-pr-validate-quickmodule-result-text-fields.md](494-pr-validate-quickmodule-result-text-fields.md), [497-pr-validate-quickmodule-request-arguments.md](497-pr-validate-quickmodule-request-arguments.md), [625-pr-validate-quickmodule-blank-user-lookup-queries.md](625-pr-validate-quickmodule-blank-user-lookup-queries.md), and [626-pr-validate-quickmodule-blank-user-result-names.md](626-pr-validate-quickmodule-blank-user-result-names.md) establish QuickModule lookup and QuickModule result records as practical workflow surfaces.

This slice is not a duplicate of Issues 313, 494, 497, 625, or 626. Issue 313 reports non-numeric returned `user_id` values with module/site/row/value context, but still lets `"-1"` parse into `-1`. Issue 494 validates direct `QMCUser.id` type and result text-field types, but still accepts negative integers. Issue 497 validates caller-provided `site_id` and `query` request arguments, not returned user identity values. Issue 625 validates blank lookup query strings, and Issue 626 validates blank returned user names.

## Related Issue / Non-Duplicate Analysis

Builds directly on [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [494-pr-validate-quickmodule-result-text-fields.md](494-pr-validate-quickmodule-result-text-fields.md), [497-pr-validate-quickmodule-request-arguments.md](497-pr-validate-quickmodule-request-arguments.md), [625-pr-validate-quickmodule-blank-user-lookup-queries.md](625-pr-validate-quickmodule-blank-user-lookup-queries.md), and [626-pr-validate-quickmodule-blank-user-result-names.md](626-pr-validate-quickmodule-blank-user-result-names.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject direct `QMCUser(id=-1, name="...")` and `QMCUser(id=-100, name="...")` with `ValueError("id must be non-negative")`.
- Reject returned QuickModule member/user rows whose `user_id` parses to a negative integer with the existing contextual malformed-ID diagnostic shape.
- Preserve direct `QMCUser(id=0, ...)` and returned `{"user_id": "0", "name": ...}` rows as non-negative identity values.
- Preserve malformed direct `QMCUser.id` type diagnostics for non-integers and booleans.
- Preserve existing contextual diagnostics for non-numeric returned `user_id` values.
- Leave QuickModule request validation, valid URL construction, query validation, response-shape diagnostics, text-field validation, retry behavior, adjacent Site/User/SiteMember workflows, and live Wikidot behavior unchanged.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- QuickModule parser hardening
- User identity state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `QMCUser(id=-1, ...)` and `QMCUser(id=-100, ...)` must raise `ValueError("id must be non-negative")`. |
| R2 | `QuickModule.member_lookup(...)` must reject returned rows whose present `user_id` parses to a negative integer with module/site/row/field/value context. |
| R3 | `QuickModule.user_lookup(...)` must reject returned rows whose present `user_id` parses to a negative integer with module/site/row/field/value context. |
| R4 | Direct `QMCUser(id=0, ...)` and returned member/user rows with `user_id="0"` must remain valid. |
| R5 | Existing malformed direct type diagnostics and non-numeric returned-ID diagnostics must remain stable. |
| R6 | Existing valid QuickModule member/user lookups, request validation, blank-name validation, text-field validation, response diagnostics, retry behavior, and adjacent Site/User/SiteMember workflows must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site/user/member data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, QuickModule tests, adjacent QuickModule/Site/SiteMember/User tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct QuickModule user result records cannot store negative user IDs. | `TestQMCUser.test_init_rejects_negative_ids` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after `_validate_qmc_integer_field(...)` rejected values below zero. | Accepting negative `QMCUser.id` values, coercing them to zero, or relying on later lookup code rejects this local completion claim. | `QMCUser` constructor | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R2 | Member lookup rejects negative returned user IDs with the established contextual parser diagnostic. | `TestQuickModuleMemberLookup.test_member_lookup_negative_user_id_includes_module_site_row_and_value_context` failed RED because `QMCUser(id=-1, ...)` was returned, then passed GREEN after `_map_user_item(...)` rejected parsed negative IDs. | Returning `QMCUser(id=-1)`, leaking only direct constructor messages, omitting module/site/row/field/value context, or hiding the observed value rejects this local completion claim. | QuickModule member row parser | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R3 | User lookup rejects negative returned user IDs with the established contextual parser diagnostic. | `TestQuickModuleUserLookup.test_user_lookup_negative_user_id_includes_module_site_row_and_value_context` failed RED because `QMCUser(id=-1, ...)` was returned, then passed GREEN after `_map_user_item(...)` rejected parsed negative IDs. | Returning `QMCUser(id=-1)`, leaking raw conversion details, omitting module/site/row/field/value context, or hiding the observed value rejects this local completion claim. | QuickModule user row parser | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R4 | Zero remains valid at both QuickModule user-ID boundaries. | `TestQMCUser.test_init_accepts_zero_id` and `TestQuickModuleUserLookup.test_user_lookup_accepts_zero_user_id` passed in RED and GREEN runs. | Requiring positive-only user IDs without separate evidence rejects this local completion claim. | Constructor and parser compatibility | `tests/unit/test_quick_module.py` |
| R5 | Existing malformed direct and returned-ID diagnostics remain stable. | `TestQMCUser.test_init_rejects_malformed_ids`, `TestQuickModuleMemberLookup.test_member_lookup_malformed_user_id_includes_module_site_row_and_value_context`, and `TestQuickModuleUserLookup.test_user_lookup_malformed_user_id_includes_module_site_row_and_value_context` passed in the same focused RED and GREEN commands. | Changing `ValueError("id must be an integer")`, accepting booleans, coercing malformed direct IDs, or losing contextual non-numeric returned-ID errors rejects this local completion claim. | Direct and parser diagnostics | `tests/unit/test_quick_module.py` |
| R6 | Existing QuickModule and adjacent workflows remain green. | The QuickModule suite passed 114 tests, adjacent QuickModule/Site/SiteMember/User coverage passed 579 tests, and the full unit suite passed 2931 tests. | Regressing valid member lookup, user lookup, page lookup, request validation, URL encoding, retry behavior, response-shape diagnostics, blank-name validation, text-field validation, Site workflows, SiteMember workflows, or User workflows rejects this local completion claim. | QuickModule and adjacent workflows | `tests/unit/test_quick_module.py`, `tests/unit/test_site.py`, `tests/unit/test_site_member.py`, `tests/unit/test_user.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw QuickModule response bodies, raw lookup queries from real sites, usernames, or private site/member/page data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, QuickModule tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `8b3c972 fix(quickmodule): validate non-negative user ids`.

- RED: `uv run pytest tests/unit/test_quick_module.py::TestQMCUser::test_init_rejects_malformed_ids tests/unit/test_quick_module.py::TestQMCUser::test_init_rejects_negative_ids tests/unit/test_quick_module.py::TestQMCUser::test_init_accepts_zero_id tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_malformed_user_id_includes_module_site_row_and_value_context tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_negative_user_id_includes_module_site_row_and_value_context tests/unit/test_quick_module.py::TestQuickModuleUserLookup::test_user_lookup_malformed_user_id_includes_module_site_row_and_value_context tests/unit/test_quick_module.py::TestQuickModuleUserLookup::test_user_lookup_negative_user_id_includes_module_site_row_and_value_context tests/unit/test_quick_module.py::TestQuickModuleUserLookup::test_user_lookup_accepts_zero_user_id -q` failed 4 negative user-ID cases before the fix; 9 malformed-input and zero-compatibility guards stayed green.
- GREEN: the same focused command passed 13 tests after QuickModule user-ID range validation was added.
- `uv run ruff format src/wikidot/util/quick_module.py tests/unit/test_quick_module.py` left both files unchanged.
- Re-running the same focused command after formatting passed 13 tests.
- `uv run pytest tests/unit/test_quick_module.py -q` passed 114 tests.
- `uv run pytest tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_user.py -q` passed 579 tests.
- `uv run pytest tests/unit -q` passed 2931 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `QMCUser(id=-1, name="test-user")` and `QMCUser(id=-100, name="test-user")` raise `ValueError("id must be non-negative")`.
- `QuickModule.member_lookup(...)` raises `ValueError` with `QuickModule user ID is malformed for module: MemberLookupQModule, site_id=..., row=..., field=user_id, value=-1` when a returned row has `user_id="-1"`.
- `QuickModule.user_lookup(...)` raises `ValueError` with `QuickModule user ID is malformed for module: UserLookupQModule, site_id=..., row=..., field=user_id, value=-1` when a returned row has `user_id="-1"`.
- `QMCUser(id=0, name="test-user")` remains accepted and stores `0`.
- `QuickModule.user_lookup(...)` continues to parse returned rows with `user_id="0"` into `QMCUser(id=0, ...)`.
- Direct `QMCUser(id=None)`, `True`, `"12345"`, and `12345.0` continue to raise `ValueError("id must be an integer")`.
- Returned non-numeric QuickModule member/user `user_id` values continue to raise the existing contextual malformed-ID diagnostic.
- Valid QuickModule member/user/page lookups, direct request validation, URL encoding, retry behavior, response diagnostics, blank-name validation, text-field validation, adjacent Site/User/SiteMember workflows, live Wikidot behavior, pushes, upstream Issues, and upstream PRs remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

QuickModule member/user lookup results feed browser-free user identity workflows. Negative user IDs can look like valid integers in direct fixtures, generated lookup queues, parser outputs, or rehydrated result records, then become impossible stored user state. Non-negative validation catches that impossible state at the constructor and parser boundaries while avoiding a stronger positive-only rule.

## Local Evidence

- Local rollout-backed drafts repeatedly use QuickModule member/user lookup for browser-free member selection, user resolution, moderation and migration tooling, attribution, local fixtures, and generated records.
- Existing local drafts covered malformed returned `user_id` diagnostics, direct `QMCUser.id` type validation, text-field validation, request argument validation, blank query validation, and blank returned-name validation, but did not cover negative QuickModule user IDs.
- The focused RED failures showed negative direct `QMCUser.id` values and negative parsed member/user `user_id` rows were accepted before this slice.
- This slice only validates non-negative QuickModule user-ID semantics. It does not change request URLs, site IDs, query validation, retry policy, response-shape diagnostics, name validation, page lookup parsing, live Wikidot behavior, or upstream actions.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw QuickModule response bodies, raw lookup query text from real sites, and private site/member/page data out of upstream discussion.

## Additional Notes

This change intentionally validates non-negative QuickModule user IDs only. It does not require positive IDs, coerce direct numeric strings, change returned non-numeric diagnostics, or broaden the same rule to higher-level `User` constructor or `Site.member_lookup(user_id=...)` boundaries; those should stay separate duplicate-checked slices if selected by future evidence.
