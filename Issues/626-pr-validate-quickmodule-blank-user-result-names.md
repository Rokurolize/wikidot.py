# PR Draft: Validate QuickModule Blank User Result Names

## Summary

`QMCUser(...)`, `QuickModule.member_lookup(...)`, and `QuickModule.user_lookup(...)` already reject non-string user result names, but empty strings and whitespace-only strings still passed validation. A blank returned identity name is not useful for browser-free member or user resolution and can silently create result records that later compare, log, or rehydrate as empty user identities.

This change rejects blank direct `QMCUser.name` values and blank member/user QuickModule row `name` fields. Direct constructors raise a simple `ValueError("name must not be empty")`, while public lookup paths raise contextual QuickModule diagnostics with module name, site ID, row index, and field. Valid QMCUser construction, valid member/user lookup rows, non-string name diagnostics, user-ID conversion diagnostics, direct blank lookup-query validation, page lookup result fields, QuickModule request behavior, retry behavior, empty-result handling, and response parser diagnostics remain unchanged.

## Outcome

QuickModule user-result objects can no longer carry blank identity names, and malformed remote member/user rows fail at the parser boundary with enough context for log-only diagnosis.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use QuickModule member/user lookup results for browser-free membership checks, user resolution, moderation tooling, migration ledgers, attribution reports, local fixtures, or rehydrated result records.

## Current Evidence

QuickModule-related drafts [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md), [318-pr-quickmodule-row-shape-context.md](318-pr-quickmodule-row-shape-context.md), [319-pr-quickmodule-response-field-context.md](319-pr-quickmodule-response-field-context.md), [320-pr-quickmodule-response-body-context.md](320-pr-quickmodule-response-body-context.md), [339-pr-quickmodule-json-decode-context.md](339-pr-quickmodule-json-decode-context.md), [494-pr-validate-quickmodule-result-text-fields.md](494-pr-validate-quickmodule-result-text-fields.md), [497-pr-validate-quickmodule-request-arguments.md](497-pr-validate-quickmodule-request-arguments.md), and [625-pr-validate-quickmodule-blank-user-lookup-queries.md](625-pr-validate-quickmodule-blank-user-lookup-queries.md) establish QuickModule lookup as a practical read surface and cover adjacent retry, response-parser, request-argument, and result text type boundaries.

This is not a duplicate of Issue 494. Issue 494 validates non-string result text fields, but it still allows blank strings. This slice adds the separate non-empty invariant only for user identity names.

This is not a duplicate of Issue 625. Issue 625 validates caller-provided blank member/user lookup query strings before request construction. This slice validates returned QuickModule user-result names after a response is decoded.

No upstream issue was filed from this local workspace.

## Changes

- Add direct `QMCUser.name` blank-string validation while preserving the existing non-string diagnostic.
- Add a contextual QuickModule row non-empty text accessor.
- Use the non-empty row accessor only for member/user row `name` fields.
- Preserve page lookup result-field behavior, including `QMCPage.title` and `QMCPage.unix_name` handling, for separate evidence.
- Preserve valid member/user lookup behavior, malformed user-ID diagnostics, row-shape diagnostics, missing-field diagnostics, request validation, URL encoding, retry behavior, and empty-result handling.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `QMCUser(id=..., name="")` and whitespace-only variants must raise `ValueError("name must not be empty")`. |
| R2 | `QuickModule.member_lookup(...)` must reject blank returned row `name` values with module/site/row/field context. |
| R3 | `QuickModule.user_lookup(...)` must reject blank returned row `name` values with module/site/row/field context. |
| R4 | Non-string direct and row `name` diagnostics must remain unchanged. |
| R5 | Page lookup result fields must remain unchanged because page title and slug semantics need separate evidence. |
| R6 | Valid member/user/page lookups, empty results, request validation, URL encoding, retry behavior, site-not-found mapping, missing-field diagnostics, row-shape diagnostics, malformed user-ID diagnostics, and response parser diagnostics must remain unchanged. |
| R7 | Focused RED/GREEN, QuickModule tests, adjacent workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R8 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct blank user-result names fail at construction. | `test_init_rejects_blank_names` failed RED for `""` and `"   "` with `DID NOT RAISE`, then passed GREEN after `_validate_qmc_user_name(...)` rejected blank strings. | Accepting blank direct `QMCUser.name`, stripping and storing an empty string, or changing valid direct construction rejects this local completion claim. | `QMCUser` constructor | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R2 | Blank member row names fail with QuickModule context. | `test_member_lookup_blank_name_includes_module_site_row_and_field_context` failed RED for `""` and `"   "` with `DID NOT RAISE`, then passed GREEN after `_row_non_empty_text_field(...)` classified the blank row field. | Returning a `QMCUser` with blank name, leaking only direct constructor diagnostics, omitting module/site/row/field context, or including raw query text rejects this local completion claim. | MemberLookupQModule row parser | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R3 | Blank user row names fail with QuickModule context. | `test_user_lookup_blank_name_includes_module_site_row_and_field_context` failed RED for `""` and `"   "` with `DID NOT RAISE`, then passed GREEN after the same row-field guard was applied to `UserLookupQModule`. | Returning a `QMCUser` with blank name, silently trimming the row value, omitting module/site/row/field context, or including raw query text rejects this local completion claim. | UserLookupQModule row parser | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R4 | Existing malformed-name type diagnostics remain stable. | Existing QMCUser non-string name tests and member/user row non-string name tests passed in QuickModule coverage. | Changing `ValueError("name must be a string")` or the existing `expected=str, actual=<type>` row diagnostic rejects this local completion claim. | Direct and row text validation | `tests/unit/test_quick_module.py` |
| R5 | Page result fields remain unchanged. | The implementation does not call the non-empty row accessor from `_map_page_item(...)`, and QuickModule page tests passed. | Rejecting blank page titles or slugs, changing `QMCPage` validation, or changing page lookup parser paths rejects this local completion claim. | PageLookupQModule result parser | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R6 | Existing QuickModule and adjacent behavior remains green. | `tests/unit/test_quick_module.py` passed 95 tests; adjacent `tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_user.py` passed 555 tests. | Regressing prior QuickModule request validation, blank lookup-query validation, parser diagnostics, valid lookups, empty results, wrapper-level site member lookup, or user/profile lookup rejects this local completion claim. | QuickModule and consumers | `tests/unit` |
| R7 | Repository quality gates pass in the local dependency environment. | Full unit passed 2814 tests; full `ruff check`, `ruff format --check`, `mypy`, `pyright`, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | verification commands below |
| R8 | No live auth material or private state is needed to prove the behavior. | The regressions use synthetic QuickModule JSON and patched HTTP responses only; this draft contains no credentials, cookies, auth JSON, raw response bodies, private usernames, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private member data, private user data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `0e9da98 fix(quickmodule): validate blank user result names`.

- RED: `uv run pytest tests/unit/test_quick_module.py::TestQMCUser::test_init_rejects_blank_names tests/unit/test_quick_module.py::TestQuickModuleMemberLookup::test_member_lookup_blank_name_includes_module_site_row_and_field_context tests/unit/test_quick_module.py::TestQuickModuleUserLookup::test_user_lookup_blank_name_includes_module_site_row_and_field_context -q` failed 6 blank-name cases with `DID NOT RAISE`.
- GREEN focused: the same command passed 6 tests after direct `QMCUser` and member/user row-name blank validation was added.
- QuickModule coverage: `uv run pytest tests/unit/test_quick_module.py -q` passed 95 tests.
- Adjacent coverage: `uv run pytest tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_user.py -q` passed 555 tests.
- `uv run pytest tests/unit -q` passed 2814 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `QMCUser(id=12345, name="")` and `QMCUser(id=12345, name="   ")` raise `ValueError("name must not be empty")`.
- `QMCUser(id=12345, name=None)`, booleans, numbers, lists, and arbitrary objects still raise `ValueError("name must be a string")`.
- Member/user QuickModule rows with `{"user_id": "12345", "name": ""}` or whitespace-only names raise `ValueError("QuickModule row field is empty for module: <module>, site_id=<id> (row=<n>, field=name)")`.
- Member/user QuickModule rows with non-string names still raise the existing contextual `expected=str, actual=<type>` diagnostic.
- Page result fields remain unchanged.
- Existing QuickModule request construction, blank lookup-query validation, retry behavior, response diagnostics, malformed user-ID diagnostics, valid lookups, empty results, adjacent site/user behavior, live request semantics, upstream Issues, upstream PRs, pushes, credentials, cookies, auth JSON, private queries, and raw response bodies remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

QuickModule member/user lookup results feed browser-free identity resolution, membership checks, moderation helpers, and generated ledgers. A returned user row with a blank name loses the identity value that downstream comparisons and reports need. Rejecting blank names at the result boundary keeps logs actionable without saving raw response bodies, while avoiding unrelated page result semantics.

## Local Evidence, Not For Upstream Paste

- The focused RED run showed direct `QMCUser` construction and member/user QuickModule row parsing accepted blank and whitespace-only names.
- Issue 494 covered non-string text fields but not blank string result names.
- Issue 625 covered blank caller-provided member/user lookup queries but not returned row names.
- This slice only validates direct and returned QuickModule user result names. It does not change page lookup result fields, general page title/slug semantics, URL encoding for valid strings, site-ID validation, retry behavior, QuickModule response parsing outside member/user name blankness, wrapper-level site member lookup behavior, direct profile lookup behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw QuickModule response bodies, private member data, private user data, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The new validators deliberately do not strip valid names before returning them. They only reject strings whose stripped form is empty, preserving any non-empty returned spelling for existing callers.
