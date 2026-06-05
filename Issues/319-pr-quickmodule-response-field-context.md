# PR Draft: Report Malformed QuickModule Response Fields

## Summary

`QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` parse Wikidot QuickModule JSON by reading a top-level `users` or `pages` field and then iterating result rows. Earlier local slices now retry transient QuickModule failures, report missing top-level response keys, report missing required row fields, report non-mapping result rows, and report present malformed `user_id` values with context. One adjacent response-shape gap remained: a present `users` or `pages` field could be an object or scalar instead of a list. After the row-shape guard, that condition was still misreported as a malformed row because iterating a dictionary yields its keys.

This local slice validates the top-level QuickModule result field before row iteration. Present non-list result fields now raise contextual `ValueError` with module name, site ID, affected response field, expected type, and observed type. The diagnostic intentionally omits the lookup query string and raw response body.

## Outcome

Malformed QuickModule result fields now fail at the response parser boundary with module/site/field/type context instead of being misreported as row-shape failures.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use QuickModule lookup for browser-free member, user, or page selection in moderation, membership, publishing, attribution, or migration tooling.

## Related Issue

Builds on [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md), and [318-pr-quickmodule-row-shape-context.md](318-pr-quickmodule-row-shape-context.md). Those drafts established QuickModule lookup as a practical read path and handled missing keys, malformed row fields, malformed row objects, and malformed user IDs. Issue 318 explicitly left non-list top-level result values as a separate response-shape boundary.

No upstream issue was filed from this local workspace.

## Changes

- Validate the present `users` or `pages` response field before row iteration.
- Convert non-list member/user result fields into contextual `ValueError`.
- Convert non-list page result fields into contextual `ValueError`.
- Preserve the existing `false` empty-result sentinel by normalizing it to an empty list before iteration.
- Preserve successful member lookup, user lookup, page lookup, empty member/user results, missing response-key diagnostics, row-shape diagnostics, missing row-field diagnostics, malformed user ID diagnostics, URL encoding, retry behavior, invalid-module checks, and site-not-found handling.

## Type Of Change

- Bug fix / diagnostics improvement
- QuickModule response-shape parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A present member/user `users` field that is neither `false` nor a list must fail at the QuickModule response parser boundary. |
| R2 | A present page `pages` field that is neither `false` nor a list must fail at the QuickModule response parser boundary. |
| R3 | The malformed-field errors must identify module name, site ID, affected response field, expected type, and observed type, while omitting the raw query string and response body. |
| R4 | Existing QuickModule behavior, Issue 313 malformed-ID diagnostics, Issue 314 response-key diagnostics, Issue 315 row-field diagnostics, Issue 318 row-shape diagnostics, adjacent site behavior, and repository quality gates must remain compatible. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `QuickModule.member_lookup(...)` raises contextual `ValueError` when `users` is an object. `QuickModule.user_lookup(...)` uses the same member/user result-field parser. | `TestQuickModuleMemberLookup.test_member_lookup_malformed_users_field_includes_module_site_field_and_type_context` expects `ValueError`. | Misreporting the object as row `user_id`, leaking a raw Python error, returning a `QMCUser`, or hiding module/site/field/type context rejects this local completion claim. | `src/wikidot/util/quick_module.py` | `tests/unit/test_quick_module.py` |
| R2 | `QuickModule.page_lookup(...)` raises contextual `ValueError` when `pages` is an object. | `TestQuickModulePageLookup.test_page_lookup_malformed_pages_field_includes_module_site_field_and_type_context` expects `ValueError`. | Misreporting the object as row `title`, leaking a raw Python error, returning a `QMCPage`, or hiding module/site/field/type context rejects this local completion claim. | `src/wikidot/util/quick_module.py` | `tests/unit/test_quick_module.py` |
| R3 | The malformed-field error names the QuickModule, `site_id=123456`, `field=users` or `field=pages`, `expected=list`, and `actual=dict`. | The focused regressions match the full message shape. | Including user-supplied query text or raw response data increases unnecessary disclosure risk. | QuickModule diagnostics | `tests/unit/test_quick_module.py` |
| R4 | Existing QuickModule and adjacent site behavior remains green. | The QuickModule file passed 27 tests and the adjacent QuickModule/site run passed 109 tests. | Regressing URL encoding, transient retry, empty member/user results, missing response-key diagnostics, row-shape diagnostics, row-field diagnostics, malformed user ID diagnostics, page lookup, invalid module handling, site-not-found handling, or site workflows rejects this local completion claim. | QuickModule/site workflows | `tests/unit/test_quick_module.py`; `tests/unit/test_site.py` |

## Testing

Implemented locally in commit `6d2ce8f fix(quick_module): report malformed result fields`.

- RED: `uv run --extra test pytest tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_malformed_users_field_includes_module_site_field_and_type_context tests/unit/test_quick_module.py::TestQuickModulePageLookup::test_page_lookup_malformed_pages_field_includes_module_site_field_and_type_context -q` failed before the fix by misreporting dict response fields as malformed string rows.
- GREEN: `uv run --extra test pytest tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_malformed_users_field_includes_module_site_field_and_type_context tests/unit/test_quick_module.py::TestQuickModulePageLookup::test_page_lookup_malformed_pages_field_includes_module_site_field_and_type_context -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_quick_module.py -q` passed 27 tests.
- `uv run --extra test pytest tests/unit/test_quick_module.py tests/unit/test_site.py -q` passed 109 tests.
- `uv run --extra test pytest tests/unit -q` passed 884 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- `QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` still request the same QuickModule endpoints.
- Present non-list `users` and `pages` fields raise contextual `ValueError`.
- `users: false` remains an accepted empty result sentinel.
- The malformed-field message includes module name, site ID, affected response field, expected type, and observed type.
- The malformed-field message does not include the raw lookup query string or raw response body.
- Empty member/user results, successful lookups, Issue 313 malformed user ID diagnostics, Issue 314 response-key diagnostics, Issue 315 row-field diagnostics, Issue 318 row-shape diagnostics, invalid-module checks, site-not-found handling, URL encoding, and retry behavior remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real QuickModule response body, local rollout paths, private account material, or private query data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Tightening response-field validation could reject the known empty-result sentinel. Mitigation: `false` is normalized to an empty list before the list check, and existing empty-result tests remained green.
- Risk: Response-field diagnostics could interfere with row-shape diagnostics. Mitigation: only the top-level result field is checked here; list values still proceed to the row-shape and row-field checks from earlier slices.
- Risk: Adding response-field context could expose lookup text. Mitigation: the diagnostic reports module, site, field, and type only.

## Dependencies

- Valid QuickModule member and user result fields are `false` or a list of row objects.
- Valid QuickModule page result fields are a list of row objects, with `false` still tolerated as an empty result sentinel by the shared accessor.
- Row objects remain validated by Issue 318 and required fields remain validated by Issue 315.

## Open Questions

None for this local slice. A broader JSON-root shape check remains a separate boundary if concrete rollout evidence selects it.

## Upstream-Safe Motivation

QuickModule lookup is useful for resolving Wikidot users, members, and pages without browser automation. If the result field itself is not iterable row data, wikidot.py should report which lookup module, site, field, and type failed instead of making maintainers infer that from a downstream row parser message. Omitting query text and raw response data keeps the diagnostic actionable without exposing unnecessary private context.

## Local Evidence, Not For Upstream Paste

- The immediate RED failure showed present object-valued `users` and `pages` fields being misreported as malformed string rows.
- Issue 318 explicitly left non-list top-level result values as a separate response-shape boundary.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, real QuickModule response bodies, raw lookup query text, and private user/member/page data out of upstream discussion.

## Additional Notes

This is a response-field diagnostics fix. It preserves valid QuickModule behavior while making malformed top-level result fields actionable in logs that cannot retain raw response bodies.
