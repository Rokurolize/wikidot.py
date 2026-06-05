# PR Draft: Report Missing QuickModule Row Fields

## Summary

`QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` parse Wikidot QuickModule JSON rows into `QMCUser` and `QMCPage` objects. Earlier local slices now retry transient QuickModule failures, validate missing top-level response keys, and report present malformed `user_id` values with context. One adjacent row-shape gap remained: rows that omitted required fields still leaked raw Python `KeyError` for `user_id`, `name`, `title`, or `unix_name`.

This local slice adds a shared QuickModule row-field accessor and a page row mapper. Missing row fields now raise contextual `ValueError` with module name, site ID, row index, and affected field. The diagnostic intentionally omits the lookup query string and raw response body.

## Outcome

Malformed QuickModule result rows now fail at the row parser boundary with module/site/row/field context instead of raw dictionary-key text.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use QuickModule lookup for browser-free member, user, or page selection in moderation, membership, publishing, attribution, or migration tooling.

## Related Issue

Builds on [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), and [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md). Those drafts established QuickModule lookup as a practical read path, handled malformed present user IDs, and handled missing top-level response keys. Issue 313 and Issue 314 both left missing user names or malformed page rows as separate follow-up boundaries.

No upstream issue was filed from this local workspace.

## Changes

- Add a shared QuickModule row-field accessor.
- Convert missing member row `user_id` fields into contextual `ValueError`.
- Convert missing user row `name` fields into contextual `ValueError`.
- Convert missing page row `title` fields into contextual `ValueError`.
- Convert missing page row `unix_name` fields into contextual `ValueError`.
- Add a dedicated QuickModule page row mapper so page rows can include row index and field context.
- Preserve successful member lookup, user lookup, page lookup, empty member results, missing response-key diagnostics, malformed user ID diagnostics, URL encoding, retry behavior, invalid-module checks, and site-not-found handling.

## Type Of Change

- Bug fix / diagnostics improvement
- QuickModule row-shape parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A member lookup row missing `user_id` must fail at the QuickModule row parser boundary. |
| R2 | A user lookup row missing `name` must fail at the QuickModule row parser boundary. |
| R3 | A page lookup row missing `title` must fail at the QuickModule row parser boundary. |
| R4 | A page lookup row missing `unix_name` must fail at the QuickModule row parser boundary. |
| R5 | The missing-field errors must identify module name, site ID, row index, and affected field, while omitting the raw query string and response body. |
| R6 | Existing QuickModule behavior, Issue 313 malformed-ID diagnostics, Issue 314 response-key diagnostics, adjacent site behavior, and repository quality gates must remain compatible. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `QuickModule.member_lookup(...)` raises contextual `ValueError` when a member row omits `user_id`. | `TestQuickModuleMemberLookup.test_member_lookup_missing_user_id_includes_module_site_row_and_field_context` expects `ValueError`. | Leaking raw `KeyError: 'user_id'`, returning a `QMCUser`, or hiding module/site/row/field context rejects this local completion claim. | `src/wikidot/util/quick_module.py` | `tests/unit/test_quick_module.py` |
| R2 | `QuickModule.user_lookup(...)` raises contextual `ValueError` when a user row omits `name`. | `TestQuickModuleUserLookup.test_user_lookup_missing_name_includes_module_site_row_and_field_context` expects `ValueError`. | Leaking raw `KeyError: 'name'`, returning a user with missing/empty name, or hiding module/site/row/field context rejects this local completion claim. | `src/wikidot/util/quick_module.py` | `tests/unit/test_quick_module.py` |
| R3 | `QuickModule.page_lookup(...)` raises contextual `ValueError` when a page row omits `title`. | `TestQuickModulePageLookup.test_page_lookup_missing_title_includes_module_site_row_and_field_context` expects `ValueError`. | Leaking raw `KeyError: 'title'`, returning a `QMCPage`, or hiding module/site/row/field context rejects this local completion claim. | `src/wikidot/util/quick_module.py` | `tests/unit/test_quick_module.py` |
| R4 | `QuickModule.page_lookup(...)` raises contextual `ValueError` when a page row omits `unix_name`. | `TestQuickModulePageLookup.test_page_lookup_missing_unix_name_includes_module_site_row_and_field_context` expects `ValueError`. | Leaking raw `KeyError: 'unix_name'`, returning a `QMCPage`, or hiding module/site/row/field context rejects this local completion claim. | `src/wikidot/util/quick_module.py` | `tests/unit/test_quick_module.py` |
| R5 | The missing-field error names the QuickModule, `site_id=123456`, `row=1`, and the affected field. | The focused regressions match the full message shape. | Including user-supplied query text or raw response data increases unnecessary disclosure risk. | QuickModule diagnostics | `tests/unit/test_quick_module.py` |
| R6 | Existing QuickModule and adjacent site behavior remains green. | The QuickModule file passed 23 tests and the adjacent QuickModule/site run passed 105 tests. | Regressing URL encoding, transient retry, empty member results, missing response-key diagnostics, malformed user ID diagnostics, page lookup, invalid module handling, site-not-found handling, or site workflows rejects this local completion claim. | QuickModule/site workflows | `tests/unit/test_quick_module.py`; `tests/unit/test_site.py` |

## Testing

Implemented locally in commit `79b85b6 fix(quick_module): report missing row fields`.

- RED: `uv run --extra test pytest tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_missing_user_id_includes_module_site_row_and_field_context tests/unit/test_quick_module.py::TestQuickModuleUserLookup::test_user_lookup_missing_name_includes_module_site_row_and_field_context tests/unit/test_quick_module.py::TestQuickModulePageLookup::test_page_lookup_missing_title_includes_module_site_row_and_field_context tests/unit/test_quick_module.py::TestQuickModulePageLookup::test_page_lookup_missing_unix_name_includes_module_site_row_and_field_context -q` failed before the fix with raw `KeyError: 'user_id'`, `KeyError: 'name'`, `KeyError: 'title'`, and `KeyError: 'unix_name'`.
- GREEN: `uv run --extra test pytest tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_missing_user_id_includes_module_site_row_and_field_context tests/unit/test_quick_module.py::TestQuickModuleUserLookup::test_user_lookup_missing_name_includes_module_site_row_and_field_context tests/unit/test_quick_module.py::TestQuickModulePageLookup::test_page_lookup_missing_title_includes_module_site_row_and_field_context tests/unit/test_quick_module.py::TestQuickModulePageLookup::test_page_lookup_missing_unix_name_includes_module_site_row_and_field_context -q` passed 4 tests.
- `uv run --extra test pytest tests/unit/test_quick_module.py -q` passed 23 tests.
- `uv run --extra test pytest tests/unit/test_quick_module.py tests/unit/test_site.py -q` passed 105 tests.
- `uv run --extra test pytest tests/unit -q` passed 878 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 80 files already formatted after formatting `src/wikidot/util/quick_module.py`.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- `QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` still request the same QuickModule endpoints.
- Missing required member/user/page row fields raise contextual `ValueError`.
- The missing-field message includes module, site ID, row index, and affected field.
- The missing-field message does not include the raw lookup query string or raw response body.
- Empty member results, successful lookups, Issue 313 malformed user ID diagnostics, Issue 314 response-key diagnostics, invalid-module checks, site-not-found handling, URL encoding, and retry behavior remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real QuickModule response body, credentials, cookies, auth JSON, local rollout paths, or private query data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Reworking page row mapping could regress valid page lookup output. Mitigation: the QuickModule file and adjacent site suite remained green.
- Risk: Treating missing row fields as contextual errors could expose lookup query text. Mitigation: the diagnostic reports module, site, row, and field only.
- Risk: Missing-row-field handling could interfere with Issue 313 malformed-ID handling. Mitigation: malformed present `user_id` still runs after the field is retrieved and remains covered by QuickModule tests.

## Dependencies

- Valid QuickModule member and user rows expose `user_id` and `name`.
- Valid QuickModule page rows expose `title` and `unix_name`.
- `MemberLookupQModule` may still represent an empty result as `users: false`.

## Open Questions

None for this local slice. Non-list response values or non-mapping row objects remain separate response-shape boundaries if concrete rollout evidence selects them.

## Upstream-Safe Motivation

QuickModule lookup is useful for resolving Wikidot users, members, and pages without browser automation. If a result row omits a required field, wikidot.py should report which lookup module, site, row, and field failed instead of surfacing an uncontextualized Python `KeyError`. Omitting query text and raw response data keeps the diagnostic actionable without exposing unnecessary private context.

## Local Evidence, Not For Upstream Paste

- The immediate RED failure showed member, user, and page QuickModule row parsing leaking raw `KeyError` for required fields.
- Issue 313 and Issue 314 explicitly left missing names and malformed page rows as separate follow-up boundaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, real QuickModule response bodies, raw lookup query text, and private user/member/page data out of upstream discussion.

## Additional Notes

This is a row-shape diagnostics fix. It preserves valid QuickModule behavior while making missing required row fields actionable in logs that cannot retain raw response bodies.
