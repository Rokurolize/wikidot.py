# PR Draft: Report Missing QuickModule Response Keys

## Summary

`QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` parse Wikidot QuickModule JSON by indexing the expected top-level response key directly. If Wikidot returns a successful HTTP response that omits `users` or `pages`, the lookup previously leaked a raw Python `KeyError` such as `KeyError: 'users'` without the QuickModule name, site ID, or affected response field.

This local slice adds a shared response-key accessor for QuickModule lookups. Missing top-level response keys now raise contextual `ValueError` with module name, site ID, and `field=<response_key>`. The diagnostic intentionally omits the lookup query string and raw response body.

## Outcome

Malformed QuickModule response shape now fails at the QuickModule parser boundary with module/site/field context instead of raw dictionary-key text.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use QuickModule lookup for browser-free member, user, or page selection in moderation, membership, publishing, attribution, or migration tooling.

## Related Issue

Builds on [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), which made QuickModule lookups retry transient 5xx responses before treating the lookup as failed. This is the follow-up response-shape boundary left open by [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), which handled present malformed member/user `user_id` values but intentionally left missing response keys for a separate slice.

No upstream issue was filed from this local workspace.

## Changes

- Add one shared QuickModule response-key accessor.
- Convert missing `users` in `MemberLookupQModule` responses into contextual `ValueError`.
- Convert missing `users` in `UserLookupQModule` responses into contextual `ValueError`.
- Convert missing `pages` in `PageLookupQModule` responses into contextual `ValueError`.
- Include module name, site ID, and affected response field in the missing-key diagnostic.
- Keep the lookup query string and raw response body out of the error message.
- Preserve successful member lookup, successful user lookup, page lookup, empty member results, malformed user ID handling, request URL encoding, retry behavior, invalid-module checks, and site-not-found handling.

## Type Of Change

- Bug fix / diagnostics improvement
- QuickModule response-shape parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A `MemberLookupQModule` response missing `users` must fail at the QuickModule response parser boundary. |
| R2 | A `UserLookupQModule` response missing `users` must fail at the QuickModule response parser boundary. |
| R3 | A `PageLookupQModule` response missing `pages` must fail at the QuickModule response parser boundary. |
| R4 | The missing-key errors must identify module name, site ID, and affected response field, while omitting the raw query string and response body. |
| R5 | Successful lookup behavior, empty member results, malformed user ID diagnostics, retry behavior, URL encoding, invalid-module checks, site-not-found handling, and repository quality gates must remain compatible. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `QuickModule.member_lookup(...)` raises contextual `ValueError` when `users` is absent. | `TestQuickModuleMemberLookup.test_member_lookup_missing_users_key_includes_module_site_and_field_context` expects `ValueError`. | Leaking raw `KeyError: 'users'`, returning an empty list, or hiding module/site/field context rejects this local completion claim. | `src/wikidot/util/quick_module.py` | `tests/unit/test_quick_module.py` |
| R2 | `QuickModule.user_lookup(...)` raises contextual `ValueError` when `users` is absent. | `TestQuickModuleUserLookup.test_user_lookup_missing_users_key_includes_module_site_and_field_context` expects `ValueError`. | Leaking raw `KeyError: 'users'`, returning an empty list, or hiding module/site/field context rejects this local completion claim. | `src/wikidot/util/quick_module.py` | `tests/unit/test_quick_module.py` |
| R3 | `QuickModule.page_lookup(...)` raises contextual `ValueError` when `pages` is absent. | `TestQuickModulePageLookup.test_page_lookup_missing_pages_key_includes_module_site_and_field_context` expects `ValueError`. | Leaking raw `KeyError: 'pages'`, returning an empty list, or hiding module/site/field context rejects this local completion claim. | `src/wikidot/util/quick_module.py` | `tests/unit/test_quick_module.py` |
| R4 | The error names the QuickModule, `site_id=123456`, and `field=users` or `field=pages`; it does not include raw query text or raw response data. | The focused regressions match the full message shape. | Including user-supplied query text or raw response data increases unnecessary disclosure risk. | QuickModule diagnostics | `tests/unit/test_quick_module.py` |
| R5 | Existing QuickModule and adjacent site behavior remains green. | The QuickModule file passed 19 tests and the adjacent QuickModule/site run passed 101 tests. | Regressing URL encoding, transient retry, empty member results, malformed user ID diagnostics, page lookup, invalid module handling, site-not-found handling, or site workflows rejects this local completion claim. | QuickModule/site workflows | `tests/unit/test_quick_module.py`; `tests/unit/test_site.py` |

## Testing

Implemented locally in commit `16ffe75 fix(quick_module): report missing response keys`.

- RED: `uv run --extra test pytest tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_missing_users_key_includes_module_site_and_field_context tests/unit/test_quick_module.py::TestQuickModuleUserLookup::test_user_lookup_missing_users_key_includes_module_site_and_field_context tests/unit/test_quick_module.py::TestQuickModulePageLookup::test_page_lookup_missing_pages_key_includes_module_site_and_field_context -q` failed before the fix with raw `KeyError: 'users'` and `KeyError: 'pages'`.
- GREEN: `uv run --extra test pytest tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_missing_users_key_includes_module_site_and_field_context tests/unit/test_quick_module.py::TestQuickModuleUserLookup::test_user_lookup_missing_users_key_includes_module_site_and_field_context tests/unit/test_quick_module.py::TestQuickModulePageLookup::test_page_lookup_missing_pages_key_includes_module_site_and_field_context -q` passed 3 tests.
- `uv run --extra test pytest tests/unit/test_quick_module.py -q` passed 19 tests.
- `uv run --extra test pytest tests/unit/test_quick_module.py tests/unit/test_site.py -q` passed 101 tests.
- `uv run --extra test pytest tests/unit -q` passed 874 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- `QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` still request the same QuickModule endpoints.
- Missing `users` in member lookup raises contextual `ValueError`.
- Missing `users` in user lookup raises contextual `ValueError`.
- Missing `pages` in page lookup raises contextual `ValueError`.
- The missing-key message includes module, site ID, and affected field.
- The missing-key message does not include the raw lookup query string or raw response body.
- Empty member results, successful lookups, Issue 313 malformed user ID diagnostics, invalid-module checks, site-not-found handling, URL encoding, and retry behavior remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real QuickModule response body, credentials, cookies, auth JSON, local rollout paths, or private query data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Treating all falsey values as missing keys could change valid empty member results. Mitigation: the new helper only checks key presence; existing `users is False` empty-member handling remains unchanged.
- Risk: Adding context could expose user-supplied lookup text or raw Wikidot response data. Mitigation: the diagnostic reports module, site, and field only.
- Risk: Refactoring response access could disturb page lookup or Issue 313 user ID handling. Mitigation: focused QuickModule tests, adjacent site tests, and the full unit suite remained green.

## Dependencies

- QuickModule member and user responses are expected to expose rows under the `users` key.
- QuickModule page responses are expected to expose rows under the `pages` key.
- `MemberLookupQModule` may still represent an empty result as `users: false`.

## Open Questions

None for this local slice. Missing user names or malformed QuickModule page rows remain separate follow-up boundaries if concrete rollout evidence selects them.

## Upstream-Safe Motivation

QuickModule lookup is useful precisely because it lets operators resolve Wikidot users, members, and pages without browser automation. If Wikidot returns a response that lacks the expected top-level result key, wikidot.py should report which QuickModule, site, and field failed instead of surfacing an uncontextualized Python `KeyError`. Omitting query text and raw response data keeps the diagnostic actionable without exposing unnecessary private context.

## Local Evidence, Not For Upstream Paste

- The immediate RED failure showed member, user, and page QuickModule lookup paths leaking raw `KeyError` for missing top-level result keys.
- The fix reuses one response-key accessor for both the generic page path and the member/user path from Issue 313.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, real QuickModule response bodies, raw lookup query text, and private user/member data out of upstream discussion.

## Additional Notes

This is a response-shape diagnostics fix. It preserves valid QuickModule behavior while making missing result keys actionable in logs that cannot retain raw response bodies.
