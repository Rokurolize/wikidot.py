# PR Draft: Validate Page ID Script Shape

## Summary

`PageCollection.get_page_ids()` fetches direct `norender/true/noredirect/true` page URLs and parses generated script metadata such as `WIKIREQUEST.info.pageId = 333;`. Earlier local slices made non-HTTP response slots, missing `pageId` metadata, and the lazy `Page.id` fallback include site/page context. One adjacent parser-shape gap remained: the direct page-ID parser matched only digit assignments, so a present malformed assignment such as `WIKIREQUEST.info.pageId = latest;` or `WIKIREQUEST.info.pageId = 123abc;` was treated exactly like absent metadata and raised the existing not-found error.

This change captures present `pageId` assignments before validation, rejects non-ASCII-digit payloads as structural parser errors, and includes the site unix name, page fullname, `field=page_id`, and observed value. Truly absent `pageId` metadata remains the existing `NotFoundException`, valid numeric IDs still assign to every page represented by the direct response URL, and page-ID request batching, duplicate URL reuse, cached ID propagation, and downstream page source/revision/vote/file workflows remain unchanged.

## Outcome

Direct page-ID lookup no longer blurs malformed generated metadata with a missing page. Callers now get a deterministic `NoElementException` for present malformed `pageId` values and the prior not-found signal only when the assignment is absent.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page lookup, source collection, revision collection, vote/file acquisition, page publishing helpers, migration tools, archival workflows, moderation tools, or generated audits that rely on `Page.id` acquisition from direct Wikidot page responses.

## Current Evidence

Local rollout-backed drafts repeatedly identify page-ID acquisition as shared infrastructure for source, revision, vote, file, publishing, and direct `Site.page.get(...)` workflows. [186-pr-page-id-response-type-context.md](186-pr-page-id-response-type-context.md), [187-pr-page-id-property-context.md](187-pr-page-id-property-context.md), [190-pr-site-page-get-direct-id-error-surface.md](190-pr-site-page-get-direct-id-error-surface.md), and [197-pr-page-id-site-context.md](197-pr-page-id-site-context.md) refined response-type, missing-ID, and fallback diagnostics without changing malformed generated-value handling. [310-pr-site-id-context.md](310-pr-site-id-context.md) fixed the analogous site bootstrap case where a present malformed `siteId` assignment was previously treated as missing metadata.

Those prior slices are not duplicates. The page-ID context drafts intentionally preserved missing `WIKIREQUEST.info.pageId` behavior; they did not distinguish a present malformed assignment from no assignment. The site-ID draft covered `Site.from_unix_name(...)`, not direct page-ID lookup.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [186-pr-page-id-response-type-context.md](186-pr-page-id-response-type-context.md), [187-pr-page-id-property-context.md](187-pr-page-id-property-context.md), [190-pr-site-page-get-direct-id-error-surface.md](190-pr-site-page-get-direct-id-error-surface.md), [197-pr-page-id-site-context.md](197-pr-page-id-site-context.md), and the analogous [310-pr-site-id-context.md](310-pr-site-id-context.md).

## Changes

- Parse present `WIKIREQUEST.info.pageId` assignments with a value-capturing regex instead of a digit-only regex.
- Require the captured `pageId` value to match ASCII digits before integer conversion.
- Raise `NoElementException("Page ID is malformed for site: <site>, page: <page> (field=page_id, value=<value>)")` for present malformed `pageId` assignments.
- Preserve `NotFoundException("Cannot find page id for site: <site>, page: <page>")` for responses with no `pageId` assignment at all.
- Preserve successful numeric ID assignment across every page sharing the same direct response URL.
- Preserve page-ID batching, duplicate URL deduplication, cached duplicate URL reuse, retained-ID validation, and non-HTTP response diagnostics.
- Add focused regression coverage for malformed `latest` and `123abc` generated page-ID values.

## Type Of Change

- Bug fix
- Parser-shape validation
- Page-ID acquisition diagnostics
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A direct page response with `WIKIREQUEST.info.pageId = latest;` must raise `NoElementException` with site, page, `field=page_id`, and `value=latest`. |
| R2 | A direct page response with an alphanumeric `pageId` payload such as `123abc` must raise the same malformed-value diagnostic instead of being treated as missing metadata. |
| R3 | Valid numeric `pageId` assignments must continue to assign the parsed integer to all pages represented by that direct response URL. |
| R4 | Direct page responses with no `WIKIREQUEST.info.pageId` assignment must keep the existing site/page-context `NotFoundException`. |
| R5 | Non-HTTP response slots must keep the existing site/page-context `UnexpectedException`. |
| R6 | Page-ID request batching, duplicate URL deduplication, cached duplicate URL reuse, retained-ID validation, and lazy `Page.id` acquisition must remain unchanged. |
| R7 | Downstream page source, revision, vote, file, and direct site page accessor workflows must remain green with valid page IDs. |
| R8 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, page acquisition tests, adjacent page/site tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `latest` fails as malformed page-ID metadata with observed value context. | Focused RED failed because the current parser raised `NotFoundException`; focused GREEN passed after value-capture validation. | Treating `latest` as missing metadata, exposing raw Python conversion text, fabricating an ID, or returning a page rejects this local completion claim. | Direct page-ID parser | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Alphanumeric payloads are not ignored by the digit-only match. | The focused regression covers `123abc` and expects the same `NoElementException` shape. | Falling through to missing-ID handling or accepting the leading digits rejects this local completion claim. | Direct page-ID parser | page acquisition tests |
| R3 | Valid numeric direct responses still assign IDs. | Existing acquisition tests for duplicate URL deduplication and cached duplicate URL reuse remained green in `TestPageCollectionAcquire`. | Regressing successful ID assignment, duplicate propagation, or cached ID reuse rejects this local completion claim. | PageCollection ID acquisition | page acquisition tests |
| R4 | Absent generated metadata remains not-found. | Existing `test_acquire_page_ids_missing_id_raises_not_found_with_page_context` remained green. | Reclassifying absent metadata as malformed would break the `Site.page.get(...)` not-found surface and rejects this local completion claim. | Missing page-ID branch | page acquisition tests |
| R5 | Non-HTTP response diagnostics remain stable. | Existing `test_acquire_page_ids_unexpected_response_type_includes_page_context` remained green. | Swallowing exceptions, changing exception type, or losing site/page context rejects this local completion claim. | Response type guard | page acquisition tests |
| R6 | Request batching and retained-ID preflight behavior remain stable. | `TestPageCollectionAcquire` passed 74 tests after the parser change. | Issuing extra direct URL requests, losing deduplication, accepting malformed retained IDs, or mutating cached IDs incorrectly rejects this local completion claim. | PageCollection acquisition boundary | page acquisition tests |
| R7 | Adjacent page and site workflows remain compatible. | Page/site-adjacent unit tests passed 1110 tests, and full unit passed 3700 tests. | Regressing source, revision, vote, file, direct page lookup, page property, page URL, or site page accessor behavior rejects this local completion claim. | Page/site workflows | affected unit suites |
| R8 | No live site state or private material is needed. | All regressions use synthetic response text and mocked request utilities. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, acquisition tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `0f47c09 fix(page): report malformed page id metadata`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_malformed_id_metadata_includes_page_and_value_context -q` failed before the fix because `latest` and `123abc` both raised `NotFoundException("Cannot find page id for site: test-site, page: test-page")`.
- GREEN focused: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_malformed_id_metadata_includes_page_and_value_context -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 74 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_source.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py -q` passed 1110 tests.
- `uv run --extra test pytest tests/unit -q` passed 3700 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- A direct response containing `WIKIREQUEST.info.pageId = latest;` raises `NoElementException("Page ID is malformed for site: test-site, page: test-page (field=page_id, value=latest)")`.
- A direct response containing `WIKIREQUEST.info.pageId = 123abc;` raises the same malformed-value diagnostic with `value=123abc`.
- A direct response containing `WIKIREQUEST.info.pageId = 333;` still assigns `333` to every page sharing that request URL.
- A direct response with no `WIKIREQUEST.info.pageId` assignment still raises `NotFoundException("Cannot find page id for site: <site>, page: <page>")`.
- Non-HTTP response slots still raise `UnexpectedException` with site/page/type context.
- Page ID batching, duplicate URL reuse, cached ID reuse, retained-ID validation, and lazy `Page.id` acquisition remain stable.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Reclassifying absent page metadata as malformed could break `Site.page.get(...)` not-found behavior. Mitigation: the new branch only runs when a `pageId` assignment is present, and the existing missing-ID test remained green.
- Risk: Tightening direct page-ID parsing could affect downstream source/revision/vote/file flows. Mitigation: valid numeric IDs use the same assignment path, and page/site-adjacent plus full unit coverage passed.
- Risk: This could be confused with earlier page-ID context drafts. Mitigation: those drafts covered response type, missing metadata, and fallback context; this slice covers present malformed script values.
- Risk: The value-capturing regex might accept harmless whitespace around the assignment operator. Mitigation: this is compatible with JavaScript assignment formatting and does not loosen the accepted scalar value; the scalar still must match ASCII digits.

## Dependencies

- Wikidot direct page responses continue to expose generated metadata through `WIKIREQUEST.info.pageId = <id>;` when a page exists and returns ID metadata.
- `RequestUtil.request(...)` continues to return response slots in request URL order.
- `Page.id` validation continues to reject malformed retained IDs and negative retained IDs at assignment/preflight boundaries.

## Open Questions

None for this local slice. Other generated script scalar parsers should be selected only with a concrete non-duplicate parser boundary and RED test.

## Upstream-Safe Motivation

Page-ID acquisition is a shared recovery point for browser-free page workflows. A present malformed generated scalar should be surfaced as a parser-shape problem with the observed value, not collapsed into "page not found" merely because a digit-only regex skipped the assignment.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated that malformed present `pageId` values currently raised the same not-found error as absent metadata.
- Existing local drafts prove page-ID acquisition is central to source, revision, vote, file, publishing, and direct page lookup workflows, but did not cover present malformed generated values.
- This slice does not change live request behavior, page lookup policy, create/edit/publish behavior, cache ownership, source/revision/vote/file parsing, upstream filing state, or any credential-bearing path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, private access material, generated markup from real private sites, real user names, and private page content out of upstream discussion.
