# PR Draft: Validate QuickModule Blank Page Result Slugs

## Summary

`QMCPage(...)` and `QuickModule.page_lookup(...)` already reject non-string page result `unix_name` values, but empty strings and whitespace-only strings still passed validation. A blank page slug is not a useful page identity and can silently create page lookup records that later cannot identify or fetch the selected page. Page titles are separate display text and remain allowed to be blank.

This change rejects blank direct `QMCPage.unix_name` values and blank `PageLookupQModule` row `unix_name` fields. Direct constructors raise `ValueError("unix_name must not be empty")`, while public page lookup paths raise contextual QuickModule diagnostics with module name, site ID, row index, and field. Valid QMCPage construction, blank titles, valid page lookup rows, non-string title/unix-name diagnostics, direct blank page lookup-query behavior, member/user result-name validation, request behavior, retry behavior, empty-result handling, and response parser diagnostics remain unchanged.

## Outcome

QuickModule page-result objects can no longer carry blank page slugs, while page title display text remains permissive.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use QuickModule page lookup results for browser-free page selection, publication tooling, migration ledgers, moderation reports, local fixtures, or rehydrated result records.

## Current Evidence

QuickModule-related drafts [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md), [318-pr-quickmodule-row-shape-context.md](318-pr-quickmodule-row-shape-context.md), [319-pr-quickmodule-response-field-context.md](319-pr-quickmodule-response-field-context.md), [320-pr-quickmodule-response-body-context.md](320-pr-quickmodule-response-body-context.md), [339-pr-quickmodule-json-decode-context.md](339-pr-quickmodule-json-decode-context.md), [494-pr-validate-quickmodule-result-text-fields.md](494-pr-validate-quickmodule-result-text-fields.md), [497-pr-validate-quickmodule-request-arguments.md](497-pr-validate-quickmodule-request-arguments.md), [625-pr-validate-quickmodule-blank-user-lookup-queries.md](625-pr-validate-quickmodule-blank-user-lookup-queries.md), and [626-pr-validate-quickmodule-blank-user-result-names.md](626-pr-validate-quickmodule-blank-user-result-names.md) establish QuickModule lookup as a practical read surface and cover adjacent retry, response-parser, request-argument, user-result, and result text type boundaries.

This is not a duplicate of Issue 494. Issue 494 validates non-string page result text fields, but it still allows blank string slugs. This slice adds the separate non-empty invariant only for the page identity slug.

This is not a duplicate of Issue 626. Issue 626 validates member/user result names. This slice validates page result `unix_name` and deliberately leaves title text unchanged.

No upstream issue was filed from this local workspace.

## Changes

- Add direct `QMCPage.unix_name` blank-string validation while preserving the existing non-string diagnostic.
- Use the contextual QuickModule row non-empty text accessor for `PageLookupQModule` row `unix_name` fields.
- Preserve blank `QMCPage.title` values and blank page lookup row titles.
- Preserve valid page lookup behavior, malformed title/unix-name type diagnostics, missing-field diagnostics, row-shape diagnostics, request validation, URL encoding, retry behavior, and empty-result handling.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `QMCPage(title=..., unix_name="")` and whitespace-only variants must raise `ValueError("unix_name must not be empty")`. |
| R2 | `QuickModule.page_lookup(...)` must reject blank returned row `unix_name` values with module/site/row/field context. |
| R3 | Direct and returned blank page titles must remain valid. |
| R4 | Non-string direct and row `title` / `unix_name` diagnostics must remain unchanged. |
| R5 | Valid member/user/page lookups, empty results, request validation, URL encoding, retry behavior, site-not-found mapping, missing-field diagnostics, row-shape diagnostics, malformed user-ID diagnostics, user result-name validation, and response parser diagnostics must remain unchanged. |
| R6 | Focused RED/GREEN, QuickModule tests, adjacent workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct blank page slugs fail at construction. | `test_init_rejects_blank_unix_names` failed RED for `""` and `"   "` with `DID NOT RAISE`, then passed GREEN after `_validate_qmc_page_unix_name(...)` rejected blank strings. | Accepting blank direct `QMCPage.unix_name`, stripping and storing an empty slug, or changing valid direct construction rejects this local completion claim. | `QMCPage` constructor | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R2 | Blank page row slugs fail with QuickModule context. | `test_page_lookup_blank_unix_name_includes_module_site_row_and_field_context` failed RED for `""` and `"   "` with `DID NOT RAISE`, then passed GREEN after the page row mapper used `_row_non_empty_text_field(...)` for `unix_name`. | Returning a `QMCPage` with blank slug, leaking only direct constructor diagnostics, omitting module/site/row/field context, or including raw query text rejects this local completion claim. | PageLookupQModule row parser | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R3 | Blank page titles remain valid. | `test_init_allows_blank_titles` and `test_page_lookup_allows_blank_title` passed in the RED and GREEN focused runs. | Rejecting blank direct or returned page titles, trimming titles, or changing title parser paths rejects this local completion claim. | Page title display text | `tests/unit/test_quick_module.py` |
| R4 | Existing malformed text diagnostics remain stable. | Existing QMCPage non-string title/unix-name tests and page row non-string title/unix-name tests passed in QuickModule coverage. | Changing `title must be a string`, `unix_name must be a string`, or the existing `expected=str, actual=<type>` row diagnostics rejects this local completion claim. | Direct and row text validation | `tests/unit/test_quick_module.py` |
| R5 | Existing QuickModule and adjacent behavior remains green. | `tests/unit/test_quick_module.py` passed 101 tests; adjacent `tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_user.py` passed 561 tests. | Regressing prior QuickModule request validation, blank lookup-query validation, user result-name validation, parser diagnostics, valid lookups, empty results, wrapper-level site member lookup, or user/profile lookup rejects this local completion claim. | QuickModule and consumers | `tests/unit` |
| R6 | Repository quality gates pass in the local dependency environment. | Full unit passed 2820 tests; full `ruff check`, `ruff format --check`, `mypy`, `pyright`, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | verification commands below |
| R7 | No live auth material or private state is needed to prove the behavior. | The regressions use synthetic QuickModule JSON and patched HTTP responses only; this draft contains no credentials, cookies, auth JSON, raw response bodies, private page names, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page data, private user data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `1044fae fix(quickmodule): validate blank page result slugs`.

- RED: `uv run pytest tests/unit/test_quick_module.py::TestQMCPage::test_init_rejects_blank_unix_names tests/unit/test_quick_module.py::TestQMCPage::test_init_allows_blank_titles tests/unit/test_quick_module.py::TestQuickModulePageLookup::test_page_lookup_allows_blank_title tests/unit/test_quick_module.py::TestQuickModulePageLookup::test_page_lookup_blank_unix_name_includes_module_site_row_and_field_context -q` failed 4 blank `unix_name` cases with `DID NOT RAISE`; the 2 blank-title preservation cases passed.
- GREEN focused: the same command passed 6 tests after direct `QMCPage.unix_name` and page row `unix_name` blank validation was added.
- QuickModule coverage: `uv run pytest tests/unit/test_quick_module.py -q` passed 101 tests.
- Adjacent coverage: `uv run pytest tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_user.py -q` passed 561 tests.
- `uv run pytest tests/unit -q` passed 2820 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `QMCPage(title="Test Page", unix_name="")` and `QMCPage(title="Test Page", unix_name="   ")` raise `ValueError("unix_name must not be empty")`.
- `QMCPage(title="", unix_name="test-page")` remains valid.
- Page lookup rows with `{"title": "Bad Page", "unix_name": ""}` or whitespace-only slugs raise `ValueError("QuickModule row field is empty for module: PageLookupQModule, site_id=<id> (row=<n>, field=unix_name)")`.
- Page lookup rows with blank titles and non-empty slugs remain valid.
- Page lookup rows with non-string titles or slugs still raise the existing contextual `expected=str, actual=<type>` diagnostic.
- Existing QuickModule request construction, blank lookup-query validation, retry behavior, response diagnostics, malformed user-ID diagnostics, user result-name validation, valid lookups, empty results, adjacent site/user behavior, live request semantics, upstream Issues, upstream PRs, pushes, credentials, cookies, auth JSON, private queries, and raw response bodies remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

QuickModule page lookup results feed browser-free page selection and generated page ledgers. A returned page row with a blank slug loses the identity value downstream code needs to address the page. Rejecting blank slugs at the result boundary keeps logs actionable without saving raw response bodies, while preserving blank titles as display text.

## Local Evidence, Not For Upstream Paste

- The focused RED run showed direct `QMCPage` construction and page QuickModule row parsing accepted blank and whitespace-only `unix_name` values.
- The same RED run showed blank direct and returned page titles remained accepted.
- Issue 494 covered non-string page text fields but not blank string page slugs.
- Issue 626 covered blank member/user result names but deliberately left page result fields for separate evidence.
- This slice only validates direct and returned QuickModule page result slugs. It does not change page title semantics, blank page lookup-query behavior, URL encoding for valid strings, site-ID validation, retry behavior, QuickModule response parsing outside page slug blankness, wrapper-level site member lookup behavior, direct profile lookup behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw QuickModule response bodies, private page data, private user data, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The new validators deliberately do not strip valid slugs before returning them. They only reject strings whose stripped form is empty, preserving any non-empty returned spelling for existing callers.
