# PR Draft: Validate PageRevision HTML Cache

## Summary

`PageRevision._html` is the optional cached HTML string behind the public `PageRevision.html` property. It is populated by lazy revision HTML acquisition, duplicate cached revision-HTML reuse, generated page-history ledgers, publication verification tooling, local fixtures, generated adapters, and rehydrated page-revision records. Earlier local slices validated page revision acquisition, response-body diagnostics, revision HTML parsing, duplicate revision HTML reuse, `PageRevisionCollection` entries and construction, direct public `revision.html = ...` assignment, direct `PageRevision` page/identity/comment/creator/time fields, direct `Page(_source=...)` cached page source state, and direct `PageRevision(_source=...)` cached source state, but direct `PageRevision(..., _html=...)` construction still accepted malformed cached values such as booleans, integers, lists, dictionaries, and arbitrary objects.

This change validates the direct constructor's optional HTML cache during `PageRevision.__post_init__`. `_html=None` remains valid for revisions that have not acquired HTML yet, real strings remain valid, and malformed non-null values now raise the same stable `ValueError("revision.html must be a string")` diagnostic used by the public `html` setter before malformed local cache state can be returned by `revision.html`.

## Outcome

Directly constructed `PageRevision` objects now fail early when optional cached HTML state is malformed, while preserving lazy HTML acquisition for `_html=None` and preserving valid preloaded HTML strings.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free page-history inventories, revision HTML comparison ledgers, publication verification tooling, translation review tooling, cached page records, local fixtures, generated adapters, or serialized and rehydrated `PageRevision` objects.

## Current Evidence

Page-revision source/HTML drafts [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), and [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md) establish revision source and HTML acquisition, retry behavior, duplicate cache reuse, lazy failure visibility, response diagnostics, and parser diagnostics as active operational surfaces.

Constructor and state-integrity drafts [431-pr-validate-page-revision-source-assignments.md](431-pr-validate-page-revision-source-assignments.md), [432-pr-validate-page-revision-html-assignments.md](432-pr-validate-page-revision-html-assignments.md), [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), [466-pr-validate-page-revision-comment-field.md](466-pr-validate-page-revision-comment-field.md), [467-pr-validate-page-revision-creator-time-fields.md](467-pr-validate-page-revision-creator-time-fields.md), [472-pr-validate-page-revision-collection-page-field.md](472-pr-validate-page-revision-collection-page-field.md), [490-pr-validate-page-constructor-source-field.md](490-pr-validate-page-constructor-source-field.md), and [509-pr-validate-page-revision-source-cache.md](509-pr-validate-page-revision-source-cache.md) establish the local pattern for validating direct record and cache state instead of relying only on parser-created objects or public property setters.

Adjacent forum revision cache draft [508-pr-validate-forum-post-revision-html-cache.md](508-pr-validate-forum-post-revision-html-cache.md) reinforces the same constructor-cache boundary on forum revision HTML records, but this slice applies the pattern to page revision HTML records.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 432. Issue 432 validates direct public `revision.html = ...` assignments and preserves the previous cached value on invalid setter input; this slice validates constructor-seeded `_html` before any public setter is invoked.

This is not a duplicate of Issues 465, 466, or 467. Those slices validate direct `PageRevision` identity, comment, creator, and timestamp fields, and explicitly leave direct `_source` and `_html` constructor cache values as separate cache concerns.

This is not a duplicate of Issue 509. Issue 509 validates the revision-level `PageRevision._source` `PageSource` cache; this slice validates the separate revision-level `PageRevision._html` string cache.

This is not a duplicate of Issue 508. Issue 508 validates `ForumPostRevision._html`; this slice validates `PageRevision._html`.

No upstream issue was filed from this local workspace.

## Changes

- Add optional cached HTML validation for direct `PageRevision(...)` construction.
- Preserve `_html=None` for revisions that should lazily acquire HTML.
- Preserve valid cached HTML strings without coercion.
- Reject booleans, integers, lists, dictionaries, and arbitrary non-string objects using `ValueError("revision.html must be a string")`.
- Add constructor tests for malformed direct `_html` values and valid cached HTML strings.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached page-revision HTML state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevision(_html=...)` must accept `None` and real strings. |
| R2 | `PageRevision(_html=...)` must reject non-`None` non-string values with `ValueError("revision.html must be a string")`. |
| R3 | Valid cached HTML strings must be returned by `revision.html` without triggering revision HTML acquisition. |
| R4 | Valid revision construction, lazy revision HTML acquisition, duplicate cached HTML reuse, public `revision.html = ...` assignment validation, revision collections, `Page.revisions`, revision source behavior, page source behavior, page file/vote behavior, and adjacent page/site workflows must remain unchanged. |
| R5 | This slice must not change revision-list acquisition, revision source acquisition, revision HTML acquisition, response-body diagnostics, parser selectors, page source text validation, request construction, live request behavior, or unrelated constructor fields. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, PageRevision tests, adjacent page workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None` and valid cached HTML strings remain accepted. | `TestPageRevision.test_init_accepts_valid_html_cache` passed before and after validation was added, preserving a valid cached string and returning it through `revision.html`. Existing constructors continue to use `_html=None`. | Rejecting missing cached HTML, triggering HTML lookup during construction, or coercing valid strings rejects this local completion claim. | `PageRevision` constructor cached HTML state | `tests/unit/test_page_revision.py` |
| R2 | Malformed optional cached HTML values fail at the constructor boundary. | `TestPageRevision.test_init_rejects_malformed_html_cache` failed RED for 5 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, integers, lists, dictionaries, arbitrary objects, or silently coercing malformed values rejects this local completion claim. | `PageRevision` constructor cached HTML state | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R3 | Valid cached HTML access remains a cache hit. | The valid-cache test asserts `revision.html == "<p>Cached HTML</p>"`, `revision.is_html_acquired() is True`, and no `amc_request_with_retry` call occurs. | Calling AMC, clearing `_html`, replacing the cached string, or treating a valid string as missing rejects this local completion claim. | `PageRevision.html` cache access | `tests/unit/test_page_revision.py` |
| R4 | Existing page revision and adjacent page workflows remain green. | `tests/unit/test_page_revision.py::TestPageRevision` passed 60 tests, `tests/unit/test_page_revision.py` passed 110 tests, adjacent page/source/revision/file/vote/site tests passed 880 tests, and the full unit suite passed 2278 tests. | Regressing lazy HTML acquisition, duplicate cached HTML reuse, HTML setter validation, revision source behavior, revision collection behavior, page source behavior, page files/votes, site workflows, or parser-created pages rejects this local completion claim. | PageRevision and adjacent page workflows | `tests/unit` |
| R5 | Broader revision semantics remain outside scope. | Existing acquisition, parser, response-body, setter, collection, page, and adjacent tests remain green; this slice only validates direct constructor cache type integrity. | Changing request construction, parser conversion, response diagnostics, revision ordering, source text extraction, HTML handling, page edit behavior, source result behavior, or live request behavior rejects this local completion claim. | PageRevision constructor scope | `src/wikidot/module/page_revision.py`, adjacent tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw page source, raw page HTML, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `00af4d1 fix(page_revision): validate html cache`.

- RED cache tests: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_malformed_html_cache tests/unit/test_page_revision.py::TestPageRevision::test_init_accepts_valid_html_cache -q` failed 5 malformed `_html` cases before the fix with `DID NOT RAISE`, while the valid cached HTML case passed.
- GREEN cache tests: the same focused command passed 6 tests after optional HTML-cache validation was added.
- Constructor/property block: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision -q` passed 60 tests.
- `uv run pytest tests/unit/test_page_revision.py -q` passed 110 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 880 tests.
- `uv run ruff format src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` left both files unchanged.
- `uv run ruff format --check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with 2 files already formatted.
- `uv run ruff check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed.
- `uv run mypy src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2278 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageRevision(_html=None)` remains valid and lazy HTML acquisition remains available.
- `PageRevision(_html="<p>Cached HTML</p>")` remains valid and `revision.html` returns the cached string without a lookup.
- `PageRevision(_html=True)`, `PageRevision(_html=100)`, `PageRevision(_html=["<p>Cached HTML</p>"])`, `PageRevision(_html={"html": "<p>Cached HTML</p>"})`, and `PageRevision(_html=object())` raise `ValueError("revision.html must be a string")` when every other constructor field is valid.
- Existing parser-created revisions, direct revision fixtures, lazy `PageRevision.html`, direct and batched `PageRevisionCollection.get_htmls()`, duplicate cached revision HTML reuse, public `revision.html = ...` assignment validation, `PageRevision.source`, `Page.revisions`, page source behavior, page file/vote behavior, and adjacent page/site workflows remain green.
- The new tests use unit-level code only and do not validate revision HTML contents, revision source contents, parser selectors, live Wikidot, credentials, cookies, auth JSON, private page data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Constructor validation could be confused with revision HTML response validation. Mitigation: the validator checks cache object type only; response content parsing and fetch diagnostics remain outside scope and existing tests stay green.
- Risk: Valid cached HTML strings could accidentally trigger acquisition. Mitigation: the valid-cache test returns the constructor-seeded string, confirms `is_html_acquired()` is true, and asserts no retry request is made.
- Risk: Public setter behavior could diverge from constructor behavior. Mitigation: the constructor reuses the same string validator as the `html` setter for non-`None` values.
