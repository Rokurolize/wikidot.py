# PR Draft: Validate Page Revision Collection Entries

## Summary

`PageRevisionCollection.get_sources()` and `PageRevisionCollection.get_htmls()` document collection entries as `PageRevision` objects, but malformed collection entries were not rejected at the public acquisition boundary. A malformed entry such as `None`, `True`, or `"100"` reached `is_source_acquired()` or `is_html_acquired()` and leaked an unstable `AttributeError` before request construction.

This change validates page-revision collection entries before acquired-cache checks, cached duplicate reuse, duplicate request grouping, retry-aware AMC request construction, response parsing, source or HTML cache assignment, or lazy revision property completion. Invalid entries now raise `ValueError("revisions list entries must be PageRevision")`. Empty valid collections, valid source reads, valid HTML reads, deduplication, parse-once duplicate response reuse, cached duplicate reuse, retry partial-success behavior, response-body diagnostics, source parser diagnostics, HTML separator handling, and lazy `PageRevision.source` / `PageRevision.html` behavior remain unchanged.

## Outcome

Page revision source and HTML callers now get deterministic Python-side preflight validation for malformed collection entries instead of accidental attribute failures from later cache or acquisition stages.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page revision source or HTML reads for translation review tooling, edit-history audits, archival jobs, local indexing, moderation support, generated workflows, or page-version comparison scripts.

## Current Evidence

Local rollout-backed drafts repeatedly treat page revision source and HTML acquisition as practical read surfaces. Existing drafts [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [164-pr-page-revision-source-parse-context.md](164-pr-page-revision-source-parse-context.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [201-pr-page-revision-lazy-site-context.md](201-pr-page-revision-lazy-site-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), and [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md) establish page revision source and HTML retrieval as active practical workflows.

Those prior slices are not duplicates. They covered retry behavior, request deduplication, parse-once duplicate response reuse, cached duplicate reuse, lazy failure visibility, site/page/revision failure context, missing response body diagnostics, malformed response body type diagnostics, and source parser diagnostics. They did not validate malformed `PageRevisionCollection` entries before public `get_sources()` / `get_htmls()` cache inspection, deduplication, request construction, or response parsing. This slice follows the recent input-boundary pattern from [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), and [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), but applies it to page revision collection entries.

## Related Issue

Builds directly on [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [164-pr-page-revision-source-parse-context.md](164-pr-page-revision-source-parse-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), and [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate every `PageRevisionCollection` entry is a `PageRevision` before source or HTML acquisition cache checks.
- Share the guard in `_generic_acquire(...)` so source and HTML acquisition fail at the same boundary.
- Preserve the existing `ValueError("Page is not set for this collection")` behavior for page-less collections.
- Preserve empty valid collection behavior, valid source and HTML reads, duplicate request deduplication, parse-once duplicate response reuse, cached duplicate reuse, retry partial-success behavior, response-body diagnostics, source parser diagnostics, HTML separator handling, and lazy `PageRevision.source` / `PageRevision.html` behavior.

## Type Of Change

- Input validation
- Public API behavior hardening
- Page revision read preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevisionCollection.get_sources()` must reject entries that are not `PageRevision` objects with `ValueError("revisions list entries must be PageRevision")` before cache or request work. |
| R2 | `PageRevisionCollection.get_htmls()` must reject entries that are not `PageRevision` objects with `ValueError("revisions list entries must be PageRevision")` before cache or request work. |
| R3 | Valid empty collections and valid source or HTML reads must remain unchanged. |
| R4 | Existing retry behavior, duplicate request handling, parse-once duplicate response reuse, cached duplicate reuse, response body diagnostics, source parser diagnostics, HTML separator handling, lazy source, and lazy HTML behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, affected page-revision tests, adjacent page tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Source acquisition collection entries without `PageRevision` objects fail before cache or request work. | `TestPageRevisionCollection.test_get_sources_rejects_non_revision_entries_before_fetch` failed RED for `None`, `True`, and `"100"` by leaking `AttributeError` through `is_source_acquired()`, then passed GREEN after shared validation was added. | Accepting missing values, booleans, or strings as revisions, inspecting invalid entry caches, grouping invalid revision IDs, calling AMC, or surfacing `AttributeError` rejects this local completion claim. | Page revision source preflight | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | HTML acquisition collection entries without `PageRevision` objects fail before cache or request work. | `TestPageRevisionCollection.test_get_htmls_rejects_non_revision_entries_before_fetch` failed RED for `None`, `True`, and `"100"` by leaking `AttributeError` through `is_html_acquired()`, then passed GREEN after shared validation was added. | Accepting missing values, booleans, or strings as revisions, inspecting invalid entry caches, grouping invalid revision IDs, calling AMC, or surfacing `AttributeError` rejects this local completion claim. | Page revision HTML preflight | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R3 | Valid empty collections and valid source or HTML reads remain unchanged. | `tests/unit/test_page_revision.py` passed 45 tests, the adjacent page/page-file/page-votes/page-revision set passed 275 tests, and the full unit suite passed 1017 tests. | Regressing `PageRevisionCollection(page=page, revisions=[])`, valid source acquisition, valid HTML acquisition, page-required errors, or source/HTML cache assignment rejects this local completion claim. | Page revision workflow | `tests/unit/test_page_revision.py`, adjacent page tests |
| R4 | Existing page revision acquisition behavior remains unchanged. | The adjacent 275-test page set and full 1017-test unit suite covered retry partial-success behavior, duplicate request handling, parse-once duplicate response reuse, cached duplicate reuse, response body diagnostics, source parser diagnostics, HTML separator handling, lazy source, and lazy HTML behavior. | Regressing retry behavior, duplicate request handling, parse-once reuse, cached duplicate reuse, missing body diagnostics, malformed body diagnostics, source parser context, HTML separator handling, lazy source failures, or lazy HTML failures rejects this local completion claim. | Page revision workflow | `tests/unit/test_page_revision.py`, `tests/unit/test_page.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic page and revision objects plus malformed local values. | Using credentials, cookies, auth JSON, live Wikidot actions, raw rollout paths, sandbox details, upstream Issues, upstream PRs, page source text from real sites, revision HTML, revision comments, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `98c7dfc fix(page_revision): validate collection entries`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_rejects_non_revision_entries_before_fetch tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_rejects_non_revision_entries_before_fetch` failed before the fix with 6 failures; malformed collection entries leaked `AttributeError` through `is_source_acquired()` or `is_html_acquired()`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_rejects_non_revision_entries_before_fetch tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_rejects_non_revision_entries_before_fetch` passed 6 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_page_revision.py` passed 45 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_page_revision.py tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_votes.py` passed 275 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1017 tests.
- `.venv/bin/ruff check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed.
- `.venv/bin/ruff format --check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with 2 files already formatted.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `PageRevisionCollection(page=page, revisions=[valid_revision, None]).get_sources()`, `[valid_revision, True]`, and `[valid_revision, "100"]` raise `ValueError("revisions list entries must be PageRevision")` before cache inspection or AMC work.
- `PageRevisionCollection(page=page, revisions=[valid_revision, None]).get_htmls()`, `[valid_revision, True]`, and `[valid_revision, "100"]` raise `ValueError("revisions list entries must be PageRevision")` before cache inspection or AMC work.
- `PageRevisionCollection(page=page, revisions=[])` remains a valid empty collection.
- `PageRevisionCollection()` still raises `ValueError("Page is not set for this collection")` from source or HTML acquisition.
- Valid source acquisition still submits `history/PageSourceModule` request bodies with integer revision IDs.
- Valid HTML acquisition still submits `history/PageVersionModule` request bodies with integer revision IDs.
- Existing retry partial-success behavior, duplicate request handling, parse-once duplicate response reuse, cached duplicate reuse, response-body diagnostics, source parser diagnostics, HTML separator handling, lazy source behavior, and lazy HTML behavior remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Page revision source and HTML acquisition depends on real `PageRevision` objects because the implementation reads revision cache state, revision IDs, and target page context before it builds source or HTML module requests. Generated workflows can accidentally pass revision IDs, serialized records, booleans, or missing values into this surface. Those malformed values should fail deterministically at the public API boundary, especially because the valid path contains cache reuse, deduplication, retry-aware request construction, response parsing, and cache assignment. The change is narrow: it rejects malformed values instead of coercing them and leaves valid read behavior unchanged.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established page revision source and HTML retrieval as practical workflows.
- The focused RED failures showed malformed public collection entries crossing into source or HTML cache checks and leaking unstable attribute failures instead of failing at the public call boundary.
- Existing page-revision drafts covered retry behavior, duplicate request handling, parse-once duplicate response reuse, cached duplicate reuse, lazy failure context, source parser context, response body context, and malformed response body type context, but not malformed public collection entry preflight.
- This slice only validates page revision collection entries. It does not change page revision-list parsing, page source fetching, page editing, publishing, source text extraction, HTML separator behavior, retry semantics, response-body diagnostics, site authentication, live Wikidot behavior, or page revision dataclass fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw action responses, page source text from real sites, revision comments, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects IDs, strings, booleans, and missing values instead of treating them as revision objects. Callers that receive revision IDs from text sources should resolve them to `PageRevision` instances before requesting revision source or HTML.
