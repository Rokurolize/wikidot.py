# PR Draft: Validate Page Rating Percent Range

## Summary

`Page.rating_percent` stores normalized 5-star rating percentage metadata from generated ListPages rows and local page fixtures. Issue 488 validated nullable numeric type at the direct constructor boundary, and Issue 240 validated malformed generated rating-percent text, but both explicitly left range semantics unchanged. The `Page` docstring already defines `rating_percent` as a normalized percentage value in the 5-star rating system, `0.0 to 1.0`; direct construction still accepted impossible values such as `-0.01`, `1.01`, `nan`, and infinities, and generated 5-star ListPages cells such as `-1%`, `101%`, `nan%`, and `inf%` became stored page state after float parsing.

This change validates rating-percent values as finite bounded percentages. Direct `Page(rating_percent=...)` values must be `None` or finite numbers between `0.0` and `1.0`, inclusive. Generated 5-star ListPages percentage text must be finite and between `0.0%` and `100.0%` before normalization. Valid `None`, `0.0`, `0.75`, `1`, malformed-type diagnostics, malformed generated text diagnostics, signed page ratings, parser-created pages, and adjacent page workflows remain unchanged.

## Outcome

Direct and parser-created `Page` records can no longer store out-of-range or non-finite 5-star rating percentages, while unavailable non-5-star percentages, valid boundary percentages, malformed-type/type-context diagnostics, signed page ratings, and ListPages search behavior remain compatible.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use ListPages page inventories, rating audits, source/revision/file/vote ledgers, generated migration or moderation rows, local fixtures, serialized/rehydrated `Page` records, or publish-adjacent verification flows that rely on normalized 5-star rating metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify ListPages page inventories and direct `Page` records as practical workflow surfaces. [240-pr-listpages-rating-field-parse-context.md](240-pr-listpages-rating-field-parse-context.md) routes malformed generated `rating_percent` text through contextual parser errors. [483-pr-validate-page-constructor-rating-field.md](483-pr-validate-page-constructor-rating-field.md) validates direct `Page.rating` types while preserving signed and floating 5-star rating values. [488-pr-validate-page-constructor-rating-percent.md](488-pr-validate-page-constructor-rating-percent.md) validates nullable numeric `rating_percent` types but explicitly excludes rating-percent range semantics. [633-pr-validate-non-negative-page-metrics.md](633-pr-validate-non-negative-page-metrics.md) validates page count and byte-size metrics while explicitly leaving `rating_percent` range validation separate because the 5-star percentage parser path has its own semantics.

This slice is not a duplicate of Issue 488. Issue 488 rejects booleans, strings, lists, dictionaries, and arbitrary objects for direct `rating_percent`, but it still accepts numeric values outside the documented normalized range. This slice is also not a duplicate of Issue 240, which rejects non-float generated percentage text such as `not-a-percent`; this follow-up covers parseable but impossible or non-finite generated values. This slice is adjacent to, but separate from, Issue 633 because page count/size metrics are non-negative integer state while `rating_percent` is nullable finite normalized 5-star metadata.

## Related Issue / Non-Duplicate Analysis

Builds directly on [240-pr-listpages-rating-field-parse-context.md](240-pr-listpages-rating-field-parse-context.md), [483-pr-validate-page-constructor-rating-field.md](483-pr-validate-page-constructor-rating-field.md), [488-pr-validate-page-constructor-rating-percent.md](488-pr-validate-page-constructor-rating-percent.md), and [633-pr-validate-non-negative-page-metrics.md](633-pr-validate-non-negative-page-metrics.md).

No upstream issue was filed from this local workspace.

## Changes

- Add finite range validation to direct `Page.rating_percent` values after the existing nullable numeric type check.
- Reject direct out-of-range or non-finite rating percentages with `ValueError("rating_percent must be between 0.0 and 1.0, or None")`.
- Add a ListPages percentage parser helper that preserves existing malformed-float diagnostics, then rejects non-finite or out-of-range raw percent text with contextual `NoElementException`.
- Validate generated 5-star `rating_percent` cells as raw `0.0..100.0` percentages before normalizing to `0.0..1.0`.
- Preserve `rating_percent=None` for non-5-star or unavailable metadata.
- Preserve valid normalized percentage boundaries, signed `Page.rating`, malformed-type diagnostics, malformed generated text diagnostics, parser-created pages, page search, source/revision/file/vote workflows, and site workflows.

## Type Of Change

- Input validation
- Parser diagnostics
- Public dataclass constructor behavior hardening
- Page rating metadata state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `Page(rating_percent=-0.01)`, `1.01`, `nan`, `inf`, and `-inf` must raise `ValueError("rating_percent must be between 0.0 and 1.0, or None")`. |
| R2 | Direct `Page(rating_percent=None)`, `0.0`, `0.75`, and `1` must remain valid and stored unchanged. |
| R3 | Existing malformed direct type diagnostics must remain `ValueError("rating_percent must be an integer, float, or None")`. |
| R4 | Generated 5-star ListPages `rating_percent` values `-1%`, `101%`, `nan%`, and `inf%` must raise contextual `NoElementException` with site, page, field, and raw percent text. |
| R5 | Existing malformed generated percentage text such as `not-a-percent` must keep the existing contextual float-field malformed diagnostic. |
| R6 | Signed page ratings, valid 5-star rating parsing, non-5-star `rating_percent=None`, parser-created pages, search, page source/revision/file/vote workflows, and site workflows must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, page constructor tests, ListPages parse/search tests, adjacent page workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Impossible direct normalized percentage values fail at the public constructor boundary. | `TestPageInit.test_init_rejects_out_of_range_rating_percent` failed RED for 5 values with `DID NOT RAISE`, then passed GREEN after `_validate_page_rating_percent_field(...)` checked finite `0.0..1.0`. | Accepting impossible percentages, accepting `nan`/infinities, clamping values, or silently coercing values rejects this local completion claim. | Page constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Valid direct nullable and boundary percentages remain accepted. | `TestPageInit.test_init_accepts_valid_rating_percent` passed in the focused RED and GREEN runs for `None`, `0.0`, `0.75`, and `1`. | Rejecting unavailable metadata, rejecting zero or full percentages, or coercing valid values rejects this local completion claim. | Page constructor compatibility | `tests/unit/test_page_constructor.py` |
| R3 | Existing malformed direct type diagnostics remain stable. | `TestPageInit.test_init_rejects_malformed_rating_percent` passed in the focused RED and GREEN commands. | Changing the malformed-type message, accepting booleans as numbers, or coercing strings/lists/dicts rejects this local completion claim. | Page constructor type validation | `tests/unit/test_page_constructor.py` |
| R4 | Impossible generated 5-star percentage cells fail with parser context before normalized page state is created. | `TestPageCollectionParse.test_parse_out_of_range_rating_percent_includes_site_page_and_value_context` failed RED for 4 generated values with `DID NOT RAISE`, then passed GREEN with contextual `NoElementException`. | Returning a `Page` with invalid `rating_percent`, raising a raw constructor `ValueError`, omitting site/page/field/value context, or silently clamping generated values rejects this local completion claim. | ListPages parser | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Existing malformed generated text diagnostics remain stable. | `TestPageCollectionParse.test_parse_malformed_rating_percent_includes_site_page_and_value_context` passed in the focused RED and GREEN commands. | Treating malformed text as a range error, changing `ListPages float field is malformed`, or dropping raw value context rejects this local completion claim. | ListPages parser compatibility | `tests/unit/test_page.py` |
| R6 | Existing page workflows remain green. | Page constructor coverage passed 181 tests, parse/search coverage passed 53 tests, adjacent page/page-constructor/site/page-file/page-votes/page-revision coverage passed 1043 tests, and full unit coverage passed 2874 tests. | Regressing signed ratings, valid 5-star ratings, non-5-star `rating_percent=None`, page search, parser-created pages, source/revision/file/vote acquisition, site page accessors, or page mutation boundaries rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_page_revision.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic `Page` construction or generated fixture data only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw ListPages HTML from real sites, page source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, page and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4d860e2 fix(page): validate rating percent range`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_rating_percent tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_rating_percent tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_out_of_range_rating_percent tests/unit/test_page.py::TestPageCollectionParse::test_parse_with_5star_rating_percent tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_rating_percent_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_out_of_range_rating_percent_includes_site_page_and_value_context -q` failed 9 new out-of-range/non-finite rating-percent cases before the fix with `DID NOT RAISE`; 11 valid and malformed-type/text guard cases stayed green.
- GREEN: the same focused command passed 20 tests after constructor and parser range validation was added.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py tests/unit/test_page.py` left 3 files unchanged.
- `uv run pytest tests/unit/test_page_constructor.py -q` passed 181 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionParse tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed 53 tests.
- `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_page_revision.py -q` passed 1043 tests.
- `uv run pytest tests/unit -q` passed 2874 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page(rating_percent=-0.01)`, `Page(rating_percent=1.01)`, `Page(rating_percent=float("nan"))`, `Page(rating_percent=float("inf"))`, and `Page(rating_percent=-float("inf"))` raise `ValueError("rating_percent must be between 0.0 and 1.0, or None")`.
- `Page(rating_percent=None)`, `Page(rating_percent=0.0)`, `Page(rating_percent=0.75)`, and `Page(rating_percent=1)` remain accepted and store the value unchanged.
- Existing malformed direct inputs still raise `ValueError("rating_percent must be an integer, float, or None")`.
- Generated 5-star ListPages `rating_percent=-1%`, `101%`, `nan%`, and `inf%` raise `NoElementException("ListPages percentage field must be between 0.0 and 100.0 for site: test-site, page: test-page (field=rating_percent, value=<raw>)")`.
- Generated 5-star ListPages `rating_percent=not-a-percent` keeps the existing malformed float diagnostic.
- Signed `Page.rating`, valid 5-star `rating`, non-5-star `rating_percent=None`, parser-created pages, page search, source/revision/file/vote workflows, and site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`rating_percent` is documented and stored as normalized 5-star percentage metadata. Numeric-but-impossible values are more dangerous than malformed strings because they can move through inventories, generated ledgers, and fixtures as apparently valid page state. Range validation keeps the public constructor and generated parser path aligned with the documented `0.0..1.0` invariant while preserving nullable non-5-star metadata and signed page ratings.

## Local Evidence

- Local rollout evidence used ListPages page inventories, rating metadata, source/revision/file/vote ledgers, generated migration or moderation rows, local fixtures, serialized records, and publish-adjacent checks.
- Existing local drafts covered malformed generated rating-percent text, direct nullable numeric type validation, and non-negative page count/size metrics, but did not cover numeric range or non-finite percentage values.
- The focused RED failures showed direct out-of-range/non-finite normalized percentages and generated out-of-range/non-finite raw percent cells were accepted as stored page state. The GREEN regressions cover invalid values, valid nullable/boundary compatibility, existing malformed type validation, existing malformed parser text validation, and contextual parser diagnostics.
- This slice only validates `rating_percent` range semantics. It does not change `Page.rating`, ListPages request construction, pagination, retry policy, source iteration, direct field scoping, string/date/user/tag parsing, returned page object shape beyond invalid percentage rejection, page ID/source/revision/file/vote acquisition, cached state, page write behavior, live Wikidot behavior, or upstream actions.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, raw ListPages HTML from real sites, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

This change intentionally validates finite percentage bounds only for `rating_percent`. Signed `Page.rating` remains valid because Wikidot PM-style page ratings can be negative and 5-star `rating` values are separate from normalized `rating_percent` metadata.
