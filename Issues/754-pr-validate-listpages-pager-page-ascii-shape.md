# PR Draft: Validate ListPages Pager Page ASCII Shape

## Summary

`PageCollection.search_pages(...)` parses the first generated `ListPagesModule` response pager to decide whether additional offsets should be fetched. The response-wide pager scan used `page_text.isdigit()` before `int(page_text)`, so generated labels containing Unicode digit glyphs such as `"\uff12"` were accepted and normalized into ordinary page number `2`. That could turn malformed generated pager metadata into a real follow-up ListPages request.

This change accepts ListPages pager page labels only when they match ASCII digits. Ordinary non-numeric pager labels such as `next` continue to be ignored, valid ASCII pagination still fetches subsequent offsets, ListPages field-value pager markup remains scoped away from the response-wide pager, and digit-like non-ASCII labels now fail with `NoElementException("ListPages pager page is malformed ...")` including site, offset, field, and observed value context.

## Outcome

Page search no longer fabricates ListPages pagination traversal from malformed generated pager labels. A `ListPagesModule` response with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like pager text now fails at the pager boundary instead of issuing unintended extra offset requests.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page searches, page/source iterators, corpus scans, required-tag collection, migration checks, local fixtures, or generated workflows where ListPages traversal must come only from structurally valid Wikidot pager metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify ListPages as a practical, heavily used read path. Existing drafts cover bounded pagination, retry-aware first and additional page fetches, iterator chunking, required-tag filtering, field markup scoping, field-value pager scoping, field text spacing, response-body diagnostics, parser diagnostics, typed scalar diagnostics, and search parameter validation.

This slice is not a duplicate of [005-pr-bound-listpages-pagination-by-limit.md](005-pr-bound-listpages-pagination-by-limit.md), which bounds client-side pagination by `limit`; [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), which routes additional page fetches through retry; [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), which retries the first page; or [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md), which protects field values from being mistaken for the response-wide pager. It is not a duplicate of response-body or field parser diagnostics, which cover page result extraction after pagination has already been selected. This slice covers the accepted-value shape of response-wide ListPages pager page labels.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [005-pr-bound-listpages-pagination-by-limit.md](005-pr-bound-listpages-pagination-by-limit.md), [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md), [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md), [183-pr-listpages-fetch-failure-context.md](183-pr-listpages-fetch-failure-context.md), [191-pr-listpages-key-parse-context.md](191-pr-listpages-key-parse-context.md), [220-pr-listpages-response-body-context.md](220-pr-listpages-response-body-context.md), [239-pr-listpages-field-type-context.md](239-pr-listpages-field-type-context.md), [240-pr-listpages-response-body-type-context.md](240-pr-listpages-response-body-type-context.md), [305-pr-listpages-timestamp-context.md](305-pr-listpages-timestamp-context.md), [306-pr-listpages-user-context.md](306-pr-listpages-user-context.md), [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md), [344-pr-validate-search-pagination-types.md](344-pr-validate-search-pagination-types.md), [382-pr-validate-page-collection-search-fullnames.md](382-pr-validate-page-collection-search-fullnames.md), [396-pr-validate-listpages-retry-control.md](396-pr-validate-listpages-retry-control.md), and the adjacent response-wide pager-page drafts [750-pr-validate-site-member-pager-page-ascii-shape.md](750-pr-validate-site-member-pager-page-ascii-shape.md), [751-pr-validate-private-message-pager-page-ascii-shape.md](751-pr-validate-private-message-pager-page-ascii-shape.md), [752-pr-validate-forum-post-pager-page-ascii-shape.md](752-pr-validate-forum-post-pager-page-ascii-shape.md), and [753-pr-validate-forum-thread-pager-page-ascii-shape.md](753-pr-validate-forum-thread-pager-page-ascii-shape.md).

## Changes

- Add a local pager-page parser for `PageCollection.search_pages(...)` that accepts only `[0-9]+` before integer conversion.
- Raise `NoElementException` with site, first-response offset, field, and observed value context when a pager label is digit-like but not ASCII digits.
- Preserve ordinary non-numeric pager labels, missing pager behavior, valid ASCII pagination, paginated retry handling, `limit` bounding, response-body diagnostics, ListPages field parsing, field-value pager filtering, and page/source iterator behavior.
- Add focused regression coverage for a response-wide ListPages pager containing fullwidth page label `"\uff12"`.

## Type Of Change

- Bug fix
- ListPages pager scalar-shape validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A response-wide ListPages pager label containing non-ASCII digit glyphs must fail before any extra offset request is issued. |
| R2 | The malformed pager diagnostic must include site, offset, field, and observed value context. |
| R3 | Valid ASCII pager labels must continue to fetch subsequent ListPages offsets. |
| R4 | Ordinary non-numeric pager labels such as `next` must continue to be ignored. |
| R5 | ListPages field-value-local pager markup must continue to be ignored as page field content, not response pagination. |
| R6 | Existing response-body, retry-exhaustion, limit-bounding, parser-context, page/source iterator, and adjacent page workflows must remain compatible. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, real page content, raw generated HTML from real accounts, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, page tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `"\uff12"` in the response-wide pager raises before an additional offset request can be made. | `test_search_pages_rejects_non_ascii_digit_pager_target` failed RED with `DID NOT RAISE`, then passed after ASCII-only pager parsing. | Returning pages, normalizing `"\uff12"` into page `2`, issuing an additional request, or silently dropping the malformed digit rejects this local completion claim. | ListPages pager parser | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | The exception reports `ListPages pager page is malformed for site: test-site, offset: 500 (field=page, value=\uff12)`. | The focused regression asserts the diagnostic family and contextual fields. | A raw `ValueError`, omitted site/offset context, omitted scalar value, or unrelated ListPages field diagnostic rejects this local completion claim. | Pager diagnostics | focused test |
| R3 | Valid ASCII pager label `2` still fetches the next offset and appends parsed pages. | Focused GREEN included `test_search_pages_pagination_preserves_query_offset` and `test_search_pages_additional_pager_requests_use_retry`. | Failing to fetch the next offset, changing offset arithmetic, bypassing retry, or returning only first-page pages rejects this local completion claim. | Valid pagination | page pagination tests |
| R4 | `next` remains ignored when no numeric page label exists. | Focused GREEN included `test_search_pages_ignores_pager_without_numeric_targets`. | Raising for `next` or making a synthetic additional request rejects this local completion claim. | Non-numeric pager compatibility | page pager test |
| R5 | Pager-like markup inside a ListPages field value remains scoped away from response pagination. | Focused GREEN included `test_search_pages_ignores_field_value_pager_markup`. | Treating field value content as response pagination or issuing an additional request rejects this local completion claim. | Field-value scoping | ListPages field-pager test |
| R6 | Adjacent page workflows remain green. | `tests/unit/test_page.py` passed 394 tests, and full unit passed 3755 tests. | Regressing first-page retry, additional-page retry, response-body diagnostics, limit bounding, field parsing, page acquisition, source iteration, metadata, revisions, files, votes, or any unit test rejects this local completion claim. | Page workflows | `tests/unit` |
| R7 | No live site state or private material is needed. | The regression uses synthetic unit-level ListPages HTML and mock AMC responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, real account names, real page content, or raw generated HTML from real accounts rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, page tests, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `79b6b8d fix(page): validate listpages pager page shape`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_rejects_non_ascii_digit_pager_target -q` failed before the fix with `DID NOT RAISE` because pager label `"\uff12"` was accepted and normalized as page `2`.
- GREEN focused pager slice: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_rejects_non_ascii_digit_pager_target tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_pagination_preserves_query_offset tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_additional_pager_requests_use_retry tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_ignores_pager_without_numeric_targets tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_ignores_field_value_pager_markup tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_failed_retry_additional_page_raises tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_missing_additional_response_body_includes_site_and_offset_context -q` passed 7 tests.
- `uv run --extra test pytest tests/unit/test_page.py -q` passed 394 tests.
- `uv run --extra test pytest tests/unit -q` passed 3755 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no ListPages pager-boundary, compatibility, architecture, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker: `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, launcher SHA256 `0518e09af8c6a44990de082462039c9593a8f969a8e0eb10426aa6b3dcf630be`.

## Acceptance Criteria

- `PageCollection.search_pages(site, SearchPagesQuery(offset=500, perPage=100))` raises `NoElementException("ListPages pager page is malformed ...")` for a response-wide pager label whose text is `"\uff12"`.
- The malformed pager diagnostic includes `site: test-site`, `offset: 500`, `field=page`, and `value=\uff12` context.
- The parser does not issue an additional ListPages request from non-ASCII digit pager text.
- Valid ASCII response-wide pager labels such as `2` still fetch and parse paginated ListPages results.
- Ordinary non-numeric pager labels such as `next` still leave ListPages as a single-page result when no numeric page label exists.
- ListPages field-value-local pager-like markup is still ignored as field content and does not drive response-wide pagination.
- Existing response-body diagnostics, retry-exhaustion behavior, limit bounding, parser-context diagnostics, page acquisition, source iteration, adjacent page suites, and full unit behavior remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real accounts, raw rollout path, real account name, real page content, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with field-value pager scoping. Mitigation: field-value pager markup remains covered by Issue 100; this slice validates response-wide pager page-label shape after pager selection.
- Risk: This could be confused with ListPages retry or limit bounding. Mitigation: Issues 005, 016, and 038 cover request count and retry behavior; this slice runs before valid additional request bodies are built.
- Risk: This could break ordinary pager labels such as `next`. Mitigation: non-numeric labels are still ignored; only digit-like non-ASCII labels that the old code treated as numeric now fail.
- Risk: This could break valid pagination. Mitigation: ASCII `[0-9]+` labels still convert to integers, and the existing offset and retry pagination tests remain green.
- Risk: Diagnostics could expose page content. Mitigation: the new diagnostic includes only site/offset context and the malformed pager scalar; tests use synthetic HTML and do not include real page content.
- Risk: Another digit-like Unicode category could behave differently than fullwidth digits. Mitigation: the code rejects any `str.isdigit()` value that does not match ASCII digits, covering fullwidth, superscript, Arabic-Indic, and similar digit glyphs.

## Dependencies

- BeautifulSoup continues to expose generated pager link text through `get_text(strip=True)`.
- Normal Wikidot ListPages pager page labels are expected to be ASCII decimal digits.
- `PageCollection._pager_from_listpages_html(...)` continues to scope the response-wide pager before page-number parsing.
- `PageCollection._listpages_response_body(...)` continues to validate first and paginated response bodies before pager and row parsing.

## Open Questions

None for this local slice. Future ListPages pagination changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

ListPages pagination is a browser-free acquisition boundary. Unicode digit normalization can silently turn malformed generated pager text into a valid-looking offset request, which is surprising and hard to diagnose in page searches, corpus scans, migration checks, required-tag ledgers, or source collection workflows. Requiring ASCII digits keeps generated pagination strict while preserving valid Wikidot pager behavior and existing parser diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: fullwidth digit pager text was accepted and normalized into page `2`.
- Existing local drafts covered ListPages bounds, first/additional retry behavior, iterator chunking, required-tag filters, field scoping, field-value pager filtering, response-body diagnostics, parser diagnostics, typed scalar diagnostics, and search parameter validation; they did not validate Unicode digit normalization in response-wide ListPages pager labels.
- This slice does not change request module names, retry policy, valid ASCII pagination, first-page parsing, paginated response-body diagnostics, field parsing, field-value pager scoping, page/source iteration, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated HTML from real accounts, real account names, real page content, private site data, and private page source out of upstream discussion.
