# PR Draft: Validate Site Accessor Parent Sites

## Summary

`SitePagesAccessor`, `SitePageAccessor`, and `SiteForumAccessor` are the public helper objects behind `Site.pages`, `Site.page`, and `Site.forum`. They are normally created from `Site.__post_init__`, but their constructors are importable and document `site: Site` as the required parent. Before this change, direct construction accepted malformed parents such as `None`, booleans, strings, dictionaries, and arbitrary objects, storing broken accessor state that failed later inside page search, page lookup/publish, or forum category reads.

This change validates accessor constructor parent sites before storing state. Malformed values now raise `ValueError("site must be a Site")`. Valid `Site` parents, normal `Site.__post_init__` accessors, page search/source iteration, page lookup/publish helpers, forum category discovery, and adjacent page/forum workflows remain unchanged.

## Outcome

Callers cannot silently construct site accessors with malformed parent-site state, while ordinary `Site.pages`, `Site.page`, and `Site.forum` usage continues to work exactly as before.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page search, source iterators, page lookup, browser-free publishing, forum category discovery, generated ledgers, local fixtures, or rehydrated helper state around `Site.pages`, `Site.page`, and `Site.forum`.

## Current Evidence

Local rollout-backed drafts repeatedly identify the three site accessors as practical workflow entry points. Page-search and source-iterator drafts such as [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [345-pr-validate-source-iterator-batch-sizes.md](345-pr-validate-source-iterator-batch-sizes.md), [396-pr-validate-listpages-retry-control.md](396-pr-validate-listpages-retry-control.md), and [409-pr-reject-boolean-search-pagination-values.md](409-pr-reject-boolean-search-pagination-values.md) establish `Site.pages` as an active operational surface. Page lookup and publish drafts such as [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [190-pr-site-page-get-direct-id-error-surface.md](190-pr-site-page-get-direct-id-error-surface.md), [347-pr-validate-publish-source-normalizer.md](347-pr-validate-publish-source-normalizer.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), and [385-pr-validate-page-lookup-not-found-flag.md](385-pr-validate-page-lookup-not-found-flag.md) establish `Site.page` as an active operational surface. Forum discovery drafts such as [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [454-pr-validate-forum-category-text-fields.md](454-pr-validate-forum-category-text-fields.md), and [476-pr-validate-forum-category-collection-site-field.md](476-pr-validate-forum-category-collection-site-field.md) establish `Site.forum` as an active operational surface.

Those prior slices are not duplicates. They validate search query controls, source batch controls, page lookup flags, publish/write inputs, forum category records and collections, response bodies, parser diagnostics, retry behavior, and adjacent collection parent fields. Issue 439 validates `SiteChange.site`, not accessor constructor parents. Issue 477 validates `PageCollection.site`, not `Site.pages`, `Site.page`, or `Site.forum` helper construction. None rejects malformed direct `SitePagesAccessor(site=...)`, `SitePageAccessor(site=...)`, or `SiteForumAccessor(site=...)` construction before broken parent state is stored.

## Related Issue / Non-Duplicate Analysis

Builds directly on the accessor workflow surfaces documented by [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [385-pr-validate-page-lookup-not-found-flag.md](385-pr-validate-page-lookup-not-found-flag.md), [454-pr-validate-forum-category-text-fields.md](454-pr-validate-forum-category-text-fields.md), [476-pr-validate-forum-category-collection-site-field.md](476-pr-validate-forum-category-collection-site-field.md), and the adjacent parent-state validation pattern from [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a shared `_validate_site_accessor_site(...)` helper for the three site accessor constructors.
- Validate `SitePagesAccessor.site`, `SitePageAccessor.site`, and `SiteForumAccessor.site` before storing parent state.
- Reject malformed parent-site values with `ValueError("site must be a Site")`.
- Preserve valid `Site` parents, normal `Site.__post_init__` accessor creation, page search/source iteration, page lookup/publish helpers, forum category discovery, and adjacent page/forum workflows.

## Type Of Change

- Input validation
- Public accessor constructor behavior hardening
- Site parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SitePagesAccessor(site=...)`, `SitePageAccessor(site=...)`, and `SiteForumAccessor(site=...)` must reject `None`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` with `ValueError("site must be a Site")`. |
| R2 | The same constructors must retain a valid `Site` parent by identity. |
| R3 | Normal `Site.__post_init__` accessor creation, `Site.pages` search and source iteration, `Site.page` lookup/publish helpers, `Site.forum.categories`, and adjacent page/forum workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, accessor tests, site tests, adjacent page/forum tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct accessor parent sites fail at the constructor boundary. | `TestSiteAccessorsInit.test_init_rejects_malformed_site` failed RED for 15 malformed accessor/site combinations because constructors did not raise, then passed GREEN after validation was added. | Accepting `None`, booleans, strings, dictionaries, arbitrary objects, or storing accessors with malformed parent-site state rejects this local completion claim. | Site accessor constructors | `src/wikidot/module/site.py`, `tests/unit/test_site_accessors.py` |
| R2 | Valid `Site` parent values remain bound by identity. | `TestSiteAccessorsInit.test_init_accepts_site` passed for all three accessor classes in the 18-test focused module run. | Copying, coercing, wrapping, rejecting, or replacing the valid parent site rejects this local completion claim. | Site accessor constructors | `tests/unit/test_site_accessors.py` |
| R3 | Existing adjacent site/page/forum workflows remain green. | `tests/unit/test_site.py` passed 264 tests; `tests/unit/test_site_accessors.py tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_forum_category.py` passed 594 tests; full unit tests passed 1942 tests. | Regressing normal `Site` initialization, page search, source iteration, page lookup, browser-free publish helpers, forum category acquisition, page collection behavior, or forum category workflows rejects this local completion claim. | Site, page, and forum workflows | `tests/unit/test_site_accessors.py`, `tests/unit/test_site.py`, `tests/unit/test_page.py`, `tests/unit/test_forum_category.py`, `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `90c4fd3 fix(site): validate accessor parent sites`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteAccessorsInit::test_init_rejects_malformed_site -q` failed 15 tests before the fix; every malformed direct accessor parent reported `DID NOT RAISE`. The focused tests were then moved into `tests/unit/test_site_accessors.py` to avoid unrelated existing pyright debt in `tests/unit/test_site.py`.
- GREEN: `uv run pytest tests/unit/test_site_accessors.py::TestSiteAccessorsInit::test_init_rejects_malformed_site -q` passed 15 tests after accessor parent-site validation was added.
- `uv run pytest tests/unit/test_site_accessors.py -q` passed 18 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 264 tests.
- `uv run pytest tests/unit/test_site_accessors.py tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_forum_category.py -q` passed 594 tests.
- `uv run pytest tests/unit -q` passed 1942 tests.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site_accessors.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/site.py tests/unit/test_site_accessors.py` passed.
- `uv run mypy src/wikidot/module/site.py tests/unit/test_site_accessors.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/site.py tests/unit/test_site_accessors.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 83 files already formatted.
- `uv run mypy src tests` passed with no issues in 83 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client/mock typing, invalid test cookie arguments, and existing site test mock typing issues. The changed source file and new accessor test module pass pyright together.

## Acceptance Criteria

- `SitePagesAccessor(None)`, `SitePagesAccessor(True)`, `SitePagesAccessor("test-site")`, `SitePagesAccessor({"unix_name": "test-site"})`, and `SitePagesAccessor(object())` raise `ValueError("site must be a Site")`.
- `SitePageAccessor(...)` rejects the same malformed parent-site values with the same error.
- `SiteForumAccessor(...)` rejects the same malformed parent-site values with the same error.
- Valid `Site` parents are stored by identity for all three accessors.
- `Site.__post_init__` still creates working `pages`, `page`, and `forum` accessors for valid `Site` objects.
- Existing page search/source iteration, page lookup/publish helpers, forum category discovery, and adjacent page/forum workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

The three site accessors are small helper wrappers, but they sit at important workflow boundaries: page inventory/source collection, page lookup/publish, and forum category discovery. `Site.__post_init__` already supplies valid parents, so the change is intentionally conservative: it only prevents direct callers, fixtures, generated adapters, or rehydrated helper state from storing malformed parent objects that later fail as less informative attribute errors or request-path errors.

## Local Evidence

- Local rollout evidence used `Site.pages` for bounded page searches, source iteration, required-tag filtering, and page/source ledgers.
- Local rollout evidence used `Site.page` for page lookup, direct page-ID fallback, browser-free publishing, source verification, and write preflight.
- Local rollout evidence used `Site.forum` for forum category discovery and category-owned thread workflows.
- Existing local drafts covered search controls, source iterator controls, page lookup controls, publish/write inputs, forum category parsing, forum category collection parent validation, and page collection parent validation, but did not cover direct site accessor constructor parents.
- This slice only validates direct site accessor constructor parent-site input. It does not change ListPages parsing, source batching, page lookup semantics, publish behavior, forum category parsing, live Wikidot behavior, or `Site.__post_init__` structure.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed parent objects instead of duck-typing anything with `unix_name`, `client`, or `amc_request`. Accessors depend on the complete `Site` object shape, and `Site.__post_init__` already provides the canonical construction path.
