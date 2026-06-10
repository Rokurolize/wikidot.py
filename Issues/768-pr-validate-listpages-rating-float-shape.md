# PR Draft: Validate ListPages Rating Float Shape

## Summary

`PageCollection._parse(...)` treats generated 5-star `ListPagesModule` `rating` fields as floats. Issue 240 made malformed rating text such as `not-a-rating` contextual, and Issue 636 made `rating_percent` finite and range checked, but one accepted-value gap remained: Python `float(...)` accepts non-ASCII decimal digit glyphs such as `\uff14.\uff10` and non-finite values such as `nan` and `inf`. That let generated 5-star rating text become `4.0`, `nan`, or `inf` before the parser noticed that the generated scalar was not a finite ASCII value.

This change validates generated 5-star `rating` values as finite ASCII float text before storing them on a `Page`. Ordinary generated 5-star values such as `4.0` still parse normally. PM/integer `rating` fields keep the existing integer parser, and `rating_percent` keeps the existing percent parser and range diagnostics from Issue 636.

## Outcome

ListPages parsing no longer manufactures valid-looking or non-finite page ratings from non-ASCII digit glyphs or Python's non-finite float spellings. A generated 5-star `rating` field containing `\uff14.\uff10`, `nan`, or `inf` now fails at the ListPages parser boundary with site, page, field, and observed value context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use ListPages-backed page search, source iteration, metadata hydration, rating audits, required-tag ledgers, publication verification, migration tooling, reconciliation scripts, or generated fixtures where page ratings must reflect strict generated scalar fields.

## Current Evidence

Local rollout-backed drafts repeatedly identify ListPages as a practical read boundary for page discovery, source collection, metadata reconciliation, required-tag filtering, publication verification, migration tooling, and large-corpus audits. Existing local drafts cover ListPages pagination bounds, retry behavior, first-fetch response validation, field scoping, field spacing, field pager markup isolation, malformed integer diagnostics, malformed rating diagnostics, non-negative metric validation, pager page ASCII-shape validation, and integer field ASCII-shape validation.

This slice is not a duplicate of [240-pr-listpages-rating-field-parse-context.md](240-pr-listpages-rating-field-parse-context.md). Issue 240 covers malformed rating text that Python rejects outright, such as `not-a-rating`. This slice covers values that Python accepts and normalizes or converts to non-finite floats.

This slice is not a duplicate of [636-pr-validate-page-rating-percent-range.md](636-pr-validate-page-rating-percent-range.md). Issue 636 covers generated 5-star `rating_percent` values, including `nan%`, `inf%`, and out-of-range percentages. This slice covers generated 5-star `rating` values without a percent sign.

This slice is not a duplicate of [767-pr-validate-listpages-integer-field-ascii-shape.md](767-pr-validate-listpages-integer-field-ascii-shape.md). Issue 767 covers integer-backed ListPages fields such as `comments`, `size`, `children`, `revisions`, `rating_votes`, and non-5-star integer `rating`. This slice covers generated 5-star float `rating`.

This slice is not a duplicate of [483-pr-validate-page-constructor-rating-field.md](483-pr-validate-page-constructor-rating-field.md). Issue 483 covers direct `Page(...)` constructor rating state. This slice validates raw generated ListPages field text before page construction.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md), [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md), [240-pr-listpages-rating-field-parse-context.md](240-pr-listpages-rating-field-parse-context.md), [483-pr-validate-page-constructor-rating-field.md](483-pr-validate-page-constructor-rating-field.md), [636-pr-validate-page-rating-percent-range.md](636-pr-validate-page-rating-percent-range.md), and [767-pr-validate-listpages-integer-field-ascii-shape.md](767-pr-validate-listpages-integer-field-ascii-shape.md).

## Changes

- Add a finite ASCII float parser for generated 5-star ListPages `rating` fields.
- Reuse the existing contextual malformed-float diagnostic text for rejected generated 5-star rating values.
- Preserve the existing permissive malformed-float helper for `rating_percent`, where the percent helper owns finite and range validation.
- Preserve non-5-star PM `rating` parsing through the integer parser.
- Add a regression test that `\uff14.\uff10`, `nan`, and `inf` raise instead of returning a `Page`.

## Type Of Change

- Bug fix
- ListPages parser validation
- Generated scalar hardening
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Generated 5-star ListPages `rating` values with non-ASCII digit glyphs or non-finite float spellings must fail before being stored on a `Page`. |
| R2 | The malformed-float diagnostic must retain site, page, field, and observed scalar value context. |
| R3 | Valid generated 5-star ASCII finite rating values must continue to parse normally. |
| R4 | Non-5-star PM `rating` and generated 5-star `rating_percent` behavior must remain unchanged. |
| R5 | Existing malformed rating, malformed rating-percent, out-of-range rating-percent, integer field, ListPages search, page metadata, and adjacent page-facing workflows must remain compatible. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, real page HTML, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | RED/GREEN, page parser/search tests, page unit tests, adjacent page-facing tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A ListPages row with generated 5-star `rating=\uff14.\uff10`, `rating=nan`, or `rating=inf` raises before `Page.rating` can become `4.0`, `nan`, or `inf`. | `test_parse_rejects_malformed_5star_rating_float_shape` failed RED with 3 `DID NOT RAISE` cases, then passed after finite ASCII 5-star rating validation. | Returning a `Page`, storing a normalized Unicode-digit float, or storing a non-finite float rejects this local completion claim. | ListPages parser | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | The exception reports `ListPages float field is malformed for site: test-site, page: test-page (field=rating, value=...)`. | The regression asserts the exact contextual diagnostic for each rejected value. | Leaking a raw `ValueError`, omitting site/page/field/value, or reporting a generic missing-element error rejects this local completion claim. | ListPages diagnostics | focused test |
| R3 | Valid generated 5-star ASCII finite values still parse. | Focused GREEN included the valid 5-star rating-percent fixture and existing 5-star malformed-rating context test; page parser/search and full page tests stayed green. | Rejecting ordinary generated ASCII 5-star rating text rejects this local completion claim. | Valid ListPages parsing | focused and page tests |
| R4 | PM integer `rating` and `rating_percent` remain on their existing helpers. | Focused GREEN included PM rating, malformed `rating_percent`, out-of-range `rating_percent`, and valid 5-star `rating_percent` tests. | Changing PM rating from integer semantics, changing `nan%`/`inf%` range diagnostics, or changing valid percent behavior rejects this local completion claim. | Rating compatibility | focused tests |
| R5 | Existing page parse/search and adjacent page-facing behavior stays stable. | Page parser/search tests passed 58 tests, full `tests/unit/test_page.py` passed 400 tests, adjacent page-facing suites passed 1125 tests, and full unit passed 3774 tests. | Regressing ListPages search, page revisions, files, votes, site workflows, or any unit test rejects this local completion claim. | Page and site workflows | `tests/unit` |
| R6 | No live site state or private material is needed. | The regression uses synthetic ListPages HTML fixture mutation and local mocked parsing only. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, real page HTML, private account data, private page names, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | RED/GREEN, page parse/search tests, page unit tests, adjacent page-facing tests, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `391ed7e fix(page): validate listpages rating float shape`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_rejects_malformed_5star_rating_float_shape -q --tb=short` failed before the fix with 3 `DID NOT RAISE` cases for `\uff14.\uff10`, `nan`, and `inf`.
- GREEN focused parser slice before helper refactor: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_rejects_malformed_5star_rating_float_shape tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_5star_rating_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_rating_percent_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_out_of_range_rating_percent_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_with_5star_rating_percent tests/unit/test_page.py::TestPageCollectionParse::test_parse_with_pm_rating tests/unit/test_page.py::TestPageCollectionParse::test_parse_rejects_non_ascii_digit_integer_field -q --tb=short` passed 12 tests.
- GREEN focused parser slice after helper refactor and formatting: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_rejects_malformed_5star_rating_float_shape tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_5star_rating_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_rating_percent_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_out_of_range_rating_percent_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_with_5star_rating_percent tests/unit/test_page.py::TestPageCollectionParse::test_parse_with_pm_rating tests/unit/test_page.py::TestPageCollectionParse::test_parse_rejects_non_ascii_digit_integer_field -q --tb=short` passed 9 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionParse tests/unit/test_page.py::TestPageCollectionSearchPages -q --tb=short` passed 58 tests.
- `uv run pytest tests/unit/test_page.py -q --tb=short` passed 400 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q --tb=short` passed 1125 tests.
- `uv run pytest tests/unit -q --tb=short` passed 3774 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted after formatting `src/wikidot/module/page.py`.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no change-propagation, cognitive-load, duplication, accidental-complexity, dependency, domain-model, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker. Code pre-commit evidence reported `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.139.0"`, local clawpatch commit `d89ca91`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `PageCollection._parse(...)` raises `NoElementException("ListPages float field is malformed ...")` for generated 5-star `rating` values of `\uff14.\uff10`, `nan`, and `inf`.
- The parser does not construct a `Page` whose rating was normalized from non-ASCII digit glyphs.
- The parser does not construct a `Page` whose generated 5-star rating is `nan` or `inf`.
- The diagnostic includes site, page, field, and observed value context.
- Valid ASCII finite generated 5-star rating values still parse normally.
- PM/integer `rating` keeps the existing integer parser.
- Existing malformed 5-star rating diagnostics from Issue 240 remain unchanged for values such as `not-a-rating`.
- Existing `rating_percent` finite and range behavior from Issue 636 remains unchanged for values such as `nan%`, `inf%`, `-1%`, and `101%`.
- Existing ListPages integer field ASCII-shape behavior from Issue 767 remains unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw real page HTML, local rollout path, private account detail, private page name, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 240. Mitigation: Issue 240 covers values that cannot be parsed by `float(...)`; this slice covers accepted values that should not become generated ratings.
- Risk: This could be confused with Issue 636. Mitigation: Issue 636 covers `rating_percent`; this slice covers 5-star `rating`.
- Risk: This could be confused with Issue 767. Mitigation: Issue 767 covers integer field values; this slice covers float rating values.
- Risk: Tightening float parsing could reject unusual but valid generated Wikidot field text. Mitigation: the change only rejects non-ASCII scalar text and non-finite values, while valid generated finite ASCII rating text remains covered by existing fixtures.
- Risk: Diagnostics could expose raw page HTML or private data. Mitigation: the diagnostic includes only site name, page name, field name, and scalar value; tests use synthetic fixture HTML.

## Dependencies

- Wikidot ListPages-generated 5-star rating fields are expected to use finite ASCII numeric text.
- `PageCollection._parse(...)` remains the source of truth for ListPages row parsing.
- Existing BeautifulSoup parsing continues to expose generated field values as strings.
- Existing `rating_percent` validation remains layered in the percentage helper.

## Open Questions

None for this local slice. Future ListPages parser changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

ListPages parsing turns generated page-row fields into page metrics used by source collection, migration, verification, rating audits, and reconciliation workflows. Unicode digit normalization and non-finite float values can silently turn malformed generated scalar metadata into valid-looking or hazardous ratings. Requiring generated 5-star rating values to be finite ASCII text keeps ListPages rating parsing strict and consistent with adjacent generated scalar-shape fixes while preserving valid ListPages behavior and established diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: fullwidth digit rating text and non-finite float spellings were accepted and returned a `Page` instead of raising.
- Existing local drafts covered ListPages pagination, fetch retry, response validation, field scoping, field spacing, field pager markup isolation, malformed integer diagnostics, malformed rating diagnostics, non-negative metric validation, pager page ASCII-shape validation, and integer field ASCII-shape validation; they did not validate accepted but malformed generated 5-star rating float values.
- This slice does not change request URLs, pagination bounds, ListPages module parameters, field key extraction, title spacing, string field parsing, integer field parsing, rating-percent parsing, page ID lookup, source iteration, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, real page HTML, real page names, private site data, usernames, passwords, and session-cookie values out of upstream discussion.

## Additional Notes

This is a generated ListPages scalar parser fix. It preserves valid finite ASCII 5-star rating parsing and existing downstream percent/range diagnostics while preventing Python's Unicode digit and non-finite float support from manufacturing ordinary page ratings out of malformed generated field metadata.
