# PR Draft: Report Malformed QuickModule Row Shapes

## Summary

`QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` parse Wikidot QuickModule JSON result rows into `QMCUser` and `QMCPage` objects. Earlier local slices now retry transient QuickModule failures, report missing top-level response keys, report missing required row fields, and report present malformed `user_id` values with context. One adjacent row-shape gap remained: a result array could contain a non-mapping row value. If that value happened to contain the expected field name as text, the row parser leaked raw Python `TypeError: string indices must be integers, not 'str'` instead of a QuickModule parser diagnostic.

This local slice adds a shared row-shape guard before QuickModule row-field lookup. Non-mapping result rows now raise contextual `ValueError` with module name, site ID, row index, expected row type, and observed row type. The diagnostic intentionally omits the lookup query string and raw response body.

## Outcome

Malformed QuickModule result rows now fail at the QuickModule row parser boundary with module/site/row/type context instead of raw Python string-indexing text.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use QuickModule lookup for browser-free member, user, or page selection in moderation, membership, publishing, attribution, or migration tooling.

## Related Issue

Builds on [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), and [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md). Those drafts established QuickModule lookup as a practical read path, handled malformed present user IDs, handled missing top-level response keys, and handled missing row fields. Issue 315 explicitly left non-mapping row objects as a separate response-shape boundary.

No upstream issue was filed from this local workspace.

## Changes

- Validate QuickModule row shape before looking up required row fields.
- Convert non-mapping member/user rows into contextual `ValueError`.
- Convert non-mapping page rows into contextual `ValueError`.
- Include module name, site ID, row index, expected row type, and observed row type in the row-shape diagnostic.
- Preserve successful member lookup, user lookup, page lookup, empty member results, missing response-key diagnostics, missing row-field diagnostics, malformed user ID diagnostics, URL encoding, retry behavior, invalid-module checks, and site-not-found handling.

## Type Of Change

- Bug fix / diagnostics improvement
- QuickModule row-shape parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A member/user lookup result row that is not a mapping must fail at the QuickModule row parser boundary. |
| R2 | A page lookup result row that is not a mapping must fail at the QuickModule row parser boundary. |
| R3 | The malformed-row errors must identify module name, site ID, row index, expected row type, and observed row type, while omitting the raw query string and response body. |
| R4 | Existing QuickModule behavior, Issue 313 malformed-ID diagnostics, Issue 314 response-key diagnostics, Issue 315 row-field diagnostics, adjacent site behavior, and repository quality gates must remain compatible. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `QuickModule.member_lookup(...)` raises contextual `ValueError` when a user row is not a mapping. `QuickModule.user_lookup(...)` uses the same member/user row parser. | `TestQuickModuleMemberLookup.test_member_lookup_malformed_row_includes_module_site_row_and_type_context` expects `ValueError`. | Leaking raw `TypeError`, returning a `QMCUser`, treating the text as an empty row, or hiding module/site/row/type context rejects this local completion claim. | `src/wikidot/util/quick_module.py` | `tests/unit/test_quick_module.py` |
| R2 | `QuickModule.page_lookup(...)` raises contextual `ValueError` when a page row is not a mapping. | `TestQuickModulePageLookup.test_page_lookup_malformed_row_includes_module_site_row_and_type_context` expects `ValueError`. | Leaking raw `TypeError`, returning a `QMCPage`, treating the text as a missing field, or hiding module/site/row/type context rejects this local completion claim. | `src/wikidot/util/quick_module.py` | `tests/unit/test_quick_module.py` |
| R3 | The malformed-row error names the QuickModule, `site_id=123456`, `row=1`, `expected=dict`, and `actual=str`. | The focused regressions match the full message shape. | Including user-supplied query text or raw response data increases unnecessary disclosure risk. | QuickModule diagnostics | `tests/unit/test_quick_module.py` |
| R4 | Existing QuickModule and adjacent site behavior remains green. | The QuickModule file passed 25 tests and the adjacent QuickModule/site run passed 107 tests. | Regressing URL encoding, transient retry, empty member results, missing response-key diagnostics, missing row-field diagnostics, malformed user ID diagnostics, page lookup, invalid module handling, site-not-found handling, or site workflows rejects this local completion claim. | QuickModule/site workflows | `tests/unit/test_quick_module.py`; `tests/unit/test_site.py` |

## Testing

Implemented locally in commit `c31f5e5 fix(quick_module): report malformed rows`.

- RED: `uv run --extra test pytest tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_malformed_row_includes_module_site_row_and_type_context tests/unit/test_quick_module.py::TestQuickModulePageLookup::test_page_lookup_malformed_row_includes_module_site_row_and_type_context -q` failed before the fix with raw `TypeError: string indices must be integers, not 'str'`.
- GREEN: `uv run --extra test pytest tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_malformed_row_includes_module_site_row_and_type_context tests/unit/test_quick_module.py::TestQuickModulePageLookup::test_page_lookup_malformed_row_includes_module_site_row_and_type_context -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_quick_module.py -q` passed 25 tests.
- `uv run --extra test pytest tests/unit/test_quick_module.py tests/unit/test_site.py -q` passed 107 tests.
- `uv run --extra test pytest tests/unit -q` passed 882 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- `QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` still request the same QuickModule endpoints.
- Non-mapping member/user/page rows raise contextual `ValueError`.
- The malformed-row message includes module name, site ID, row index, expected row type, and observed row type.
- The malformed-row message does not include the raw lookup query string or raw response body.
- Empty member results, successful lookups, Issue 313 malformed user ID diagnostics, Issue 314 response-key diagnostics, Issue 315 row-field diagnostics, invalid-module checks, site-not-found handling, URL encoding, and retry behavior remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real QuickModule response body, local rollout paths, private account material, or private query data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Treating row-shape validation as a broad QuickModule response rewrite could change too much at once. Mitigation: this slice only validates individual result row objects at the existing row-field boundary.
- Risk: Row-shape diagnostics could interfere with missing-field diagnostics. Mitigation: mapping rows still proceed to the existing field check, and the QuickModule suite remained green.
- Risk: Adding row-shape context could expose lookup text. Mitigation: the diagnostic reports module, site, row, and type only.

## Dependencies

- Valid QuickModule member and user rows are mapping objects with `user_id` and `name`.
- Valid QuickModule page rows are mapping objects with `title` and `unix_name`.
- `MemberLookupQModule` may still represent an empty result as `users: false`.

## Open Questions

None for this local slice. Non-list top-level result values remain a separate response-shape boundary if concrete rollout evidence selects them.

## Upstream-Safe Motivation

QuickModule lookup is useful for resolving Wikidot users, members, and pages without browser automation. If a result row is not an object, wikidot.py should report which lookup module, site, row, and type failed instead of surfacing raw Python string-indexing text. Omitting query text and raw response data keeps the diagnostic actionable without exposing unnecessary private context.

## Local Evidence, Not For Upstream Paste

- The immediate RED failure showed member/user and page QuickModule row parsing leaking raw `TypeError` for string rows that contain the expected field name.
- Issue 315 explicitly left non-mapping row objects as a separate response-shape boundary.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, real QuickModule response bodies, raw lookup query text, and private user/member/page data out of upstream discussion.

## Additional Notes

This is a row-shape diagnostics fix. It preserves valid QuickModule behavior while making malformed result rows actionable in logs that cannot retain raw response bodies.
