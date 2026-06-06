# PR Draft: Validate Page Collection Initialization

## Summary

`PageCollection` documents `pages` as `list[Page] | None`, but its constructor accepted any truthy iterable or list entries that were not `Page` objects. A caller could construct `PageCollection(site, "test-page")`, `PageCollection(site, ("test-page",))`, or `PageCollection(site, [None])`; the malformed collection then failed later in `find(...)`, acquisition helpers, iterators, or tests with unstable attribute errors.

This change validates constructor input before storing entries. Non-list `pages` now raises `ValueError("pages must be a list")`; list entries that are not `Page` now raise `ValueError("pages list entries must be Page")`. `pages=None`, empty collections, valid `Page` lists, site inference from a valid first page, loaded collection search, page search parsing, iterator use, page ID/source/revision/vote/file acquisition, and the existing acquisition-method internal entry guard remain unchanged.

## Outcome

Callers cannot silently create malformed `PageCollection` instances through the public constructor, while existing acquisition methods still defend against later list mutation before remote work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page search, source collection, direct page lookup, metadata hydration, translation review tooling, archival jobs, generated reports, local fixtures, or resumable ledgers that construct `PageCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify `PageCollection` construction and use as practical workflow surfaces. Existing drafts [002-pr-batch-source-page-id-lookups.md](002-pr-batch-source-page-id-lookups.md), [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md), [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [132-pr-reuse-cached-duplicate-page-ids.md](132-pr-reuse-cached-duplicate-page-ids.md), [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md), and [382-pr-validate-page-collection-find-fullname.md](382-pr-validate-page-collection-find-fullname.md) establish page collections as an active operational boundary.

Those prior slices are not duplicates. Issues002, 006, 062-066, and 127-132 covered source/detail batching, retries, deduplication, and cached duplicate reuse; Issues004, 018, 019, and 049 covered search/source iterator workflows; Issue368 validated collection entries inside acquisition methods before request work; Issue382 validated the caller-provided `find(fullname=...)` key. None of them validates the `PageCollection(site, pages=...)` constructor itself before malformed entries become stored list state.

## Related Issue

Builds directly on [002-pr-batch-source-page-id-lookups.md](002-pr-batch-source-page-id-lookups.md), [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md), and [382-pr-validate-page-collection-find-fullname.md](382-pr-validate-page-collection-find-fullname.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `PageCollection.__init__(..., pages=...)` with the existing page-list validator.
- Preserve `pages=None` as an empty collection.
- Reject non-list `pages` with `ValueError("pages must be a list")`.
- Reject non-`Page` list entries with `ValueError("pages list entries must be Page")`.
- Keep the existing acquisition-method validation so later list mutation cannot reach request construction.
- Update iterator tests that were using `MagicMock` page stand-ins to use real `Page` fixtures.

## Type Of Change

- Input validation
- Public constructor behavior hardening
- Page collection state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageCollection(site, "test-page")` and `PageCollection(site, ("test-page",))` must raise `ValueError("pages must be a list")` before storing collection entries. |
| R2 | `PageCollection(site, [None])`, `PageCollection(site, [True])`, and `PageCollection(site, ["test-page"])` must raise `ValueError("pages list entries must be Page")` before storing collection entries. |
| R3 | `PageCollection(site, None)`, `PageCollection(site, [])`, and `PageCollection(site, [valid_page])` must remain valid. |
| R4 | Existing acquisition methods must still reject malformed entries introduced after construction before request, AMC, parser, or cache work. |
| R5 | Page search parsing, `Site.pages.iter_search(...)`, loaded collection `find(...)`, page ID/source/revision/vote/file acquisition, duplicate cache reuse, and adjacent page/site workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, page collection/search/acquisition tests, adjacent page/site tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list constructor input fails at the public constructor boundary. | `TestPageCollectionInit.test_init_rejects_non_list_pages` failed RED for `"test-page"` and `("test-page",)` because the constructor did not raise, then passed GREEN after constructor validation was added. | Treating a string as character entries, accepting tuples, storing malformed values, or deferring failure to iteration rejects this local completion claim. | PageCollection constructor | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Non-`Page` constructor list entries fail at the public constructor boundary. | `TestPageCollectionInit.test_init_rejects_non_page_entries` failed RED for `None`, `True`, and `"test-page"` because the constructor did not raise, then passed GREEN after constructor validation was added. | Accepting missing values, booleans, strings, serialized page names, or fixture stand-ins as stored pages rejects this local completion claim. | PageCollection constructor | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Valid constructor inputs remain green. | Existing `TestPageCollectionInit` tests for site plus empty pages and site plus valid pages passed in the 116-test page collection/search/acquisition run. | Rejecting `pages=None`, empty valid lists, valid page lists, or normal site assignment rejects this local completion claim. | PageCollection constructor | `tests/unit/test_page.py` |
| R4 | Acquisition methods still reject malformed entries introduced after construction. | `TestPageCollectionAcquire.test_acquire_rejects_non_page_entries_before_fetch` now creates a valid collection, appends malformed values, and still passes 15 cases without calling request surfaces. | Removing acquisition-method validation, allowing later mutation to reach ID/source/revision/vote/file request planning, or calling `RequestUtil`/AMC rejects this local completion claim. | PageCollection acquisition methods | `tests/unit/test_page.py` |
| R5 | Existing page collection and site workflows remain green. | Page collection init/parse/search/acquisition tests passed 116 tests, page/page-file/page-revision/page-votes/site tests passed 516 tests, and full unit tests passed 1494 tests. | Regressing ListPages parsing, bounded search iteration, required-tag filtering, source iteration, page ID/source/revision/vote/file acquisition, duplicate cache reuse, page writes, publish helpers, or site accessors rejects this local completion claim. | Page and site workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent page/site tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `140dbd9 fix(page): validate page collection initialization`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionInit::test_init_rejects_non_list_pages tests/unit/test_page.py::TestPageCollectionInit::test_init_rejects_non_page_entries -q` failed 5 tests before the fix with `Failed: DID NOT RAISE <class 'ValueError'>`; malformed constructor inputs were accepted and stored.
- GREEN: the same focused command passed 5 tests after adding constructor validation.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionInit tests/unit/test_page.py::TestPageCollectionParse tests/unit/test_page.py::TestPageCollectionSearchPages tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 116 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 516 tests.
- `uv run --extra test pytest tests/unit -q` passed 1494 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py tests/unit/test_site.py` left 3 files unchanged.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `PageCollection(site, "test-page")` and `PageCollection(site, ("test-page",))` raise `ValueError("pages must be a list")`.
- `PageCollection(site, [None])`, `PageCollection(site, [True])`, and `PageCollection(site, ["test-page"])` raise `ValueError("pages list entries must be Page")`.
- `PageCollection(site, None)`, `PageCollection(site, [])`, and `PageCollection(site, [valid_page])` continue to work.
- A valid collection that is later mutated with a malformed entry still causes `get_page_ids()`, `get_page_sources()`, `get_page_revisions()`, `get_page_votes()`, and `get_page_files()` to raise `ValueError("pages list entries must be Page")` before request work.
- Existing `PageCollection.find(...)`, `PageCollection.search_pages(...)`, `Site.pages.iter_search(...)`, `Site.pages.iter_sources(...)`, page ID/source/revision/vote/file acquisition, duplicate cache reuse, page write helpers, and site/page workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageCollection` is the shared object shape behind page search results, source collection, page ID hydration, revision/vote/file acquisition, duplicate cache reuse, and iterator workflows. Generated workflows and tests can accidentally pass page names, serialized records, booleans, missing values, or mock stand-ins into the constructor. Constructor validation keeps malformed local state out of the collection while preserving the existing method-level guard against later mutation.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used `PageCollection(site, pages).get_page_sources()` as a practical batch-first source path and repeatedly exercised search/source iterators plus page detail acquisition.
- Existing local drafts covered collection acquisition entries, loaded collection search keys, search pagination controls, page ID/source/revision/vote/file batching, duplicate cache reuse, and parser/response diagnostics, but did not cover `PageCollection.__init__(..., pages=...)`.
- The focused RED failures showed malformed constructor inputs were accepted. The GREEN regressions cover non-list input, malformed list entries, valid constructor input preservation, and the existing acquisition guard after explicit post-construction mutation.
- This slice only validates constructor input and updates test fixtures to use real `Page` objects. It does not change ListPages parsing, search request planning, source/revision/vote/file acquisition, duplicate cache reuse, page write behavior, live Wikidot behavior, or site authentication.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, page source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects duck-typed page-like objects and test mocks in `PageCollection`. Callers should construct real `Page` instances before storing them in a `PageCollection`; test suites that only need iteration should either use real lightweight `Page` fixtures or avoid the concrete collection type.
