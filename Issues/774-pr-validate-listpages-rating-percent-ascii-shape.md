# PR Draft: Validate ListPages Rating Percent ASCII Shape

## Summary

`PageCollection._parse(...)` parses 5-star ListPages `rating_percent` fields into normalized `Page.rating_percent` values for page inventories, rating audits, source/revision/file/vote traversal, and publish-adjacent verification. Issue [240-pr-listpages-rating-field-parse-context.md](240-pr-listpages-rating-field-parse-context.md) made malformed non-float `rating_percent` text fail with contextual `NoElementException`, and Issue [488-pr-validate-page-constructor-rating-percent.md](488-pr-validate-page-constructor-rating-percent.md) validates direct `Page.rating_percent` construction. One parser boundary remained: Python `float(...)` accepts non-ASCII decimal digit glyphs, so generated 5-star `rating_percent` text such as `\uff17\uff15%` could be normalized to `0.75` instead of being reported as malformed Wikidot module output.

This change rejects non-ASCII generated `rating_percent` text before float conversion. Valid ASCII percentage text, existing malformed-float diagnostics, and existing percentage range diagnostics remain unchanged.

## Outcome

Generated ListPages 5-star rating percentage text no longer uses Python's broad float grammar as the protocol boundary. Non-ASCII digit glyphs are rejected with the existing contextual ListPages float-field diagnostic before a `Page` object is constructed.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free ListPages searches, page/rating inventories, publish verification, migration ledgers, source/revision/file/vote workflows, or local fixtures derived from generated page metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify ListPages parsing and page rating metadata as practical surfaces. Issue 240 covers raw malformed `rating_percent` text such as `not-a-percent`; Issue 488 covers direct constructor type integrity; Issue [636-pr-validate-page-rating-percent-range.md](636-pr-validate-page-rating-percent-range.md) covers direct constructor range validation; Issue [767-pr-validate-listpages-integer-field-ascii-shape.md](767-pr-validate-listpages-integer-field-ascii-shape.md) covers generated ListPages integer fields; Issue [768-pr-validate-listpages-rating-float-shape.md](768-pr-validate-listpages-rating-float-shape.md) covers generated 5-star `rating` float values; Issue [773-pr-validate-rating-points-ascii-shape.md](773-pr-validate-rating-points-ascii-shape.md) covers page rating action response `points`. None covers generated 5-star `rating_percent` digit glyphs before float conversion.

The focused RED test demonstrated the gap: a generated 5-star `rating_percent` value containing `\uff17\uff15%` did not raise and was accepted as a normal 75 percent rating.

## Related Issue / Non-Duplicate Analysis

Builds on [240-pr-listpages-rating-field-parse-context.md](240-pr-listpages-rating-field-parse-context.md), [488-pr-validate-page-constructor-rating-percent.md](488-pr-validate-page-constructor-rating-percent.md), [636-pr-validate-page-rating-percent-range.md](636-pr-validate-page-rating-percent-range.md), [767-pr-validate-listpages-integer-field-ascii-shape.md](767-pr-validate-listpages-integer-field-ascii-shape.md), [768-pr-validate-listpages-rating-float-shape.md](768-pr-validate-listpages-rating-float-shape.md), and [773-pr-validate-rating-points-ascii-shape.md](773-pr-validate-rating-points-ascii-shape.md).

No upstream issue was filed from this local workspace.

## Changes

- Require generated ListPages `rating_percent` text to be ASCII before calling the shared float parser.
- Preserve valid ASCII percentage text and normalized `Page.rating_percent` output.
- Preserve existing `ListPages float field is malformed ...` diagnostics for malformed float text.
- Preserve existing `ListPages percentage field must be between 0.0 and 100.0 ...` diagnostics for ASCII out-of-range and non-finite values.
- Add a focused RED/GREEN parser regression for fullwidth 75 percent text.

## Type Of Change

- Bug fix
- Parser boundary hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Generated 5-star `rating_percent` text containing non-ASCII digits must raise `NoElementException` before constructing a `Page`. |
| R2 | The malformed non-ASCII diagnostic must identify site, page, field, and observed value using the existing ListPages float-field error shape. |
| R3 | Valid ASCII percentage values, including `75%`, must continue to parse and normalize to `0.75`. |
| R4 | Existing malformed text and range diagnostics, including `not-a-percent`, `-1%`, `101%`, `nan%`, and `inf%`, must remain stable. |
| R5 | Existing ListPages parsing, search pagination, page construction, page source/revision/file/vote workflows, and site workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, affected ListPages parser/search tests, adjacent page/site tests, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `\uff17\uff15%` fails instead of becoming `0.75`. | `TestPageCollectionParse.test_parse_rejects_non_ascii_digit_rating_percent` failed RED with `DID NOT RAISE`, then passed GREEN after the ASCII guard was added. | Accepting non-ASCII digit glyphs, constructing a `Page`, or normalizing the value rejects this local completion claim. | ListPages 5-star rating-percent parser | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | The failure names `site: test-site`, `page: test-page`, `field=rating_percent`, and the observed value. | The focused regression asserts the exact `ListPages float field is malformed ...` message. | Omitting field/value context or leaking raw ListPages HTML rejects this local completion claim. | Parser diagnostics | `tests/unit/test_page.py` |
| R3 | Valid ASCII 5-star rating-percent parsing remains supported. | `test_parse_with_5star_rating_percent` passed in the focused 11-test set and broader suites. | Rejecting `75%`, changing `0.75`, or altering non-5-star rating behavior rejects this local completion claim. | ListPages parser compatibility | `tests/unit/test_page.py` |
| R4 | Existing malformed/range diagnostics remain stable. | The focused 11-test set covered `not-a-percent`, `-1%`, `101%`, `nan%`, `inf%`, malformed 5-star rating, and 5-star rating float-shape cases. | Reclassifying ASCII range errors or changing existing messages rejects this local completion claim. | ListPages parser diagnostics | `tests/unit/test_page.py` |
| R5 | Adjacent page workflows remain green. | Affected PageCollectionParse/SearchPages passed 59 tests, adjacent page/page_constructor/site/page_file/page_votes/page_revision passed 1349 tests, and full unit passed 3785 tests. | Regressing page construction, page lookup, source/revision/file/vote acquisition, or site workflows rejects this local completion claim. | Page and site workflows | `tests/unit` |
| R6 | The local proof stays unit-level and private-data-free. | The draft and regressions use synthetic fixture values only. | Requiring live Wikidot, credentials, cookies, auth JSON, raw rollout paths, page source text, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `c040164 fix(page): validate rating percent ascii shape`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_rejects_non_ascii_digit_rating_percent -q --tb=short` failed before the fix with `DID NOT RAISE`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_with_5star_rating_percent tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_rating_percent_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_rejects_non_ascii_digit_rating_percent tests/unit/test_page.py::TestPageCollectionParse::test_parse_out_of_range_rating_percent_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_5star_rating_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_rejects_malformed_5star_rating_float_shape -q` passed 11 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionParse tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed 59 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_page_revision.py -q` passed 1349 tests.
- `uv run pytest tests/unit -q` passed 3785 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: CLI `0.5.0`, local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- A generated ListPages response whose 5-star `rating_percent` value contains non-ASCII digits raises `NoElementException`.
- The exception keeps the existing ListPages float-field diagnostic shape and includes site, page, field, and value.
- Valid ASCII `rating_percent` values still parse and normalize.
- Existing malformed text and range diagnostics remain stable.
- Existing ListPages, page, site, page-file, page-vote, and page-revision workflows remain green.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

ListPages-generated rating metadata is protocol output, not user-authored free text. Accepting non-ASCII digit glyphs by relying on Python's broad float parser can hide malformed Wikidot module output and pollute page inventories or rating audit ledgers. A small ASCII guard aligns `rating_percent` with the adjacent ListPages integer, 5-star rating, and page rating action response boundaries while preserving valid ASCII behavior.

## Local Evidence

- Local rollout-backed drafts use ListPages and page rating metadata for browser-free page inventory, source collection, publish verification, rating audits, and generated ledgers.
- Existing local drafts covered malformed `rating_percent` text, direct constructor validation, direct constructor range validation, ListPages integer ASCII shape, 5-star rating float shape, and action response points ASCII shape, but not generated `rating_percent` digit glyphs.
- The focused RED failure showed fullwidth 75 percent text was accepted before the fix.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw ListPages HTML, page source text, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally checks ASCII before calling the existing ListPages float parser rather than adding a new decimal grammar. This preserves the existing accepted ASCII float syntax and existing range diagnostics while blocking the observed non-ASCII digit normalization path.
