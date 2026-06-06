# PR Draft: Validate Page Constructor Rating Field

## Summary

`Page.rating` stores the scalar rating value used by browser-free page inventories, vote ledgers, rating audits, duplicate-cache reuse, publish-adjacent reports, and local rehydrated `Page` fixtures. Parser-created pages already convert generated ListPages rating cells into `int` or `float` values, and write actions already validate returned rating action points before mutating local state. Before this change, direct `Page(...)` construction still accepted malformed ratings such as `rating=None`, `rating=True`, `rating="10"`, or `rating=[]`, storing invalid state that could later leak into comparisons, ledgers, audit rows, or downstream page-vote workflows.

This change validates the direct constructor's `rating` field during `Page.__post_init__`. Malformed ratings now raise `ValueError("rating must be an integer or float")`; valid integer and floating-point ratings remain accepted. Valid page construction, parser-created pages, page vote/cancel workflows, page source/revision/file/vote workflows, site workflows, and nullable `rating_percent` fixture behavior remain unchanged.

## Outcome

Callers cannot silently construct `Page` objects with malformed rating values, while valid integer and 5-star floating-point ratings continue to work as before.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page inventories, vote and rating audits, page publishing checks, source/revision/file/vote ledgers, duplicate page-cache reuse, generated audit rows, migration tooling, local fixtures, or rehydrated `Page` objects.

## Current Evidence

Local rollout-backed drafts already establish page ratings as operationally meaningful. Parser-side drafts such as [240-pr-listpages-rating-field-parse-context.md](240-pr-listpages-rating-field-parse-context.md) validate malformed generated ListPages rating cells before parsed `Page` construction. Rating action drafts such as [244-pr-page-rating-points-context.md](244-pr-page-rating-points-context.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), and [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md) protect page vote writes, returned rating points, and local rating mutation. Recent direct-constructor hardening in [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md) and [482-pr-validate-page-constructor-count-fields.md](482-pr-validate-page-constructor-count-fields.md) validates adjacent page identity and count metadata boundaries.

Those prior slices are not duplicates. Issue 240 validates generated ListPages rating parsing before parser-created page rows exist. Issues 244 and 337 validate rating action responses before `Page.rating` is updated after a write. Issue 353 validates the public `Page.vote(value=...)` input. Issues 481 and 482 validate direct page identity and count fields only. None validates direct `Page(rating=...)` construction before malformed rating values become stored page state.

## Related Issue / Non-Duplicate Analysis

Builds directly on the page rating and constructor surfaces documented by [240-pr-listpages-rating-field-parse-context.md](240-pr-listpages-rating-field-parse-context.md), [244-pr-page-rating-points-context.md](244-pr-page-rating-points-context.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md), and [482-pr-validate-page-constructor-count-fields.md](482-pr-validate-page-constructor-count-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a direct page rating-field validator that rejects booleans and non-numeric values.
- Validate `Page.rating` during `Page.__post_init__`.
- Reject malformed direct ratings with stable `ValueError("rating must be an integer or float")`.
- Preserve valid integer ratings, valid 5-star floating-point ratings, `rating_percent` behavior, parser-created pages, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page rating-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(rating=...)` must reject non-numeric and boolean values with `ValueError("rating must be an integer or float")`. |
| R2 | `Page(rating=...)` must continue accepting integer and floating-point ratings. |
| R3 | Valid `Page` construction, parser-created pages, page vote/cancel workflows, page source/revision/file/vote workflows, and site workflows must remain unchanged. |
| R4 | This slice must not validate `rating_percent`, rating range semantics, parent site, user fields, timestamps, tags, parent fullname, cached source/revisions/votes/files, or parser-derived nullable metadata. |
| R5 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, constructor tests, adjacent page/site/page-file/page-vote tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct `Page.rating` values fail at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_rating` failed RED for 4 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting `None`, booleans, strings, lists, arbitrary non-numeric objects, or silently coercing malformed ratings rejects this local completion claim. | `Page` constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Valid integer and floating-point ratings remain accepted. | `TestPageInit.test_init_accepts_valid_rating_numbers` passed for `10` and `4.0`; existing ListPages 5-star parsing tests stayed green. | Rejecting valid integer ratings, rejecting valid float ratings, or changing stored numeric values rejects this local completion claim. | `Page` constructor and parser-created pages | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py` |
| R3 | Existing valid page and site workflows remain green. | `tests/unit/test_page_constructor.py` passed 43 tests; adjacent page/site/page-file/page-vote tests passed 670 tests; full unit tests passed 2025 tests. | Regressing valid fixture construction, parser-created pages, page vote/cancel behavior, page lookup, page source/revision/file/vote workflows, or site workflows rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit` |
| R4 | Broader parser metadata remains outside scope. | Existing nullable `rating_percent`, creator, updater, timestamp, comment, parent, tag, cache, and collection fixture patterns remain unchanged and adjacent tests stay green. | Validating or changing rating percent, rating range, parent site, users, timestamps, tags, parent fullname, cached state, or parser-derived nullable metadata rejects this local completion claim. | Page constructor scope | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py`, adjacent tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `aa7e0d1 fix(page): validate constructor rating field`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_rating -q` failed 4 tests before the fix; every malformed rating case reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_rating tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_rating_numbers -q` passed 6 tests after rating validation was added.
- `uv run pytest tests/unit/test_page_constructor.py -q` passed 43 tests.
- `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py -q` passed 670 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed.
- `uv run mypy src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2025 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client/mock typing, invalid test cookie arguments, and existing site test mock typing issues. The changed source file and constructor test module pass pyright together.

## Acceptance Criteria

- `Page(rating=None)`, `Page(rating=True)`, `Page(rating="10")`, and `Page(rating=[])` raise `ValueError("rating must be an integer or float")` when every other constructor field is valid.
- `Page(rating=10)` and `Page(rating=4.0)` are accepted and store the value unchanged.
- Existing parser-created pages, direct page fixtures, page lookup behavior, page vote/cancel behavior, page source/revision/file/vote workflows, and site workflows remain green.
- The new tests use unit-level code only and do not validate `rating_percent`, rating range semantics, broader `Page` metadata, require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page.rating` affects browser-free page inventories, vote ledgers, rating audits, duplicate-cache reuse, and generated workflow records. Parser and write-path validations already protect specific routes into page rating data, so this change is intentionally conservative: it only prevents direct callers, fixtures, generated adapters, or rehydrated page state from storing malformed ratings that later fail as less informative comparison, cache, or diagnostic behavior.

## Local Evidence

- Local rollout evidence used page ratings in page inventories, ListPages parsing, page vote/cancel workflows, vote ledgers, rating audits, duplicate cache reuse, and site workflows.
- Existing local drafts covered ListPages rating parsing, returned rating action points, rating action status, public vote input values, direct page identity construction, and direct page count construction, but did not cover direct `Page(rating=...)` construction.
- Existing unit fixtures intentionally allow `rating_percent` and some broader parser metadata to be nullable. This slice preserves that pattern and validates only `rating`.
- This slice does not change parser extraction, page write behavior, page ID/source/revision/file/vote acquisition, cached state, live Wikidot behavior, `rating_percent`, rating range semantics, user/timestamp metadata, tags, parent fullname, or parent site validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change rejects malformed rating values rather than coercing them. Booleans are rejected even though `bool` is a subclass of `int`; negative integers, zero, and floating-point values remain governed by existing semantics because this slice validates type integrity, not rating-system range rules.
