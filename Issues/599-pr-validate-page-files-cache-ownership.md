# PR Draft: Validate Page Files Cache Ownership

## Summary

`Page._files` is the optional cached `PageFileCollection` behind the public `Page.files` property. Issue 493 validated the direct constructor cache shape and non-file entries, and Issue 589 validated file-entry ownership at the `PageFileCollection(page, files)` constructor boundary. One direct cache-slot gap remained: a caller could construct a valid `PageFileCollection` for another page and pass it as `Page(..., _files=...)`, or mutate a valid collection after construction so it contained a `PageFile` retained from another page before storing it on the receiving `Page`. The receiving page then exposed cached attachment state for a different page.

This change validates cached file ownership during `Page.__post_init__` after existing cache type and entry checks. Cached file collections now compare the collection parent page, when present, and every cached file's retained page against the receiving page by the same retained `Site` object and compatible page identity: matching page IDs when both sides have IDs, otherwise matching `fullname`. Mismatches raise `ValueError("page.files must belong to the page")` before the malformed cache is stored. Valid same-page cached file collections, `_files=None`, existing malformed-cache diagnostics, empty no-parent collection semantics, lazy file acquisition, duplicate cached file reuse, file cache invalidation, and adjacent page workflows remain unchanged.

## Outcome

Directly constructed `Page` file caches reject wrong-page file collections before `Page.files` can expose cross-page cached attachment state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free attachment inventories, page asset ledgers, generated migration records, publication verification reports, local fixtures, adapters, or serialized and rehydrated `Page` objects.

## Current Evidence

Prior cache and ownership drafts establish the surrounding behavior. [493-pr-validate-page-constructor-files-cache.md](493-pr-validate-page-constructor-files-cache.md) validates the optional `_files` cache object shape and non-file entries. [589-pr-validate-page-file-collection-page-ownership.md](589-pr-validate-page-file-collection-page-ownership.md) validates `PageFileCollection` constructor entry ownership for explicit and inferred collection parents. [536-pr-preserve-empty-page-file-parent.md](536-pr-preserve-empty-page-file-parent.md) preserves readable empty no-parent file collections. [586-pr-validate-page-batch-target-site.md](586-pr-validate-page-batch-target-site.md), [587-pr-validate-page-revision-collection-page-ownership.md](587-pr-validate-page-revision-collection-page-ownership.md), [588-pr-validate-page-vote-collection-page-ownership.md](588-pr-validate-page-vote-collection-page-ownership.md), [597-pr-validate-page-revisions-cache-ownership.md](597-pr-validate-page-revisions-cache-ownership.md), and [598-pr-validate-page-votes-cache-ownership.md](598-pr-validate-page-votes-cache-ownership.md) establish retained-owner and direct cache-slot ownership hardening as active operational boundaries.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 493. Issue 493 rejects malformed `_files` values and collections containing non-`PageFile` entries; it does not compare a cached collection's retained page or cached file parent pages with the `Page` being constructed.

This is not a duplicate of Issue 589. Issue 589 protects `PageFileCollection(page, files)` from initially storing files whose retained page differs from the collection page. This slice covers the separate `Page` cache slot, including empty collections for another page and collections that were valid at construction but later mutated before being passed to the `Page` constructor.

This slice has no public setter component because `Page.files` exposes only a getter.

No upstream issue was filed from this local workspace.

## Changes

- Add cached file ownership validation for direct `Page(...)` construction.
- Reject cached `PageFileCollection` objects whose own `page`, when present, describes a different page.
- Reject cached file entries whose retained `file.page` describes a different page.
- Preserve `_files=None`, valid same-page cached collections, empty no-parent collection semantics, existing malformed-cache diagnostics, lazy file acquisition, duplicate cached file reuse, file cache invalidation, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached page file ownership integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(_files=PageFileCollection(other_page, []))` must reject the different cached collection page with `ValueError("page.files must belong to the page")` before storing cached state. |
| R2 | `Page(_files=collection_mutated_with_file_from_other_page)` must reject the different retained file page with the same diagnostic before storing cached state. |
| R3 | Valid same-page cached file collections must remain accepted and `page.files` must return the cached collection without triggering acquisition. |
| R4 | Existing malformed `_files` diagnostics from Issue 493 must remain unchanged. |
| R5 | Existing lazy file-list acquisition, duplicate cached file reuse, file cache invalidation, empty no-parent file collections, and adjacent page/revision/vote/site workflows must remain unchanged. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Cached collection parent pages from another page fail at the constructor boundary. | `TestPageInit.test_init_rejects_files_cache_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN after `Page.__post_init__` called the ownership preflight. | Accepting `PageFileCollection(other_page, [])`, storing the mismatched cache, or deferring the failure to `page.files` rejects this local completion claim. | `Page._files` cache parent state | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Valid cached collections that are mutated with another page's file fail at the same constructor boundary. | `TestPageInit.test_init_rejects_files_cache_entry_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN after each cached file's retained page was checked. | Accepting a same-page collection with a different-page file entry or returning it through `page.files` rejects this local completion claim. | `Page._files` cache entry ownership | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Valid same-page constructor caches remain accepted. | The focused constructor group passed valid optional file-cache coverage and still returns the cached collection. | Rejecting a valid preloaded same-page file cache or triggering file acquisition during construction rejects this local completion claim. | `Page._files` cache access | `tests/unit/test_page_constructor.py` |
| R4 | Existing malformed-cache diagnostics remain stable. | The focused constructor group also passed malformed `_files` and malformed collection-entry tests from Issue 493. | Changing existing diagnostics, accepting non-collection values, or accepting non-file cache entries rejects this local completion claim. | `Page` file cache shape validation | `tests/unit/test_page_constructor.py` |
| R5 | Adjacent page workflows remain green. | Direct page constructor/page/page_file coverage passed 554 tests, adjacent page/page-constructor/page-revision/page-file/page-source/page_votes/site coverage passed 999 tests, and full unit coverage passed 2719 tests. | Regressing lazy `Page.files`, duplicate cached file reuse, file cache invalidation, empty no-parent file collections, page revision/vote/source behavior, site accessors, or parser-created page behavior rejects this local completion claim. | Page workflows | `tests/unit` |
| R6 | No live auth material or private site state is needed to prove the behavior. | The regressions use synthetic valid `Page`, `PageFileCollection`, and `PageFile` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, attachment payloads, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `2bea7fb fix(page): validate files cache ownership`.

- RED cached collection page ownership: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_files_cache_from_different_page -q` failed before the fix with `DID NOT RAISE`.
- RED cached file entry ownership: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_files_cache_entry_from_different_page -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused constructor file-cache coverage: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_optional_files tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_optional_files tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_optional_file_entries tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_files_cache_from_different_page tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_files_cache_entry_from_different_page -q` passed 9 tests.
- Direct page constructor/page/page_file coverage: `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_file.py -q` passed 554 tests.
- Adjacent page/page-constructor/page-revision/page-file/page-source/page_votes/site tests: `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_source.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 999 tests.
- `uv run pytest tests/unit -q` passed 2719 tests.
- `uv run ruff format` left 87 files unchanged.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page(_files=PageFileCollection(other_page, []))` raises `ValueError("page.files must belong to the page")` before storing cached state.
- `Page(_files=same-page-collection-mutated-with-other-page-file)` raises the same diagnostic before storing cached state.
- `Page(_files=PageFileCollection(same_logical_page, []))` remains valid for constructor-time preloaded cache use where the new `Page` instance cannot be referenced before construction.
- Existing `_files=None`, malformed `_files` object rejection, non-file cache-entry rejection, lazy file acquisition, duplicate cached file reuse, file cache invalidation, empty no-parent file collection behavior, and adjacent page/revision/vote/site behavior remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page._files` is a direct cache slot for browser-free attachment inventories and generated asset ledgers. If the cached collection or one of its retained file entries belongs to another page, callers can read coherent-looking but cross-page attachment state through `Page.files`. Constructor-time ownership validation keeps direct fixtures, rehydrated records, and generated caches from silently storing another page's files under the current page.

## Local Evidence, Not For Upstream Paste

- The constructor RED failures showed `Page` could accept an empty `PageFileCollection` whose collection parent page was another page and a same-page collection mutated after construction with another page's valid file.
- Existing local drafts covered file-list acquisition, parser diagnostics, response diagnostics, optional `_files` cache shape, file collection target ownership, empty no-parent file collections, and adjacent revision/vote cache ownership, but did not validate that cached file collections stored on a `Page` belong to that page.
- This slice only validates cached file ownership during `Page` construction. It does not change file-list parsing, file URL normalization, file lookup semantics, page file mutation behavior, cache invalidation behavior, live site behavior, authentication semantics, or parser selectors.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, attachment payloads, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The constructor ownership check intentionally allows same-logical-page preloaded file collections because a caller cannot create a collection whose `page is new_page` before `new_page` exists. The comparison therefore requires the same retained `Site` object and uses page IDs when both sides have them; if either side lacks an ID, it falls back to `fullname`. Different-site, different-ID, and different-fullname cache evidence are rejected. Empty no-parent file collections remain a collection-level capability; if entries are later appended before construction, each retained file page is still checked against the receiving `Page`.
