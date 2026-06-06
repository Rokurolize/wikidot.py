# PR Draft: Validate Page Constructor Parent Fullname

## Summary

`Page.parent_fullname` stores the optional parent page identity used by browser-free page inventories, metadata updates, publish ledgers, rehydrated workflow state, and local audit rows. Write-side parent helpers already validate `parent_fullname` as `str | None`, and successful empty-string clears are already normalized to `None` after parent metadata writes. Before this change, direct `Page(...)` construction still accepted malformed parent values such as `parent_fullname=True`, `parent_fullname=3`, or `parent_fullname=[]`, and it stored `parent_fullname=""` as an empty string instead of the established no-parent state.

This change validates the direct constructor's `parent_fullname` field during `Page.__post_init__` by reusing the existing `_normalize_parent_fullname(...)` helper. Malformed parent values now raise `ValueError("parent_fullname must be a string or None")`; valid parent strings are preserved; `None` and `""` both store `None`. Valid page construction, parser-created pages, parent write/publish behavior, page source/revision/file/vote workflows, and site workflows remain unchanged.

## Outcome

Callers cannot silently construct `Page` objects with malformed parent metadata, and direct empty-string parent state now matches the existing write-path clear semantics.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page inventories, parent metadata writes, page publishing checks, source/revision/file/vote ledgers, generated audit rows, migration tooling, local fixtures, or rehydrated `Page` objects.

## Current Evidence

Local rollout-backed drafts already establish page parent metadata as operationally meaningful. Parent write drafts such as [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md) reject malformed parent values before direct parent writes, batched metadata writes, or high-level publish workflows. Empty-clear normalization in [265-pr-page-empty-parent-clear-normalization.md](265-pr-page-empty-parent-clear-normalization.md) ensures successful `Page.set_parent("")` and `Page.set_metadata(parent_fullname="")` leave local `parent_fullname is None`. Recent direct-constructor hardening in [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md), [482-pr-validate-page-constructor-count-fields.md](482-pr-validate-page-constructor-count-fields.md), and [483-pr-validate-page-constructor-rating-field.md](483-pr-validate-page-constructor-rating-field.md) validates adjacent page identity, count, and rating metadata boundaries.

Those prior slices are not duplicates. Issue 265 normalizes successful write-side empty parent clears after action status validation. Issue 343 validates public write/publish inputs before remote writes or local parent mutation. Issues 481, 482, and 483 validate direct page identity, count, and rating fields only. None validates direct `Page(parent_fullname=...)` construction before malformed or inconsistent parent state is stored.

## Related Issue / Non-Duplicate Analysis

Builds directly on the parent metadata and constructor surfaces documented by [265-pr-page-empty-parent-clear-normalization.md](265-pr-page-empty-parent-clear-normalization.md), [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md), [482-pr-validate-page-constructor-count-fields.md](482-pr-validate-page-constructor-count-fields.md), and [483-pr-validate-page-constructor-rating-field.md](483-pr-validate-page-constructor-rating-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `Page.parent_fullname` during `Page.__post_init__` with the existing `_normalize_parent_fullname(...)` helper.
- Reject malformed direct parent values with stable `ValueError("parent_fullname must be a string or None")`.
- Preserve valid parent strings and `None`.
- Normalize direct constructor `parent_fullname=""` to `None`, matching existing write-path clear semantics.
- Preserve parser-created pages, parent writes, metadata writes, publish workflows, and adjacent page/site behavior.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(parent_fullname=...)` must reject non-string, non-`None` values with `ValueError("parent_fullname must be a string or None")`. |
| R2 | `Page(parent_fullname="")` must store `parent_fullname is None`, matching existing parent-clear semantics. |
| R3 | `Page(parent_fullname="parent-page")` and `Page(parent_fullname=None)` must remain valid. |
| R4 | Valid `Page` construction, parser-created pages, parent writes, metadata writes, publish workflows, page source/revision/file/vote workflows, and site workflows must remain unchanged. |
| R5 | This slice must not validate parent name syntax, tags, users, timestamps, `rating_percent`, cached source/revisions/votes/files, parent site, or other parser-derived nullable metadata. |
| R6 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, constructor tests, adjacent page/site/page-file/page-vote tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct `Page.parent_fullname` values fail at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_parent_fullname` failed RED for 3 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, numbers, lists, arbitrary non-string objects, or silently coercing malformed values rejects this local completion claim. | `Page` constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Direct empty-string parent construction normalizes to no-parent state. | `TestPageInit.test_init_accepts_valid_parent_fullname` failed RED for `parent_fullname=""` because the constructor stored `""`, then passed GREEN after `_normalize_parent_fullname(...)` was reused. | Leaving direct constructor `parent_fullname == ""` rejects this local completion claim. | `Page` constructor parent state | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Valid parent string and `None` inputs remain accepted. | The same focused test passed for `"parent-page"` and `None`; adjacent parent write/publish tests stayed green. | Rejecting valid parent strings, rejecting `None`, or changing non-empty parent strings rejects this local completion claim. | Page constructor and parent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py` |
| R4 | Existing valid page and site workflows remain green. | `tests/unit/test_page_constructor.py` passed 49 tests; adjacent page/site/page-file/page-vote tests passed 676 tests; full unit tests passed 2031 tests. | Regressing valid fixture construction, parser-created pages, parent writes, metadata writes, publish behavior, page lookup, page source/revision/file/vote workflows, or site workflows rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit` |
| R5 | Broader parser metadata remains outside scope. | Existing nullable parser metadata fixture patterns remain unchanged and adjacent tests stay green. | Validating or changing parent name syntax, tags, users, timestamps, `rating_percent`, cached state, parent site, or other parser-derived nullable metadata rejects this local completion claim. | Page constructor scope | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py`, adjacent tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `3e9e051 fix(page): validate constructor parent fullname`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_parent_fullname tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_parent_fullname -q` failed 4 tests before the fix: `parent_fullname=""` stayed as an empty string, and malformed values reported `DID NOT RAISE`.
- GREEN: the same focused command passed 6 tests after constructor parent normalization was added.
- `uv run pytest tests/unit/test_page_constructor.py -q` passed 49 tests.
- `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py -q` passed 676 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed.
- `uv run mypy src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2031 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client/mock typing, invalid test cookie arguments, and existing site test mock typing issues. The changed source file and constructor test module pass pyright together.

## Acceptance Criteria

- `Page(parent_fullname=True)`, `Page(parent_fullname=3)`, and `Page(parent_fullname=[])` raise `ValueError("parent_fullname must be a string or None")` when every other constructor field is valid.
- `Page(parent_fullname="")` stores `parent_fullname is None`.
- `Page(parent_fullname="parent-page")` stores `"parent-page"` unchanged.
- `Page(parent_fullname=None)` stores `None`.
- Existing parser-created pages, direct page fixtures, parent write/publish behavior, page lookup behavior, page source/revision/file/vote workflows, and site workflows remain green.
- The new tests use unit-level code only and do not validate parent name syntax, tags, users, timestamps, `rating_percent`, broader `Page` metadata, require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Parent page state affects browser-free publishing, metadata ledgers, page inventories, and generated workflow records. Write-side APIs already define `None` and `""` as parent clears and reject values outside `str | None`, so this change is intentionally conservative: it applies the same local parent-state contract to direct `Page(...)` construction.

## Local Evidence

- Local rollout evidence used parent metadata in browser-free publish workflows, metadata writes, page inventories, generated ledgers, and local audit rows.
- Existing local drafts covered write-side parent input validation and empty-string clear normalization, but did not cover direct `Page(parent_fullname=...)` construction.
- Existing unit fixtures use `None` or valid parent strings, and adjacent tests prove write/publish parent behavior remains unchanged.
- This slice does not change parser extraction, page write behavior, page ID/source/revision/file/vote acquisition, cached state, live Wikidot behavior, parent name syntax, user/timestamp metadata, tags, `rating_percent`, or parent site validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change rejects malformed parent values rather than coercing them. Empty strings are normalized because the existing parent-write contract already treats `""` as a clear and stores the no-parent state as `None`.
