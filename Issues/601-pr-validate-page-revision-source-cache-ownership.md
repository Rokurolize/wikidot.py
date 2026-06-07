# PR Draft: Validate Page Revision Source Cache Ownership

## Summary

`PageRevision._source` is the optional cached `PageSource` object behind the public `PageRevision.source` property and setter. Issue 431 validated public `revision.source = ...` assignment shape, Issue 509 validated direct constructor `_source` shape, and Issue 430 validated `PageSource.wiki_text`. One direct cache ownership gap remained: callers could construct or assign a valid `PageSource` whose retained `source.page` described another page. The receiving revision then exposed coherent-looking source text through `PageRevision.source`, but the cached `PageSource.page` still pointed at a different page.

This change validates cached source ownership during `PageRevision.__post_init__` and direct `revision.source = ...` assignment after existing `PageSource` object checks. The retained `source.page` must describe the revision's page by the same retained `Site` object and compatible page identity: matching page IDs when both sides have IDs, otherwise matching `fullname`. Mismatches raise `ValueError("revision.source must belong to the revision page")` before the malformed cache is stored. Valid same-page cached sources, `_source=None`, existing malformed-cache diagnostics, lazy revision source acquisition, duplicate revision source reuse, revision HTML behavior, page source behavior, and adjacent page workflows remain unchanged.

## Outcome

Directly constructed and directly assigned page revision source caches reject wrong-page `PageSource` wrappers before `PageRevision.source` can expose cross-page cached source state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free revision source inventories, historical source ledgers, migration records, publication verification reports, local fixtures, adapters, or serialized and rehydrated `PageRevision` objects.

## Current Evidence

Prior revision-source drafts establish the surrounding behavior. [431-pr-validate-page-revision-source-assignments.md](431-pr-validate-page-revision-source-assignments.md) validates public `PageRevision.source = ...` assignment shape and explicitly left `PageSource.page` ownership outside scope. [509-pr-validate-page-revision-source-cache.md](509-pr-validate-page-revision-source-cache.md) validates direct constructor `_source` shape and does not validate ownership. [430-pr-validate-page-source-wiki-text.md](430-pr-validate-page-source-wiki-text.md) validates source text shape while preserving `PageSource.page` storage behavior. [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md) and [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md) already prove duplicate cached revision source reuse should preserve ownership by wrapping copied text in a new `PageSource` for each target page. [587-pr-validate-page-revision-collection-page-ownership.md](587-pr-validate-page-revision-collection-page-ownership.md) validates collection-level page ownership, but it does not reject a caller-provided wrong-owner source cache stored on an otherwise valid revision.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 431. Issue 431 rejects non-`PageSource` setter values and preserves the previous cache on malformed assignment; it explicitly does not validate owner identity for real `PageSource` values.

This is not a duplicate of Issue 509. Issue 509 rejects non-`PageSource` constructor `_source` values; it does not validate `PageSource.page` ownership.

This is not a duplicate of Issue 587. Issue 587 validates that revisions in a `PageRevisionCollection` belong to the collection page; it does not validate the retained owner inside a revision's cached `PageSource`.

This is not a duplicate of Issues 126 or 128. Those issues preserve ownership while reusing duplicate cached revision source text, but they do not reject caller-provided wrong-owner source wrappers at the `PageRevision` cache slot.

No upstream issue was filed from this local workspace.

## Changes

- Add cached source ownership validation for direct `PageRevision(...)` construction.
- Add the same ownership validation for public `revision.source = ...` assignments.
- Reject `PageSource` values whose retained `source.page` describes another page.
- Preserve `_source=None`, valid same-page cached sources, existing malformed-cache diagnostics, lazy revision source acquisition, duplicate cached revision source reuse, revision HTML behavior, page source behavior, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Public property setter behavior hardening
- Cached page revision source ownership integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevision(_source=PageSource(other_page, ...))` must reject the different cached source page with `ValueError("revision.source must belong to the revision page")` before storing cached state. |
| R2 | `revision.source = PageSource(other_page, ...)` must reject the different cached source page with the same diagnostic before mutating an existing valid cache. |
| R3 | Valid same-page cached source objects must remain accepted through construction and assignment. |
| R4 | Existing malformed `_source` and `revision.source = ...` diagnostics from Issues 431 and 509 must remain unchanged. |
| R5 | Existing lazy revision source acquisition, duplicate cached revision source reuse, revision HTML behavior, page source behavior, and adjacent page/revision/file/source/vote/site workflows must remain unchanged. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Cached source objects from another page fail at the constructor boundary. | `TestPageRevision.test_init_rejects_source_cache_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN after `PageRevision.__post_init__` called the ownership preflight. | Accepting `PageSource(other_page, ...)`, storing the mismatched cache, or deferring the failure to later revision source reads rejects this local completion claim. | `PageRevision._source` cache parent state | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Setter assignments from another page fail before replacing an existing valid cache. | `TestPageRevision.test_source_setter_rejects_source_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN after the setter validated retained ownership before assigning `_source`. | Replacing the previous cache, accepting another page's source wrapper, or surfacing the wrong owner through `revision.source.page` rejects this local completion claim. | `PageRevision.source` setter | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R3 | Valid same-page constructor and setter source caches remain accepted. | `tests/unit/test_page_revision.py` passed 115 tests, including valid optional-source, same-logical-page source, and setter cases. | Rejecting a valid preloaded same-page source cache, triggering source lookup during construction, or changing valid setter behavior rejects this local completion claim. | Page revision source cache access | `tests/unit/test_page_revision.py` |
| R4 | Existing malformed-cache diagnostics remain stable. | Direct page revision/source coverage passed 121 tests, including malformed `_source`, malformed setter-value, and `PageSource.wiki_text` coverage. | Changing `ValueError("revision.source must be PageSource")`, accepting malformed values, or clearing the previous cache on malformed assignment rejects this local completion claim. | Revision source cache shape validation | `tests/unit/test_page_revision.py`, `tests/unit/test_page_source.py` |
| R5 | Adjacent page workflows remain green. | Adjacent page/page-constructor/page-revision/page-file/page-source/page_votes/site coverage passed 1004 tests, and full unit coverage passed 2724 tests. | Regressing lazy `PageRevision.source`, duplicate cached revision source reuse, revision HTML behavior, page source behavior, page revision collection behavior, page file/vote/site behavior, or page source validation rejects this local completion claim. | Page revision workflows | `tests/unit` |
| R6 | No live auth material or private site state is needed to prove the behavior. | The regressions use synthetic valid `Page`, `PageRevision`, and `PageSource` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `689cf65 fix(page_revision): validate source cache ownership`.

- RED constructor source ownership: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_source_cache_from_different_page tests/unit/test_page_revision.py::TestPageRevision::test_source_setter_rejects_source_from_different_page -q` failed before the fix with both tests reporting `DID NOT RAISE`.
- GREEN focused ownership coverage: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_init_accepts_source_cache_from_same_logical_page tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_source_cache_from_different_page tests/unit/test_page_revision.py::TestPageRevision::test_source_setter_rejects_source_from_different_page -q` passed 3 tests.
- Page revision coverage: `uv run pytest tests/unit/test_page_revision.py -q` passed 115 tests.
- Direct page revision/source coverage: `uv run pytest tests/unit/test_page_revision.py tests/unit/test_page_source.py -q` passed 121 tests.
- Adjacent page/page-constructor/page-revision/page-file/page-source/page_votes/site tests: `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_source.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1004 tests.
- `uv run pytest tests/unit -q` passed 2724 tests.
- `uv run ruff format src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` left 2 files unchanged.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageRevision(_source=PageSource(other_page, "cached revision source"))` raises `ValueError("revision.source must belong to the revision page")` before storing cached state.
- `revision.source = PageSource(other_page, "other revision source")` raises the same diagnostic and preserves the previous valid cached source.
- `PageRevision(_source=PageSource(same_logical_page, "cached revision source"))` remains valid for constructor-time preloaded cache use where same retained site and compatible page identity describe the revision page.
- `revision.source = PageSource(revision.page, "cached revision source")` remains valid.
- Existing `_source=None`, malformed `_source` object rejection, malformed `revision.source` assignment rejection, lazy revision source acquisition, duplicate cached revision source reuse, revision HTML behavior, page source behavior, and adjacent page/revision/file/source/vote/site behavior remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageRevision._source` is a direct cache slot for browser-free revision source inventories, duplicate revision-source reuse, source ledgers, and historical migration checks. If a cached `PageSource` belongs to another page, callers can read the revision's `source` property and receive source state whose retained owner points elsewhere. Constructor and setter ownership validation keeps direct fixtures, rehydrated records, and generated caches from silently storing another page's source wrapper under the current revision.

## Local Evidence, Not For Upstream Paste

- The constructor RED failure showed `PageRevision` could accept a `PageSource` whose retained page was another page.
- The setter RED failure showed `revision.source = PageSource(other_page, ...)` replaced an existing valid cache instead of raising.
- Existing local drafts covered revision source acquisition, parser diagnostics, response diagnostics, optional `_source` cache shape, public revision source assignment shape, `PageSource.wiki_text`, duplicate cached revision source reuse, collection page ownership, and adjacent page cache ownership, but did not validate that cached source wrappers stored on a `PageRevision` belong to the revision page.
- This slice only validates cached source ownership during `PageRevision` construction and direct source assignment. It does not change source parsing, source text validation, lazy source acquisition, revision HTML behavior, page source behavior, live site behavior, authentication semantics, or parser selectors.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The constructor ownership check intentionally allows same-logical-page preloaded source objects because a caller cannot create a `PageSource` whose `page is new_revision.page` before all objects exist in every fixture or deserialization flow. The comparison therefore requires the same retained `Site` object and uses page IDs when both sides have them; if either side lacks an ID, it falls back to `fullname`. Different-site, different-ID, and different-fullname source evidence are rejected.
