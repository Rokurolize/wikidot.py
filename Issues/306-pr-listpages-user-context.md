# PR Draft: Report Malformed ListPages Users

## Summary

`PageCollection._parse(...)` parses generated `list/ListPagesModule` fields for page search, metadata hydration, source iteration, page lookup refreshes, and publish-adjacent verification flows. Earlier local slices made ListPages acquisition retry-aware, response-body-aware, structurally scoped, text-spacing-safe, field-key parser errors site/page/field-aware, generated integer fields site/page/field/value-aware, generated rating fields site/page/field/value-aware, and generated timestamp fields site/page/field/value-aware. One adjacent linked-user parser gap remained: when `created_by_linked`, `updated_by_linked`, or `commented_by_linked` contained a present direct `span.printuser` with malformed user metadata, the shared `user_parse(...)` utility raised raw `ValueError` without the affected site, page, field, or observed user metadata value.

This local slice keeps successful ListPages linked-user parsing and the shared `user_parse(...)` utility unchanged. It catches malformed present ListPages linked-user metadata at the page parser boundary and raises `NoElementException` with site unix name, parsed page fullname, affected linked-user field, and the offending direct user `onclick` value or fallback rendered text.

## Outcome

Malformed ListPages linked-user values now fail with ListPages-local field context instead of leaking a raw shared user parser exception.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use ListPages-driven page search, source collection, metadata hydration, publishing verification, corpus indexing, author ledgers, or generated page audit reports.

## Related Issue

Builds on [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md), [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md), [183-pr-listpages-fetch-failure-context.md](183-pr-listpages-fetch-failure-context.md), [191-pr-listpages-key-parse-context.md](191-pr-listpages-key-parse-context.md), [220-pr-listpages-response-body-context.md](220-pr-listpages-response-body-context.md), [239-pr-listpages-integer-field-parse-context.md](239-pr-listpages-integer-field-parse-context.md), [240-pr-listpages-rating-field-parse-context.md](240-pr-listpages-rating-field-parse-context.md), and [305-pr-listpages-timestamp-context.md](305-pr-listpages-timestamp-context.md). Those drafts established ListPages as a heavily used read path and established adjacent context-rich diagnostics for generated ListPages structure and scalar values.

This slice also follows the shared user parser-boundary pattern from [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md), [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), and the shared parser validation slices [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md) and [302-pr-regular-user-href-validation.md](302-pr-regular-user-href-validation.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a small ListPages linked-user parser that raises contextual `NoElementException` on malformed generated `span.printuser` values.
- Route `created_by_linked`, `updated_by_linked`, and `commented_by_linked` through that helper when their direct `span.printuser` element is present.
- Include site unix name, parsed page fullname, affected field, and the observed direct user `onclick` value or fallback rendered text in the parser error.
- Align the shared local user-value helper with `user_parse(...)` by reporting the last direct user link's `onclick` value when a `span.printuser` contains avatar and display-name anchors.
- Preserve the existing `None` behavior when a linked-user field has no present direct `span.printuser`.
- Preserve successful ListPages parsing, field scoping, string value spacing, tag parsing, timestamp parsing, integer count parsing, rating parsing, rating-percent normalization, pagination, retry behavior, source iteration, publish-adjacent search refreshes, and `Page` object construction.
- Add a focused public `PageCollection._parse(...)` regression for a malformed `created_by_linked` `userInfo(latest)` value.

## Type Of Change

- Bug fix / diagnostics improvement
- ListPages parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated ListPages response with malformed present `created_by_linked`, `updated_by_linked`, or `commented_by_linked` direct `span.printuser` metadata must fail at the ListPages parser boundary. |
| R2 | The malformed linked-user error must identify the affected site, parsed page fullname, field, and observed direct user metadata value. |
| R3 | Existing valid ListPages linked-user parsing and missing-linked-user-element behavior must remain compatible. |
| R4 | Existing ListPages response handling, pagination, retry, field scoping, key diagnostics, integer diagnostics, rating diagnostics, timestamp diagnostics, string spacing, tag parsing, search behavior, source iteration, and page construction must remain unchanged. |
| R5 | Focused, page-level, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `PageCollection._parse(site, html_body)` raises `NoElementException` for `userInfo(latest)` in a generated ListPages `created_by_linked` value. | `TestPageCollectionParse.test_parse_malformed_user_field_includes_site_page_and_value_context` mutates the generated display-name anchor and expects `NoElementException`. | Leaking raw `ValueError`, fabricating a user, returning `None` for a present malformed linked user, silently skipping the page, or returning a malformed `Page` rejects this local completion claim. | `src/wikidot/module/page.py` | `tests/unit/test_page.py` |
| R2 | The error names `site: test-site`, `page: scp-001`, `field=created_by_linked`, and `value=WIKIDOT.page.listeners.userInfo(latest); return false;`. | The focused regression matches all fields. | Omitting site, page fullname, field name, or the bad direct user metadata value makes the failure ambiguous and rejects this local completion claim. | ListPages linked-user diagnostics | `tests/unit/test_page.py` |
| R3 | Valid ListPages linked-user rows still parse, and missing linked-user values still become `None`. | Focused GREEN includes `test_parse_single_page` and `test_parse_missing_optional_fields`; the page-level suite passed 156 tests. | Regressing `created_by`, `updated_by`, `commented_by`, or missing optional field behavior rejects this local completion claim. | ListPages page parsing | `tests/unit/test_page.py` |
| R4 | Adjacent ListPages diagnostics and workflows stay green. | Focused GREEN includes integer, timestamp, and rating diagnostics; the full page suite covers search, pagination, retry, source iteration, publish-adjacent helpers, page IDs, revision/vote/file acquisition, and mutation-adjacent behavior. | Regressing field scoping, missing-key diagnostics, integer/rating/timestamp diagnostics, string spacing, tag parsing, search behavior, pagination, retry, or `Page` object construction rejects this local completion claim. | ListPages and page workflows | `tests/unit/test_page.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `da10e9e fix(page): report malformed listpages users`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_user_field_includes_site_page_and_value_context -q` failed before the fix with `ValueError: user id is not found`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_user_field_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_single_page tests/unit/test_page.py::TestPageCollectionParse::test_parse_missing_optional_fields tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_odate_field_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_integer_field_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_rating_includes_site_page_and_value_context -q` passed 6 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 156 tests.
- `uv run pytest tests/unit -q` passed 864 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 80 files already formatted.
- `uv run mypy src` passed with no issues in 35 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` could not spawn `pyright` because no executable was available in this environment.

## Acceptance Criteria

- A generated ListPages response whose present `created_by_linked`, `updated_by_linked`, or `commented_by_linked` direct `span.printuser` value has malformed user metadata raises `NoElementException`.
- The malformed linked-user message includes the site `unix_name`, parsed page fullname when available, affected field name, and observed direct user metadata value.
- Missing ListPages linked-user elements continue to produce `None`.
- Valid ListPages linked users still parse through `user_parse(...)`.
- Successful ListPages parsing, field scoping, string value spacing, tag parsing, timestamp parsing, integer count parsing, rating parsing, rating-percent normalization, pagination, retry behavior, source iteration, publish-adjacent search refreshes, and `Page` object construction remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, raw generated ListPages HTML from real sites, page titles from real sites, credentials, cookies, auth JSON, or private page content is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Wrapping shared-parser `ValueError` could hide an unexpected linked-user parsing failure. Mitigation: the wrapper preserves exception chaining with `from exc` and adds only ListPages location metadata.
- Risk: Changing the shared user parser could affect unrelated modules. Mitigation: this slice intentionally leaves `user_parse(...)` unchanged and validates parser-adjacent page behavior through the full unit suite.
- Risk: `span.printuser` values can contain both avatar and display-name anchors. Mitigation: the reported metadata value now mirrors `user_parse(...)` by using the last direct user link's `onclick` value when present.
- Risk: Missing linked-user elements are already represented as `None` in ListPages parsing. Mitigation: the wrapper only runs when a direct `span.printuser` is present and malformed, preserving existing missing-value behavior.

## Dependencies

- BeautifulSoup continues to expose direct ListPages `span.printuser` elements and direct anchor metadata in generated page fields.
- The shared `user_parse(...)` utility remains the source of truth for valid Wikidot user metadata extraction.
- ListPages output continues to present linked-user values under `span.set > span.value > span.printuser` for `created_by_linked`, `updated_by_linked`, and `commented_by_linked` when users exist.

## Open Questions

None for this local slice. Broader centralization of repeated user/timestamp value helpers could be considered later only if it reduces duplication without changing parser behavior.

## Upstream-Safe Motivation

ListPages is a core read surface for page search, metadata hydration, source collection, publication verification, and author ledgers. When Wikidot returns a present linked-user field with malformed generated metadata, wikidot.py should fail with a structured parser error naming the affected site, page, field, and observed value instead of leaking a generic shared helper exception. That keeps logs actionable without retaining raw ListPages HTML, raw response JSON, credentials, or local rollout paths.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified ListPages as a practical workflow surface by improving first-page and paginated retry behavior, source iteration, required-tag filtering, field scoping, pager filtering, field spacing, fetch diagnostics, field-key diagnostics, response-body validation, integer field value diagnostics, rating field value diagnostics, and timestamp value diagnostics.
- Recent user parser-boundary drafts validated the same shared `user_parse(...)` failure pattern in forum post lists, forum post edit metadata, recent changes, and page revision lists.
- The immediate RED failure showed the same raw `ValueError` class that prior parser-boundary user slices converted in adjacent modules.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated ListPages HTML, page names from real sites, page titles from real sites, page source text, and private page content out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It narrows a raw utility-parser exception into the same local exception family used by surrounding ListPages parser diagnostics.
