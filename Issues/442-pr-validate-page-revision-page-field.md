# PR Draft: Validate Page Revision Page Field

## Summary

`PageRevision` records carry the parent `Page` object used by lazy revision source and HTML acquisition, duplicate revision cache reuse, revision snapshot ledgers, and page history exports. Earlier local slices validated revision collection entries, `Page.revisions` assignments, `PageRevisionCollection(...)` initialization, direct `PageRevision.source` assignments, and direct `PageRevision.html` assignments, but the public `PageRevision(...)` constructor still accepted malformed `page` values such as `None`, booleans, strings, dictionaries, and arbitrary objects.

This change validates `PageRevision.page` at initialization. Malformed values now raise `ValueError("page must be a Page")`. Existing lazy revision source/HTML acquisition, revision collection behavior, duplicate cached revision reuse, parser-created revision rows, source/html setter validation, and adjacent page workflows remain unchanged for valid `Page` objects.

## Outcome

Callers cannot silently construct revision ledger rows whose parent page is not a `Page`, while valid parser-created, fixture-created, and manually created page revisions continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page revision history, source/HTML comparison, duplicate revision cache reuse, revision snapshot ledgers, translation audits, migration scripts, rollback tooling, publication verification, or local tests that construct `PageRevision` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page revision ownership as a practical workflow surface. Existing drafts [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [201-pr-page-revision-lazy-site-context.md](201-pr-page-revision-lazy-site-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [431-pr-validate-page-revision-source-assignments.md](431-pr-validate-page-revision-source-assignments.md), and [432-pr-validate-page-revision-html-assignments.md](432-pr-validate-page-revision-html-assignments.md) establish revision reads, retry behavior, deduplication, duplicate owner preservation, cache reuse, response diagnostics, collection-entry validation, and adjacent revision cache-field integrity as active operational boundaries.

Those prior slices are not duplicates. They covered revision source/HTML acquisition, retry/fallback behavior, response diagnostics, collection entries, collection initialization, `Page.revisions` assignment, and direct revision source/html cache mutation. None validates direct `PageRevision(page=...)` construction before malformed parent-page state becomes stored dataclass state.

## Related Issue

Builds directly on [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [431-pr-validate-page-revision-source-assignments.md](431-pr-validate-page-revision-source-assignments.md), and [432-pr-validate-page-revision-html-assignments.md](432-pr-validate-page-revision-html-assignments.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PageRevision.page` validation at dataclass initialization.
- Reject non-`Page` values with `ValueError("page must be a Page")`.
- Update page revision unit fixtures to use real `Page` objects instead of generic page mocks for valid revisions.
- Preserve existing lazy revision source/HTML acquisition, duplicate cached revision reuse, parser-created revision rows, source/html setter validation, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Revision parent-page state integrity
- Test fixture tightening

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevision(page=None)`, `True`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` must raise `ValueError("page must be a Page")` when every other revision field is valid. |
| R2 | Valid `Page` instances must remain valid and preserve existing revision fields. |
| R3 | Existing lazy revision source/HTML acquisition, duplicate cached revision reuse, source/html setter validation, revision collection behavior, page revision parsing, and adjacent page workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, adjacent page revision/page tests, full unit tests, lint, format, mypy, source-file pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor pages fail at the public dataclass boundary. | `TestPageRevision.test_init_rejects_malformed_pages` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after page validation was added. | Accepting missing values, booleans, strings, dictionaries, arbitrary objects, or emitting revision rows with non-`Page` parent state rejects this local completion claim. | PageRevision constructor | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Valid page semantics stay green. | Existing page revision unit tests passed after the local fixture was moved to a real `Page` object. | Rejecting valid `Page` instances, coercing page-like mocks, or changing stored revision fields rejects this local completion claim. | PageRevision fixtures and parser-created revisions | `tests/unit/test_page_revision.py`, `tests/unit/test_page.py` |
| R3 | Existing adjacent revision workflows remain green. | `tests/unit/test_page_revision.py` passed 71 tests, `tests/unit/test_page.py` passed 250 tests, and full unit tests passed 1697 tests. | Regressing lazy source/HTML reads, retry exhaustion behavior, duplicate cached revision reuse, revision parser rows, source/html setter validation, page revision caches, or adjacent page workflows rejects this local completion claim. | Page revision and page workflows | `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, source text from real sites, revision comments, revision HTML, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `3322302 fix(page_revision): validate revision page`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_malformed_pages -q` failed 5 tests before the fix; every malformed `page` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_malformed_pages -q` passed 5 tests.
- `uv run ruff check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed.
- `uv run pytest tests/unit/test_page_revision.py -q` passed 71 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 250 tests.
- `uv run pyright src/wikidot/module/page_revision.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 1697 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `uv run pyright src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 114 existing full-tree typing errors, including intentional invalid-input test fixtures, fixture `None` mismatches, invalid `test_search_pages_query` parameter calls, and one unrelated BeautifulSoup narrowing warning in `src/wikidot/module/forum_post.py`. The changed source file and changed test file pass pyright together.

## Acceptance Criteria

- `PageRevision(page=None)`, `True`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` raise `ValueError("page must be a Page")`.
- Valid `Page` instances remain valid as `page`.
- Existing lazy `PageRevision.source` and `PageRevision.html` acquisition still use the owning page and still report site/page/revision context if acquisition leaves the cache unset.
- Existing revision source extraction, rendered HTML parsing, duplicate cached revision reuse, collection behavior, parser-created revisions, and adjacent page workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageRevision.page` is the parent context behind lazy revision source/HTML reads, duplicate page revision list deduplication, cached duplicate revision reuse, revision snapshot ledgers, and publication audits. Constructor validation keeps malformed local parent-page state out of revision rows while preserving parser and caller paths that construct revisions from real `Page` objects.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used page-owned duplicate revision lists and verified each parsed `PageRevision.page` points at the owning duplicate page object.
- Existing local drafts covered revision acquisition, retry/fallback behavior, duplicate request deduplication, parse-once reuse, lazy failure context, response-body diagnostics, `Page.revisions` assignment validation, `PageRevisionCollection` initialization validation, collection entry validation, and direct revision source/html assignment validation, but did not cover direct `PageRevision(page=...)` construction.
- The focused RED failures showed invalid constructor page fields were accepted as dataclass state. The GREEN regression covers missing, boolean, string, dictionary, and arbitrary object page values.
- This slice only validates page revision parent-page constructor input. It does not change lazy revision acquisition, revision source parsing, HTML separator trimming, source/html setter validation, page collection behavior, create/edit, publish, live site behavior, or parser behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, source text from real sites, revision comments, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates only that `page` is a `Page` instance. It does not validate page IDs, page fullnames, site identity, cached source/html state, revision ID shape, author shape, timestamp shape, or live client authentication at `PageRevision` construction time; those are separate page object, parser, revision-field, and workflow concerns.
