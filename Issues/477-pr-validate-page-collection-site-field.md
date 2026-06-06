# PR Draft: Validate Page Collection Site Field

## Summary

`PageCollection` stores the optional explicit parent `Site` used by browser-free page search, source collection, page ID hydration, revision/vote/file acquisition, duplicate cache reuse, iterator workflows, generated reports, local fixtures, and rehydrated page state. Earlier local slices validated page-list fetching, response bodies, parser diagnostics, collection `pages` containers and entries, loaded collection lookup keys, page ID/source/revision/vote/file acquisition, and adjacent optional collection parents, but `PageCollection(site=..., pages=...)` still accepted malformed explicit parent sites such as booleans, strings, dictionaries, and arbitrary objects.

This change validates non-`None` `PageCollection.site` constructor arguments before storing collection state. Malformed explicit values now raise `ValueError("site must be a Site")`. The existing `site=None` inference behavior remains valid when a collection is built from a valid first page. Valid `Site` parents, empty explicit-site page collections, valid `Page` lists, iteration, lookup, page search parsing, source/revision/vote/file acquisition, duplicate cache reuse, lazy page properties, and adjacent page/site workflows remain unchanged.

## Outcome

Callers cannot silently construct page collections with malformed explicit parent-site state, while parser-created, fixture-created, inferred-parent, cached, and manually created valid page collections continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page search, large-corpus source collection, source-result ledgers, translation review tooling, archival jobs, page metadata hydration, page detail acquisition, generated reports, or local tests that construct `PageCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page collections as practical workflow surfaces and as the entry point for downstream page ID, source, revision, vote, file, iterator, and publish-adjacent workflows. Existing drafts [002-pr-batch-source-page-id-lookups.md](002-pr-batch-source-page-id-lookups.md), [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [132-pr-reuse-cached-duplicate-page-ids.md](132-pr-reuse-cached-duplicate-page-ids.md), [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md), [382-pr-validate-page-collection-find-fullname.md](382-pr-validate-page-collection-find-fullname.md), [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [470-pr-validate-page-vote-collection-page-field.md](470-pr-validate-page-vote-collection-page-field.md), [471-pr-validate-page-file-collection-page-field.md](471-pr-validate-page-file-collection-page-field.md), and [472-pr-validate-page-revision-collection-page-field.md](472-pr-validate-page-revision-collection-page-field.md) establish page collections as an active operational boundary.

Those prior slices are not duplicates. Issue 417 validates only the collection's `pages` container and entries while preserving valid site-supplied construction. Issue 368 validates collection entries inside acquisition methods before request work. Issue 382 validates the `find(fullname=...)` lookup key. Issues 470-472 validate page-owned vote/file/revision collection parents, not the `PageCollection.site` parent. Issues 002, 006, 062-066, and 127-132 cover batching, retry, deduplication, and cached duplicate reuse, not explicit parent-site construction. None validates direct non-`None` `PageCollection(site=...)` construction before malformed parent-site state becomes stored collection state in manually constructed collections, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [002-pr-batch-source-page-id-lookups.md](002-pr-batch-source-page-id-lookups.md), [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md), [382-pr-validate-page-collection-find-fullname.md](382-pr-validate-page-collection-find-fullname.md), [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), and the adjacent optional collection parent validation pattern from [470-pr-validate-page-vote-collection-page-field.md](470-pr-validate-page-vote-collection-page-field.md), [471-pr-validate-page-file-collection-page-field.md](471-pr-validate-page-file-collection-page-field.md), [472-pr-validate-page-revision-collection-page-field.md](472-pr-validate-page-revision-collection-page-field.md), [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md), and [476-pr-validate-forum-category-collection-site-field.md](476-pr-validate-forum-category-collection-site-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate non-`None` `PageCollection.site` values at constructor initialization.
- Reject malformed explicit parent-site values with `ValueError("site must be a Site")`.
- Preserve `site=None` inference from a valid first page, valid empty page collections with an explicit valid site, valid `Page` lists, iteration, `find(...)`, page search parsing, source/revision/vote/file acquisition, duplicate cache reuse, lazy page properties, and adjacent page/site workflows.

## Type Of Change

- Input validation
- Public collection constructor behavior hardening
- Page collection parent-site state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageCollection(site=True)`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` must raise `ValueError("site must be a Site")` when `pages` is otherwise valid. |
| R2 | `PageCollection(pages=[valid_page])` must still infer the site from the first page, and `PageCollection(site=<valid Site>, pages=[])` must remain constructible. |
| R3 | Valid `Site` parent values, valid empty page lists, valid `Page` lists, iteration, `find(...)`, page search parsing, source/revision/vote/file acquisition, duplicate cache reuse, lazy page properties, page write helpers, and adjacent page/site workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, constructor tests, page tests, adjacent page/site workflow tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed explicit collection parent sites fail at the public constructor boundary. | `TestPageCollectionInit.test_init_rejects_malformed_sites` failed RED for 4 malformed non-`None` values because the constructor did not raise, then passed GREEN after site validation was added. | Accepting booleans, strings, dictionaries, arbitrary objects, or emitting page collections with malformed explicit parent-site state rejects this local completion claim. | PageCollection constructor | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Optional inference and valid empty explicit-site collection semantics stay green. | `TestPageCollectionInit.test_init_infers_site_from_first_page` and existing empty initialization tests passed in the 18-test constructor run and 255-test page module run. | Losing parent-site inference from the first valid page, rejecting empty valid collections with explicit valid sites, or changing stored site identity rejects this local completion claim. | PageCollection constructor | `tests/unit/test_page.py` |
| R3 | Existing adjacent page and site workflows remain green. | `tests/unit/test_page.py` passed 255 tests, adjacent page/page-file/page-revision/page-votes/site tests passed 724 tests, and full unit tests passed 1924 tests. | Regressing ListPages parsing, search pagination, source iteration, page ID/source/revision/vote/file acquisition, duplicate cache reuse, lazy page properties, page write helpers, site page accessors, or adjacent page object workflows rejects this local completion claim. | Page and site workflows | `tests/unit/test_page.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d9ef61d fix(page): validate page collection site`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionInit::test_init_rejects_malformed_sites -q` failed 4 tests before the fix; every malformed explicit `site` input reported `DID NOT RAISE`.
- GREEN: the same focused command passed 4 tests after `PageCollection` explicit site validation was added.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionInit -q` passed 18 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 255 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 724 tests.
- `uv run pytest tests/unit -q` passed 1924 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page.py` passed.
- `uv run mypy src/wikidot/module/page.py tests/unit/test_page.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_page.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test page fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client mock typing, invalid test cookie arguments, and site test mock typing issues. The changed source file and changed page test file pass pyright together.

## Acceptance Criteria

- `PageCollection(site=True)`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` raise `ValueError("site must be a Site")`.
- `PageCollection(pages=[valid_page])` still infers the site from the first valid page.
- `PageCollection(site=<valid Site>, pages=[])` and `PageCollection(site=<valid Site>, pages=[valid_page])` remain valid.
- Existing valid `Page` lists, iteration, `find(...)`, page search parsing, source/revision/vote/file acquisition, duplicate cache reuse, lazy page properties, page write helpers, and adjacent page/site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageCollection.site` is the collection-level parent used by browser-free page search, source acquisition, page ID hydration, revision/vote/file acquisition, duplicate cache reuse, iterator workflows, and generated source or publication-adjacent ledgers. Parser paths already create collections with valid owning sites or infer the parent from valid pages; direct constructor validation keeps malformed explicit collection parents out of generated ledgers, archive comparisons, publication audits, and downstream tooling while preserving parser and caller paths that intentionally use site inference.

## Local Evidence

- Local rollout evidence used browser-free page searches, source collection, iterator workflows, page detail acquisition, generated ledgers, and tests that seed page collections directly.
- Existing local drafts covered ListPages fetch retry behavior, page search pagination, source iteration, duplicate page detail reuse, parser contexts, response diagnostics, collection pages/entry validation, collection lookup-key validation, and adjacent page-owned collection parent validation, but did not cover direct non-`None` `PageCollection(site=...)` construction.
- The focused RED failures showed invalid explicit constructor parent sites were accepted as collection state. The GREEN regression covers boolean, string, dictionary, and arbitrary object values while preserving inference from a valid first page.
- This slice only validates page collection explicit parent-site constructor input. It does not change ListPages parsing, search request planning, page ID/source/revision/vote/file acquisition, duplicate cache reuse, page write behavior, live Wikidot behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates type only for explicit non-`None` parent values. It does not compare collection parent identity with each contained page, coerce dictionaries into sites, change site inference from a valid first page, verify page/site membership, or change live client authentication; those are separate parser, collection-consistency, and workflow concerns.
