# PR Draft: Validate Page Source Cache Ownership

## Summary

`Page._source` is the optional cached `PageSource` object behind the public `Page.source` property and setter. Issue 414 validated public `Page.source = ...` assignment shape, Issue 490 validated direct constructor `_source` shape, and Issue 430 validated `PageSource.wiki_text`. One direct cache ownership gap remained: callers could construct or assign a valid `PageSource` whose retained `source.page` described another page. The receiving page then exposed coherent-looking source text through `Page.source`, but the cached `PageSource.page` still pointed at a different owner.

This change validates cached source ownership during `Page.__post_init__` and direct `page.source = ...` assignment after existing `PageSource` object checks. The retained `source.page` must describe the receiving page by the same retained `Site` object and compatible page identity: matching page IDs when both sides have IDs, otherwise matching `fullname`. Mismatches raise `ValueError("page.source must belong to the page")` before the malformed cache is stored. Valid same-page cached sources, `_source=None`, existing malformed-cache diagnostics, lazy source acquisition, explicit source refresh, duplicate cached source reuse, source iterators, publish verification, and adjacent page workflows remain unchanged.

## Outcome

Directly constructed and directly assigned page source caches reject wrong-page `PageSource` wrappers before `Page.source` can expose cross-page cached source state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free source inventories, page source ledgers, generated migration records, publication verification reports, local fixtures, adapters, or serialized and rehydrated `Page` objects.

## Current Evidence

Prior source-cache drafts establish the surrounding behavior. [414-pr-validate-page-source-assignments.md](414-pr-validate-page-source-assignments.md) validates public `Page.source = ...` assignment shape and explicitly left `PageSource.page` ownership outside scope. [490-pr-validate-page-constructor-source-field.md](490-pr-validate-page-constructor-source-field.md) validates direct constructor `_source` shape and explicitly left ownership outside scope. [430-pr-validate-page-source-wiki-text.md](430-pr-validate-page-source-wiki-text.md) validates source text shape while preserving `PageSource.page` storage behavior. [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md) already proves duplicate cached source reuse should preserve ownership by wrapping copied text in a new `PageSource` for each target page. [597-pr-validate-page-revisions-cache-ownership.md](597-pr-validate-page-revisions-cache-ownership.md), [598-pr-validate-page-votes-cache-ownership.md](598-pr-validate-page-votes-cache-ownership.md), and [599-pr-validate-page-files-cache-ownership.md](599-pr-validate-page-files-cache-ownership.md) establish retained-owner checks for adjacent direct `Page` cache slots.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 414. Issue 414 rejects non-`PageSource` setter values and preserves the previous cache on malformed assignment; it explicitly does not validate owner identity for real `PageSource` values.

This is not a duplicate of Issue 490. Issue 490 rejects non-`PageSource` constructor `_source` values; it explicitly does not validate `PageSource.page` ownership.

This is not a duplicate of Issue 127. Issue 127 preserves ownership while reusing duplicate cached source text, but it does not reject caller-provided wrong-owner source wrappers at the `Page` cache slot.

No upstream issue was filed from this local workspace.

## Changes

- Add cached source ownership validation for direct `Page(...)` construction.
- Add the same ownership validation for public `page.source = ...` assignments.
- Reject `PageSource` values whose retained `source.page` describes another page.
- Preserve `_source=None`, valid same-page cached sources, existing malformed-cache diagnostics, lazy source acquisition, explicit source refresh, duplicate cached source reuse, source iterators, publish verification, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Public property setter behavior hardening
- Cached page source ownership integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(_source=PageSource(other_page, ...))` must reject the different cached source page with `ValueError("page.source must belong to the page")` before storing cached state. |
| R2 | `page.source = PageSource(other_page, ...)` must reject the different cached source page with the same diagnostic before mutating an existing valid cache. |
| R3 | Valid same-page cached source objects must remain accepted through construction and assignment. |
| R4 | Existing malformed `_source` and `page.source = ...` diagnostics from Issues 414 and 490 must remain unchanged. |
| R5 | Existing lazy source acquisition, explicit source refresh, duplicate cached source reuse, source iterator result behavior, page create/edit, publish verification, and adjacent page/revision/vote/file/site workflows must remain unchanged. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Cached source objects from another page fail at the constructor boundary. | `TestPageInit.test_init_rejects_source_cache_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN after `Page.__post_init__` called the ownership preflight. | Accepting `PageSource(other_page, ...)`, storing the mismatched cache, or deferring the failure to later source reads rejects this local completion claim. | `Page._source` cache parent state | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Setter assignments from another page fail before replacing an existing valid cache. | `TestPageProperties.test_source_setter_rejects_source_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN after the setter validated retained ownership before assigning `_source`. | Replacing the previous cache, accepting another page's source wrapper, or surfacing the wrong owner through `page.source.page` rejects this local completion claim. | `Page.source` setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Valid same-page constructor and setter source caches remain accepted. | Focused constructor/source-property coverage passed valid optional-source and setter cases. | Rejecting a valid preloaded same-page source cache, triggering source lookup during construction, or changing valid setter behavior rejects this local completion claim. | Page source cache access | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py` |
| R4 | Existing malformed-cache diagnostics remain stable. | Focused constructor/source-property coverage still passed malformed `_source` and malformed setter-value tests. | Changing `ValueError("page.source must be PageSource")`, accepting malformed values, or clearing the previous cache on malformed assignment rejects this local completion claim. | Page source cache shape validation | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py` |
| R5 | Adjacent page workflows remain green. | Direct page constructor/page/page_source coverage passed 472 tests, adjacent page/page-constructor/page-revision/page-file/page-source/page_votes/site coverage passed 1001 tests, and full unit coverage passed 2721 tests. | Regressing lazy `Page.source`, `refresh_source()`, duplicate cached source reuse, source iterators, page create/edit, publish verification, page revision/vote/file behavior, or site accessors rejects this local completion claim. | Page workflows | `tests/unit` |
| R6 | No live auth material or private site state is needed to prove the behavior. | The regressions use synthetic valid `Page` and `PageSource` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `118259f fix(page): validate source cache ownership`.

- RED constructor source ownership: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_source_cache_from_different_page -q` failed before the fix with `DID NOT RAISE`.
- RED setter source ownership: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_source_setter_rejects_source_from_different_page -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused constructor source coverage: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_optional_source tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_optional_source tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_source_cache_from_different_page -q` passed 6 tests.
- GREEN focused source-property coverage: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_source_setter_rejects_invalid_sources tests/unit/test_page.py::TestPageProperties::test_source_setter_rejects_source_from_different_page tests/unit/test_page.py::TestPageProperties::test_source_property_auto_acquire tests/unit/test_page.py::TestPageProperties::test_refresh_source_forces_remote_source_fetch -q` passed 8 tests.
- Direct page constructor/page/page_source coverage: `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_source.py -q` passed 472 tests.
- Adjacent page/page-constructor/page-revision/page-file/page-source/page_votes/site tests: `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_source.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1001 tests.
- `uv run pytest tests/unit -q` passed 2721 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py tests/unit/test_page.py` left 3 files unchanged.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page(_source=PageSource(other_page, "cached source"))` raises `ValueError("page.source must belong to the page")` before storing cached state.
- `page.source = PageSource(other_page, "other source")` raises the same diagnostic and preserves the previous valid cached source.
- `Page(_source=PageSource(same_logical_page, "cached source"))` remains valid for constructor-time preloaded cache use where the new `Page` instance cannot be referenced before construction.
- `page.source = PageSource(page, "cached source")` remains valid.
- Existing `_source=None`, malformed `_source` object rejection, malformed `page.source` assignment rejection, lazy source acquisition, explicit source refresh, duplicate cached source reuse, source iterator result behavior, page create/edit, publish verification, and adjacent page/revision/vote/file/site behavior remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page._source` is a direct cache slot for browser-free source inventories, source iterators, publish verification, and generated source ledgers. If a cached `PageSource` belongs to another page, callers can read the current page's `source` property and receive source state whose retained owner points elsewhere. Constructor and setter ownership validation keeps direct fixtures, rehydrated records, and generated caches from silently storing another page's source wrapper under the current page.

## Local Evidence, Not For Upstream Paste

- The constructor RED failure showed `Page` could accept a `PageSource` whose retained page was another page.
- The setter RED failure showed `page.source = PageSource(other_page, ...)` replaced an existing valid cache instead of raising.
- Existing local drafts covered source acquisition, parser diagnostics, response diagnostics, optional `_source` cache shape, public source assignment shape, `PageSource.wiki_text`, duplicate cached source reuse, and adjacent revision/vote/file cache ownership, but did not validate that cached source wrappers stored on a `Page` belong to that page.
- This slice only validates cached source ownership during `Page` construction and direct source assignment. It does not change source parsing, source text validation, lazy source acquisition, source iterator fallback behavior, page write behavior, live site behavior, authentication semantics, or parser selectors.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The constructor ownership check intentionally allows same-logical-page preloaded source objects because a caller cannot create a `PageSource` whose `page is new_page` before `new_page` exists. The comparison therefore requires the same retained `Site` object and uses page IDs when both sides have them; if either side lacks an ID, it falls back to `fullname`. Different-site, different-ID, and different-fullname source evidence are rejected.
