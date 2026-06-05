# PR Draft: Report Malformed QuickModule User IDs

## Summary

`QuickModule.member_lookup(...)` and `QuickModule.user_lookup(...)` parse Wikidot QuickModule JSON rows into `QMCUser` objects. Earlier local slices made QuickModule requests retry-aware, but the returned `user_id` fields still used direct `int(item["user_id"])` conversion inside duplicated lambdas. If Wikidot returned a present non-numeric value such as `latest`, the lookup leaked raw Python `ValueError: invalid literal for int()` without the QuickModule name, site ID, result row, affected field, or observed value.

This local slice keeps request construction, retry behavior, invalid-module handling, site-not-found handling, empty member results, successful member lookup, successful user lookup, page lookup, `QMCUser`, and `QMCPage` behavior unchanged. It routes member/user row parsing through one shared mapper and raises `ValueError` with module name, site ID, row index, `field=user_id`, and the observed malformed value when a present `user_id` cannot be converted to an integer. The diagnostic intentionally omits the original query string.

## Outcome

Malformed QuickModule member/user `user_id` values now fail with module/site/row/value context instead of raw integer-conversion text.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use QuickModule lookup for browser-free member or user selection in moderation, membership, invitation, attribution, or migration tooling.

## Related Issue

Builds on [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), which made QuickModule lookups retry transient 5xx responses before treating the lookup as failed. This slice also follows the scalar parser-boundary pattern from [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md), [302-pr-regular-user-href-validation.md](302-pr-regular-user-href-validation.md), [308-pr-site-application-user-context.md](308-pr-site-application-user-context.md), [310-pr-site-id-context.md](310-pr-site-id-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), and [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a shared QuickModule user-row mapper for member and user lookup rows.
- Convert present malformed `user_id` values into contextual `ValueError`.
- Include module name, site ID, row index, `field=user_id`, and observed scalar value in the malformed-ID diagnostic.
- Keep the original lookup query out of the error message.
- Preserve empty `MemberLookupQModule` results that return `users: false`.
- Preserve successful member lookup, successful user lookup, page lookup, invalid-module checks, site-not-found handling, URL encoding, and retry behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- QuickModule scalar parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A QuickModule member lookup row with a present non-numeric `user_id` must fail at the QuickModule row parser boundary. |
| R2 | A QuickModule user lookup row with a present non-numeric `user_id` must fail at the QuickModule row parser boundary. |
| R3 | The malformed-ID errors must identify module name, site ID, row index, affected field, and observed value, while omitting the raw query string. |
| R4 | Successful member lookup, user lookup, page lookup, empty member results, request URL encoding, retry behavior, invalid-module checks, and site-not-found handling must remain compatible. |
| R5 | Focused, QuickModule-level, adjacent site/QuickModule, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `QuickModule.member_lookup(...)` raises contextual `ValueError` for `{"user_id": "latest"}`. | `TestQuickModuleMemberLookup.test_member_lookup_malformed_user_id_includes_module_site_row_and_value_context` expects `ValueError`. | Leaking raw `ValueError: invalid literal`, returning a `QMCUser`, or hiding the observed value rejects this local completion claim. | `src/wikidot/util/quick_module.py` | `tests/unit/test_quick_module.py` |
| R2 | `QuickModule.user_lookup(...)` raises contextual `ValueError` for `{"user_id": "latest"}`. | `TestQuickModuleUserLookup.test_user_lookup_malformed_user_id_includes_module_site_row_and_value_context` expects `ValueError`. | Leaking raw integer-conversion text, silently coercing the value, or returning a `QMCUser` rejects this local completion claim. | `src/wikidot/util/quick_module.py` | `tests/unit/test_quick_module.py` |
| R3 | The error names the QuickModule, `site_id=123456`, `row=1`, `field=user_id`, and `value=latest`, and does not include the lookup query. | The focused regressions match the full message shape. | Omitting module, site, row, field, or value makes the failure ambiguous; including user query text increases unnecessary disclosure risk. | QuickModule diagnostics | `tests/unit/test_quick_module.py` |
| R4 | Existing QuickModule and adjacent site behavior remains green. | The QuickModule file passed 16 tests and the adjacent QuickModule/site run passed 98 tests. | Regressing URL encoding, transient retry, empty member results, page lookup, invalid module handling, site-not-found handling, or site workflows rejects this local completion claim. | QuickModule/site workflows | `tests/unit/test_quick_module.py`; `tests/unit/test_site.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `53280a5 fix(quick_module): report malformed user ids`.

- RED: `uv run --extra test pytest tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_malformed_user_id_includes_module_site_row_and_value_context tests/unit/test_quick_module.py::TestQuickModuleUserLookup::test_user_lookup_malformed_user_id_includes_module_site_row_and_value_context -q` failed before the fix with raw `ValueError: invalid literal for int() with base 10: 'latest'`.
- GREEN: `uv run --extra test pytest tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_malformed_user_id_includes_module_site_row_and_value_context tests/unit/test_quick_module.py::TestQuickModuleUserLookup::test_user_lookup_malformed_user_id_includes_module_site_row_and_value_context -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_quick_module.py -q` passed 16 tests.
- `uv run --extra test pytest tests/unit/test_quick_module.py tests/unit/test_site.py -q` passed 98 tests.
- `uv run --extra test pytest tests/unit -q` passed 871 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- `QuickModule.member_lookup(...)` and `QuickModule.user_lookup(...)` still request the same QuickModule endpoints.
- A present malformed member/user `user_id` value raises contextual `ValueError`.
- The malformed `user_id` message includes module, site ID, row index, `field=user_id`, and observed value.
- The malformed `user_id` message does not include the raw lookup query string.
- Empty member results, successful member lookup, successful user lookup, page lookup, invalid-module checks, site-not-found handling, URL encoding, and retry behavior remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real QuickModule response body, credentials, cookies, auth JSON, local rollout paths, or private query data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Adding context could expose user-supplied lookup text. Mitigation: the diagnostic reports module/site/row/value only and intentionally omits the query string.
- Risk: Refactoring duplicated lambdas could change valid lookup output. Mitigation: the full QuickModule suite and adjacent site suite remained green.
- Risk: Treating QuickModule diagnostics as a broad response-shape rewrite could change too much at once. Mitigation: this slice only wraps malformed present `user_id` scalar conversion and leaves missing response keys, missing names, page rows, and request handling unchanged.

## Dependencies

- QuickModule member and user responses continue to expose rows under the `users` key.
- Valid member and user rows continue to expose integer-compatible `user_id` values and `name` values.
- `MemberLookupQModule` may still represent an empty result as `users: false`.

## Open Questions

None for this local slice. Missing QuickModule response keys, missing user names, or malformed page rows should remain separate follow-up boundaries if concrete rollout evidence selects them.

## Upstream-Safe Motivation

QuickModule lookup is a small but practical browser-free helper for resolving users and members. If Wikidot emits a user row with a malformed scalar ID, wikidot.py should report which lookup module, site, row, field, and value failed instead of forcing operators to infer the context from a raw Python conversion exception. Omitting the query string keeps the diagnostic useful without exposing unnecessary user-supplied lookup text.

## Local Evidence, Not For Upstream Paste

- Earlier local QuickModule work established lookup retries as practical because transient QuickModule failures can affect member/user/page selection.
- The immediate RED failure showed both member and user lookup paths leaking raw `ValueError: invalid literal for int() with base 10: 'latest'`.
- The fix reuses one mapper for both duplicated user-row paths and leaves page lookup on the existing generic mapper.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, real QuickModule response bodies, raw lookup query text, and private user/member data out of upstream discussion.

## Additional Notes

This is a parser diagnostics fix. It preserves valid QuickModule behavior while making malformed member/user IDs actionable in logs that cannot retain raw response bodies.
