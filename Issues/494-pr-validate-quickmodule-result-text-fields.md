# PR Draft: Validate QuickModule Result Text Fields

## Summary

`QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` parse Wikidot QuickModule rows into `QMCUser` and `QMCPage` records. Earlier local slices already retry transient QuickModule failures and report malformed JSON, response bodies, top-level result fields, row objects, missing row fields, and malformed `user_id` values with module/site/row context. One adjacent gap remained: present row text fields such as `name`, `title`, and `unix_name` could be non-strings and still become stored result objects. Direct `QMCUser(...)` and `QMCPage(...)` construction also accepted malformed `id`, `name`, `title`, and `unix_name` values.

This change validates QuickModule row text fields before constructing result objects and validates direct `QMCUser` / `QMCPage` dataclass construction. Public lookup paths now raise contextual `ValueError` messages with module name, site ID, row index, field, expected type, and observed type for malformed text fields. Direct result constructors now enforce simple stored-field invariants with stable field-level diagnostics.

## Outcome

Malformed QuickModule result text fields now fail at the parser boundary with useful context, and manually constructed QuickModule result objects can no longer carry non-integer IDs or non-string text fields.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use QuickModule lookup results for browser-free member selection, user resolution, page selection, moderation tools, migration ledgers, attribution reports, or local fixtures and rehydrated result records.

## Current Evidence

QuickModule-related drafts [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md), [318-pr-quickmodule-row-shape-context.md](318-pr-quickmodule-row-shape-context.md), [319-pr-quickmodule-response-field-context.md](319-pr-quickmodule-response-field-context.md), [320-pr-quickmodule-response-body-context.md](320-pr-quickmodule-response-body-context.md), and [339-pr-quickmodule-json-decode-context.md](339-pr-quickmodule-json-decode-context.md) establish QuickModule lookup as a practical read surface and cover adjacent parser boundaries.

Those prior slices are not duplicates. They cover request retry, JSON decoding, response root shape, result-field shape, row object shape, required field presence, and `user_id` scalar conversion. None validates the present text value type for `name`, `title`, or `unix_name`, and none validates direct `QMCUser(...)` / `QMCPage(...)` construction before malformed local state is stored.

## Related Issue / Non-Duplicate Analysis

Builds directly on the QuickModule parser hardening in Issues 313 through 320 and follows the public dataclass constructor hardening pattern used across site, page, forum, vote, file, revision, and result-ledger records.

No upstream issue was filed from this local workspace.

## Changes

- Add direct `QMCUser` constructor validation for `id` and `name`.
- Add direct `QMCPage` constructor validation for `title` and `unix_name`.
- Add a QuickModule row text-field accessor that preserves missing-field diagnostics while rejecting present non-string values with module/site/row/field/type context.
- Use the row text-field accessor for member/user `name` and page `title` / `unix_name`.
- Add focused RED/GREEN tests for direct constructors and public lookup parser diagnostics.

## Type Of Change

- Input validation
- QuickModule parser diagnostics improvement
- Public dataclass constructor behavior hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `QMCUser(id=...)` must reject non-integer IDs, including booleans, with `ValueError("id must be an integer")`. |
| R2 | `QMCUser(name=...)` must reject non-string names with `ValueError("name must be a string")`. |
| R3 | `QMCPage(title=...)` and `QMCPage(unix_name=...)` must reject non-string values with stable field-level `ValueError` messages. |
| R4 | `QuickModule.member_lookup(...)` and `QuickModule.user_lookup(...)` must reject present non-string `name` row fields with module/site/row/field/type context. |
| R5 | `QuickModule.page_lookup(...)` must reject present non-string `title` and `unix_name` row fields with module/site/row/field/type context. |
| R6 | Existing valid lookups, empty results, missing-field diagnostics, row-shape diagnostics, response diagnostics, malformed `user_id` diagnostics, URL encoding, retry behavior, invalid-module checks, and site-not-found handling must remain unchanged. |
| R7 | Focused RED/GREEN, QuickModule tests, adjacent site/member/user tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct `QMCUser.id` values fail at construction. | `TestQMCUser.test_init_rejects_malformed_ids` failed RED for 5 malformed values with `DID NOT RAISE`, then passed GREEN after validation was added. | Accepting `None`, booleans, numeric strings, floats, or arbitrary objects rejects this local completion claim. | `QMCUser` constructor | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R2 | Malformed direct `QMCUser.name` values fail at construction. | `TestQMCUser.test_init_rejects_malformed_names` failed RED for 5 malformed values with `DID NOT RAISE`, then passed GREEN after validation was added. | Accepting missing values, booleans, integers, lists, or arbitrary objects rejects this local completion claim. | `QMCUser` constructor | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R3 | Malformed direct page result text fields fail at construction. | `TestQMCPage.test_init_rejects_malformed_titles` and `test_init_rejects_malformed_unix_names` failed RED for 10 malformed values with `DID NOT RAISE`, then passed GREEN after validation was added. | Accepting non-string page titles or unix names rejects this local completion claim. | `QMCPage` constructor | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R4 | Member/user row names fail with contextual QuickModule diagnostics. | `test_member_lookup_malformed_name_includes_module_site_row_field_and_type_context` and `test_user_lookup_malformed_name_includes_module_site_row_field_and_type_context` failed RED, then passed GREEN. | Returning `QMCUser(name=12345)`, leaking only direct constructor messages, or omitting module/site/row/field/type context rejects this local completion claim. | QuickModule member/user row parser | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R5 | Page row titles and unix names fail with contextual QuickModule diagnostics. | `test_page_lookup_malformed_title_includes_module_site_row_field_and_type_context` and `test_page_lookup_malformed_unix_name_includes_module_site_row_field_and_type_context` failed RED, then passed GREEN. | Returning `QMCPage` records with non-string fields, leaking only direct constructor messages, or omitting module/site/row/field/type context rejects this local completion claim. | QuickModule page row parser | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R6 | Existing QuickModule and adjacent site behavior remains green. | QuickModule tests passed 54 tests, adjacent site/site-member/user/QuickModule tests passed 383 tests, and full unit tests passed 2143 tests. | Regressing prior Issues 313-320 diagnostics, valid member/user/page lookups, empty results, retry behavior, URL encoding, invalid-module handling, or site workflows rejects this local completion claim. | QuickModule and adjacent workflows | `tests/unit/test_quick_module.py`, `tests/unit/test_site.py`, `tests/unit/test_site_member.py`, `tests/unit/test_user.py`, `tests/unit` |
| R7 | Repository quality gates pass in the local dependency environment. | Full ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright was run and reported as existing unrelated full-tree test typing errors. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `2d5722a fix(quick_module): validate result text fields`.

- RED: `uv run --extra test pytest -q tests/unit/test_quick_module.py::TestQMCUser::test_init_rejects_malformed_ids tests/unit/test_quick_module.py::TestQMCUser::test_init_rejects_malformed_names tests/unit/test_quick_module.py::TestQMCPage::test_init_rejects_malformed_titles tests/unit/test_quick_module.py::TestQMCPage::test_init_rejects_malformed_unix_names tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_malformed_name_includes_module_site_row_field_and_type_context tests/unit/test_quick_module.py::TestQuickModuleUserLookup::test_user_lookup_malformed_name_includes_module_site_row_field_and_type_context tests/unit/test_quick_module.py::TestQuickModulePageLookup::test_page_lookup_malformed_title_includes_module_site_row_field_and_type_context tests/unit/test_quick_module.py::TestQuickModulePageLookup::test_page_lookup_malformed_unix_name_includes_module_site_row_field_and_type_context` failed 24 new malformed-field cases before the fix with `DID NOT RAISE`.
- GREEN: the same focused command passed 24 tests after result text-field validation was added.
- `uv run --extra test pytest -q tests/unit/test_quick_module.py` passed 54 tests.
- `uv run --extra test pytest -q tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_user.py tests/unit/test_quick_module.py` passed 383 tests.
- `uv run --extra test pytest -q tests/unit` passed 2143 tests.
- `uv run ruff format src/wikidot/util/quick_module.py tests/unit/test_quick_module.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/util/quick_module.py tests/unit/test_quick_module.py` passed.
- `uv run mypy src/wikidot/util/quick_module.py tests/unit/test_quick_module.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/util/quick_module.py tests/unit/test_quick_module.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 44 existing full-tree test typing errors outside this slice, including intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client/mock typing, invalid test cookie arguments, and existing site test mock typing issues. The changed source file and touched test module pass pyright together.

## Acceptance Criteria

- Valid `QMCUser(id=12345, name="test-user")` and `QMCPage(title="Test Page", unix_name="test-page")` construction remains valid.
- Direct `QMCUser(id=None)`, `True`, `"12345"`, `12345.0`, and `object()` raise `ValueError("id must be an integer")`.
- Direct `QMCUser(name=None)`, `True`, `12345`, `[]`, and `object()` raise `ValueError("name must be a string")`.
- Direct `QMCPage(title=...)` and `QMCPage(unix_name=...)` reject non-string values with field-level `ValueError` messages.
- Public QuickModule lookups reject present non-string `name`, `title`, and `unix_name` row fields with module/site/row/field/type context.
- Missing row fields still use the existing "row field is missing" diagnostic, and malformed row objects still use the existing row-shape diagnostic.
- Existing QuickModule request construction, retry behavior, response diagnostics, malformed user-ID diagnostics, valid lookups, empty results, adjacent site behavior, live request semantics, upstream Issues, upstream PRs, pushes, credentials, cookies, auth JSON, private queries, and raw response bodies remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Direct constructor validation could degrade public lookup diagnostics. Mitigation: parser paths validate row text fields before constructing `QMCUser` or `QMCPage`, preserving module/site/row/field/type context.
- Risk: Text-field validation could mask missing-field diagnostics. Mitigation: `_row_text_field(...)` calls the existing `_row_field(...)` first, so missing fields still use the prior diagnostic.
- Risk: Boolean IDs could be accepted because `bool` is an `int` subclass in Python. Mitigation: direct `QMCUser.id` validation rejects booleans explicitly.

## Dependencies

- Valid QuickModule user/member rows provide `user_id` plus a string `name`.
- Valid QuickModule page rows provide string `title` and `unix_name`.
- Prior QuickModule diagnostics remain responsible for malformed JSON, response-body shape, top-level result fields, row object shape, missing fields, and malformed `user_id` conversion.

## Open Questions

None for this local slice. Remaining QuickModule work should come from fresh duplicate checks rather than reopening covered parser-boundary diagnostics.

## Upstream-Safe Motivation

QuickModule lookup results feed browser-free user, member, and page selection workflows. If Wikidot returns a malformed present text field, wikidot.py should report the exact lookup module, site, row, and field instead of letting non-string data become stored result state. Direct result constructors should enforce the same basic invariants for fixtures and rehydrated records.

## Local Evidence

- Rollout-backed local drafts repeatedly use QuickModule lookup for site membership, user lookup, and page lookup workflows.
- Existing local drafts covered QuickModule retries, malformed JSON, missing response keys, response body shape, result field shape, row shape, missing row fields, and malformed `user_id` values, but did not cover present malformed row text values or direct result object construction.
- The focused RED failures showed all new malformed direct fields and malformed row text values were accepted before this slice.
- This slice does not change request URLs, query serialization, retry policy, empty-result sentinel handling, `user_id` conversion, response parsing boundaries already covered by Issues 313 through 320, live Wikidot behavior, site workflows, or private payload handling.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, real QuickModule response bodies, raw lookup query text, usernames, passwords, session cookies, credentials, auth JSON, and private user/member/page data out of upstream discussion.

## Additional Notes

The parser and constructor validators deliberately produce different diagnostics. Public lookup paths should carry module/site/row context because they classify remote response data, while direct `QMCUser` and `QMCPage` constructors should report simple field invariants for local state.
