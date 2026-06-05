# PR Draft: Report Malformed Page Revision Timestamps

## Summary

`PageCollection.get_page_revisions()` parses Wikidot page history rows from `history/PageRevisionListModule` and converts each revision row's `span.odate` into `PageRevision.created_at`. The surrounding page history parser already reports malformed revision row IDs, malformed revision numbers, missing author elements, malformed author user metadata, and missing timestamp elements with site/page/revision context. One adjacent boundary still called the shared `odate_parse(...)` utility directly: when the timestamp element existed but carried a malformed `time_...` class, the shared parser's raw `ValueError` escaped without identifying the page history row.

This local slice keeps the shared `odate_parse(...)` utility unchanged. It catches malformed present page revision timestamp metadata at the page history parser boundary and raises `NoElementException` with site unix name, page fullname, page ID, revision ID, `field=created_at`, and the offending `time_...` class value.

## Outcome

Malformed page revision timestamps now fail with page/revision-local context instead of leaking a raw shared timestamp parser exception.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who parse page history for browser-free audit, archival indexing, source collection, import workflows, rollback inspection, or generated page-change ledgers.

## Related Issue

Builds on [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [150-pr-page-revision-failure-context.md](150-pr-page-revision-failure-context.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), [222-pr-page-revision-batch-response-body-context.md](222-pr-page-revision-batch-response-body-context.md), [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md), [237-pr-page-revision-number-parse-context.md](237-pr-page-revision-number-parse-context.md), and [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md). Those drafts established page revision acquisition as a practical read path with retry, deduplication, parser reuse, row-cell scoping, comment spacing, response-body diagnostics, row-ID diagnostics, revision-number diagnostics, and malformed author diagnostics.

This slice also follows the shared timestamp parser-boundary pattern from [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), [287-pr-private-message-detail-timestamp-value-context.md](287-pr-private-message-detail-timestamp-value-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [296-pr-forum-post-list-timestamp-context.md](296-pr-forum-post-list-timestamp-context.md), and [298-pr-forum-post-list-edit-timestamp-context.md](298-pr-forum-post-list-edit-timestamp-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Convert malformed present page revision `span.odate` metadata from raw `ValueError` into contextual `NoElementException`.
- Include site unix name, page fullname, page ID, revision ID, `field=created_at`, and the observed direct `time_...` class value in the parser error.
- Preserve the shared `odate_parse(...)` utility behavior and parser tests.
- Preserve successful `PageCollection.get_page_revisions()` parsing and valid timestamp handling.
- Preserve existing response-body diagnostics, row-cell scoping, malformed revision row ID diagnostics, malformed revision number diagnostics, missing author diagnostics, malformed author diagnostics, missing timestamp diagnostics, comment spacing, duplicate page-ID deduplication, cached revision reuse, source/HTML cloning, retry behavior, and lazy `Page.revisions` behavior.
- Add a focused public `PageCollection.get_page_revisions()` regression for a malformed created-at `time_latest` value.

## Type Of Change

- Bug fix / diagnostics improvement
- Page revision parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A structural page revision row with malformed present created-at `span.odate` metadata must fail at the page revision parser boundary. |
| R2 | The malformed timestamp error must identify the affected site, page, page ID, revision ID, field, and observed direct `time_...` class value. |
| R3 | Existing valid page revision parsing must remain compatible. |
| R4 | Existing page revision response handling, retry, deduplication, cache reuse, row-cell scoping, row-ID diagnostics, revision-number diagnostics, author diagnostics, missing timestamp diagnostics, comment spacing, source cloning, and lazy revision behavior must remain unchanged. |
| R5 | Focused, page-level, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `PageCollection.get_page_revisions()` raises `NoElementException` for `class="odate time_latest"` in a structural page history created-at element. | `TestPageCollectionAcquire.test_acquire_revisions_malformed_created_at_includes_site_page_and_value_context` returns a page revision-list body and expects `NoElementException`. | Leaking raw `ValueError`, fabricating a timestamp, silently skipping the revision, returning `created_at=None`, or returning a malformed `PageRevision` rejects this local completion claim. | `src/wikidot/module/page.py` | `tests/unit/test_page.py` |
| R2 | The error names `site: test-site`, `page: test-page`, `revision: 456`, `id=12345`, `field=created_at`, and `value=time_latest`. | The focused regression matches all fields. | Omitting page identity, revision identity, field name, page ID, or the bad class value makes the failure ambiguous and rejects this local completion claim. | Page revision diagnostics | `tests/unit/test_page.py` |
| R3 | Valid page revision rows still parse through the existing public acquisition API. | Focused GREEN includes revision-list success and nested row-cell scoping; `tests/unit/test_page.py` passed 154 tests. | Regressing revision IDs, revision numbers, authors, timestamps, comments, duplicate-page reuse, cache reuse, or collection ownership rejects this local completion claim. | Page revision acquisition | `tests/unit/test_page.py` |
| R4 | Adjacent page revision diagnostics stay green. | Focused GREEN includes missing timestamp context and malformed author context; the page-level run includes existing row-ID, revision-number, missing-cell, and missing-author diagnostics. | Rewording unrelated diagnostics, weakening direct row-cell scoping, or changing missing-element behavior rejects this local completion claim. | Page revision diagnostics and acquisition | `tests/unit/test_page.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `3d73d72 fix(page): report malformed revision timestamps`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_created_at_includes_site_page_and_value_context -q` failed before the fix with `ValueError: invalid literal for int() with base 10: 'latest'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_created_at_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_missing_created_at_includes_site_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_created_by_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_success tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_ignores_nested_table_cells -q` passed 5 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 154 tests.
- `uv run pytest tests/unit -q` passed 862 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 80 files already formatted.
- `uv run mypy src` passed with no issues in 35 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` could not spawn `pyright` because no executable was available in this environment.

## Acceptance Criteria

- `PageCollection.get_page_revisions()` raises `NoElementException` when a page revision-list response has a structural created-at `span.odate` element whose direct `time_...` class cannot be parsed by the shared odate parser.
- The malformed created-at error includes the site unix name, page fullname, page ID, revision ID, `field=created_at`, and observed direct `time_...` class value.
- Valid page revision rows still parse created-at timestamps through `odate_parser(...)`.
- Existing response-body diagnostics, row-cell scoping, malformed revision row ID diagnostics, malformed revision number diagnostics, missing author diagnostics, malformed author diagnostics, missing timestamp diagnostics, comment spacing, duplicate page-ID deduplication, cached revision reuse, source/HTML cloning, retry behavior, and lazy `Page.revisions` behavior remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, raw generated page history from real sites, page titles from real sites, credentials, cookies, auth JSON, or private page content is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Wrapping shared-parser `ValueError` could hide an unexpected timestamp parsing failure. Mitigation: the wrapper preserves exception chaining with `from exc` and adds only page revision location metadata.
- Risk: Changing the shared odate parser could affect unrelated modules. Mitigation: this slice intentionally leaves `odate_parse(...)` unchanged and validates parser-adjacent page behavior through the full unit suite.
- Risk: Timestamp-like markup inside the comment cell could be mistaken for the structural created-at timestamp. Mitigation: existing direct row-cell scoping remains unchanged, and focused GREEN includes the nested row-cell scoping test.

## Dependencies

- BeautifulSoup continues to expose direct page revision-list `span.odate` elements and direct class values in generated page history rows.
- The shared `odate_parse(...)` utility remains the source of truth for valid Wikidot odate metadata extraction.
- Page revision-list rows still identify created-at timestamps through the direct created-at cell of `table.page-history > tr[id^=revision-row-]`.

## Open Questions

None for this local slice. Broader centralization of repeated user/timestamp value helpers could be considered later only if it reduces duplication without changing parser behavior.

## Upstream-Safe Motivation

Page revision history is a common read path for source collection, audit ledgers, rollback inspection, and archival tooling. If Wikidot emits a structural page history row with malformed direct created-at metadata, wikidot.py should return a structured parser failure naming the affected site, page, revision, field, and observed value instead of forcing operators to infer context from a raw shared helper exception. That keeps page revision diagnostics actionable without retaining generated page history HTML, raw response JSON, credentials, or local rollout paths.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established page revision acquisition as a practical read path, including retry-aware revision-list fetching, duplicate page-ID deduplication, cached revision-list reuse, response-body validation, structural row-cell parser context, row-ID diagnostics, revision-number diagnostics, author diagnostics, comment spacing, source/HTML cloning, and lazy revision behavior.
- Recent timestamp parser-boundary drafts validated the same shared `odate_parse(...)` failure pattern in recent changes, private messages, site members, forum thread lists, forum thread details, forum post lists, forum post edit metadata, and forum post revisions.
- The immediate RED failure showed the same raw `ValueError` class that prior parser-boundary timestamp slices converted in adjacent modules.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated page history HTML, page names from real sites, page titles from real sites, page source text, and private page content out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It narrows a raw utility-parser exception into the same local exception family used by surrounding page revision diagnostics.
