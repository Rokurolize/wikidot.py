# PR Draft: Validate PageCollection Constructor Site Ownership

## Summary

`PageCollection` already validates explicit `site` type, `pages` container shape, page entry types, empty parentless state, retained batch parent state, acquisition-time page/site ownership, retained page IDs, and downstream page detail acquisition. One constructor-state gap remained: direct `PageCollection(site=site_a, pages=[page_from_site_b])` accepted a valid page from another site, and `PageCollection(pages=[page_from_site_a, page_from_site_b])` inferred `site_a` while still storing the second site's page.

This change validates page-entry site ownership during `PageCollection(...)` construction after page entry validation and effective parent-site selection, but before list state is stored. Pages whose retained `page.site` is not the collection site now raise `ValueError("pages must belong to the collection site")`. Valid same-site collections, empty collections, inferred same-site collections, `find(...)`, ListPages parsing, page ID/source/revision/vote/file acquisition, duplicate cache reuse, lazy page properties, post-construction mutation guards, and adjacent page/source/revision/file/vote/site workflows remain compatible.

## Outcome

Generated, fixture-built, or rehydrated page collections can no longer store pages from one site under another site's collection parent. Corrupted ownership fails at construction instead of waiting until page-ID or detail acquisition.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page search, large-corpus source collection, page ID hydration, source/revision/vote/file detail reads, duplicate cached page reuse, publication verification, migration or audit ledgers, local fixtures, serialized page rows, and direct `PageCollection` construction.

## Current Evidence

Local rollout-backed drafts establish `PageCollection` as a practical workflow surface. [002-pr-batch-source-page-id-lookups.md](002-pr-batch-source-page-id-lookups.md), [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [132-pr-reuse-cached-duplicate-page-ids.md](132-pr-reuse-cached-duplicate-page-ids.md), [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md), [382-pr-validate-page-collection-find-fullname.md](382-pr-validate-page-collection-find-fullname.md), [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md), [540-pr-preserve-empty-page-collection-parent.md](540-pr-preserve-empty-page-collection-parent.md), [572-pr-validate-page-collection-batch-site.md](572-pr-validate-page-collection-batch-site.md), and [664-pr-validate-page-collection-retained-page-id-state.md](664-pr-validate-page-collection-retained-page-id-state.md) cover page search, source/detail batching, iterator workflows, collection entry validation, collection lookup keys, constructor shape validation, explicit site type validation, empty parentless state, batch-time retained parent validation, and retained page-ID preflights.

This slice is not a duplicate of those drafts. Issue 572 validates mismatched page ownership in `_get_site_for_batch()` so post-construction mutations still fail before request work; it does not reject mismatched pages at direct `PageCollection(...)` construction. Issue 477 validates the explicit `site` type. Issue 417 validates that `pages` is a list of `Page` entries. Issue 540 preserves empty parentless state. Issue 664 validates retained page IDs during `get_page_ids()`. This slice brings `PageCollection` constructor ownership to the same direct-state standard already used by page vote, page file, page revision, forum thread, forum category, forum post, and forum post revision collections.

No upstream issue was filed from this local workspace.

## Changes

- Validate `PageCollection` page ownership during construction for explicit parent sites.
- Validate inferred-parent collections so all pages must belong to the first page's site.
- Validate the inferred parent site before storing it as collection state.
- Preserve acquisition-time ownership preflights for post-construction list mutation.
- Preserve valid empty collections, explicit same-site collections, inferred same-site collections, page search parsing, and page detail acquisition behavior.

## Type Of Change

- Constructor validation
- Page collection state hardening
- Cache and batch ownership integrity
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageCollection(site=site_a, pages=[page_from_site_b])` must reject the different-site page with `ValueError("pages must belong to the collection site")` before storing collection list state. |
| R2 | `PageCollection(pages=[page_from_site_a, page_from_site_b])` must infer `site_a` from the first page and reject the mixed-site second page with the same diagnostic. |
| R3 | Post-construction collection mutations must still be caught by page ID/source/revision/vote/file acquisition before request work. |
| R4 | Valid empty collections, explicit same-site collections, inferred same-site collections, `find(...)`, ListPages parsing, search pagination, page ID/source/revision/vote/file acquisition, duplicate cache reuse, lazy page properties, and adjacent page/source/revision/file/vote/site workflows must remain compatible. |
| R5 | Focused RED/GREEN, PageCollection constructor coverage, page collection parse/search/acquisition coverage, full page module coverage, adjacent page/detail/site tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Explicit different-site page entries fail at the constructor boundary. | `test_init_rejects_page_from_different_site` failed RED with `DID NOT RAISE`, then passed GREEN after constructor ownership validation. | Accepting the mismatched page, storing it in list state, or deferring failure to page-ID acquisition rejects this local completion claim. | `PageCollection.__init__` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Inferred-parent mixed-site entries fail before list state is stored. | `test_init_rejects_mixed_page_sites_when_site_is_inferred` failed RED with `DID NOT RAISE`, then passed after the inferred-parent ownership preflight was added. | Inferring the first page site while retaining another site's page rejects this local completion claim. | `PageCollection.__init__` | `tests/unit/test_page.py` |
| R3 | Acquisition guards still catch mutated collections. | `test_get_page_ids_rejects_page_from_different_site_before_fetch` now appends a mismatched page after valid construction and still passes without `RequestUtil.request` calls. | Removing the acquisition preflight, calling request helpers, or mutating page IDs for a mismatched page rejects this local completion claim. | Page collection acquisition | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Existing page collection behavior remains green. | `TestPageCollectionInit` passed 25 tests, page collection init/parse/search/acquire coverage passed 150 tests, `tests/unit/test_page.py` passed 377 tests, adjacent page/page_constructor/page_source/page_revision/page_file/page_votes/site coverage passed 1295 tests, and full unit coverage passed 3543 tests. | Regressing same-site collections, inferred same-site collections, empty collections, ListPages parsing, search pagination, source iteration, page ID/source/revision/vote/file acquisition, duplicate cache reuse, lazy page properties, page writes, or site accessors rejects this local completion claim. | Page collection and adjacent workflows | `tests/unit` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit, ruff check, ruff format check, mypy, pyright, and `git diff --check` passed after the code change. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No private material or live action is needed to prove the behavior. | All regressions use synthetic `Site` and `Page` objects and local unit tests; the draft contains no credentials, cookies, auth JSON, raw response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `f135260 fix(page): validate collection site ownership`.

- RED explicit constructor ownership: `uv run pytest tests/unit/test_page.py::TestPageCollectionInit::test_init_rejects_page_from_different_site -q` failed before the fix with `DID NOT RAISE`.
- GREEN explicit constructor ownership: the same focused command passed after explicit parent-site ownership validation was added.
- RED inferred constructor ownership: `uv run pytest tests/unit/test_page.py::TestPageCollectionInit::test_init_rejects_mixed_page_sites_when_site_is_inferred -q` failed before the inferred branch fix with `DID NOT RAISE`.
- GREEN focused ownership coverage: `uv run pytest tests/unit/test_page.py::TestPageCollectionInit::test_init_rejects_page_from_different_site tests/unit/test_page.py::TestPageCollectionInit::test_init_rejects_mixed_page_sites_when_site_is_inferred -q` passed 2 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionInit -q` passed 25 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionInit tests/unit/test_page.py::TestPageCollectionParse tests/unit/test_page.py::TestPageCollectionSearchPages tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 150 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 377 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1295 tests.
- `uv run pytest tests/unit -q` passed 3543 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left 2 files unchanged.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageCollection(site=site_a, pages=[page_from_site_b])` raises `ValueError("pages must belong to the collection site")`.
- `PageCollection(pages=[page_from_site_a, page_from_site_b])` raises the same diagnostic after inferring `site_a` from the first page.
- Valid empty collections, explicit same-site collections, and inferred same-site collections continue to work.
- Page ID acquisition still rejects a mismatched page appended after construction before request work.
- Existing `find(...)`, ListPages parsing, search pagination, source iteration, page ID/source/revision/vote/file acquisition, duplicate cache reuse, lazy page properties, page writes, and site accessors remain green.
- The new tests use synthetic objects only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Existing callers may have constructed page collections with inconsistent parent state and only used them as lists. Mitigation: this state conflicts with existing batch-time ownership, parser-created search results, and adjacent collection constructor ownership contracts; failing at construction is deterministic and easier to debug.
- Risk: Post-construction mutation could bypass constructor validation. Mitigation: the existing acquisition-time ownership preflight remains active and the test now explicitly covers mutation by appending a mismatched page after construction.
- Risk: Comparing sites by identity may reject logically equal rehydrated site objects. Mitigation: this matches existing collection ownership semantics in this codebase, where collection entries belong to the exact retained parent object used for request/cache operations.

## Out Of Scope

Changing ListPages parsing, comparing site ownership by `unix_name` or ID instead of object identity, changing page source/revision/vote/file response parsing, changing retained page-ID semantics, changing `Page` constructor validation, changing live Wikidot behavior, pushing changes, opening upstream Issues, and opening upstream PRs are outside this slice.

## Why This Matters

`PageCollection` is the shared object behind page search, source collection, page ID hydration, revision/vote/file acquisition, duplicate cached page reuse, source iteration, publication verification, and migration ledgers. A collection parent and its entries should describe the same site before request/cache state is planned. Constructor validation prevents local fixtures, generated ledgers, or rehydrated records from silently carrying another site's page under the wrong site.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used browser-free page searches, page source collection, source iteration, publish verification, duplicate cached page reuse, and page-level audit evidence.
- Existing local drafts covered collection entry shape, explicit collection parent type, empty parentless collections, batch-time retained parent validation, acquisition-time page/site ownership, retained page IDs, ListPages parsing, batching, retries, and duplicate cache reuse; they did not reject mismatched page entries at direct `PageCollection(...)` construction.
- The focused RED failures showed explicit and inferred mismatched construction stored a page from another site. The GREEN regressions cover explicit and inferred constructor rejection, post-construction mutation guards, page collection compatibility, adjacent workflows, full unit compatibility, lint, format, type, pyright, and whitespace gates.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
