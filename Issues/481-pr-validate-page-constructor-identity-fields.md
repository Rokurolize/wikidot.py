# PR Draft: Validate Page Constructor Identity Fields

## Summary

`Page` objects carry the core page identity used by URL construction, direct page lookup, page source/revision/file/vote ledgers, page write workflows, publish verification, duplicate-cache reuse, and local browser-free fixtures. Most `Page` objects are produced by parser and lookup helpers, but direct `Page(...)` construction is public and widely used by tests, generated ledgers, and rehydrated workflow state. Before this change, direct construction accepted malformed identity text such as `fullname=None`, `name=True`, `category=[]`, or `title=123456`, storing invalid state that could later leak into URLs, lookup keys, diagnostics, cache grouping, or audit records.

This change validates the direct constructor's identity text fields during `Page.__post_init__`. Malformed `fullname`, `name`, `category`, and `title` values now raise stable `ValueError("<field> must be a string")` diagnostics. Valid `Page` construction, parser-created pages, page lookup, page source/revision/file/vote workflows, site workflows, and existing nullable parser metadata fixtures remain unchanged.

## Outcome

Callers cannot silently construct `Page` objects with malformed identity text, while valid page records and existing page/site workflows continue to work as before.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page inventories, page source collection, page publishing, revision/source/file/vote ledgers, duplicate page-cache reuse, generated audit rows, migration tooling, local fixtures, or rehydrated `Page` objects.

## Current Evidence

Local rollout-backed drafts repeatedly identify page identity as an operational boundary. ListPages and page lookup drafts such as [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md), and [382-pr-validate-page-collection-find-fullname.md](382-pr-validate-page-collection-find-fullname.md) establish `fullname`, `name`, `category`, and `title` as meaningful parser and lookup fields. Page write drafts such as [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), and [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md) establish caller-input validation for page mutations. Page state drafts such as [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), [414-pr-validate-page-source-assignments.md](414-pr-validate-page-source-assignments.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), and [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md) establish page identity and parent-state integrity as active local surfaces.

Those prior slices are not duplicates. Issue 092 scopes parsed ListPages field extraction, Issue 116 preserves parsed text spacing, Issue 382 validates lookup keys passed to an existing `PageCollection`, Issues 343, 349, and 350 validate explicit page mutation inputs, Issue 413 validates direct `Page.id` assignment, Issue 414 validates direct `Page.source` assignment, Issue 415 validates direct `Page.revisions` assignment, and Issue 477 validates the collection's parent `Site`. None validates direct `Page(fullname=...)`, `Page(name=...)`, `Page(category=...)`, or `Page(title=...)` construction before malformed identity text becomes stored page state.

## Related Issue / Non-Duplicate Analysis

Builds directly on the page identity and state surfaces documented by [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [382-pr-validate-page-collection-find-fullname.md](382-pr-validate-page-collection-find-fullname.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), [414-pr-validate-page-source-assignments.md](414-pr-validate-page-source-assignments.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), and [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a `Page.__post_init__` constructor validation hook.
- Validate `Page.fullname`, `Page.name`, `Page.category`, and `Page.title` with the existing page text-field validator.
- Reject malformed identity text with stable `ValueError("<field> must be a string")` messages.
- Preserve valid direct construction, parser-created pages, existing page/site fixtures, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page identity-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(fullname=...)` must reject non-string values with `ValueError("fullname must be a string")`. |
| R2 | `Page(name=...)` must reject non-string values with `ValueError("name must be a string")`. |
| R3 | `Page(category=...)` must reject non-string values with `ValueError("category must be a string")`. |
| R4 | `Page(title=...)` must reject non-string values with `ValueError("title must be a string")`. |
| R5 | Valid `Page` construction, parser-created pages, page lookup, page source/revision/file/vote workflows, and site workflows must remain unchanged. |
| R6 | This slice must not validate broader `Page` metadata such as parent site, counts, rating fields, user fields, timestamps, tags, parent fullname, cached source/revisions/votes/files, or parser-derived nullable metadata. |
| R7 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, constructor tests, adjacent page/site/page-file/page-vote tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct `Page.fullname` values fail at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_identity_text` failed RED for 4 malformed `fullname` values because constructors did not raise, then passed GREEN after validation was added. | Accepting `None`, booleans, integers, lists, arbitrary non-strings, or silently coercing malformed fullnames rejects this local completion claim. | `Page` constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Malformed direct `Page.name` values fail at the constructor boundary. | The same RED/GREEN test failed and then passed for malformed `name` values. | Accepting non-string page names or storing malformed page names rejects this local completion claim. | `Page` constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Malformed direct `Page.category` values fail at the constructor boundary. | The same RED/GREEN test failed and then passed for malformed `category` values. | Accepting non-string page categories or storing malformed category values rejects this local completion claim. | `Page` constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R4 | Malformed direct `Page.title` values fail at the constructor boundary. | The same RED/GREEN test failed and then passed for malformed `title` values. | Accepting non-string titles or relying only on page write API title validation rejects this local completion claim. | `Page` constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R5 | Existing valid page and site workflows remain green. | `tests/unit/test_page_constructor.py` passed 17 tests; adjacent page/site/page-file/page-vote tests passed 644 tests; full unit tests passed 1999 tests. | Regressing valid fixture construction, parser-created pages, `Page.get_url()`, page lookup, page source/revision/file/vote workflows, or site workflows rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit` |
| R6 | Broader parser metadata remains outside scope. | Existing nullable `rating_percent`, creator, updater, timestamp, comment, parent, cache, and collection fixture patterns remain unchanged and adjacent tests stay green. | Validating or changing parent site, counters, rating fields, users, timestamps, tags, parent fullname, cached state, or parser-derived nullable metadata rejects this local completion claim. | Page constructor scope | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py`, adjacent tests |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `a73a355 fix(page): validate constructor identity fields`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_identity_text -q` failed 16 tests before the fix; every malformed identity text case reported `DID NOT RAISE`.
- GREEN: the same focused command passed 16 tests after constructor identity validation was added.
- `uv run pytest tests/unit/test_page_constructor.py -q` passed 17 tests.
- `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py -q` passed 644 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed.
- `uv run mypy src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 1999 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client/mock typing, invalid test cookie arguments, and existing site test mock typing issues. The changed source file and new constructor test module pass pyright together.

## Acceptance Criteria

- `Page(fullname=None)`, `Page(fullname=True)`, `Page(fullname=123456)`, and `Page(fullname=[])` raise `ValueError("fullname must be a string")` when every other constructor field is valid.
- `Page(name=None)`, `Page(name=True)`, `Page(name=123456)`, and `Page(name=[])` raise `ValueError("name must be a string")`.
- `Page(category=None)`, `Page(category=True)`, `Page(category=123456)`, and `Page(category=[])` raise `ValueError("category must be a string")`.
- `Page(title=None)`, `Page(title=True)`, `Page(title=123456)`, and `Page(title=[])` raise `ValueError("title must be a string")`.
- Valid page identity text is stored unchanged.
- Existing parser-created pages, direct page fixtures, page lookup behavior, page source/revision/file/vote workflows, and site workflows remain green.
- The new tests use unit-level code only and do not validate broader `Page` metadata, require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page` identity text is used by URL construction, lookup keys, source/revision/file/vote ledgers, publishing diagnostics, duplicate-cache reuse, and generated workflow records. Parser and write-path validations already protect specific routes into page data, so this change is intentionally conservative: it only prevents direct callers, fixtures, generated adapters, or rehydrated page state from storing malformed identity text that later fails as less informative URL, cache, or diagnostic behavior.

## Local Evidence

- Local rollout evidence used page identity in page inventories, ListPages parsing, direct lookup, source collection, publishing, revision/file/vote ledgers, duplicate cache reuse, and site workflows.
- Existing local drafts covered ListPages field parsing, lookup key validation, page write title/comment inputs, direct page ID/source/revisions/votes assignment validation, and collection parent-site validation, but did not cover direct `Page(...)` identity text construction.
- Existing unit fixtures intentionally allow some broader parser metadata to be nullable. This slice preserves that pattern and validates only `fullname`, `name`, `category`, and `title`.
- This slice does not change direct page lookup, parser extraction, page write behavior, page ID/source/revision/file/vote acquisition, cached state, live Wikidot behavior, or parent site validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change rejects malformed identity text rather than coercing it. Empty strings remain valid because existing page creation, direct page lookup, parser fallback, and test fixtures rely on the existing string semantics rather than non-empty string enforcement.
