# PR Draft: Validate Non-Negative Page Metrics

## Summary

`Page` records store scalar page metrics used by browser-free page inventories, source/revision/file/vote ledgers, `latest_revision`, edit result reconciliation, duplicate-cache reuse, publication checks, migration tooling, and generated audit rows. Issue 482 validated that direct `Page.children_count`, `comments_count`, `size`, `votes_count`, and `revisions_count` values are non-boolean integers, but it intentionally left negative integers under existing semantics. One follow-up gap remained: direct `Page(...)` construction accepted impossible negative counts and byte sizes, and ListPages-generated negative count fields parsed as ordinary integers before becoming stored page state.

This change validates the five page count/size fields as non-negative integers. Direct negative constructor values now raise field-specific diagnostics such as `ValueError("children_count must be non-negative")`. ListPages-generated negative `comments`, `size`, `children`, `rating_votes`, and `revisions` values now raise contextual `NoElementException` diagnostics with site, page, field, and value. Zero counts and zero page size remain valid, and negative page ratings remain valid because page ratings can be negative.

## Outcome

Direct and parser-created `Page` records can no longer store negative count or size metrics, while valid zero metrics, valid positive metrics, signed page ratings, parser field context, and adjacent page workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use ListPages page inventories, source collection, publishing checks, revision/file/vote ledgers, duplicate page-cache reuse, generated audit rows, migration tooling, local fixtures, or rehydrated `Page` objects.

## Current Evidence

Local rollout-backed drafts already establish page count metadata as operationally meaningful. [239-pr-listpages-integer-field-parse-context.md](239-pr-listpages-integer-field-parse-context.md) validates malformed generated ListPages integer cells before parsed `Page` construction. [153-pr-latest-revision-failure-context.md](153-pr-latest-revision-failure-context.md), [196-pr-page-property-site-context.md](196-pr-page-property-site-context.md), and [262-pr-page-edit-revision-count-sync.md](262-pr-page-edit-revision-count-sync.md) show `revisions_count` affects page revision selection and edit reconciliation. [482-pr-validate-page-constructor-count-fields.md](482-pr-validate-page-constructor-count-fields.md) validates count and size field integer type. [632-pr-validate-non-negative-page-file-sizes.md](632-pr-validate-non-negative-page-file-sizes.md) is the adjacent non-negative byte-size follow-up pattern for page attachments.

This slice is not a duplicate of Issue 482. Issue 482 validated integer type and boolean rejection for direct page count fields, and its additional notes explicitly left negative integers to existing semantics. This follow-up covers the separate domain invariant that counts and byte sizes cannot be negative, while preserving zero and signed page ratings. This slice is also not a duplicate of Issue 239, which validates malformed non-integer ListPages values such as `not-a-number`; this follow-up covers parseable but impossible negative generated count values.

## Related Issue / Non-Duplicate Analysis

Builds directly on [239-pr-listpages-integer-field-parse-context.md](239-pr-listpages-integer-field-parse-context.md), [482-pr-validate-page-constructor-count-fields.md](482-pr-validate-page-constructor-count-fields.md), and [632-pr-validate-non-negative-page-file-sizes.md](632-pr-validate-non-negative-page-file-sizes.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a shared page non-negative integer-field validator that preserves existing non-boolean integer diagnostics.
- Validate `Page.children_count`, `Page.comments_count`, `Page.size`, `Page.votes_count`, and `Page.revisions_count` through that non-negative helper during `Page.__post_init__`.
- Add a ListPages non-negative integer parser wrapper for `rating_votes`, `comments`, `size`, `children`, and `revisions`.
- Preserve signed `rating` parsing and direct negative `Page.rating` values.
- Preserve zero values for all five count/size metrics.
- Preserve existing parser-created pages, direct page construction, search, `Page.latest_revision`, edit revision-count sync, page source/revision/file/vote workflows, and site workflows.

## Type Of Change

- Input validation
- Parser diagnostics
- Public dataclass constructor behavior hardening
- Page metric state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `Page(children_count=-1)`, `comments_count=-1`, `size=-1`, `votes_count=-1`, and `revisions_count=-1` must raise `ValueError("<field> must be non-negative")`. |
| R2 | Direct zero values for all five fields must remain valid. |
| R3 | Existing malformed type diagnostics for all five fields must remain `ValueError("<field> must be an integer")`. |
| R4 | ListPages-generated negative count/size fields must raise contextual `NoElementException` with site, page, field, and raw value. |
| R5 | Signed page ratings must remain valid for direct construction and regular ListPages rating parsing. |
| R6 | Parser-created pages, search, `Page.latest_revision`, edit revision-count sync, page source/revision/file/vote workflows, and site workflows must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, constructor tests, parse/search tests, adjacent page workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative direct count/size metrics fail at the public constructor boundary. | `TestPageInit.test_init_rejects_negative_counts` failed RED for 5 fields with `DID NOT RAISE`, then passed GREEN after `_validate_page_non_negative_integer_field(...)` was added. | Accepting negative page metrics, coercing them to zero, or deferring failure to later page workflows rejects this local completion claim. | Page constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Zero page metrics remain valid. | `TestPageInit.test_init_allows_zero_counts` passed in RED and GREEN and asserts all five fields store `0`. | Rejecting zero counts or requiring positive page metrics rejects this local completion claim. | Page constructor compatibility | `tests/unit/test_page_constructor.py` |
| R3 | Existing malformed-type diagnostics remain stable. | `TestPageInit.test_init_rejects_malformed_counts` passed in the focused RED and GREEN commands. | Changing type diagnostics, accepting booleans as integers, or coercing strings/floats rejects this local completion claim. | Page constructor type validation | `tests/unit/test_page_constructor.py` |
| R4 | Negative generated ListPages count values fail with parser context. | `TestPageCollectionParse.test_parse_negative_count_field_includes_site_page_and_value_context` failed RED with `DID NOT RAISE`, then passed GREEN with `NoElementException("ListPages integer field must be non-negative ...")`. | Returning a `Page` with negative generated counts, raising a raw constructor `ValueError`, omitting site/page/field/value context, or silently clamping the value rejects this local completion claim. | ListPages parser | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Signed page ratings remain valid. | `TestPageInit.test_init_accepts_negative_rating` and `TestPageCollectionParse.test_parse_malformed_rating_includes_site_page_and_value_context` stayed green in the focused RED and GREEN commands. | Applying non-negative validation to `rating` or changing regular rating integer parsing rejects this local completion claim. | Page rating compatibility | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py` |
| R6 | Existing page workflows remain green. | Page constructor coverage passed 176 tests, parse/search coverage passed 49 tests, adjacent page/page-constructor/site/page-file/page-votes/page-revision coverage passed 1034 tests, and full unit coverage passed 2856 tests. | Regressing valid fixture construction, parser-created pages, search pagination, `Page.latest_revision`, edit count sync, page lookup, source/revision/file/vote workflows, or site workflows rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_page_revision.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic `Page` or ListPages fixture data only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw ListPages HTML from real sites, page source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `ef9a925 fix(page): validate non-negative page metrics`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_negative_counts tests/unit/test_page_constructor.py::TestPageInit::test_init_allows_zero_counts tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_negative_rating tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_counts tests/unit/test_page.py::TestPageCollectionParse::test_parse_negative_count_field_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_integer_field_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_rating_includes_site_page_and_value_context -q` failed 6 new negative-metric cases before the fix with `DID NOT RAISE`; zero-count, negative-rating, malformed count-type, malformed integer, and regular rating parser guards stayed green.
- GREEN: the same focused command passed 30 tests after constructor and parser non-negative validation was added.
- `uv run pytest tests/unit/test_page_constructor.py -q` passed 176 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionParse tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed 49 tests.
- `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_page_revision.py -q` passed 1034 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py tests/unit/test_page.py` left 3 files unchanged.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page_constructor.py tests/unit/test_page.py` passed.
- `uv run pytest tests/unit -q` passed 2856 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page(children_count=-1)`, `Page(comments_count=-1)`, `Page(size=-1)`, `Page(votes_count=-1)`, and `Page(revisions_count=-1)` raise the matching `ValueError("<field> must be non-negative")`.
- `Page(children_count=0, comments_count=0, size=0, votes_count=0, revisions_count=0)` remains valid.
- Existing malformed type inputs for those five fields still raise `ValueError("<field> must be an integer")`.
- A generated ListPages `comments=-1` field raises `NoElementException("ListPages integer field must be non-negative for site: test-site, page: scp-001 (field=comments, value=-1)")`.
- Regular signed page ratings remain valid and continue using the existing integer parser behavior.
- Existing parser-created pages, page search, `Page.latest_revision`, edit revision-count sync, page source/revision/file/vote workflows, and site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Page metrics describe counts and byte sizes, so negative values are impossible page state. Parser-side integer conversion already makes malformed textual values visible; this follow-up catches parseable but impossible negatives while preserving signed page ratings and zero-count compatibility. Direct constructor validation keeps generated ledgers, local fixtures, rehydrated records, and downstream audit tooling from carrying impossible page metrics.

## Local Evidence

- Local rollout evidence used page count metadata in ListPages inventories, page detail ledgers, source/revision/file/vote acquisition, duplicate cache reuse, edit reconciliation, and site workflows.
- Existing local drafts covered ListPages integer parsing, latest-revision failure context, edit revision-count sync, direct page ID/source/revisions/votes assignments, direct page count-field type validation, and non-negative PageFile size validation, but did not cover negative Page metrics.
- The focused RED failures showed negative direct page metrics and negative generated ListPages counts were accepted as page state. The GREEN regressions cover negative values, zero compatibility, pre-existing malformed type validation, negative rating compatibility, and contextual parser diagnostics.
- This slice only validates non-negative page count/size metrics. It does not change `rating`, `rating_percent`, direct page lookup, parser selectors, page write behavior, page ID/source/revision/file/vote acquisition, cached state, live Wikidot behavior, user/timestamp metadata, tags, parent fullname, or parent site validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, raw ListPages HTML from real sites, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates page count and size metrics only. `Page.rating` remains signed because Wikidot PM-style page ratings can be negative; `rating_percent` range validation remains separate because the 5-star percentage path has its own parser semantics.
