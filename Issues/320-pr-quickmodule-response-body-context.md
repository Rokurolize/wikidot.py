# PR Draft: Report Malformed QuickModule Response Bodies

## Summary

`QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` parse Wikidot QuickModule JSON by reading a dictionary-like response body, selecting a top-level `users` or `pages` field, and then iterating result rows. Earlier local slices now retry transient QuickModule failures, report missing top-level response keys, report malformed result fields, report non-mapping result rows, report missing required row fields, and report present malformed `user_id` values with context. One adjacent response-shape gap remained: if the JSON root itself was a string or list, the parser could leak raw Python string/list indexing errors before any QuickModule diagnostic was raised.

This local slice validates the QuickModule JSON root before key lookup. Non-dictionary response bodies now raise contextual `ValueError` with module name, site ID, expected root type, and observed root type. The diagnostic intentionally omits the lookup query string and raw response body.

## Outcome

Malformed QuickModule response bodies now fail at the response parser boundary with module/site/type context instead of raw Python container-indexing text.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use QuickModule lookup for browser-free member, user, or page selection in moderation, membership, publishing, attribution, or migration tooling.

## Related Issue

Builds on [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md), [318-pr-quickmodule-row-shape-context.md](318-pr-quickmodule-row-shape-context.md), and [319-pr-quickmodule-response-field-context.md](319-pr-quickmodule-response-field-context.md). Those drafts covered adjacent QuickModule parser boundaries while leaving the response root shape as a separate final boundary.

No upstream issue was filed from this local workspace.

## Changes

- Validate the QuickModule response body is a dictionary before checking result keys.
- Convert non-dictionary member/user response bodies into contextual `ValueError`.
- Convert non-dictionary page response bodies into contextual `ValueError`.
- Preserve successful member lookup, user lookup, page lookup, empty member/user results, missing response-key diagnostics, malformed response-field diagnostics, row-shape diagnostics, missing row-field diagnostics, malformed user ID diagnostics, URL encoding, retry behavior, invalid-module checks, and site-not-found handling.

## Type Of Change

- Bug fix / diagnostics improvement
- QuickModule response-shape parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A member/user lookup response body that is not a dictionary must fail at the QuickModule response parser boundary. |
| R2 | A page lookup response body that is not a dictionary must fail at the QuickModule response parser boundary. |
| R3 | The malformed-body errors must identify module name, site ID, expected root type, and observed root type, while omitting the raw query string and response body. |
| R4 | Existing QuickModule behavior, Issues 313/314/315/318/319 diagnostics, adjacent site behavior, and repository quality gates must remain compatible. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `QuickModule.member_lookup(...)` raises contextual `ValueError` when the response body is a string. `QuickModule.user_lookup(...)` uses the same member/user response parser. | `TestQuickModuleMemberLookup.test_member_lookup_malformed_response_body_includes_module_site_and_type_context` expects `ValueError`. | Leaking raw string-indexing text, returning a `QMCUser`, or hiding module/site/type context rejects this local completion claim. | `src/wikidot/util/quick_module.py` | `tests/unit/test_quick_module.py` |
| R2 | `QuickModule.page_lookup(...)` raises contextual `ValueError` when the response body is a list. | `TestQuickModulePageLookup.test_page_lookup_malformed_response_body_includes_module_site_and_type_context` expects `ValueError`. | Leaking raw list-indexing text, returning a `QMCPage`, or hiding module/site/type context rejects this local completion claim. | `src/wikidot/util/quick_module.py` | `tests/unit/test_quick_module.py` |
| R3 | The malformed-body error names the QuickModule, `site_id=123456`, `expected=dict`, and `actual=str` or `actual=list`. | The focused regressions match the full message shape. | Including user-supplied query text or raw response data increases unnecessary disclosure risk. | QuickModule diagnostics | `tests/unit/test_quick_module.py` |
| R4 | Existing QuickModule and adjacent site behavior remains green. | The QuickModule file passed 29 tests and the adjacent QuickModule/site run passed 111 tests. | Regressing URL encoding, transient retry, empty member/user results, missing response-key diagnostics, response-field diagnostics, row-shape diagnostics, row-field diagnostics, malformed user ID diagnostics, page lookup, invalid module handling, site-not-found handling, or site workflows rejects this local completion claim. | QuickModule/site workflows | `tests/unit/test_quick_module.py`; `tests/unit/test_site.py` |

## Testing

Implemented locally in commit `4df3147 fix(quick_module): report malformed response bodies`.

- RED: `uv run --extra test pytest tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_malformed_response_body_includes_module_site_and_type_context tests/unit/test_quick_module.py::TestQuickModulePageLookup::test_page_lookup_malformed_response_body_includes_module_site_and_type_context -q` failed before the fix with raw string/list indexing `TypeError`.
- GREEN: `uv run --extra test pytest tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_malformed_response_body_includes_module_site_and_type_context tests/unit/test_quick_module.py::TestQuickModulePageLookup::test_page_lookup_malformed_response_body_includes_module_site_and_type_context -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_quick_module.py -q` passed 29 tests.
- `uv run --extra test pytest tests/unit/test_quick_module.py tests/unit/test_site.py -q` passed 111 tests.
- `uv run --extra test pytest tests/unit -q` passed 886 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- `QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` still request the same QuickModule endpoints.
- Non-dictionary QuickModule response bodies raise contextual `ValueError`.
- The malformed-body message includes module name, site ID, expected root type, and observed root type.
- The malformed-body message does not include the raw lookup query string or raw response body.
- Empty member/user results, successful lookups, Issues 313/314/315/318/319 diagnostics, invalid-module checks, site-not-found handling, URL encoding, and retry behavior remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real QuickModule response body, local rollout paths, private account material, or private query data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Root-shape validation could mask existing missing-key diagnostics. Mitigation: dictionary responses still proceed to the existing key check unchanged.
- Risk: Root-shape diagnostics could interfere with response-field or row-shape diagnostics. Mitigation: only the root object is checked here; dictionary responses still proceed through the field, row, field-presence, and user-ID checks from earlier slices.
- Risk: Adding response-root context could expose lookup text. Mitigation: the diagnostic reports module, site, and type only.

## Dependencies

- Valid QuickModule responses are dictionary-like JSON objects.
- Result fields remain validated by Issue 319.
- Row objects remain validated by Issue 318 and required fields remain validated by Issue 315.

## Open Questions

None for this local slice. Remaining useful work should move back to the broader direct parser/scalar audit rather than continuing to subdivide this now-covered QuickModule response parser path.

## Upstream-Safe Motivation

QuickModule lookup is useful for resolving Wikidot users, members, and pages without browser automation. If the response body itself is not an object, wikidot.py should report which lookup module, site, and type failed instead of surfacing raw Python indexing text. Omitting query text and raw response data keeps the diagnostic actionable without exposing unnecessary private context.

## Local Evidence, Not For Upstream Paste

- The immediate RED failure showed string/list QuickModule response roots leaking raw container-indexing `TypeError`.
- Issue 319 covered malformed present result fields, leaving only the root shape as a separate QuickModule response parser boundary.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, real QuickModule response bodies, raw lookup query text, and private user/member/page data out of upstream discussion.

## Additional Notes

This is a response-root diagnostics fix. It preserves valid QuickModule behavior while making malformed response bodies actionable in logs that cannot retain raw response bodies.
