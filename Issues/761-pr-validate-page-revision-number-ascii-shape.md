# PR Draft: Validate Page Revision Number ASCII Shape

## Summary

`PageCollection.get_page_revisions()` parses generated `history/PageRevisionListModule` rows into page-owned `PageRevision` objects. Issue 237 converted malformed revision-number cells such as `not-a-number.` into contextual `NoElementException`, and Issue 637 rejects parseable negative revision numbers such as `-1.`. One accepted-value gap remained: the revision-number helper still passed the stripped cell text directly to `int(...)`, so a generated cell containing a non-ASCII digit glyph such as `\uff13.` was accepted and normalized into ordinary `rev_no=3`.

This change accepts generated page-history revision numbers only when the numeric text matches ASCII digits, with the existing optional leading minus retained so negative ASCII values continue through the established non-negative diagnostic. Valid generated cells such as `3.` continue to parse normally, malformed text keeps the contextual `Revision number is malformed ...` path, negative ASCII cells keep the contextual `Revision number must be non-negative ...` path, and non-ASCII digit-like cells now fail before any `PageRevision` collection is assigned.

## Outcome

Page revision-list parsing no longer fabricates revision numbers by normalizing malformed generated cell metadata. A `PageRevisionListModule` response with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like revision-number text now fails at the revision-number parser boundary with site, page, structural revision ID, page ID, field, and observed value context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page revision history reads, source/html revision fetching, publication audits, migration ledgers, rollback tooling, local fixtures, cached page-revision records, or generated review records where `PageRevision.rev_no` must reflect structurally valid Wikidot page-history metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify page revision-list acquisition as a practical retry-aware read surface. Existing drafts cover revision-list retries, duplicate request reduction, parse reuse, row-cell scoping, comment spacing, cached duplicate revision reuse, response-body diagnostics, row-ID diagnostics, malformed revision-number diagnostics, non-negative revision-number validation, author/timestamp diagnostics, revision source/html reads, collection validation, direct revision identity validation, and generated scalar ASCII-shape fixes.

This slice is not a duplicate of [237-pr-page-revision-number-parse-context.md](237-pr-page-revision-number-parse-context.md). Issue 237 converts non-integer text such as `not-a-number.` into a contextual parser error; it did not cover Unicode digit normalization inside text that Python's `int(...)` accepts.

This slice is also not a duplicate of [637-pr-validate-non-negative-revision-numbers.md](637-pr-validate-non-negative-revision-numbers.md), which covers negative direct revision numbers and generated negative page-history cells such as `-1.`. The new ASCII-shape check deliberately preserves the existing negative-value path for ASCII `-1.`.

It is also not a duplicate of [756-pr-validate-page-revision-row-id-ascii-shape.md](756-pr-validate-page-revision-row-id-ascii-shape.md), [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md), or [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), which cover structural row IDs, ID ranges, or direct constructor state rather than generated revision-number cell Unicode normalization.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), [222-pr-page-revision-batch-response-body-context.md](222-pr-page-revision-batch-response-body-context.md), [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md), [237-pr-page-revision-number-parse-context.md](237-pr-page-revision-number-parse-context.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [332-pr-page-revision-list-response-body-type-context.md](332-pr-page-revision-list-response-body-type-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), [637-pr-validate-non-negative-revision-numbers.md](637-pr-validate-non-negative-revision-numbers.md), [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md), [756-pr-validate-page-revision-row-id-ascii-shape.md](756-pr-validate-page-revision-row-id-ascii-shape.md), and adjacent generated-scalar ASCII-shape drafts [757-pr-validate-forum-post-id-ascii-shape.md](757-pr-validate-forum-post-id-ascii-shape.md), [758-pr-validate-forum-post-revision-id-ascii-shape.md](758-pr-validate-forum-post-revision-id-ascii-shape.md), [759-pr-validate-recent-change-revision-cell-ascii-shape.md](759-pr-validate-recent-change-revision-cell-ascii-shape.md), and [760-pr-validate-forum-thread-detail-post-count-ascii-shape.md](760-pr-validate-forum-thread-detail-post-count-ascii-shape.md).

## Changes

- Require ASCII `-?[0-9]+` before integer conversion when parsing generated page-history revision-number cells.
- Preserve successful parsing for valid generated cells such as `3.` and the existing direct `PageRevision` constructor behavior.
- Preserve the existing contextual malformed-number diagnostic for non-integer text such as `not-a-number.`.
- Preserve the existing contextual non-negative diagnostic for negative ASCII cells such as `-1.`.
- Add focused regression coverage for a generated page-history revision-number cell containing fullwidth text `\uff13.`.

## Type Of Change

- Bug fix
- Page revision-list generated scalar validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated page-history revision-number cell containing non-ASCII digit glyphs must fail before a `PageRevisionCollection` is assigned. |
| R2 | The malformed revision-number diagnostic must identify the site, page, structural revision ID, page ID, affected field, and observed raw value. |
| R3 | Valid generated ASCII revision-number cells such as `3.` must continue to parse into the same revision numbers. |
| R4 | Existing malformed text and negative ASCII revision-number paths must keep their established diagnostics. |
| R5 | Existing revision-list response validation, row-ID parsing, row-cell scoping, author parsing, timestamp parsing, comment extraction, duplicate page-ID grouping, cached revision reuse, lazy page revision properties, page-revision source/html workflows, and adjacent site workflows must remain compatible. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, real page history HTML, raw page contents, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, page acquisition tests, page module tests, adjacent page/page-revision/site tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `\uff13.` raises before page revisions are assigned. | `test_acquire_revisions_rejects_non_ascii_digit_revision_number` failed RED with `DID NOT RAISE`, then passed after ASCII-only revision-number parsing. | Returning a `PageRevision`, normalizing `"\uff13"` into `rev_no=3`, assigning `_revisions`, or silently skipping the row rejects this local completion claim. | Page revision-number parser | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | The exception reports `Revision number is malformed for site: test-site, page: test-page, revision: 1000003 (id=12345, field=revision_number, value=\uff13.)`. | The focused regression asserts the diagnostic family, structural revision ID, page ID, field, and observed value. | A raw `ValueError`, omitted site/page/revision/page-ID context, omitted field/value, or unrelated parser diagnostic rejects this local completion claim. | Revision-number diagnostics | focused test |
| R3 | Valid ASCII revision-number cells still parse successfully. | Focused GREEN included `test_acquire_revisions_success`; `TestPageCollectionAcquire` passed 76 tests and `tests/unit/test_page.py` passed 396 tests. | Rejecting `3.`, changing parsed revision numbers, changing revision count, or changing successful row fields rejects this local completion claim. | Valid revision-list parsing | `tests/unit/test_page.py` |
| R4 | Existing malformed and negative paths stay stable. | Focused GREEN included `test_acquire_revisions_malformed_revision_number_includes_site_page_and_value_context` and `test_acquire_revisions_negative_revision_number_includes_site_page_and_value_context`. | Accepting `not-a-number.`, reclassifying `-1.` as malformed text, dropping context, or changing the non-negative diagnostic rejects this local completion claim. | Parser compatibility | `tests/unit/test_page.py` |
| R5 | Adjacent page and site workflows remain green. | Adjacent page/page-revision/site coverage passed 934 tests, and full unit passed 3762 tests. | Regressing response-body diagnostics, row-ID parsing, row-cell scoping, author/timestamp parsing, comment extraction, duplicate reuse, cached revision reuse, lazy properties, page revision source/html behavior, site workflows, or any unit test rejects this local completion claim. | Page and adjacent workflows | `tests/unit` |
| R6 | No live site state or private material is needed. | The regression mutates the synthetic `page_revisionlist` fixture and uses mocked AMC responses only. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw page history HTML from real sites, real account names, real page content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, page acquisition, page module, adjacent suite, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `bbc8312 fix(page): validate revision number ascii shape`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_rejects_non_ascii_digit_revision_number -q` failed before the fix with `DID NOT RAISE` because `\uff13.` was accepted and normalized as `rev_no=3`.
- GREEN focused page revision-number slice: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_rejects_non_ascii_digit_revision_number tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_revision_number_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_negative_revision_number_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_rejects_non_ascii_digit_revision_row_id tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_revision_id_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_success -q` passed 6 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 76 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 396 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 934 tests.
- `uv run pytest tests/unit -q` passed 3762 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no parser boundary, compatibility, architecture, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker: `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, local clawpatch commit `59e2dea`, launcher SHA256 `d6726fac4db7531d06c27d38e71e881f5e6360b1536df9a51f72bd8c4913ece1`.

## Acceptance Criteria

- `PageCollection.get_page_revisions()` raises `NoElementException("Revision number is malformed ...")` for a generated revision-number cell whose text is `\uff13.`.
- The malformed revision-number diagnostic includes `site: test-site`, `page: test-page`, `revision: 1000003`, `id=12345`, `field=revision_number`, and `value=\uff13.` context.
- The parser does not create or assign a `PageRevision(rev_no=3, ...)` from non-ASCII digit revision-number metadata.
- Valid ASCII generated revision-number cells such as `3.` still parse successfully.
- Existing malformed text such as `not-a-number.` still raises the contextual malformed revision-number diagnostic.
- Existing negative ASCII text such as `-1.` still raises the contextual non-negative revision-number diagnostic.
- Existing response-body diagnostics, row-ID parsing, row-cell scoping, author/timestamp diagnostics, comment extraction, duplicate page-ID grouping, cached revision reuse, lazy revision properties, page revision source/html workflows, site workflows, and full unit behavior remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real accounts, raw rollout path, real account name, real page content, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 237. Mitigation: Issue 237 covers malformed text that `int(...)` rejects; this slice covers Unicode digit glyphs that `int(...)` accepts.
- Risk: This could be confused with Issue 637. Mitigation: Issue 637 covers negative revision numbers; this slice keeps ASCII negative text valid for parser classification so the existing non-negative diagnostic remains intact.
- Risk: This could be confused with Issue 756. Mitigation: Issue 756 covers generated structural row IDs; this slice covers generated revision-number cells after row ID parsing succeeds.
- Risk: This could alter valid page history parsing. Mitigation: ASCII `[0-9]+` generated revision-number cells still convert to integers, and successful acquisition plus adjacent page/page-revision/site tests remain green.
- Risk: Diagnostics could expose page content. Mitigation: the diagnostic includes only site/page identifiers, page ID, structural revision ID, field name, and the compact revision-number scalar; tests use synthetic fixture HTML and do not include real page content.

## Dependencies

- BeautifulSoup continues to expose generated page-history revision-number cells through the first direct structural `td`.
- Normal Wikidot page history revision-number cells are expected to use ASCII decimal digits, conventionally followed by a trailing period.
- Existing page revision-list parser context continues to identify site, page, page ID, structural revision ID, field, and raw scalar value.
- Existing `PageRevision` constructor validation continues to validate direct record state after parser-side conversion.

## Open Questions

None for this local slice. Future generated scalar-shape changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Page revision numbers are durable generated ordering metadata for revision source/html fetches, history audits, rollback decisions, publication verification, migration ledgers, and cached records. Unicode digit normalization can silently turn malformed generated cell text into a valid-looking revision number. Requiring ASCII digits keeps generated revision-number parsing strict while preserving valid Wikidot history rows and existing contextual parser diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: a fullwidth generated revision-number cell was accepted and normalized into `rev_no=3`.
- Existing local drafts covered page revision-list retry behavior, duplicate request reduction, parse reuse, row-cell scoping, comment spacing, cached duplicate revision reuse, response-body diagnostics, non-numeric row-ID context, Unicode row-ID normalization, revision-number context, negative revision-number validation, author/timestamp context, direct revision identity validation, and adjacent generated scalar ASCII-shape fixes; they did not validate Unicode digit normalization in page revision-number cells.
- This slice does not change request module names, retry policy, response-body validation, valid ASCII history rows, row-ID parsing, user parsing, timestamp parsing, comment extraction, cached duplicate reuse, lazy source/html properties, live Wikidot behavior, direct `PageRevision` constructors, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated HTML from real accounts, real account names, real page content, private site data, and private page source out of upstream discussion.
