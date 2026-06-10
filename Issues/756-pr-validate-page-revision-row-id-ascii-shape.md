# PR Draft: Validate Page Revision Row ID ASCII Shape

## Summary

`PageCollection.get_page_revisions()` parses generated `history/PageRevisionListModule` rows whose structural IDs use the `revision-row-<id>` form. The contextual row-ID parser added by Issue 236 still used `raw_id.isdigit()` before `int(raw_id)`, so generated IDs containing Unicode digit glyphs such as `"revision-row-\uff11\uff12\uff13"` were accepted and normalized into ordinary revision ID `123`.

This change accepts generated page revision row IDs only when the suffix matches ASCII digits. Valid generated IDs such as `revision-row-1000003` continue to parse normally, malformed non-numeric IDs keep the same contextual `NoElementException`, and digit-like non-ASCII IDs now fail with `NoElementException("Revision ID is malformed ...")` including site, page, page ID, field, and observed value context.

## Outcome

Page revision-list parsing no longer fabricates revision identities by normalizing malformed generated row metadata. A `PageRevisionListModule` response with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like row ID text now fails at the row-ID parser boundary before any `PageRevision` records are created.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page revision history reads, source/html revision fetching, publication audits, migration ledgers, rollback tooling, local fixtures, or generated workflows where revision identity must come only from structurally valid Wikidot row metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify page revision-list acquisition as a practical retry-aware read surface. Existing drafts cover revision-list retries, duplicate request reduction, parse reuse, row-cell scoping, comment spacing, cached duplicate revision reuse, response-body diagnostics, row-ID diagnostics, revision-number diagnostics, author/timestamp diagnostics, revision source/html reads, collection validation, and direct revision identity validation.

This slice is not a duplicate of [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md). Issue 236 converted malformed non-numeric `revision-row-*` values such as `revision-row-not-a-number` from raw `ValueError` into contextual `NoElementException`, but its parser still accepted Unicode digit glyphs because Python `str.isdigit()` is broader than ASCII decimal syntax. This slice covers the accepted-value shape of the generated revision row ID suffix.

It is also not a duplicate of [237-pr-page-revision-number-parse-context.md](237-pr-page-revision-number-parse-context.md), [637-pr-validate-non-negative-revision-numbers.md](637-pr-validate-non-negative-revision-numbers.md), [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md), or [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), which cover revision-number cells, range validation, and direct constructor state rather than generated structural row-ID Unicode normalization.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), [222-pr-page-revision-batch-response-body-context.md](222-pr-page-revision-batch-response-body-context.md), [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md), [237-pr-page-revision-number-parse-context.md](237-pr-page-revision-number-parse-context.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [332-pr-page-revision-list-response-body-type-context.md](332-pr-page-revision-list-response-body-type-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), [637-pr-validate-non-negative-revision-numbers.md](637-pr-validate-non-negative-revision-numbers.md), [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md), and adjacent generated-scalar ASCII-shape drafts [734-pr-validate-page-id-script-shape.md](734-pr-validate-page-id-script-shape.md), [744-pr-validate-page-file-row-id-ascii-shape.md](744-pr-validate-page-file-row-id-ascii-shape.md), [748-pr-validate-regular-user-onclick-id-ascii-shape.md](748-pr-validate-regular-user-onclick-id-ascii-shape.md), and [749-pr-validate-deleted-user-data-id-ascii-shape.md](749-pr-validate-deleted-user-data-id-ascii-shape.md).

## Changes

- Require ASCII `[0-9]+` before integer conversion when parsing generated page revision row ID suffixes.
- Preserve the existing contextual `NoElementException` message family for missing prefixes, non-numeric suffixes, and now non-ASCII digit suffixes.
- Preserve successful revision-list parsing, revision number parsing, editor parsing, timestamp parsing, comment extraction, duplicate page-ID grouping, cached revision reuse, row-cell scoping, response-body diagnostics, lazy `Page.revisions`, and `Page.latest_revision`.
- Add focused regression coverage for a generated row ID containing fullwidth revision ID text `"revision-row-\uff11\uff12\uff13"`.

## Type Of Change

- Bug fix
- Page revision-list generated identity validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated page revision row ID containing non-ASCII digit glyphs must fail before any `PageRevision` is created from that row. |
| R2 | The malformed row-ID diagnostic must include site, page, page ID, field, and observed value context. |
| R3 | Valid ASCII `revision-row-<digits>` IDs must continue to parse and populate revision collections. |
| R4 | Existing malformed non-numeric row IDs such as `revision-row-not-a-number` must keep the contextual `NoElementException` path. |
| R5 | Existing revision-list response-body, row-cell scoping, revision-number, author, timestamp, comment, duplicate, cache, page-revision, and site workflows must remain compatible. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, real page content, raw generated HTML from real accounts, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, page acquisition tests, adjacent page/page-revision/site tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `"revision-row-\uff11\uff12\uff13"` raises before revision collection assignment. | `test_acquire_revisions_rejects_non_ascii_digit_revision_row_id` failed RED with `DID NOT RAISE`, then passed after ASCII-only row-ID parsing. | Returning a `PageRevision`, normalizing `"\uff11\uff12\uff13"` into revision ID `123`, assigning `_revisions`, or silently skipping the row rejects this local completion claim. | Page revision row-ID parser | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | The exception reports `Revision ID is malformed for site: test-site, page: test-page (id=12345, field=revision_row_id, value=revision-row-\uff11\uff12\uff13)`. | The focused regression asserts the diagnostic family and contextual fields. | A raw `ValueError`, omitted site/page/page-ID context, omitted field/value, or unrelated row diagnostic rejects this local completion claim. | Row-ID diagnostics | focused test |
| R3 | Valid ASCII revision row IDs still parse successfully. | `TestPageCollectionAcquire` passed 75 tests, including successful revision acquisition from the fixture row IDs. | Rejecting `revision-row-1000003`, changing revision IDs, changing revision count, or breaking normal history parsing rejects this local completion claim. | Valid revision-list parsing | `tests/unit/test_page.py` |
| R4 | Non-numeric row IDs retain contextual failure. | Focused GREEN included `test_acquire_revisions_malformed_revision_id_includes_site_page_and_value_context`. | Reintroducing raw `ValueError`, changing the message family, or skipping malformed rows rejects this local completion claim. | Existing row-ID diagnostic | `tests/unit/test_page.py` |
| R5 | Adjacent revision and site workflows remain green. | `tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py` passed 932 tests, and full unit passed 3757 tests. | Regressing response-body diagnostics, row-cell scoping, revision numbers, users, timestamps, comments, duplicate reuse, lazy properties, page workflows, site workflows, or any unit test rejects this local completion claim. | Page and site workflows | `tests/unit` |
| R6 | No live site state or private material is needed. | The regression uses a synthetic fixture-derived page revision-list body and mock AMC responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, real account names, real page content, or raw generated HTML from real accounts rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, acquisition tests, adjacent suite, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `0b20d59 fix(page): validate revision row id ascii shape`.

- Initial RED fixture correction: the first test draft used a hand-built row with malformed `printuser` markup, which proved normalization by reaching a later user-parser diagnostic; the fixture was corrected to reuse the valid `page_revisionlist` row and change only the generated row ID.
- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_rejects_non_ascii_digit_revision_row_id -q` failed before the fix with `DID NOT RAISE` because `revision-row-\uff11\uff12\uff13` was accepted and normalized as revision ID `123`.
- GREEN focused row-ID slice: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_rejects_non_ascii_digit_revision_row_id tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_revision_id_includes_site_page_and_value_context -q` passed 2 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 75 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 932 tests.
- `uv run pytest tests/unit -q` passed 3757 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no revision row-ID boundary, compatibility, architecture, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker: `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, local clawpatch commit `59e2dea`, launcher SHA256 `d6726fac4db7531d06c27d38e71e881f5e6360b1536df9a51f72bd8c4913ece1`.

## Acceptance Criteria

- `PageCollection.get_page_revisions()` raises `NoElementException("Revision ID is malformed ...")` for a generated row ID whose suffix is `"\uff11\uff12\uff13"`.
- The malformed row-ID diagnostic includes `site: test-site`, `page: test-page`, `id=12345`, `field=revision_row_id`, and `value=revision-row-\uff11\uff12\uff13` context.
- The parser does not create or assign a `PageRevision(id=123, ...)` from non-ASCII digit row metadata.
- Valid ASCII structural row IDs such as `revision-row-1000003` still parse successfully.
- Existing malformed non-numeric structural row IDs such as `revision-row-not-a-number` still raise contextual `NoElementException`.
- Existing response-body diagnostics, row-cell scoping, revision-number diagnostics, author/timestamp diagnostics, comment extraction, duplicate page-ID grouping, cached revision reuse, lazy revision properties, page workflows, site workflows, and full unit behavior remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real accounts, raw rollout path, real account name, real page content, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 236. Mitigation: Issue 236 covers non-numeric row-ID diagnostics; this slice covers Unicode digit normalization that still passed the old numeric branch.
- Risk: This could be confused with revision number or direct revision identity validation. Mitigation: revision-number cells, direct `PageRevision` constructor fields, and non-negative ranges remain separate surfaces with separate tests and drafts.
- Risk: This could break valid revision history parsing. Mitigation: ASCII `[0-9]+` generated row IDs still convert to integers, and successful acquisition plus adjacent page/page-revision/site tests remain green.
- Risk: Diagnostics could expose page content. Mitigation: the diagnostic includes only site/page identifiers, page ID, field name, and the malformed scalar; tests use synthetic fixture HTML and do not include real page content.
- Risk: Another digit-like Unicode category could behave differently than fullwidth digits. Mitigation: the code rejects any suffix that does not match ASCII `[0-9]+`, covering fullwidth, superscript, Arabic-Indic, and similar digit glyphs.

## Dependencies

- BeautifulSoup continues to expose generated page history row IDs through `rev_element["id"]`.
- Normal Wikidot page history row IDs are expected to use ASCII decimal digits after `revision-row-`.
- Page revision-list response body validation continues to run before row parsing.
- Existing `PageRevision` constructor identity validation continues to validate direct record state after parser-side conversion.

## Open Questions

None for this local slice. Future generated identity-shape changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Page revision row IDs are durable generated identity metadata for revision source/html fetches, history audits, rollback decisions, publication verification, migration ledgers, and local fixtures. Unicode digit normalization can silently turn malformed generated row metadata into a valid-looking revision ID. Requiring ASCII digits keeps generated identity parsing strict while preserving valid Wikidot history rows and existing contextual parser diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: a fullwidth generated row ID suffix was accepted and normalized into revision ID `123`.
- Existing local drafts covered page revision-list retry behavior, duplicate request reduction, parse reuse, row-cell scoping, comment spacing, cached duplicate revision reuse, response-body diagnostics, non-numeric row-ID context, revision-number context, author/timestamp context, direct revision identity validation, and adjacent generated scalar ASCII-shape fixes; they did not validate Unicode digit normalization in page revision row IDs.
- This slice does not change request module names, retry policy, response-body validation, valid ASCII history rows, revision number parsing, user parsing, timestamp parsing, comment extraction, cached duplicate reuse, lazy source/html properties, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated HTML from real accounts, real account names, real page content, private site data, and private page source out of upstream discussion.
