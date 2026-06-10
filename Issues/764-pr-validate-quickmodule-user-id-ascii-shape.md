# PR Draft: Validate QuickModule User ID ASCII Shape

## Summary

`QuickModule.member_lookup(...)` and `QuickModule.user_lookup(...)` parse returned `user_id` fields from Wikidot QuickModule JSON rows into `QMCUser` records. Issue 313 already converted non-numeric values such as `latest` into contextual QuickModule parser diagnostics, and Issue 646 already rejects negative returned IDs such as `-1`. One accepted-value gap remained: `_map_user_item(...)` still used `int(str(user_id_value))`, so Python accepted Unicode decimal digit strings such as `\uff11\uff12\uff13\uff14\uff15` and normalized them into ordinary `id=12345`.

This change requires returned QuickModule user IDs to match ASCII `-?[0-9]+` before integer conversion. Valid ASCII returned IDs such as `"12345"` and `"0"` continue to parse normally, non-numeric returned IDs keep the established contextual malformed-ID diagnostic, negative ASCII returned IDs keep the established contextual negative-ID diagnostic, and Unicode digit-like values now fail before a `QMCUser` is returned.

## Outcome

QuickModule member/user lookups no longer fabricate user identities by normalizing malformed returned `user_id` scalars. A QuickModule response row with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like `user_id` text now fails at the shared QuickModule user-row parser boundary with module, site, row, field, and observed value context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free QuickModule member lookup or user lookup for membership resolution, moderation tools, invitation and application workflows, migration ledgers, attribution reports, local fixtures, or generated review records where `QMCUser.id` must reflect structurally valid Wikidot identity metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify QuickModule member/user lookup as a practical browser-free identity workflow. Existing drafts cover retry-aware QuickModule requests, malformed JSON diagnostics, response-body diagnostics, missing response keys, malformed top-level result fields, malformed row objects, missing row fields, malformed non-numeric returned `user_id` values, non-negative returned QuickModule user IDs, result text-field validation, blank result-name validation, request argument validation, blank lookup-query validation, Site member-lookup filter validation, direct `QMCUser` constructor validation, and adjacent user identity boundaries.

This slice is not a duplicate of [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md). Issue 313 reports non-numeric returned `user_id` values with module/site/row/value context, but a fullwidth digit string is numeric to Python `int(...)` and was still accepted.

This slice is not a duplicate of [646-pr-validate-non-negative-quickmodule-user-ids.md](646-pr-validate-non-negative-quickmodule-user-ids.md). Issue 646 rejects negative direct and returned QuickModule user IDs, while this slice preserves the negative ASCII path and rejects Unicode digit normalization before conversion.

This slice is also not a duplicate of [494-pr-validate-quickmodule-result-text-fields.md](494-pr-validate-quickmodule-result-text-fields.md), which validates direct `QMCUser.id` types and result text fields but does not change returned row `user_id` ASCII shape.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md), [318-pr-quickmodule-row-shape-context.md](318-pr-quickmodule-row-shape-context.md), [319-pr-quickmodule-response-field-context.md](319-pr-quickmodule-response-field-context.md), [320-pr-quickmodule-response-body-context.md](320-pr-quickmodule-response-body-context.md), [339-pr-quickmodule-json-decode-context.md](339-pr-quickmodule-json-decode-context.md), [494-pr-validate-quickmodule-result-text-fields.md](494-pr-validate-quickmodule-result-text-fields.md), [497-pr-validate-quickmodule-request-arguments.md](497-pr-validate-quickmodule-request-arguments.md), [625-pr-validate-quickmodule-blank-user-lookup-queries.md](625-pr-validate-quickmodule-blank-user-lookup-queries.md), [626-pr-validate-quickmodule-blank-user-result-names.md](626-pr-validate-quickmodule-blank-user-result-names.md), [646-pr-validate-non-negative-quickmodule-user-ids.md](646-pr-validate-non-negative-quickmodule-user-ids.md), [648-pr-validate-non-negative-site-member-lookup-user-ids.md](648-pr-validate-non-negative-site-member-lookup-user-ids.md), and adjacent generated-scalar ASCII-shape drafts [756-pr-validate-page-revision-row-id-ascii-shape.md](756-pr-validate-page-revision-row-id-ascii-shape.md), [761-pr-validate-page-revision-number-ascii-shape.md](761-pr-validate-page-revision-number-ascii-shape.md), [762-pr-validate-forum-category-count-ascii-shape.md](762-pr-validate-forum-category-count-ascii-shape.md), and [763-pr-validate-forum-thread-list-post-count-ascii-shape.md](763-pr-validate-forum-thread-list-post-count-ascii-shape.md).

## Changes

- Require ASCII `-?[0-9]+` before integer conversion when parsing returned QuickModule member/user row `user_id` values.
- Preserve successful parsing for valid returned ASCII user IDs such as `"12345"` and `"0"`.
- Preserve the existing contextual malformed-ID diagnostic for non-numeric returned user IDs such as `latest`.
- Preserve the existing contextual negative-ID diagnostic for negative ASCII returned user IDs such as `-1`.
- Add regression coverage for returned member/user row `user_id="\uff11\uff12\uff13\uff14\uff15"`.

## Type Of Change

- Bug fix
- QuickModule returned scalar validation
- User identity parser hardening
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Returned QuickModule member/user row `user_id` values containing non-ASCII digit glyphs must fail before a `QMCUser` is returned. |
| R2 | The malformed user-ID diagnostic must identify the QuickModule name, site ID, row, affected field, and observed raw value. |
| R3 | Valid returned ASCII user IDs such as `"12345"` and `"0"` must continue to parse into the same `QMCUser.id` values. |
| R4 | Existing non-numeric and negative ASCII returned-ID paths must keep their established diagnostics. |
| R5 | Existing QuickModule request validation, retry behavior, JSON diagnostics, response-shape diagnostics, text-field validation, blank-name validation, page lookup behavior, Site member lookup, SiteMember workflows, and direct User workflows must remain compatible. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, real QuickModule payloads, raw lookup queries, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, QuickModule tests, adjacent Site/SiteMember/User tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `\uff11\uff12\uff13\uff14\uff15` in a returned QuickModule member/user row `user_id` raises before a result list is returned. | `test_member_lookup_fullwidth_digit_user_id_includes_module_site_row_and_value_context` and `test_user_lookup_fullwidth_digit_user_id_includes_module_site_row_and_value_context` failed RED with `DID NOT RAISE`, then passed after ASCII-only ID parsing. | Returning `QMCUser(id=12345)`, normalizing the raw scalar, or silently dropping the row rejects this local completion claim. | Shared QuickModule user-row parser | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R2 | The exception reports `QuickModule user ID is malformed ... (row=1, field=user_id, value=\uff11\uff12\uff13\uff14\uff15)` with the correct module and site. | Both new regressions assert the diagnostic family, module, site ID, structural row, field, and observed value. | A raw `ValueError`, omitted module/site/row context, omitted field/value, or unrelated parser diagnostic rejects this local completion claim. | QuickModule diagnostics | focused tests |
| R3 | Valid ASCII returned IDs still parse successfully. | Focused GREEN included `test_user_lookup_accepts_zero_user_id`; `tests/unit/test_quick_module.py` passed 116 tests. | Rejecting `"12345"` or `"0"`, changing parsed user IDs, changing result names, or changing valid lookup result shape rejects this local completion claim. | Valid QuickModule parsing | `tests/unit/test_quick_module.py` |
| R4 | Existing non-numeric and negative returned-ID diagnostics stay stable. | Focused GREEN included `test_member_lookup_malformed_user_id_includes_module_site_row_and_value_context`, `test_user_lookup_malformed_user_id_includes_module_site_row_and_value_context`, `test_member_lookup_negative_user_id_includes_module_site_row_and_value_context`, and `test_user_lookup_negative_user_id_includes_module_site_row_and_value_context`. | Accepting `latest`, accepting `-1`, reclassifying negative ASCII values before the non-negative guard, dropping context, or changing direct constructor diagnostics rejects this local completion claim. | Parser compatibility | `tests/unit/test_quick_module.py` |
| R5 | Adjacent identity workflows remain green. | Adjacent QuickModule/Site/SiteMember/User coverage passed 687 tests, and full unit passed 3767 tests. | Regressing request URL construction, retry behavior, response diagnostics, page lookup, member lookup, Site workflows, SiteMember workflows, direct User workflows, or any unit test rejects this local completion claim. | QuickModule and consumers | `tests/unit` |
| R6 | No live site state or private material is needed. | The regressions use mocked QuickModule responses only. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, real QuickModule bodies, raw lookup query text, usernames, private site/member/page data, or private account names rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, QuickModule suite, adjacent suite, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `04a8af2 fix(quickmodule): validate user id ascii shape`.

- RED: `uv run pytest tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_fullwidth_digit_user_id_includes_module_site_row_and_value_context tests/unit/test_quick_module.py::TestQuickModuleUserLookup::test_user_lookup_fullwidth_digit_user_id_includes_module_site_row_and_value_context -q` failed before the fix with two `DID NOT RAISE` failures because returned QuickModule user ID text `\uff11\uff12\uff13\uff14\uff15` was accepted and normalized as `id=12345`.
- GREEN focused QuickModule ID slice: `uv run pytest tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_fullwidth_digit_user_id_includes_module_site_row_and_value_context tests/unit/test_quick_module.py::TestQuickModuleUserLookup::test_user_lookup_fullwidth_digit_user_id_includes_module_site_row_and_value_context tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_malformed_user_id_includes_module_site_row_and_value_context tests/unit/test_quick_module.py::TestQuickModuleUserLookup::test_user_lookup_malformed_user_id_includes_module_site_row_and_value_context tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_negative_user_id_includes_module_site_row_and_value_context tests/unit/test_quick_module.py::TestQuickModuleUserLookup::test_user_lookup_negative_user_id_includes_module_site_row_and_value_context tests/unit/test_quick_module.py::TestQuickModuleUserLookup::test_user_lookup_accepts_zero_user_id -q` passed 7 tests.
- `uv run pytest tests/unit/test_quick_module.py -q` passed 116 tests.
- `uv run pytest tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_user.py -q` passed 687 tests.
- `uv run pytest tests/unit -q` passed 3767 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no parser boundary, compatibility, architecture, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker: `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, local clawpatch commit `59e2dea`, launcher SHA256 `d6726fac4db7531d06c27d38e71e881f5e6360b1536df9a51f72bd8c4913ece1`.

## Acceptance Criteria

- `QuickModule.member_lookup(...)` raises `ValueError("QuickModule user ID is malformed ...")` for a returned member row whose `user_id` is `\uff11\uff12\uff13\uff14\uff15`.
- `QuickModule.user_lookup(...)` raises the same diagnostic family for a returned user row whose `user_id` is `\uff11\uff12\uff13\uff14\uff15`.
- The malformed user-ID diagnostics include the QuickModule name, `site_id=123456`, `row=1`, `field=user_id`, and the observed returned scalar value.
- The parser does not create or return `QMCUser(id=12345, ...)` from non-ASCII digit user-ID metadata.
- Valid ASCII returned IDs such as `"12345"` and `"0"` still parse successfully.
- Existing non-numeric returned IDs such as `latest` still raise the contextual malformed-ID diagnostic.
- Existing negative ASCII returned IDs such as `-1` still raise the contextual negative-ID diagnostic.
- Existing request validation, retry behavior, JSON diagnostics, response-body diagnostics, response-field diagnostics, row-shape diagnostics, row-field diagnostics, text-field validation, blank-name validation, page lookup behavior, Site member lookup, SiteMember behavior, direct User behavior, adjacent workflows, and full unit behavior remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw QuickModule payload from real accounts, raw rollout path, private lookup query, private user/member/page data, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 313. Mitigation: Issue 313 covers values that Python already rejects as non-numeric; this slice covers Unicode decimal digit text that Python accepts.
- Risk: This could be confused with Issue 646. Mitigation: Issue 646 covers negative direct and returned IDs; this slice keeps ASCII negative values parseable so the existing non-negative diagnostic remains intact.
- Risk: This could alter valid QuickModule user lookup behavior. Mitigation: ASCII returned IDs still convert through `int(...)`, valid zero-ID compatibility is preserved, the QuickModule suite passed, and adjacent Site/SiteMember/User coverage remained green.
- Risk: Diagnostics could expose lookup queries or response bodies. Mitigation: the diagnostic includes only module, site ID, row, field, and compact scalar value; tests use synthetic mocked QuickModule responses and do not include raw real responses or query text.

## Dependencies

- QuickModule member and user responses continue to expose returned rows under the `users` key.
- Normal Wikidot QuickModule returned user IDs are expected to use ASCII decimal digits.
- Existing QuickModule parser context continues to identify module, site, row, field, and raw scalar value.
- Existing `QMCUser` constructor validation continues to validate direct record state after parser-side conversion.

## Open Questions

None for this local slice. Future generated scalar-shape changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

QuickModule member/user lookups feed browser-free identity selection, membership checks, moderation tools, migration ledgers, attribution reports, local fixtures, and downstream action preflight. Unicode digit normalization can silently turn malformed returned identity metadata into a valid-looking `QMCUser.id`. Requiring ASCII digits keeps returned identity parsing strict while preserving valid QuickModule rows and established contextual diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED tests demonstrated prior behavior: fullwidth returned QuickModule member/user `user_id` values were accepted and normalized into `id=12345`.
- Existing local drafts covered QuickModule retries, response-shape diagnostics, malformed non-numeric returned IDs, negative returned IDs, direct `QMCUser` constructor validation, result text fields, blank names, request validation, member lookup filters, and adjacent generated scalar ASCII-shape fixes; they did not validate Unicode digit normalization in returned QuickModule user IDs.
- This slice does not change request URLs, site IDs, query validation, retry policy, JSON parsing, response-body validation, result-field validation, row-shape validation, name parsing, page lookup parsing, Site workflows, SiteMember workflows, direct User constructors, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, real QuickModule response bodies, raw lookup query text from real sites, usernames, passwords, private member data, private page data, and private site data out of upstream discussion.

## Additional Notes

This is a parser-boundary validation fix. It preserves valid ASCII QuickModule result behavior while preventing Python's Unicode digit support from manufacturing ordinary user IDs out of malformed remote identity metadata.
