# PR Draft: Preserve Empty Page Collection Parent State

## Summary

`PageCollection(site=None, pages=[])` and the default `PageCollection()` constructor still inferred the parent from `self[0]` after earlier constructor and explicit-site validation slices. Direct callers, fixture builders, generated page ledgers, source-collection setup, archival jobs, and rehydration paths could hit `IndexError: list index out of range` before receiving a usable empty collection.

This change makes the empty no-parent state explicit by storing `self.site = None`, typing the collection parent as `Site | None`, and keeping empty parentless batch accessors chainable. Valid explicit `Site` parents, first-page parent inference, empty site-supplied collections, page search parsing, ID/source/revision/vote/file acquisition, duplicate cache reuse, lazy page properties, page write helpers, and adjacent page/site workflows remain unchanged.

## Outcome

Empty no-parent page collections now expose the readable `site is None` sentinel instead of leaking a constructor-time `IndexError`.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page searches, large-corpus source collection, translation review tooling, archival jobs, generated source ledgers, local fixtures, or tests that construct `PageCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify `PageCollection` as a practical workflow surface for search results, source collection, page ID hydration, revision/vote/file acquisition, duplicate cache reuse, iterator workflows, generated reports, and local fixtures. Existing drafts [002-pr-batch-source-page-id-lookups.md](002-pr-batch-source-page-id-lookups.md), [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [132-pr-reuse-cached-duplicate-page-ids.md](132-pr-reuse-cached-duplicate-page-ids.md), [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md), [382-pr-validate-page-collection-find-fullname.md](382-pr-validate-page-collection-find-fullname.md), [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md), [529-pr-validate-search-query-string-fields.md](529-pr-validate-search-query-string-fields.md), [533-pr-validate-page-fullname-inputs.md](533-pr-validate-page-fullname-inputs.md), and [534-pr-validate-search-pages-arguments.md](534-pr-validate-search-pages-arguments.md) establish page collections and ListPages workflows as active operational boundaries.

This is not a duplicate of Issue 417 or Issue 477. Issue 417 validates the `pages` container and entries while preserving valid empty collections. Issue 477 validates malformed non-`None` explicit `site` values and preserves `site=None` inference from a valid first page. Neither asserts that an empty no-parent collection can be constructed, exposes `site is None`, and keeps empty batch accessors as no-ops.

No upstream issue was filed from this local workspace.

## Changes

- Assign `self.site = None` when `PageCollection` is constructed with no site and no pages.
- Type the collection parent as `Site | None` to match supported constructor semantics.
- Add a small batch-site guard so empty parentless collections return `self` from `get_page_ids()`, `get_page_sources()`, `get_page_revisions()`, `get_page_votes()`, and `get_page_files()`.
- Preserve valid explicit parents, first-page parent inference, empty site-supplied collections, page search parsing, acquisition workflows, duplicate cache reuse, lazy page properties, and adjacent page/site workflows.

## Type Of Change

- Contract repair
- Public collection constructor state hardening
- Page collection parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageCollection(site=None, pages=[])` and `PageCollection()` must expose `site is None` and length 0 instead of raising `IndexError`. |
| R2 | Empty parentless `get_page_ids()`, `get_page_sources()`, `get_page_revisions()`, `get_page_votes()`, and `get_page_files()` must return `self` without request work. |
| R3 | `PageCollection(site=<valid Site>, pages=[])` and `PageCollection(site=<valid Site>, pages=[valid_page])` must remain valid. |
| R4 | `PageCollection(site=None, pages=[valid_page])` must still infer the parent from the first page. |
| R5 | Existing malformed explicit parent and malformed page-list validation from Issues 417 and 477 must continue to reject invalid input. |
| R6 | Page search parsing, ID/source/revision/vote/file acquisition, duplicate cache reuse, lazy page properties, page write helpers, site accessors, and adjacent page/site workflows must remain unchanged. |
| R7 | Page tests, adjacent page/site workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R8 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Empty no-parent construction leaves a readable `site is None` state. | `test_init_empty_without_site_exposes_none_site` failed RED before the fix with `IndexError: list index out of range`, then passed GREEN after the constructor assigned `None`. | Raising `IndexError`, rejecting omitted input, missing `site`, or changing the empty collection length rejects this local completion claim. | PageCollection constructor | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Empty parentless batch accessors remain chainable no-ops. | The focused GREEN constructor test asserted all five batch methods return the same empty collection. | Issuing requests, requiring a site, raising attribute errors, or returning a different object for empty parentless collections rejects this local completion claim. | PageCollection batch accessors | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Explicit valid parent paths remain stable. | The focused constructor GREEN command covered existing explicit-site empty and populated construction tests. | Losing the explicit parent, changing valid empty-list behavior, or changing valid page-list construction rejects this local completion claim. | PageCollection constructor | `tests/unit/test_page.py` |
| R4 | First-page parent inference remains available. | The focused constructor GREEN command covered `test_init_infers_site_from_first_page`. | Rejecting omitted parents with non-empty pages or failing to preserve inferred parent state rejects this local completion claim. | PageCollection constructor | `tests/unit/test_page.py` |
| R5 | Existing malformed explicit parent and page-list preflights remain intact. | The focused constructor GREEN command covered malformed explicit parent, non-list pages, and non-page entry cases. | Accepting booleans, strings, dictionaries, arbitrary objects, malformed page containers, or malformed page entries rejects this local completion claim. | Constructor validation | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R6 | Existing page and adjacent site workflows remain stable. | `tests/unit/test_page.py` passed 280 tests, adjacent page/site workflow tests passed 800 tests, and full unit tests passed 2558 tests. | Regressing ListPages parsing, search pagination, source iteration, page ID/source/revision/vote/file acquisition, duplicate cache reuse, lazy page properties, page write helpers, site accessors, or adjacent page object workflows rejects this local completion claim. | Page and site workflows | `tests/unit/test_page.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_source.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, page module passed, adjacent page/site workflows passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R8 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic state and local mocks; this draft contains no credentials, cookies, auth JSON, raw response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `873d826 fix(page): preserve empty collection parent`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionInit::test_init_empty_without_site_exposes_none_site -q` failed before the fix with `IndexError: list index out of range`.
- GREEN focused constructor coverage: `uv run pytest tests/unit/test_page.py::TestPageCollectionInit -q` passed 23 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 280 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_source.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 800 tests.
- `uv run pytest tests/unit -q` passed 2558 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page.py` passed.
- `uv run ruff format --check src/wikidot/module/page.py tests/unit/test_page.py` passed with 2 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `PageCollection(site=None, pages=[])` and `PageCollection()` return an empty collection with `collection.site is None`.
- Empty parentless `get_page_ids()`, `get_page_sources()`, `get_page_revisions()`, `get_page_votes()`, and `get_page_files()` return `self` without request work.
- `PageCollection(site=<valid Site>, pages=[])` keeps that explicit parent.
- `PageCollection(site=<valid Site>, pages=[valid_page])` remains valid.
- `PageCollection(site=None, pages=[valid_page])` still infers the parent from the first valid page.
- Malformed explicit parent values from Issue 477 still raise `ValueError("site must be a Site")`, and malformed `pages` values from Issue 417 still raise their existing constructor errors.
- Existing valid `Page` lists, iteration, `find(...)`, page search parsing, source/revision/vote/file acquisition, duplicate cache reuse, lazy page properties, page write helpers, site accessors, and adjacent page/site workflows remain green.
- The tests use local synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Optional parent typing could be read as permission to use a parentless collection for remote page operations. Mitigation: this slice only keeps empty parentless accessors as no-ops; populated collections without a site still fail before batch request work.
- Risk: This could be mistaken for broader collection consistency validation. Mitigation: the change does not compare the collection parent with each contained page and does not change search, parser, acquisition, or duplicate-cache behavior.
- Risk: This could be confused with Issues 417 or 477. Mitigation: those slices validate malformed constructor input; this slice repairs the preserved empty no-parent branch.

## Out Of Scope

Changing ListPages parsing, comparing collection parent identity with each contained page, coercing dictionaries into sites, rejecting `site=None`, changing direct acquisition, changing lazy page behavior, changing live Wikidot behavior, changing page-owned vote/file/revision collection contracts, and creating upstream Issues or PRs are outside this slice.

## Why This Matters

The empty no-parent state is useful for local fixtures, generated page ledgers, archival jobs, and source-collection setup that may construct a page collection before a concrete `Site` owner is attached. A readable `site is None` sentinel is easier to reason about than a default constructor that crashes before returning a collection.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used browser-free page searches, source collection, iterator workflows, page detail acquisition, generated ledgers, and tests that seed page collections directly.
- Issue 417 preserved valid empty collection construction with an explicit site and Issue 477 preserved `site=None` inference from a first page, but the fully empty no-parent constructor branch was not covered by an assertion and still indexed `self[0]`.
- The focused RED failure reproduced the constructor crash without live Wikidot access. The GREEN regression now proves the empty collection exposes the documented sentinel and keeps empty batch methods chainable while broader page/site and repository gates prove adjacent behavior remains stable.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, page source text, private messages, private content, private site data, and source text from real sites out of upstream discussion.
