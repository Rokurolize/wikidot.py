# PR Draft: Validate PageRevision Source Cache

## Summary

`PageRevision._source` is the optional cached `PageSource` object behind the public `PageRevision.source` property. It is populated by lazy revision source acquisition, duplicate cached revision-source reuse, generated page-history ledgers, publication verification tooling, local fixtures, generated adapters, and rehydrated page-revision records. Earlier local slices validated page revision acquisition, response-body diagnostics, revision source parsing, duplicate revision source reuse, `PageRevisionCollection` entries and construction, direct public `revision.source = ...` assignment, direct `PageRevision` page/identity/comment/creator/time fields, and direct `Page(_source=...)` cached page source state, but direct `PageRevision(..., _source=...)` construction still accepted malformed cached values such as booleans, integers, strings, lists, dictionaries, and arbitrary objects.

This change validates the direct constructor's optional source cache during `PageRevision.__post_init__`. `_source=None` remains valid for revisions that have not acquired source yet, real `PageSource` objects remain valid, and malformed non-null values now raise the same stable `ValueError("revision.source must be PageSource")` diagnostic used by the public `source` setter before malformed local cache state can be returned by `revision.source`.

## Outcome

Directly constructed `PageRevision` objects now fail early when optional cached source state is malformed, while preserving lazy source acquisition for `_source=None` and preserving valid preloaded `PageSource` objects.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free page-history inventories, revision source comparison ledgers, publication verification tooling, translation review tooling, cached page records, local fixtures, generated adapters, or serialized and rehydrated `PageRevision` objects.

## Current Evidence

Page-revision source drafts [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [164-pr-page-revision-source-parse-context.md](164-pr-page-revision-source-parse-context.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), and [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md) establish revision source acquisition, retry behavior, duplicate cache reuse, lazy failure visibility, response diagnostics, and parser diagnostics as active operational surfaces.

Constructor and state-integrity drafts [430-pr-validate-page-source-wiki-text.md](430-pr-validate-page-source-wiki-text.md), [431-pr-validate-page-revision-source-assignments.md](431-pr-validate-page-revision-source-assignments.md), [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), [466-pr-validate-page-revision-comment-field.md](466-pr-validate-page-revision-comment-field.md), [467-pr-validate-page-revision-creator-time-fields.md](467-pr-validate-page-revision-creator-time-fields.md), [472-pr-validate-page-revision-collection-page-field.md](472-pr-validate-page-revision-collection-page-field.md), and [490-pr-validate-page-constructor-source-field.md](490-pr-validate-page-constructor-source-field.md) establish the local pattern for validating direct record and cache state instead of relying only on parser-created objects or public property setters.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 431. Issue 431 validates direct public `revision.source = ...` assignments and preserves the previous cached value on invalid setter input; this slice validates constructor-seeded `_source` before any public setter is invoked.

This is not a duplicate of Issues 465, 466, or 467. Those slices validate direct `PageRevision` identity, comment, creator, and timestamp fields, and explicitly leave direct `_source` and `_html` constructor cache values as separate cache concerns.

This is not a duplicate of Issue 430. Issue 430 validates the `PageSource.wiki_text` value object's text field, not whether a `PageRevision` cache slot contains a `PageSource`.

This is not a duplicate of Issue 490. Issue 490 validates the page-level `Page._source` cache; this slice validates the revision-level `PageRevision._source` cache.

No upstream issue was filed from this local workspace.

## Changes

- Add optional cached source validation for direct `PageRevision(...)` construction.
- Preserve `_source=None` for revisions that should lazily acquire source.
- Preserve valid cached `PageSource` objects without coercion.
- Reject booleans, integers, strings, lists, dictionaries, and arbitrary non-`PageSource` objects using `ValueError("revision.source must be PageSource")`.
- Add constructor tests for malformed direct `_source` values and valid cached `PageSource` objects.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached page-revision source state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevision(_source=...)` must accept `None` and real `PageSource` objects. |
| R2 | `PageRevision(_source=...)` must reject non-`None` non-`PageSource` values with `ValueError("revision.source must be PageSource")`. |
| R3 | Valid cached source objects must be returned by `revision.source` without triggering revision source acquisition. |
| R4 | Valid revision construction, lazy revision source acquisition, duplicate cached source reuse, public `revision.source = ...` assignment validation, revision HTML behavior, revision collections, `Page.revisions`, page source behavior, page file/vote behavior, and adjacent page/site workflows must remain unchanged. |
| R5 | This slice must not change revision-list acquisition, revision source acquisition, revision HTML acquisition, response-body diagnostics, parser selectors, page source text validation, request construction, live request behavior, or unrelated constructor fields. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, PageRevision tests, adjacent page workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None` and valid cached `PageSource` objects remain accepted. | `TestPageRevision.test_init_accepts_valid_source_cache` passed before and after validation was added, preserving a valid cached object and returning it through `revision.source`. Existing constructors continue to use `_source=None`. | Rejecting missing cached source, triggering source lookup during construction, or coercing valid `PageSource` objects rejects this local completion claim. | `PageRevision` constructor cached source state | `tests/unit/test_page_revision.py` |
| R2 | Malformed optional cached source values fail at the constructor boundary. | `TestPageRevision.test_init_rejects_malformed_source_cache` failed RED for 6 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, integers, strings, lists, dictionaries, arbitrary objects, or silently coercing malformed values rejects this local completion claim. | `PageRevision` constructor cached source state | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R3 | Valid cached source access remains a cache hit. | The valid-cache test asserts `revision.source == source`, `revision.is_source_acquired() is True`, and no `amc_request_with_retry` call occurs. | Calling AMC, clearing `_source`, replacing the cached object, or treating a valid `PageSource` as missing rejects this local completion claim. | `PageRevision.source` cache access | `tests/unit/test_page_revision.py` |
| R4 | Existing page revision and adjacent page workflows remain green. | `tests/unit/test_page_revision.py::TestPageRevision` passed 54 tests, `tests/unit/test_page_revision.py` passed 104 tests, adjacent page/source/revision/file/vote/site tests passed 874 tests, and the full unit suite passed 2272 tests. | Regressing lazy source acquisition, duplicate cached source reuse, source setter validation, revision HTML behavior, revision collection behavior, page source behavior, page files/votes, site workflows, or parser-created pages rejects this local completion claim. | PageRevision and adjacent page workflows | `tests/unit` |
| R5 | Broader revision semantics remain outside scope. | Existing acquisition, parser, response-body, setter, collection, page, and adjacent tests remain green; this slice only validates direct constructor cache type integrity. | Changing request construction, parser conversion, response diagnostics, revision ordering, source text extraction, HTML handling, page edit behavior, source result behavior, or live request behavior rejects this local completion claim. | PageRevision constructor scope | `src/wikidot/module/page_revision.py`, adjacent tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw page source, raw page HTML, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `f122b36 fix(page_revision): validate source cache`.

- RED cache tests: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_malformed_source_cache tests/unit/test_page_revision.py::TestPageRevision::test_init_accepts_valid_source_cache -q` failed 6 malformed `_source` cases before the fix with `DID NOT RAISE`, while the valid cached `PageSource` case passed.
- GREEN cache tests: the same focused command passed 7 tests after optional source-cache validation was added.
- Constructor/property block: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision -q` passed 54 tests.
- `uv run pytest tests/unit/test_page_revision.py -q` passed 104 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 874 tests.
- `uv run ruff format src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` reformatted the test file and left the source file unchanged.
- `uv run ruff format --check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with 2 files already formatted.
- `uv run ruff check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed.
- `uv run mypy src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2272 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageRevision(_source=None)` remains valid and lazy source acquisition remains available.
- `PageRevision(_source=PageSource(...))` remains valid and `revision.source` returns the cached object without a lookup.
- `PageRevision(_source=True)`, `PageRevision(_source=100)`, `PageRevision(_source="cached revision source")`, `PageRevision(_source=["cached revision source"])`, `PageRevision(_source={"wiki_text": "cached revision source"})`, and `PageRevision(_source=object())` raise `ValueError("revision.source must be PageSource")` when every other constructor field is valid.
- Existing parser-created revisions, direct revision fixtures, lazy `PageRevision.source`, direct and batched `PageRevisionCollection.get_sources()`, duplicate cached revision source reuse, public `revision.source = ...` assignment validation, `PageRevision.html`, `Page.revisions`, page source behavior, page file/vote behavior, and adjacent page/site workflows remain green.
- The new tests use unit-level code only and do not validate revision source contents, parser selectors, live Wikidot, credentials, cookies, auth JSON, private page data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Constructor validation could be confused with page-source text validation. Mitigation: the validator checks cache object type only; `PageSource.wiki_text` validation remains the value object's responsibility.
- Risk: Valid cached `PageSource` objects could accidentally trigger acquisition. Mitigation: the valid-cache test asserts the cached object is returned and no retry request is made.
- Risk: Public setter behavior could diverge from constructor behavior. Mitigation: the constructor reuses the same `PageSource` validator as the `source` setter for non-`None` values.
