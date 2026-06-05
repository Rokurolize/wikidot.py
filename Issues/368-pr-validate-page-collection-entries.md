# PR Draft: Validate Page Collection Entries

## Summary

`PageCollection` acquisition methods document collection entries as `Page` objects, but malformed entries were not rejected before cache inspection or request planning. A malformed entry such as `None`, `True`, or `"test-page"` reached `_id`, `_source`, `_revisions`, `_votes`, or `_files` access and leaked unstable `AttributeError` failures before page-ID lookup, AMC request construction, or parser work.

This change validates page collection entries before page-ID cache checks, source cache checks, revision/vote/file cache checks, cached duplicate reuse, duplicate request grouping, retry-aware AMC request construction, direct page-ID GET construction, response-body validation, parser work, or lazy page property completion. Invalid entries now raise `ValueError("pages list entries must be Page")`. Empty valid collections, valid page-ID reads, valid source reads, revision-list reads, vote-list reads, file-list reads, retry behavior, duplicate request deduplication, cached duplicate reuse, response diagnostics, parser diagnostics, lazy `Page` properties, and page mutation helpers remain unchanged.

## Outcome

Page collection callers now get deterministic Python-side preflight validation for malformed collection entries instead of accidental attribute failures from later cache or acquisition stages.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page collection reads for source collection, translation review tooling, edit-history audits, page vote audits, attached-file inventories, publishing verification, local indexing, generated workflows, or archival jobs.

## Current Evidence

Local rollout-backed drafts repeatedly treat `PageCollection` acquisition as a practical read surface. Existing drafts [002-pr-batch-source-page-id-lookups.md](002-pr-batch-source-page-id-lookups.md), [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md), [008-pr-skip-cached-source-fetches.md](008-pr-skip-cached-source-fetches.md), [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md), [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), and [132-pr-reuse-cached-duplicate-page-ids.md](132-pr-reuse-cached-duplicate-page-ids.md) establish page collection ID/source/revision/vote/file acquisition as active practical workflows.

Those prior slices are not duplicates. They covered batching, retry behavior, cached-skip behavior, request deduplication, cached duplicate reuse, parser scoping, parser diagnostics, response-body diagnostics, response-body type diagnostics, and lazy property failure context. Recent collection-entry slices [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), and [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md) validated adjacent source/HTML collection objects, but they did not validate malformed `PageCollection` entries before public page ID/source/revision/vote/file acquisition.

## Related Issue

Builds directly on [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [132-pr-reuse-cached-duplicate-page-ids.md](132-pr-reuse-cached-duplicate-page-ids.md), and the response-body type series [331-pr-page-source-response-body-type-context.md](331-pr-page-source-response-body-type-context.md), [332-pr-page-revision-list-response-body-type-context.md](332-pr-page-revision-list-response-body-type-context.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), and [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate every `PageCollection.get_page_ids()`, `get_page_sources()`, `get_page_revisions()`, `get_page_votes()`, and `get_page_files()` entry is a `Page` before cache checks or request construction.
- Preserve empty valid collection behavior, valid page-ID reads, valid source reads, revision-list reads, vote-list reads, file-list reads, retry behavior, duplicate request deduplication, cached duplicate reuse, response diagnostics, parser diagnostics, lazy `Page` properties, and page mutation helpers.

## Type Of Change

- Input validation
- Public API behavior hardening
- Page collection read preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageCollection.get_page_ids()` must reject entries that are not `Page` objects with `ValueError("pages list entries must be Page")` before direct page-ID lookup work. |
| R2 | `PageCollection.get_page_sources()`, `get_page_revisions()`, `get_page_votes()`, and `get_page_files()` must reject entries that are not `Page` objects with `ValueError("pages list entries must be Page")` before cache, page-ID, request, or parser work. |
| R3 | Valid empty collections and valid ID/source/revision/vote/file reads must remain unchanged. |
| R4 | Existing retry behavior, duplicate request handling, cached duplicate reuse, response diagnostics, parser diagnostics, lazy page properties, and page mutation helpers must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, affected page tests, adjacent page tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Page-ID collection entries without `Page` objects fail before direct page-ID lookup work. | `TestPageCollectionAcquire.test_acquire_rejects_non_page_entries_before_fetch` failed RED for `None`, `True`, and `"test-page"` on `get_page_ids()` by leaking `AttributeError` through `_id`, then passed GREEN after validation was added. | Accepting missing values, booleans, or strings as pages, inspecting invalid entry ID caches, building direct page-ID URLs, calling `RequestUtil.request`, or surfacing `AttributeError` rejects this local completion claim. | Page ID preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Source/revision/vote/file collection entries without `Page` objects fail before cache, ID, request, or parser work. | The same focused regression failed RED for the four detail methods by leaking `AttributeError` through `_source`, `_revisions`, `_votes`, or `_files`, then passed GREEN after validation was added. | Accepting missing values, booleans, or strings as pages, inspecting invalid entry detail caches, resolving invalid page IDs, calling AMC, parsing responses, or surfacing `AttributeError` rejects this local completion claim. | Page detail preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Valid empty collections and valid ID/source/revision/vote/file reads remain unchanged. | `tests/unit/test_page.py` passed 200 tests, the adjacent page/page-file/page-revision/page-votes/site set passed 394 tests, and the full unit suite passed 1038 tests. | Regressing `PageCollection(site, [])`, valid page-ID lookup, valid source acquisition, valid revision-list acquisition, valid vote-list acquisition, valid file-list acquisition, or cache assignment rejects this local completion claim. | Page collection workflows | `tests/unit/test_page.py`, adjacent page tests |
| R4 | Existing page collection behavior remains unchanged. | The adjacent 394-test page set and full 1038-test unit suite covered retry behavior, duplicate request handling, cached duplicate reuse, response diagnostics, parser diagnostics, lazy page properties, page file direct reads, page revision source/HTML reads, vote collection behavior, site page accessors, iterators, and page mutation helpers. | Regressing retry behavior, duplicate request handling, cached duplicate reuse, response diagnostics, parser diagnostics, source/revision/vote/file ownership, lazy property failures, site accessors, iterators, publishing, edit, vote, metadata, rename, or delete behavior rejects this local completion claim. | Page workflow | `tests/unit/test_page.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic page objects plus malformed local values. | Using credentials, cookies, auth JSON, live Wikidot actions, raw rollout paths, sandbox details, upstream Issues, upstream PRs, page source text from real sites, revision comments, file names, voter names, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `9e1a0a3 fix(page): validate collection entries`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_rejects_non_page_entries_before_fetch` failed before the fix with 15 failures; malformed collection entries leaked `AttributeError` through `_id`, `_source`, `_revisions`, `_votes`, or `_files`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_rejects_non_page_entries_before_fetch` passed 15 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_page.py` passed 200 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py` passed 394 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1038 tests.
- `.venv/bin/ruff check src/wikidot/module/page.py tests/unit/test_page.py` passed.
- `.venv/bin/ruff format --check src/wikidot/module/page.py tests/unit/test_page.py` passed with 2 files already formatted.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `PageCollection(site=site, pages=[valid_page, None]).get_page_ids()`, `.get_page_sources()`, `.get_page_revisions()`, `.get_page_votes()`, and `.get_page_files()` raise `ValueError("pages list entries must be Page")` before direct page-ID GETs, AMC work, or parser work.
- The same five public methods reject `[valid_page, True]` and `[valid_page, "test-page"]` with the same stable error.
- `PageCollection(site=site, pages=[])` remains a valid empty collection for acquisition calls.
- Valid page-ID lookup, source acquisition, revision-list acquisition, vote-list acquisition, and file-list acquisition still use the existing request payloads and cache assignment semantics.
- Existing retry behavior, duplicate request handling, cached duplicate reuse, response diagnostics, parser diagnostics, lazy page properties, site accessors, iterators, and page mutation helpers remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Page collection acquisition depends on real `Page` objects because the implementation reads page IDs, cache fields, page URLs, fullnames, and site context before it builds direct page-ID requests or AMC detail requests. Generated workflows can accidentally pass page fullnames, serialized records, booleans, or missing values into these collection surfaces. Those malformed values should fail deterministically at the public API boundary, especially because the valid paths contain cache reuse, deduplication, retry-aware request construction, response parsing, and cache assignment. The change is narrow: it rejects malformed values instead of coercing them and leaves valid read behavior unchanged.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established page collection ID/source/revision/vote/file acquisition as practical workflows.
- The focused RED failures showed malformed public collection entries crossing into ID/source/revision/vote/file cache checks and leaking unstable attribute failures instead of failing at the public call boundary.
- Existing page collection drafts covered batching, retry behavior, cached-skip behavior, duplicate request handling, cached duplicate reuse, response diagnostics, parser diagnostics, lazy property context, source extraction, revision parsing, vote parsing, file parsing, and page-ID lookup behavior, but not malformed public collection entry preflight.
- This slice only validates page collection entries for acquisition calls. It does not change ListPages parsing, source parsing, revision parsing, vote parsing, file parsing, page editing, publishing, metadata writes, page deletion, retry semantics, response-body diagnostics, site authentication, live Wikidot behavior, or page dataclass fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw action responses, page source text, revision comments, file names, voter names, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects page fullnames, IDs, booleans, and missing values instead of treating them as page objects. Callers that receive page names or IDs from text sources should resolve them to `Page` instances before requesting collection details.
