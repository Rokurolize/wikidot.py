# PR Draft: Validate Page Constructor Source Field

## Summary

`Page._source` is the optional cached `PageSource` object behind the public `Page.source` property. It is used by lazy source reads, explicit refresh behavior, duplicate source cache reuse, source iterators, publish verification, source ledgers, local fixtures, and rehydrated page records. Public `Page.source = ...` assignment already validates that assigned values are real `PageSource` objects, and `PageSource(...)` already validates `wiki_text`, but direct dataclass construction still accepted malformed `_source` values such as booleans, strings, dictionaries, and arbitrary objects.

This change validates the direct constructor's optional source cache during `Page.__post_init__`. `_source=None` remains valid for pages that have not acquired source yet, real `PageSource` objects remain valid, and malformed non-null values now raise `ValueError("page.source must be PageSource")` before they can make `Page.source` return a non-source object.

## Outcome

Directly constructed `Page` objects now fail early when optional cached source state is malformed, while preserving lazy source acquisition for `_source=None` and preserving valid preloaded `PageSource` objects.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free page inventories, source iterators, publish verification helpers, source ledgers, local fixtures, generated adapters, or serialized and rehydrated `Page` objects.

## Current Evidence

[414-pr-validate-page-source-assignments.md](414-pr-validate-page-source-assignments.md) validates public `Page.source = ...` assignment before mutating `_source`. [430-pr-validate-page-source-wiki-text.md](430-pr-validate-page-source-wiki-text.md) validates `PageSource.wiki_text`. [429-pr-validate-source-result-outcomes.md](429-pr-validate-source-result-outcomes.md) validates source-result outcome state. [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md) validates write-path source text inputs. Recent direct `Page` constructor slices validate identity, counts, rating, parent fullname, tags, site, nullable metadata, rating-percent, and cached page-ID fields.

Those prior slices are not duplicates. Issue 414 covers post-construction assignment through the public `Page.source` setter, not direct dataclass initialization. Issue 430 covers the source value object's `wiki_text`, not the optional page source cache field. Issue 429 covers result rows, not `Page` instances. Issue 349 covers write API source strings, not cached `PageSource` objects. Issues 481 through 489 validate other direct `Page` constructor fields only. None validates direct `Page(_source=...)` construction before malformed cached-source state is stored.

## Related Issue / Non-Duplicate Analysis

Builds directly on [414-pr-validate-page-source-assignments.md](414-pr-validate-page-source-assignments.md), [430-pr-validate-page-source-wiki-text.md](430-pr-validate-page-source-wiki-text.md), [429-pr-validate-source-result-outcomes.md](429-pr-validate-source-result-outcomes.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), and the direct `Page` constructor hardening in [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md) through [489-pr-validate-page-constructor-id-field.md](489-pr-validate-page-constructor-id-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add optional cached source validation for direct `Page(...)` construction.
- Preserve `_source=None` for pages that should lazily acquire source.
- Preserve valid `PageSource` objects without coercion.
- Reject booleans, strings, dictionaries, and arbitrary non-source objects with a stable `ValueError` diagnostic.
- Add constructor tests for valid optional source state and malformed direct `_source` values.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached source state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(_source=...)` must accept `None` and real `PageSource` objects. |
| R2 | `Page(_source=...)` must reject non-`None` non-`PageSource` values with `ValueError("page.source must be PageSource")`. |
| R3 | Valid page construction, lazy source acquisition, public `Page.source` assignment validation, `PageSource` construction validation, parser-created pages, source iterators, publish verification, and page source/revision/file/vote workflows must remain unchanged. |
| R4 | This slice must not validate `PageSource.page` ownership, source text contents, source parsing, write source strings, source-result rows, cached revisions/votes/files/metas, live request behavior, or unrelated constructor fields. |
| R5 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, constructor tests, adjacent page/site/page-file/page-vote/page-revision tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None` and valid `PageSource` cached source values remain accepted. | `TestPageInit.test_init_accepts_valid_optional_source` passed RED and GREEN, preserving `_source=None` and returning a valid cached `PageSource` through `page.source`. | Rejecting missing cached source, triggering source lookup during construction, or coercing valid source objects rejects this local completion claim. | `Page` constructor cached-source state | `tests/unit/test_page_constructor.py` |
| R2 | Malformed optional cached source values fail at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_optional_source` failed RED for 4 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, strings, dictionaries, arbitrary objects, or silently coercing malformed values rejects this local completion claim. | `Page` constructor cached-source state | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Existing page source workflows remain green. | Constructor tests passed 116 tests; adjacent page/site/page-file/page-vote/page-revision tests passed 840 tests; full unit tests passed 2098 tests. | Regressing lazy source acquisition, `Page.source` assignment validation, `PageSource` construction validation, parser-created pages, page collection behavior, source iterators, publish verification, or page source/revision/file/vote workflows rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_page_revision.py`, `tests/unit` |
| R4 | Broader source and parser semantics remain outside scope. | Existing source parser, source iterator, write source, source-result, publish, and adjacent tests remain green; this slice only validates direct constructor cache type integrity. | Adding ownership checks, changing lazy acquisition, changing request construction, changing parser conversion, changing source text validation, or touching live request behavior rejects this local completion claim. | Page constructor scope | `src/wikidot/module/page.py`, adjacent tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `6485945 fix(page): validate constructor page source`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_optional_source tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_optional_source -q` failed 4 malformed `_source` cases before the fix with `DID NOT RAISE`, while the valid optional-source case passed.
- GREEN: the same focused command passed 5 tests after optional cached source validation was added.
- `uv run pytest tests/unit/test_page_constructor.py -q` passed 116 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_page_revision.py tests/unit/test_page_constructor.py -q` passed 840 tests.
- `uv run pytest tests/unit -q` passed 2098 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 44 existing full-tree test typing errors outside this slice, including intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client/mock typing, invalid test cookie arguments, and existing site test mock typing issues. The changed source file and touched test module pass pyright together.

## Acceptance Criteria

- `Page(_source=None)` remains valid and lazy source acquisition remains available.
- `Page(_source=PageSource(...))` remains valid and `page.source` returns the cached object without a lookup.
- `Page(_source=True)`, `Page(_source="cached source")`, `Page(_source={"wiki_text": "cached source"})`, and `Page(_source=object())` raise `ValueError("page.source must be PageSource")` when every other constructor field is valid.
- Existing parser-created pages, direct page fixtures, page collection behavior, lazy `Page.source`, public `Page.source` setter validation, `PageSource` construction validation, source iterator behavior, publish verification, and adjacent page workflows remain green.
- The new tests use unit-level code only and do not validate `PageSource.page` ownership, source text contents, source parsing, live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Cached source is a shared state surface for source reads, source iterators, publish verification, and generated ledgers. Direct construction is useful for fixtures and rehydrated records, but malformed cached source values should fail at construction instead of making `Page.source` return unusable state.

## Local Evidence

- Local rollout evidence used cached page source state in browser-free page inventories, source iterators, publish verification, source ledgers, and generated audit records.
- Existing local drafts covered lazy source diagnostics, direct `Page.source` assignment, `PageSource.wiki_text`, source-result outcomes, and page-write source strings, but did not cover direct optional cached-source construction.
- Existing unit fixtures already relied on `_source=None` being valid for lazy source acquisition and `PageSource` being valid for preloaded source records, so this change validates only malformed non-null values.
- This slice does not change parser extraction, page write behavior, collection inference behavior, query serialization, page ID/source/revision/file/vote acquisition logic, revision/vote/file/meta cache semantics, live Wikidot behavior, site client internals, source text validation, or unrelated constructor fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The validator does not add `PageSource.page` ownership checks. Existing assignment validation only requires a `PageSource` object, and this constructor slice deliberately preserves that behavior while closing the direct dataclass cache-shape bypass.
