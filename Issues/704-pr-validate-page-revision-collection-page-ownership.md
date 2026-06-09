# PR Draft: Validate PageRevisionCollection Constructor Page Ownership

## Summary

`PageRevisionCollection` already validates its optional `page` object, revision container shape, revision entry types, retained revision IDs during lookup/acquisition, and source/HTML acquisition ownership. One constructor-state gap remained: direct `PageRevisionCollection(page=page_a, revisions=[revision_from_page_b])` accepted a valid revision retained from another page, and `PageRevisionCollection(revisions=[revision_from_page_a, revision_from_page_b])` inferred `page_a` while still storing the second page's revision.

This change validates revision entry ownership during `PageRevisionCollection(...)` construction after entry validation and effective page selection, but before list state is stored. Revisions whose retained `revision.page` is not the collection page now raise `ValueError("revisions must belong to the collection page")`. Valid same-page collections, empty collections, inferred same-page collections, `find(...)`, source/HTML acquisition, lazy `PageRevision.source` / `html`, post-construction mutation guards, and `Page.revisions` setter diagnostics remain compatible.

## Outcome

Generated or rehydrated page-history collections can no longer store revisions from one page under another page's collection parent. Corrupted ownership fails at construction instead of waiting until source/HTML acquisition or later cache validation.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page history reads, duplicate cached revision reuse, source/HTML comparison, publication verification, migration or audit ledgers, local fixtures, serialized and rehydrated page revisions, and direct `PageRevisionCollection` construction.

## Current Evidence

Local rollout-backed drafts establish page revisions as a practical workflow surface. [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), [222-pr-page-revision-batch-response-body-context.md](222-pr-page-revision-batch-response-body-context.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [472-pr-validate-page-revision-collection-page-field.md](472-pr-validate-page-revision-collection-page-field.md), [491-pr-validate-page-constructor-revisions-cache.md](491-pr-validate-page-constructor-revisions-cache.md), [587-pr-validate-page-revision-collection-page-ownership.md](587-pr-validate-page-revision-collection-page-ownership.md), and [676-pr-validate-page-revision-collection-retained-id-state.md](676-pr-validate-page-revision-collection-retained-id-state.md) cover page revision reads, source/HTML acquisition, cached duplicate reuse, parser diagnostics, response diagnostics, direct row validation, collection entry validation, collection parent validation, page cache validation, acquisition-time ownership, and retained-ID lookup hardening.

This slice is not a duplicate of those drafts. Issue 587 validates mismatched revision ownership in the shared source/HTML acquisition helper, so post-construction mutations still fail before request work; it does not reject mismatched revisions at direct `PageRevisionCollection(...)` construction. Issue 419 validates that `revisions` is a list of `PageRevision` entries, Issue 472 validates the explicit collection `page` type, Issue 442 validates each `PageRevision.page` type, Issue 491 validates `Page(_revisions=...)` cache shape, and Issue 676 validates retained revision IDs during `find(...)`. Adjacent Issues 588 and 589 already apply constructor ownership validation to page vote and page file collections; this slice brings page revision collections to the same direct-state standard.

No upstream issue was filed from this local workspace.

## Changes

- Validate `PageRevisionCollection` revision ownership during construction for explicit parent pages.
- Validate inferred-parent collections so all revisions must belong to the first revision's page.
- Preserve source/HTML acquisition ownership preflights for post-construction list mutation.
- Preserve the existing `Page.revisions = [...]` ownership diagnostic, `ValueError("page.revisions must belong to the page")`, when list assignment is the public surface.

## Type Of Change

- Constructor validation
- Page-history collection state hardening
- Cache ownership integrity
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevisionCollection(page=page_a, revisions=[revision_from_page_b])` must reject the different-page revision with `ValueError("revisions must belong to the collection page")` before storing collection list state. |
| R2 | `PageRevisionCollection(revisions=[revision_from_page_a, revision_from_page_b])` must infer `page_a` from the first revision and reject the mixed-page second revision with the same diagnostic. |
| R3 | Post-construction collection mutations must still be caught by `get_sources()` and `get_htmls()` before AMC request work or cache mutation. |
| R4 | `Page.revisions = [revision_from_page_b]` on `page_a` must keep the existing public setter diagnostic, `ValueError("page.revisions must belong to the page")`, and must not corrupt the prior revision cache. |
| R5 | Existing valid same-page collections, empty collections, inferred same-page collections, collection lookup, source/HTML acquisition, lazy revision properties, page constructor cache validation, and adjacent page/file/vote/source/site workflows must remain compatible. |
| R6 | Focused RED/GREEN, PageRevisionCollection coverage, full page-revision tests, adjacent page/source/file/vote/site tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Explicit different-page revision entries fail at the constructor boundary. | `test_init_rejects_revision_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN after constructor ownership validation. | Accepting the mismatched revision, storing it in list state, or deferring failure to source/HTML acquisition rejects this local completion claim. | `PageRevisionCollection.__init__` | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Inferred-parent mixed-page entries fail before list state is stored. | `test_init_rejects_mixed_revision_pages_when_page_is_inferred` passed after the same constructor ownership preflight was added. | Inferring the first revision page while retaining another page's revision rejects this local completion claim. | `PageRevisionCollection.__init__` | `tests/unit/test_page_revision.py` |
| R3 | Acquisition guards still catch mutated collections. | `test_get_sources_rejects_revision_from_different_page_before_fetch` and `test_get_htmls_rejects_revision_from_different_page_before_fetch` now append a mismatched revision after construction and still pass with no `amc_request_with_retry` call and no cache mutation. | Removing the acquisition preflight, calling AMC, or mutating `_source` / `_html` for a mismatched revision rejects this local completion claim. | Source/HTML acquisition | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R4 | Page setter diagnostics remain stable. | The adjacent suite initially failed because the new constructor diagnostic leaked through `Page.revisions = [...]`; the implementation now translates that list-assignment path back to `page.revisions must belong to the page`, and the focused page setter test passed. | Changing the public setter error text or corrupting the prior cache rejects this local completion claim. | `Page.revisions` setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Existing page revision behavior remains green. | PageRevisionCollection passed 78 tests, `tests/unit/test_page_revision.py` passed 175 tests, adjacent page/page_revision/page_source/page_file/page_votes/site coverage passed 1076 tests, and full unit coverage passed 3541 tests. | Regressing same-page collections, inferred same-page collections, lookup, source/HTML parsing, duplicate reuse, lazy source/HTML, page constructor caches, or adjacent workflows rejects this local completion claim. | Page revision and adjacent workflows | `tests/unit` |
| R6 | Repository quality gates pass in the local dependency environment. | Full unit, ruff check, ruff format check, mypy, pyright, and `git diff --check` passed after the code change. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No private material or live action is needed to prove the behavior. | All regressions use synthetic page/revision/user objects and local unit tests; the draft contains no credentials, cookies, auth JSON, raw response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `501ff7d fix(page_revision): validate collection page ownership`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_init_rejects_revision_from_different_page -q` failed before the fix with `DID NOT RAISE`, proving direct construction accepted a revision from another page.
- GREEN focused constructor/acquisition coverage: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_init_rejects_revision_from_different_page tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_rejects_revision_from_different_page_before_fetch tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_rejects_revision_from_different_page_before_fetch -q` passed 3 tests.
- `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection -q` passed 78 tests.
- `uv run pytest tests/unit/test_page_revision.py -q` passed 175 tests.
- `uv run pytest tests/unit/test_page.py::TestPageProperties::test_revisions_setter_rejects_list_entry_from_different_page -q` passed after preserving the public setter diagnostic.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_source.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1076 tests.
- `uv run pytest tests/unit -q` passed 3541 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageRevisionCollection(page=page_a, revisions=[revision_from_page_b])` raises `ValueError("revisions must belong to the collection page")`.
- `PageRevisionCollection(revisions=[revision_from_page_a, revision_from_page_b])` raises the same diagnostic after inferring `page_a` from the first revision.
- Valid empty collections, explicit same-page collections, and inferred same-page collections continue to work.
- `get_sources()` and `get_htmls()` still reject a mismatched revision appended after construction before request work or cache mutation.
- `Page.revisions = [revision_from_page_b]` on a different page continues to raise `ValueError("page.revisions must belong to the page")` and preserves the previous cache.
- Existing page revision lookup, retained-ID validation, source/HTML acquisition, lazy source/HTML properties, page `_revisions` constructor cache validation, and adjacent page/source/file/vote/site workflows remain green.
- The new tests use synthetic objects only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Existing callers may have constructed page revision collections with inconsistent parent state and only used them as lists. Mitigation: this state is impossible for parser-created revision collections and conflicts with existing source/HTML acquisition, page cache, page vote, and page file ownership contracts; failing at construction is deterministic and easier to debug.
- Risk: The new constructor diagnostic could leak through `Page.revisions = [...]` and break existing setter-level tests or caller expectations. Mitigation: the page setter translates the collection ownership diagnostic back to its existing `page.revisions must belong to the page` message for list assignment.
- Risk: Post-construction mutation could bypass constructor validation. Mitigation: the existing acquisition-time ownership preflight remains active and the tests now explicitly cover mutation by appending a mismatched revision after construction.
- Risk: Comparing pages by identity may reject logically equal rehydrated page objects. Mitigation: this matches existing `PageFileCollection` and `PageVoteCollection` constructor ownership semantics and parser-created page-owned collections, where entries belong to the exact owning `Page` object.

## Out Of Scope

Changing revision-list parsing, comparing page ownership by fullname instead of object identity, changing page source or HTML response parsing, changing retained revision ID semantics, changing `PageRevision` constructor validation, changing page source/file/vote workflows, changing live Wikidot behavior, pushing changes, opening upstream Issues, and opening upstream PRs are outside this slice.

## Why This Matters

Page revision collections back browser-free history reads, revision source/HTML comparison, publish verification, duplicate cached revision reuse, audit ledgers, and migration checks. A collection parent and its entries should describe the same page before cache state is stored. Constructor validation prevents local fixtures, generated ledgers, or rehydrated records from silently carrying another page's revision under the wrong page.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used page history, source/HTML acquisition, latest revision checks, duplicate cached revision reuse, and page-level audit evidence.
- Existing local drafts covered revision acquisition retries, duplicate request reduction, parser diagnostics, response-body diagnostics, direct revision field validation, collection entry validation, explicit collection parent validation, acquisition-time ownership, page `_revisions` cache validation, and retained revision IDs; they did not reject mismatched revision entries at direct `PageRevisionCollection(...)` construction.
- The focused RED failure showed explicit mismatched construction stored a revision from another page. The GREEN regressions cover explicit and inferred constructor rejection, post-construction mutation guards, public page setter diagnostic stability, adjacent workflows, full unit compatibility, lint, format, type, pyright, and whitespace gates.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
