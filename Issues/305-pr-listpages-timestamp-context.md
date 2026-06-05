# PR Draft: Report Malformed ListPages Timestamps

## Summary

`PageCollection._parse(...)` parses generated `list/ListPagesModule` fields for page search, metadata hydration, source iteration, page lookup refreshes, and publish-adjacent verification flows. Earlier local slices made ListPages acquisition retry-aware, response-body-aware, structurally scoped, text-spacing-safe, field-key parser errors site/page/field-aware, generated integer fields site/page/field/value-aware, and generated rating fields site/page/field/value-aware. One adjacent timestamp value parser gap remained: when `created_at`, `updated_at`, or `commented_at` contained a present `span.odate` with malformed `time_...` metadata, the shared `odate_parse(...)` utility raised raw `ValueError` without the affected site, page, field, or observed class value.

This local slice keeps successful ListPages timestamp parsing and the shared `odate_parse(...)` utility unchanged. It catches malformed present ListPages timestamp metadata at the page parser boundary and raises `NoElementException` with site unix name, parsed page fullname, affected timestamp field, and the offending `time_...` class value.

## Outcome

Malformed ListPages timestamp values now fail with ListPages-local field context instead of leaking a raw shared timestamp parser exception.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use ListPages-driven page search, source collection, metadata hydration, publishing verification, corpus indexing, or generated page ledgers.

## Related Issue

Builds on [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md), [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md), [183-pr-listpages-fetch-failure-context.md](183-pr-listpages-fetch-failure-context.md), [191-pr-listpages-key-parse-context.md](191-pr-listpages-key-parse-context.md), [220-pr-listpages-response-body-context.md](220-pr-listpages-response-body-context.md), [239-pr-listpages-integer-field-parse-context.md](239-pr-listpages-integer-field-parse-context.md), and [240-pr-listpages-rating-field-parse-context.md](240-pr-listpages-rating-field-parse-context.md). Those drafts established ListPages as a heavily used read path and established adjacent context-rich diagnostics for generated ListPages structure and scalar values.

This slice also follows the shared timestamp parser-boundary pattern from [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), [287-pr-private-message-detail-timestamp-value-context.md](287-pr-private-message-detail-timestamp-value-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [296-pr-forum-post-list-timestamp-context.md](296-pr-forum-post-list-timestamp-context.md), [298-pr-forum-post-list-edit-timestamp-context.md](298-pr-forum-post-list-edit-timestamp-context.md), and [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a small ListPages odate-field parser that raises contextual `NoElementException` on malformed generated timestamp values.
- Route `created_at`, `updated_at`, and `commented_at` through that helper when their `span.odate` element is present.
- Include site unix name, parsed page fullname, affected field, and the observed direct `time_...` class value in the parser error.
- Preserve the existing `None` behavior when a timestamp field has no present `span.odate`.
- Preserve successful ListPages parsing, field scoping, string value spacing, user/tag parsing, integer count parsing, rating parsing, rating-percent normalization, pagination, retry behavior, source iteration, publish-adjacent search refreshes, and `Page` object construction.
- Add a focused public `PageCollection._parse(...)` regression for a malformed `created_at` `time_latest` value.

## Type Of Change

- Bug fix / diagnostics improvement
- ListPages parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated ListPages response with malformed present `created_at`, `updated_at`, or `commented_at` `span.odate` metadata must fail at the ListPages parser boundary. |
| R2 | The malformed timestamp error must identify the affected site, parsed page fullname, field, and observed direct `time_...` class value. |
| R3 | Existing valid ListPages timestamp parsing and missing-timestamp-element behavior must remain compatible. |
| R4 | Existing ListPages response handling, pagination, retry, field scoping, key diagnostics, integer diagnostics, rating diagnostics, string spacing, user/tag parsing, search behavior, source iteration, and page construction must remain unchanged. |
| R5 | Focused, page-level, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `PageCollection._parse(site, html_body)` raises `NoElementException` for `class="odate time_latest"` in a generated ListPages `created_at` value. | `TestPageCollectionParse.test_parse_malformed_odate_field_includes_site_page_and_value_context` mutates the generated `created_at` class and expects `NoElementException`. | Leaking raw `ValueError`, fabricating a timestamp, returning `None` for a present malformed timestamp, silently skipping the page, or returning a malformed `Page` rejects this local completion claim. | `src/wikidot/module/page.py` | `tests/unit/test_page.py` |
| R2 | The error names `site: test-site`, `page: scp-001`, `field=created_at`, and `value=time_latest`. | The focused regression matches all fields. | Omitting site, page fullname, field name, or the bad class value makes the failure ambiguous and rejects this local completion claim. | ListPages timestamp diagnostics | `tests/unit/test_page.py` |
| R3 | Valid ListPages timestamp rows still parse, and missing timestamp values still become `None`. | Focused GREEN includes `test_parse_single_page` and `test_parse_missing_optional_fields`; the page-level suite passed 155 tests. | Regressing `created_at`, `updated_at`, `commented_at`, or missing optional field behavior rejects this local completion claim. | ListPages page parsing | `tests/unit/test_page.py` |
| R4 | Adjacent ListPages diagnostics and workflows stay green. | Focused GREEN includes integer and rating diagnostics; the full page suite covers search, pagination, retry, source iteration, publish-adjacent helpers, page IDs, revision/vote/file acquisition, and mutation-adjacent behavior. | Regressing field scoping, missing-key diagnostics, integer/rating diagnostics, string spacing, user/tag parsing, search behavior, pagination, retry, or `Page` object construction rejects this local completion claim. | ListPages and page workflows | `tests/unit/test_page.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `e6a124c fix(page): report malformed listpages timestamps`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_odate_field_includes_site_page_and_value_context -q` failed before the fix with `ValueError: invalid literal for int() with base 10: 'latest'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_odate_field_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_single_page tests/unit/test_page.py::TestPageCollectionParse::test_parse_missing_optional_fields tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_integer_field_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_rating_includes_site_page_and_value_context -q` passed 5 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 155 tests.
- `uv run pytest tests/unit -q` passed 863 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 80 files already formatted.
- `uv run mypy src` passed with no issues in 35 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` could not spawn `pyright` because no executable was available in this environment.

## Acceptance Criteria

- A generated ListPages response whose present `created_at`, `updated_at`, or `commented_at` `span.odate` value has malformed `time_...` metadata raises `NoElementException`.
- The malformed timestamp message includes the site `unix_name`, parsed page fullname when available, affected field name, and observed `time_...` class value.
- Missing ListPages timestamp elements continue to produce `None`.
- Valid ListPages timestamps still parse through `odate_parser(...)`.
- Successful ListPages parsing, field scoping, string value spacing, user/tag parsing, integer count parsing, rating parsing, rating-percent normalization, pagination, retry behavior, source iteration, publish-adjacent search refreshes, and `Page` object construction remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, raw generated ListPages HTML from real sites, page titles from real sites, credentials, cookies, auth JSON, or private page content is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Wrapping shared-parser `ValueError` could hide an unexpected timestamp parsing failure. Mitigation: the wrapper preserves exception chaining with `from exc` and adds only ListPages location metadata.
- Risk: Changing the shared odate parser could affect unrelated modules. Mitigation: this slice intentionally leaves `odate_parse(...)` unchanged and validates parser-adjacent page behavior through the full unit suite.
- Risk: Missing timestamp elements are already represented as `None` in ListPages parsing. Mitigation: the wrapper only runs when a direct `span.odate` is present and malformed, preserving existing missing-value behavior.

## Dependencies

- BeautifulSoup continues to expose direct ListPages `span.odate` elements and direct class values in generated page fields.
- The shared `odate_parse(...)` utility remains the source of truth for valid Wikidot odate metadata extraction.
- ListPages output continues to present timestamp values under `span.set > span.value > span.odate` for `created_at`, `updated_at`, and `commented_at` when timestamps exist.

## Open Questions

None for this local slice. Broader centralization of repeated user/timestamp value helpers could be considered later only if it reduces duplication without changing parser behavior.

## Upstream-Safe Motivation

ListPages is a core read surface for page search, metadata hydration, source collection, and publication verification. When Wikidot returns a present timestamp field with malformed generated metadata, wikidot.py should fail with a structured parser error naming the affected site, page, field, and observed value instead of leaking a generic shared helper exception. That keeps logs actionable without retaining raw ListPages HTML, raw response JSON, credentials, or local rollout paths.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified ListPages as a practical workflow surface by improving first-page and paginated retry behavior, source iteration, required-tag filtering, field scoping, pager filtering, field spacing, fetch diagnostics, field-key diagnostics, response-body validation, integer field value diagnostics, and rating field value diagnostics.
- Recent timestamp parser-boundary drafts validated the same shared `odate_parse(...)` failure pattern in recent changes, private messages, site members, forum thread lists, forum thread details, forum post lists, forum post edit metadata, forum post revisions, and page revision lists.
- The immediate RED failure showed the same raw `ValueError` class that prior parser-boundary timestamp slices converted in adjacent modules.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated ListPages HTML, page names from real sites, page titles from real sites, page source text, and private page content out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It narrows a raw utility-parser exception into the same local exception family used by surrounding ListPages parser diagnostics.
