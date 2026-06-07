# PR Draft: Validate Page Revisions Cache Ownership

## Summary

`Page._revisions` is the optional cached `PageRevisionCollection` behind the public `Page.revisions` property and setter, and cached revisions are also consumed by `Page.latest_revision` without going through source/HTML acquisition. Issue 491 validated the direct constructor cache shape and non-revision entries, Issue 416-class setter work validates malformed assignment shapes for adjacent caches, and Issue 587 validates page-revision source/HTML acquisition targets. One direct cache ownership gap remained: a caller could construct `Page(..., _revisions=PageRevisionCollection(other_page, []))`, mutate a valid collection to contain a `PageRevision` retained from another page before passing it to the `Page` constructor, or assign another page's collection/list through `page.revisions = ...`. The receiving page then exposed cached revision state that described a different page.

This change validates cached revision ownership during `Page.__post_init__` and during direct `page.revisions = ...` assignment after existing cache type and entry checks. Non-null cached collections now compare the collection parent page, when present, and every cached revision's retained page against the receiving page by the same retained `Site` object and compatible page identity: matching page IDs when both sides have IDs, otherwise matching `fullname`. Mismatches raise `ValueError("page.revisions must belong to the page")` before the malformed cache is stored. Valid same-page cached collections, `_revisions=None`, existing malformed-cache diagnostics, lazy revision acquisition, duplicate cached revision reuse, revision source/HTML acquisition, and adjacent page/file/vote/site workflows remain unchanged.

## Outcome

Directly constructed and directly assigned `Page` revision caches reject wrong-page revision collections before `Page.revisions` or `Page.latest_revision` can expose cross-page cached state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free page revision inventories, source/HTML comparison ledgers, translation review tooling, generated migration records, publication verification reports, local fixtures, adapters, or serialized and rehydrated `Page` objects.

## Current Evidence

Prior cache and ownership drafts establish the surrounding behavior. [491-pr-validate-page-constructor-revisions-cache.md](491-pr-validate-page-constructor-revisions-cache.md) validates the optional `_revisions` cache object shape and non-revision entries. [413-pr-validate-page-revisions-assignments.md](413-pr-validate-page-revisions-assignments.md) validates public `page.revisions = ...` assignment shape and preserves an existing cache on malformed assignments. [587-pr-validate-page-revision-collection-page-ownership.md](587-pr-validate-page-revision-collection-page-ownership.md) validates source/HTML acquisition targets before request work. [586-pr-validate-page-batch-target-site.md](586-pr-validate-page-batch-target-site.md), [588-pr-validate-page-vote-collection-page-ownership.md](588-pr-validate-page-vote-collection-page-ownership.md), [589-pr-validate-page-file-collection-page-ownership.md](589-pr-validate-page-file-collection-page-ownership.md), [594-pr-validate-forum-post-revisions-cache-ownership.md](594-pr-validate-forum-post-revisions-cache-ownership.md), [595-pr-validate-forum-thread-posts-cache-ownership.md](595-pr-validate-forum-thread-posts-cache-ownership.md), and [596-pr-validate-forum-category-threads-cache-ownership.md](596-pr-validate-forum-category-threads-cache-ownership.md) establish retained-owner and direct cache-slot ownership hardening as active operational boundaries.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 491. Issue 491 rejects malformed `_revisions` values and collections containing non-`PageRevision` entries; it does not compare a cached collection's retained page or cached revision parent pages with the `Page` being constructed.

This is not a duplicate of Issue 413. Issue 413 rejects malformed direct `Page.revisions` setter assignments and non-revision entries while preserving the previous valid cache; it does not reject valid collections or lists whose retained pages belong to another page.

This is not a duplicate of Issue 587. Issue 587 protects `PageRevisionCollection.get_sources()` and `get_htmls()` from requesting revision data through a collection page while target revisions retain another page. This slice covers the separate `Page` cache slot and public setter, including reads like `Page.latest_revision` that can consume cached revision entries without invoking source/HTML acquisition.

No upstream issue was filed from this local workspace.

## Changes

- Add cached revision ownership validation for direct `Page(...)` construction.
- Add the same ownership validation to the public `page.revisions = ...` setter before `_revisions` mutation.
- Recognize `PageRevisionCollection` setter values before the broader `list` branch, because `PageRevisionCollection` subclasses `list`; this preserves collection parent evidence for validation instead of rebinding it away.
- Reject cached `PageRevisionCollection` objects whose own `page`, when present, describes a different page.
- Reject cached revision entries whose retained `revision.page` describes a different page.
- Preserve `_revisions=None`, valid same-page cached collections, existing malformed-cache diagnostics, lazy revision acquisition, duplicate cached revision reuse, revision source/HTML acquisition, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Public cache setter behavior hardening
- Cached page revision ownership integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(_revisions=PageRevisionCollection(other_page, []))` must reject the different cached collection page with `ValueError("page.revisions must belong to the page")` before storing cached state. |
| R2 | `Page(_revisions=collection_mutated_with_revision_from_other_page)` must reject the different retained revision page with the same diagnostic before storing cached state. |
| R3 | `page.revisions = PageRevisionCollection(other_page, [])` must reject the different cached collection page before replacing the existing cache. |
| R4 | `page.revisions = [revision_from_other_page]` must reject the different retained revision page before replacing the existing cache. |
| R5 | Valid same-page cached revision collections must remain accepted and `page.revisions` must return the cached collection without triggering acquisition. |
| R6 | Existing malformed `_revisions` and setter diagnostics from Issues 491 and 413 must remain unchanged. |
| R7 | Existing lazy revision-list acquisition, duplicate cached revision reuse, revision source/HTML acquisition, latest-revision lookup for valid data, and adjacent page/file/vote/site workflows must remain unchanged. |
| R8 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Cached collection parent pages from another page fail at the constructor boundary. | `TestPageInit.test_init_rejects_revisions_cache_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN after `Page.__post_init__` called the ownership preflight. | Accepting `PageRevisionCollection(other_page, [])`, storing the mismatched cache, or deferring the failure to `page.revisions` rejects this local completion claim. | `Page._revisions` cache parent state | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Valid cached collections that are mutated with another page's revision fail at the same constructor boundary. | `TestPageInit.test_init_rejects_revisions_cache_entry_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN after each cached revision's retained page was checked. | Accepting a same-page collection with a different-page revision entry, returning it through `page.revisions`, or relying only on later source/HTML guards rejects this local completion claim. | `Page._revisions` cache entry ownership | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Direct setter assignments from another page fail before replacing the previous cache. | `TestPageProperties.test_revisions_setter_rejects_collection_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN after the setter reused the ownership preflight and checked `PageRevisionCollection` before `list`. | Replacing a valid cache with another page's collection, discarding collection parent evidence through the list branch, or clearing the previous cache on failure rejects this local completion claim. | `Page.revisions` setter parent state | `tests/unit/test_page.py` |
| R4 | Direct list assignments with another page's revision fail before replacing the previous cache. | `TestPageProperties.test_revisions_setter_rejects_list_entry_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN after raw-list assignments were converted and checked for retained-page ownership. | Replacing a valid cache with a different-page revision entry or clearing the previous cache on failure rejects this local completion claim. | `Page.revisions` setter entry ownership | `tests/unit/test_page.py` |
| R5 | Valid same-page constructor caches remain accepted. | `TestPageInit.test_init_accepts_valid_optional_revisions` passed in the focused constructor group and still returns the cached collection. | Rejecting a valid preloaded same-page revision cache or triggering revision acquisition during construction rejects this local completion claim. | `Page._revisions` cache access | `tests/unit/test_page_constructor.py` |
| R6 | Existing malformed-cache and malformed-assignment diagnostics remain stable. | The focused setter group also passed malformed constructor and setter value/entry tests from Issues 491 and 413. | Changing existing diagnostics, accepting non-collection values, or accepting non-revision cache entries rejects this local completion claim. | `Page` revision cache shape validation | `tests/unit/test_page.py`, `tests/unit/test_page_constructor.py` |
| R7 | Adjacent page workflows remain green. | `tests/unit/test_page_constructor.py` passed 160 tests, `tests/unit/test_page.py` passed 298 tests, `tests/unit/test_page_revision.py` passed 112 tests, adjacent page/page-constructor/page-revision/page-file/page-vote/site coverage passed 987 tests, and full unit coverage passed 2713 tests. | Regressing lazy `Page.revisions`, duplicate cached revision reuse, `Page.latest_revision`, revision source/HTML acquisition, page file/vote behavior, site accessors, or parser-created page behavior rejects this local completion claim. | Page workflows | `tests/unit` |
| R8 | No live auth material or private site state is needed to prove the behavior. | The regressions use synthetic valid `Page`, `PageRevisionCollection`, and `PageRevision` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text from real sites, revision HTML from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `ca82871 fix(page): validate revisions cache ownership`.

- RED cached collection page ownership: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_revisions_cache_from_different_page -q` failed before the fix with `DID NOT RAISE`.
- RED cached revision entry ownership: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_revisions_cache_entry_from_different_page -q` failed before the fix with `DID NOT RAISE`.
- RED setter collection ownership: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_revisions_setter_rejects_collection_from_different_page -q` failed before the fix with `DID NOT RAISE`.
- RED setter list-entry ownership: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_revisions_setter_rejects_list_entry_from_different_page -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused constructor cache coverage: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_optional_revisions tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_revisions_cache_from_different_page tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_revisions_cache_entry_from_different_page -q` passed 3 tests.
- GREEN focused setter cache coverage: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_revisions_setter_rejects_invalid_collections tests/unit/test_page.py::TestPageProperties::test_revisions_setter_rejects_invalid_entries tests/unit/test_page.py::TestPageProperties::test_revisions_setter_rejects_invalid_collection_entries tests/unit/test_page.py::TestPageProperties::test_revisions_setter_rejects_collection_from_different_page tests/unit/test_page.py::TestPageProperties::test_revisions_setter_rejects_list_entry_from_different_page -q` passed 14 parameterized tests.
- Page constructor module coverage: `uv run pytest tests/unit/test_page_constructor.py -q` passed 160 tests.
- Page module coverage: `uv run pytest tests/unit/test_page.py -q` passed 298 tests.
- Page revision module coverage: `uv run pytest tests/unit/test_page_revision.py -q` passed 112 tests.
- Adjacent page/page-constructor/page-revision/page-file/page-vote/site tests: `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 987 tests.
- `uv run pytest tests/unit -q` passed 2713 tests.
- `uv run ruff format` left 87 files unchanged.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page(_revisions=PageRevisionCollection(other_page, []))` raises `ValueError("page.revisions must belong to the page")` before storing cached state.
- `Page(_revisions=same-page-collection-mutated-with-other-page-revision)` raises the same diagnostic before storing cached state.
- `page.revisions = PageRevisionCollection(other_page, [])` raises the same diagnostic and leaves the previous cache unchanged.
- `page.revisions = [revision_from_other_page]` raises the same diagnostic and leaves the previous cache unchanged.
- `Page(_revisions=PageRevisionCollection(same_logical_page, []))` remains valid for constructor-time preloaded cache use where the new `Page` instance cannot be referenced before construction.
- Existing `_revisions=None`, malformed `_revisions` object rejection, non-revision cache-entry rejection, direct setter malformed object rejection, direct setter non-revision entry rejection, lazy revision acquisition, duplicate cached revision reuse, revision source/HTML acquisition, latest-revision lookup, and adjacent page/file/vote/site behavior remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page._revisions` is a direct cache slot and `Page.revisions` is a public assignment boundary for browser-free page revision inventories. If the cached collection or one of its retained revision entries belongs to another page, callers can read coherent-looking but cross-page revision state through `Page.revisions` and `Page.latest_revision`. Constructor-time and setter-time ownership validation keep direct fixtures, rehydrated records, and generated caches from silently storing another page's revision history under the current page.

## Local Evidence, Not For Upstream Paste

- The constructor RED failures showed `Page` could accept an empty `PageRevisionCollection` whose collection parent page was another page and a same-page collection mutated after construction with another page's valid revision.
- The setter RED failures showed direct assignment could replace an existing valid cache with another page's collection or raw revision list.
- The setter implementation also exposed that `PageRevisionCollection` must be checked before `list`, because it subclasses `list`; otherwise direct collection assignments lose their collection parent evidence before validation.
- Existing local drafts covered revision-list acquisition, parser diagnostics, response diagnostics, optional `_revisions` cache shape, setter shape, revision source/HTML target ownership, and adjacent vote/file cache ownership, but did not validate that cached revision collections stored on a `Page` belong to that page.
- This slice only validates cached revision ownership during `Page` construction and direct assignment. It does not change revision-list parsing, revision source/HTML parsing, collection constructor semantics, lazy cache invalidation, live site behavior, authentication semantics, or parser selectors.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text from real sites, revision HTML from real sites, and private site data out of upstream discussion.

## Additional Notes

The constructor ownership check intentionally allows same-logical-page preloaded revision collections because a caller cannot create a collection whose `page is new_page` before `new_page` exists. The comparison therefore requires the same retained `Site` object and uses page IDs when both sides have them; if either side lacks an ID, it falls back to `fullname`. Different-site, different-ID, and different-fullname cache evidence are rejected.
