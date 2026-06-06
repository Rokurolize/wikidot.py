# PR Draft: Validate Page Constructor Site

## Summary

`Page.site` is the parent `Site` object used by URL generation, AMC request routing, lazy page source/revision/file/vote acquisition, source and publish ledgers, parser-created page rows, and local rehydrated `Page` fixtures. Adjacent parent-site boundaries already validate `PageCollection.site`, site accessors, and site-scoped records, but direct `Page(...)` construction still accepted malformed parent sites such as `site=None`, `site=True`, `site="test-site"`, `site={"unix_name": "test-site"}`, or `site=object()`. Those values could be stored as page state and fail later as less-informative attribute errors when page workflows access `site.url`, `site.unix_name`, `site.client`, or AMC methods.

This change validates the direct constructor's `site` field during `Page.__post_init__`. Malformed parent sites now raise `ValueError("site must be a Site")`, and valid `Site` instances remain accepted. Valid page construction, parser-created pages, page collection behavior, site accessors, page source/revision/file/vote workflows, query tag behavior, and site workflows remain unchanged.

## Outcome

Directly constructed `Page` objects now fail early when their parent site is malformed, preserving the same parent-object integrity contract already used by adjacent collection, accessor, and result surfaces.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page inventories, page lookup/publish workflows, source/revision/file/vote acquisition, generated ledgers, migration tooling, local fixtures, or rehydrated `Page` objects.

## Current Evidence

Local rollout-backed drafts already establish parent-site context as operationally meaningful. [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md) validates explicit `PageCollection.site`, [478-pr-validate-site-accessor-parent-sites.md](478-pr-validate-site-accessor-parent-sites.md) validates site accessor parents, [439-pr-validate-site-change-site-field.md](439-pr-validate-site-change-site-field.md) validates recent-change site records, and [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md) relies on `page.site.unix_name` for compact result ledgers. Recent direct-constructor hardening in [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md), [482-pr-validate-page-constructor-count-fields.md](482-pr-validate-page-constructor-count-fields.md), [483-pr-validate-page-constructor-rating-field.md](483-pr-validate-page-constructor-rating-field.md), [484-pr-validate-page-constructor-parent-fullname.md](484-pr-validate-page-constructor-parent-fullname.md), and [485-pr-validate-page-constructor-tags.md](485-pr-validate-page-constructor-tags.md) validates adjacent page metadata boundaries.

Those prior slices are not duplicates. Issue 477 validates collection-level explicit site state, including `site=None` inference from a first valid page. Issue 478 validates accessor parent sites. Issue 439 validates `SiteChange.site`. Issues 440 and 441 validate result objects' `page` fields, not the page's own parent site. Issues 481 through 485 validate direct page identity, count, rating, parent fullname, and tags only. None validates direct `Page(site=...)` construction before malformed parent-site state is stored.

## Related Issue / Non-Duplicate Analysis

Builds directly on the parent-site and page constructor surfaces documented by [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [439-pr-validate-site-change-site-field.md](439-pr-validate-site-change-site-field.md), [440-pr-validate-source-result-page-field.md](440-pr-validate-source-result-page-field.md), [441-pr-validate-publish-result-page-field.md](441-pr-validate-publish-result-page-field.md), [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md), [478-pr-validate-site-accessor-parent-sites.md](478-pr-validate-site-accessor-parent-sites.md), and [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md) through [485-pr-validate-page-constructor-tags.md](485-pr-validate-page-constructor-tags.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a direct page-site validator that requires `Site`.
- Keep `PageCollection.site` validation behavior unchanged by delegating its existing helper to the shared page-site validator.
- Validate `Page.site` during `Page.__post_init__`.
- Reject malformed direct page sites with stable `ValueError("site must be a Site")`.
- Update page-file and page-vote unit helpers to construct valid `Page` fixtures with real `Site` objects instead of `MagicMock` sites.
- Preserve valid page construction, parser-created pages, collection behavior, source/revision/file/vote workflows, and site workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page parent-site integrity
- Test fixture tightening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(site=...)` must reject non-`Site` values with `ValueError("site must be a Site")`. |
| R2 | Valid `Page(site=<Site>)` construction must remain accepted and store the same parent `Site`. |
| R3 | Existing `PageCollection.site` validation, parser-created pages, page source/revision/file/vote workflows, and site workflows must remain unchanged. |
| R4 | Test-only valid `Page` fixtures that exercise page files and page votes must use real `Site` parents instead of depending on malformed mock-site construction. |
| R5 | This slice must not validate site client internals, page metadata users, timestamps, `rating_percent`, cached source/revisions/votes/files, URL syntax, tag syntax, parent fullname syntax, or live request behavior. |
| R6 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, constructor tests, adjacent page/site/page-file/page-vote/page-revision tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct `Page.site` values fail at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_site` failed RED for 5 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting `None`, booleans, strings, dictionaries, arbitrary objects, or duck-typed site-like mocks rejects this local completion claim. | `Page` constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Valid `Site` parents remain accepted and stored. | `TestPageInit.test_init_accepts_valid_identity_text` now asserts the constructed page stores the original `Site`; the focused GREEN passed. | Replacing, coercing, or rejecting valid `Site` instances rejects this local completion claim. | `Page` constructor parent state | `tests/unit/test_page_constructor.py` |
| R3 | Existing valid page and site workflows remain green. | `tests/unit/test_page_constructor.py` passed 62 tests; adjacent page/site/page-file/page-vote/page-revision tests passed 786 tests; full unit tests passed 2044 tests. | Regressing valid fixture construction, parser-created pages, page collection behavior, page lookup, page source/revision/file/vote workflows, or site workflows rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_page_revision.py`, `tests/unit` |
| R4 | Valid page-file and page-vote fixtures no longer rely on mock parent sites. | `tests/unit/test_page_file.py` and `tests/unit/test_page_votes.py` helpers now instantiate `Site` and retain mocked AMC methods only where those tests need them; adjacent tests passed after the fixture update. | Weakening the production validator to accept arbitrary mocks, or leaving valid tests dependent on malformed page parent-site state, rejects this local completion claim. | Unit fixture integrity | `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py` |
| R5 | Broader site internals and parser metadata remain outside scope. | Existing nullable parser metadata fixture patterns, query behavior, and adjacent tests remain unchanged and green. | Validating or changing site client internals, page users, timestamps, `rating_percent`, cached state, URL syntax, tag syntax, parent fullname syntax, or live request behavior rejects this local completion claim. | Page constructor scope | `src/wikidot/module/page.py`, adjacent tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `3df4b37 fix(page): validate constructor site`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_site -q` failed 5 tests before the fix; every malformed site case reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_identity_text tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_site -q` passed 6 tests after page-site validation was added.
- `uv run pytest tests/unit/test_page_constructor.py -q` passed 62 tests.
- `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_page_revision.py -q` passed 786 tests after page-file and page-vote helpers were updated to use real `Site` parents.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py tests/unit/test_page_file.py tests/unit/test_page_votes.py` left 4 files unchanged.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page_constructor.py tests/unit/test_page_file.py tests/unit/test_page_votes.py` passed.
- `uv run ruff format --check src/wikidot/module/page.py tests/unit/test_page_constructor.py tests/unit/test_page_file.py tests/unit/test_page_votes.py` passed with 4 files already formatted.
- `uv run mypy src/wikidot/module/page.py tests/unit/test_page_constructor.py tests/unit/test_page_file.py tests/unit/test_page_votes.py` passed with no issues in 4 source files.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_page_constructor.py tests/unit/test_page_file.py tests/unit/test_page_votes.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- `uv run pytest tests/unit -q` passed 2044 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client/mock typing, invalid test cookie arguments, and existing site test mock typing issues. The changed source file and touched test modules pass pyright together.

## Acceptance Criteria

- `Page(site=None)`, `Page(site=True)`, `Page(site="test-site")`, `Page(site={"unix_name": "test-site"})`, and `Page(site=object())` raise `ValueError("site must be a Site")` when every other constructor field is valid.
- `Page(site=<valid Site>)` remains accepted and stores the same `Site` object.
- Existing parser-created pages, direct page fixtures, page collection behavior, page lookup behavior, page source/revision/file/vote workflows, and site workflows remain green.
- Test helpers that construct valid `Page` objects for page-file and page-vote tests use real `Site` parents.
- The new tests use unit-level code only and do not validate site client internals, page users, timestamps, `rating_percent`, cached state, URL syntax, tag syntax, parent fullname syntax, require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Page parent-site state is not optional in direct page workflows: it drives URLs, site identities, AMC calls, source/revision/file/vote acquisition, result ledgers, and contextual diagnostics. Adjacent collection and accessor surfaces already require real `Site` parents, so this change applies the same runtime invariant to direct `Page(...)` construction and tightens local valid fixtures accordingly.

## Local Evidence

- Local rollout evidence used `Page.site` for source collection, publish ledgers, URL generation, page file/vote/revision acquisition, required-tag filtering, and site-aware diagnostics.
- Existing local drafts covered page collection parent-site validation, site accessor parent validation, result object page validation, and direct page metadata validation, but did not cover direct `Page(site=...)` construction.
- Existing page-file and page-vote unit helpers used `MagicMock` sites for otherwise valid `Page` fixtures. Those helpers now use real `Site` objects while preserving mocked AMC methods for local unit tests.
- This slice does not change parser extraction, page write behavior, collection inference behavior, query serialization, page ID/source/revision/file/vote acquisition logic, cached state, live Wikidot behavior, site client internals, user/timestamp metadata, `rating_percent`, tags, parent fullname, or URL syntax validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change rejects malformed parent sites rather than accepting duck-typed site-like objects. That keeps direct page construction aligned with the repository's recent runtime validation pattern for parent objects and stored record state.
