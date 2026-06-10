# PR Draft: Validate ListPages Integer Field ASCII Shape

## Summary

`PageCollection._parse(...)` converts generated `ListPagesModule` integer fields such as `rating_votes`, `comments`, `size`, `children`, `revisions`, and non-5-star `rating` through `_parse_listpages_integer_field(...)`. Issue 239 made malformed integer text such as `not-a-number` contextual, Issue 240 made malformed float/rating text contextual, and Issue 754 tightened the ListPages pager page parameter, but one accepted-value gap remained: Python `int(...)` accepts Unicode decimal digit glyphs such as `\uff12`, so a generated field could be normalized into an ordinary integer before the parser noticed the scalar shape was not the ASCII decimal shape produced by normal Wikidot markup.

This change requires generated ListPages integer fields to match ASCII `-?[0-9]+` before integer conversion. Valid ASCII positive integers and the existing ASCII negative path continue through the same downstream non-negative validation. Unicode digit-like values now fail with the existing contextual `NoElementException` family instead of being silently normalized.

## Outcome

ListPages parsing no longer manufactures ordinary page metrics from non-ASCII digit glyphs. A page row whose generated integer field contains fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like text now fails at the ListPages parser boundary with site, page, field, and observed value context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use ListPages-backed page search, source iteration, metadata hydration, required-tag ledgers, publication verification, migration tooling, reconciliation scripts, or generated fixtures where page metrics must reflect strict generated scalar fields.

## Current Evidence

Local rollout-backed drafts repeatedly identify ListPages as a practical read boundary for page discovery, source collection, required-tag filtering, publication verification, and large-corpus reconciliation. Existing local drafts cover ListPages pagination bounds, retry behavior, first-fetch response validation, field scoping, field spacing, field pager markup isolation, malformed integer diagnostics, malformed rating diagnostics, non-negative metric validation, and pager page ASCII-shape validation.

This slice is not a duplicate of [239-pr-listpages-integer-field-parse-context.md](239-pr-listpages-integer-field-parse-context.md). Issue 239 covers integer field values that Python rejects outright, such as `not-a-number`. This slice covers Unicode decimal digit glyphs that Python accepts and normalizes.

This slice is not a duplicate of [240-pr-listpages-rating-field-parse-context.md](240-pr-listpages-rating-field-parse-context.md). Issue 240 covers malformed float/rating fields and 5-star percentage parsing, while this slice applies to integer-backed ListPages fields.

This slice is not a duplicate of [754-pr-validate-listpages-pager-page-ascii-shape.md](754-pr-validate-listpages-pager-page-ascii-shape.md). Issue 754 validates page numbers discovered from the ListPages pager; this slice validates generated integer field values inside each parsed page row.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md), [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md), [239-pr-listpages-integer-field-parse-context.md](239-pr-listpages-integer-field-parse-context.md), [240-pr-listpages-rating-field-parse-context.md](240-pr-listpages-rating-field-parse-context.md), [633-pr-validate-non-negative-page-metrics.md](633-pr-validate-non-negative-page-metrics.md), and [754-pr-validate-listpages-pager-page-ascii-shape.md](754-pr-validate-listpages-pager-page-ascii-shape.md).

## Changes

- Require ASCII `-?[0-9]+` in generated ListPages integer field text before integer conversion.
- Preserve valid ASCII integer parsing for positive generated metrics.
- Preserve valid ASCII negative parsing into the existing non-negative guard so count-like fields retain the established "must be non-negative" diagnostic.
- Preserve existing contextual malformed-integer diagnostics for non-numeric and now non-ASCII digit integer fields.
- Add a regression test that `comments=\uff12` raises instead of returning `comments=2`.

## Type Of Change

- Bug fix
- ListPages parser validation
- Generated scalar hardening
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Generated ListPages integer fields with non-ASCII digit glyphs must fail before being stored on a `Page`. |
| R2 | The malformed-integer diagnostic must retain site, page, field, and observed scalar value context. |
| R3 | Valid ASCII integer fields must continue to parse normally, including ASCII negatives that are later rejected by the existing non-negative helper for count-like fields. |
| R4 | Existing malformed integer, malformed rating, 5-star rating, ListPages search, page metadata, and adjacent page-facing workflows must remain compatible. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, real page HTML, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, page parser/search tests, page unit tests, adjacent page-facing tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A ListPages row with `comments=\uff12` raises before `Page.comments` can become `2`. | `test_parse_rejects_non_ascii_digit_integer_field` failed RED with `DID NOT RAISE`, then passed after ASCII-only integer field validation. | Returning a `Page`, storing `comments=2`, or silently dropping the row rejects this local completion claim. | ListPages parser | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | The exception reports `ListPages integer field is malformed for site: test-site, page: scp-001 (field=comments, value=\uff12)`. | The regression asserts the exact contextual diagnostic. | Leaking a raw `ValueError`, omitting site/page/field/value, or reporting a generic missing-element error rejects this local completion claim. | ListPages diagnostics | focused test |
| R3 | Valid ASCII values still parse, and ASCII `-1` still reaches the non-negative guard for count-like fields. | Focused GREEN included malformed integer, non-ASCII integer, negative count, malformed rating, single page, PM rating, and 5-star rating percent cases. | Rejecting ordinary ASCII generated fields, changing count diagnostics, or changing rating behavior rejects this local completion claim. | Valid ListPages parsing | focused tests |
| R4 | Existing page parse/search and adjacent page-facing behavior stays stable. | Page parser/search tests passed 55 tests, full `tests/unit/test_page.py` passed 397 tests, adjacent page-facing suites passed 1122 tests, and full unit passed 3771 tests. | Regressing ListPages search, page revisions, files, votes, site workflows, or any unit test rejects this local completion claim. | Page and site workflows | `tests/unit` |
| R5 | No live site state or private material is needed. | The regression uses synthetic ListPages HTML fixture mutation and local mocked parsing only. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, real page HTML, private account data, private page names, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, page parse/search tests, page unit tests, adjacent page-facing tests, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `27dc177 fix(page): validate listpages integer ascii shape`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_rejects_non_ascii_digit_integer_field -q` failed before the fix with `DID NOT RAISE` because `comments=\uff12` was normalized to integer `2`.
- GREEN focused parser slice: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_rejects_non_ascii_digit_integer_field tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_integer_field_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_negative_count_field_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_rating_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_single_page tests/unit/test_page.py::TestPageCollectionParse::test_parse_with_pm_rating tests/unit/test_page.py::TestPageCollectionParse::test_parse_with_5star_rating_percent -q` passed 7 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionParse tests/unit/test_page.py::TestPageCollectionSearchPages -q --tb=short` passed 55 tests.
- `uv run pytest tests/unit/test_page.py -q --tb=short` passed 397 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q --tb=short` passed 1122 tests.
- `uv run pytest tests/unit -q --tb=short` passed 3771 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted after formatting `tests/unit/test_page.py`.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no change-propagation, cognitive-load, duplication, accidental-complexity, dependency, domain-model, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker. Code pre-commit evidence reported `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.139.0"`, local clawpatch commit `d89ca91`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `PageCollection._parse(...)` raises `NoElementException("ListPages integer field is malformed ...")` for a generated integer field value of `\uff12`.
- The parser does not construct a `Page` whose metric was normalized from non-ASCII digit glyphs.
- The diagnostic includes site, page, field, and observed value context.
- Valid ASCII generated integer fields still parse normally.
- ASCII negative values still flow into the existing non-negative diagnostic for count-like fields.
- Existing malformed integer diagnostics from Issue 239 remain unchanged for values such as `not-a-number`.
- Existing malformed rating and 5-star percentage behavior from Issue 240 remains unchanged.
- Existing ListPages pager page ASCII-shape behavior from Issue 754 remains unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw real page HTML, local rollout path, private account detail, private page name, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 239. Mitigation: Issue 239 covers values that cannot be parsed by `int(...)`; this slice covers Unicode decimal digit glyphs that Python parses successfully.
- Risk: This could be confused with Issue 754. Mitigation: Issue 754 covers pager page numbers; this slice covers generated row field values.
- Risk: Tightening integer parsing could reject unusual but valid generated Wikidot field text. Mitigation: normal generated ListPages integer fields are ASCII decimal text, and the existing ASCII positive and ASCII negative paths remained covered.
- Risk: Diagnostics could expose raw page HTML or private data. Mitigation: the diagnostic includes only site name, page name, field name, and scalar value; tests use synthetic fixture HTML.

## Dependencies

- Wikidot ListPages-generated integer fields are expected to use ASCII decimal text.
- `PageCollection._parse(...)` remains the source of truth for ListPages row parsing.
- Existing BeautifulSoup parsing continues to expose generated field values as strings.
- Existing non-negative metric validation remains layered on top of integer parsing.

## Open Questions

None for this local slice. Future ListPages parser changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

ListPages parsing turns generated page-row fields into page metrics used by source collection, migration, verification, and reconciliation workflows. Unicode digit normalization can silently turn malformed generated scalar metadata into valid-looking integers. Requiring ASCII digits keeps generated integer parsing strict and consistent with adjacent generated scalar-shape fixes while preserving valid ListPages behavior and established diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: a fullwidth `comments` value was accepted and returned a `Page` instead of raising.
- Existing local drafts covered ListPages pagination, fetch retry, response validation, field scoping, field spacing, field pager markup isolation, malformed integer diagnostics, malformed rating diagnostics, non-negative metric validation, and pager page ASCII-shape validation; they did not validate Unicode digit normalization inside generated integer fields.
- This slice does not change request URLs, pagination bounds, ListPages module parameters, field key extraction, title spacing, string field parsing, rating percent parsing, page ID lookup, source iteration, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, real page HTML, real page names, private site data, usernames, passwords, and session-cookie values out of upstream discussion.

## Additional Notes

This is a generated ListPages scalar parser fix. It preserves valid ASCII parsing and existing downstream non-negative diagnostics while preventing Python's Unicode digit support from manufacturing ordinary page metrics out of malformed generated field metadata.
