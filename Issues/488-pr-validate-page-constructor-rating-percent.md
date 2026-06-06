# PR Draft: Validate Page Constructor Rating Percent

## Summary

`Page.rating_percent` stores normalized 5-star rating percentage metadata from generated ListPages rows and local page fixtures. It is intentionally nullable: non-5-star rating rows and some direct fixtures represent unavailable 5-star percentage data as `None`. Parser-side ListPages handling already converts valid 5-star percentage text into a numeric fraction and reports malformed generated `rating_percent` values with contextual parser diagnostics, but direct `Page(...)` construction still accepted malformed non-null values such as booleans, strings, lists, dictionaries, or arbitrary objects.

This change validates the direct constructor's `rating_percent` field during `Page.__post_init__`. `None` remains valid, integer and floating-point numeric values remain valid, and booleans or non-numeric values now raise `ValueError("rating_percent must be an integer, float, or None")`. The `Page` dataclass annotation and docstring now match the already-observed nullable fixture/parser behavior.

## Outcome

Directly constructed `Page` objects now fail early when optional 5-star rating-percent metadata is malformed, while preserving `None` for unavailable values and preserving numeric values from parsers, fixtures, and create-page fallback state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build page inventories, rating audits, ListPages metadata ledgers, source/revision/file/vote workflows, local fixtures, or rehydrated `Page` objects.

## Current Evidence

[240-pr-listpages-rating-field-parse-context.md](240-pr-listpages-rating-field-parse-context.md) already validates malformed generated `rating_percent` text at the ListPages parser boundary. [483-pr-validate-page-constructor-rating-field.md](483-pr-validate-page-constructor-rating-field.md) validates direct `Page.rating` values but explicitly leaves `rating_percent` behavior unchanged. Recent direct `Page` constructor slices validate identity, counts, rating, parent fullname, tags, site, and nullable user/timestamp metadata, but each one preserves or explicitly excludes `rating_percent`.

Those prior slices are not duplicates. Issue 240 validates parser conversion from Wikidot HTML to page params. Issue 483 validates the separate scalar `rating` field, not `rating_percent`. Issues 481 through 487 validate other direct `Page` fields only. None validates direct `Page(rating_percent=...)` construction before malformed non-null rating-percent state is stored.

## Related Issue / Non-Duplicate Analysis

Builds directly on [240-pr-listpages-rating-field-parse-context.md](240-pr-listpages-rating-field-parse-context.md), [483-pr-validate-page-constructor-rating-field.md](483-pr-validate-page-constructor-rating-field.md), and the direct `Page` constructor hardening in [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md) through [487-pr-validate-page-constructor-nullable-metadata.md](487-pr-validate-page-constructor-nullable-metadata.md).

No upstream issue was filed from this local workspace.

## Changes

- Add nullable `rating_percent` validation for direct `Page(...)` construction.
- Preserve `rating_percent=None` for non-5-star or unavailable percentage metadata.
- Preserve numeric integer and floating-point rating-percent values without coercion.
- Reject booleans and non-numeric values with a stable `ValueError` diagnostic.
- Update `Page` dataclass annotations and docstring to match the actual nullable behavior.
- Add constructor tests for valid `None`/numeric values and malformed non-null values.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Nullable rating metadata typing correction
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(rating_percent=...)` must accept `None`, integers, and floats. |
| R2 | `Page(rating_percent=...)` must reject booleans and non-numeric values with `ValueError("rating_percent must be an integer, float, or None")`. |
| R3 | Valid page construction, parser-created pages, ListPages rating-percent parsing, page source/revision/file/vote workflows, and site workflows must remain unchanged. |
| R4 | This slice must not validate rating-percent range semantics, `Page.rating`, parent site, tags, user fields, timestamp fields, cached source/revisions/votes/files, live request behavior, or parser-side rating conversion. |
| R5 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, constructor tests, adjacent page/site/page-file/page-vote/page-revision tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None`, integer, and floating-point rating-percent values remain accepted and stored unchanged. | `TestPageInit.test_init_accepts_valid_rating_percent` passed RED and GREEN for `None`, `0.0`, `0.75`, and `1`. | Rejecting unavailable percentage metadata or coercing numeric values rejects this local completion claim. | `Page` constructor rating-percent state | `tests/unit/test_page_constructor.py` |
| R2 | Malformed non-null rating-percent values fail at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_rating_percent` failed RED for 5 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, strings, lists, dictionaries, arbitrary objects, or silently coercing malformed values rejects this local completion claim. | `Page` constructor rating-percent state | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Existing page workflows remain green. | Constructor tests passed 103 tests; adjacent page/site/page-file/page-vote/page-revision tests passed 827 tests; full unit tests passed 2085 tests. | Regressing parser-created pages, ListPages rating-percent parsing, direct page fixtures, page collection behavior, page source/revision/file/vote workflows, or site workflows rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_page_revision.py`, `tests/unit` |
| R4 | Broader rating and parser semantics remain outside scope. | Existing parser-side rating tests and adjacent tests remain green; this slice only validates direct constructor type integrity. | Adding range checks, changing `Page.rating`, changing parser conversion, changing cached state, or touching live request behavior rejects this local completion claim. | Page constructor scope | `src/wikidot/module/page.py`, adjacent tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `c9febc9 fix(page): validate rating percent`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_rating_percent tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_rating_percent -q` failed 5 malformed non-null `rating_percent` cases before the fix; each malformed case reported `DID NOT RAISE`, while the 4 valid cases passed.
- GREEN: the same focused command passed 9 tests after `rating_percent` validation was added.
- `uv run pytest tests/unit/test_page_constructor.py -q` passed 103 tests.
- `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_page_revision.py -q` passed 827 tests.
- `uv run pytest tests/unit -q` passed 2085 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 44 existing full-tree test typing errors outside this slice, including intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client/mock typing, invalid test cookie arguments, and existing site test mock typing issues. The changed source file and touched test module pass pyright together.

## Acceptance Criteria

- `Page(rating_percent=None)`, `Page(rating_percent=0.0)`, `Page(rating_percent=0.75)`, and `Page(rating_percent=1)` remain accepted and store the value unchanged.
- `Page(rating_percent=True)`, `Page(rating_percent="0.75")`, `Page(rating_percent=[])`, `Page(rating_percent={})`, and `Page(rating_percent=object())` raise `ValueError("rating_percent must be an integer, float, or None")` when every other constructor field is valid.
- Existing parser-created pages, ListPages rating-percent parsing, direct page fixtures, page collection behavior, page lookup behavior, page source/revision/file/vote workflows, and site workflows remain green.
- The new tests use unit-level code only and do not validate rating-percent range semantics, `Page.rating`, parser-side rating conversion, live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`rating_percent` is small metadata, but malformed non-null values can pollute inventories and generated ledgers long after construction. Parser-side malformed percentage text already fails with context, so direct construction should preserve the same type integrity while retaining `None` for unavailable non-5-star metadata.

## Local Evidence

- Local rollout evidence used page ratings and rating-percent metadata in page inventories, ListPages parsing, rating audits, and source/revision/file/vote workflows.
- Existing local drafts covered parser-side generated `rating_percent` diagnostics and direct `Page.rating` validation, but did not cover direct nullable `Page.rating_percent` construction.
- Existing unit fixtures already relied on `rating_percent=None` being valid for non-5-star or unavailable percentage metadata, so this change validates only malformed non-null values.
- This slice does not change parser extraction, page write behavior, collection inference behavior, query serialization, page ID/source/revision/file/vote acquisition logic, cached state, live Wikidot behavior, site client internals, `Page.rating`, rating-percent range semantics, user/timestamp metadata, tags, parent fullname, or URL syntax validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The validator rejects booleans even though `bool` is a subclass of `int`. It does not add range checks because this slice is about constructor type integrity, not rating-system semantics.
