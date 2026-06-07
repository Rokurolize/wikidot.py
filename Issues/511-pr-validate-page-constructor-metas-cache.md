# PR Draft: Validate Page Constructor Metas Cache

## Summary

`Page._metas` is the optional cached `dict[str, str]` behind the public `Page.metas` property. It is populated by lazy meta-tag acquisition, browser-free page inventories, publication metadata ledgers, local fixtures, generated adapters, and serialized or rehydrated page records. Earlier local slices validated meta-tag setter/write inputs, meta fetch retry behavior, meta response diagnostics, nullable page metadata fields, direct page scalar fields, direct page `_source` cache, direct page `_revisions` cache, direct page `_votes` cache, direct page `_files` cache, and page-revision caches, but direct `Page(..., _metas=...)` construction still accepted malformed cached values such as booleans, strings, lists, non-string keys, non-string values, and arbitrary objects.

This change validates the direct constructor's optional metas cache during `Page.__post_init__`. `_metas=None` remains valid for pages that have not acquired meta tags yet, real `dict[str, str]` caches remain valid, and malformed non-null values now raise the same stable diagnostics used by public meta update paths before malformed local cache state can be returned by `page.metas`.

## Outcome

Directly constructed `Page` objects now fail early when optional cached meta state is malformed, while preserving lazy meta acquisition for `_metas=None` and preserving valid preloaded meta dictionaries.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free page inventories, publication metadata ledgers, translation review tooling, local fixtures, generated adapters, or serialized and rehydrated `Page` objects.

## Current Evidence

Meta-related drafts [007-pr-batch-meta-tag-updates.md](007-pr-batch-meta-tag-updates.md), [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [046-pr-retry-page-meta-fetch.md](046-pr-retry-page-meta-fetch.md), [192-pr-page-auxiliary-fetch-site-context.md](192-pr-page-auxiliary-fetch-site-context.md), [219-pr-page-meta-response-body-context.md](219-pr-page-meta-response-body-context.md), [249-pr-preserve-metas-on-failed-set.md](249-pr-preserve-metas-on-failed-set.md), [335-pr-page-meta-response-body-type-context.md](335-pr-page-meta-response-body-type-context.md), and [348-pr-validate-meta-tag-inputs.md](348-pr-validate-meta-tag-inputs.md) establish meta tags as an active operational surface across reads, writes, retries, diagnostics, cache mutation, and input validation.

Constructor and state-integrity drafts [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md) through [489-pr-validate-page-constructor-id-field.md](489-pr-validate-page-constructor-id-field.md), [490-pr-validate-page-constructor-source-field.md](490-pr-validate-page-constructor-source-field.md), [491-pr-validate-page-constructor-revisions-cache.md](491-pr-validate-page-constructor-revisions-cache.md), [492-pr-validate-page-constructor-votes-cache.md](492-pr-validate-page-constructor-votes-cache.md), [493-pr-validate-page-constructor-files-cache.md](493-pr-validate-page-constructor-files-cache.md), [487-pr-validate-page-nullable-metadata.md](487-pr-validate-page-nullable-metadata.md), [509-pr-validate-page-revision-source-cache.md](509-pr-validate-page-revision-source-cache.md), and [510-pr-validate-page-revision-html-cache.md](510-pr-validate-page-revision-html-cache.md) establish the local pattern for validating direct record and cache state instead of relying only on parser-created objects or public setters.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 348. Issue 348 validates public meta input paths such as `Page.metas = ...`, `Page.set_metadata(metas=...)`, and publish metadata input; this slice validates constructor-seeded `_metas` before any setter or write helper is invoked.

This is not a duplicate of Issue 249. Issue 249 preserves the previous `_metas` cache when a meta update action fails; this slice validates the shape of an initial direct constructor cache.

This is not a duplicate of Issues 046, 192, 219, or 335. Those slices cover meta fetch retry, exhausted-fetch context, response-body diagnostics, and response-body type diagnostics; this slice does not change live acquisition or response parsing.

This is not a duplicate of Issue 487. Issue 487 validates nullable page metadata fields such as creator, timestamps, comment, and parent/children state; it does not validate the `_metas` cache dictionary.

This is not a duplicate of Issues 490 through 493. Those slices validate page `_source`, `_revisions`, `_votes`, and `_files` constructor caches; this slice validates the separate page `_metas` cache.

No upstream issue was filed from this local workspace.

## Changes

- Add optional cached meta validation for direct `Page(...)` construction.
- Preserve `_metas=None` for pages that should lazily acquire meta tags.
- Preserve valid `dict[str, str]` meta caches without coercion.
- Reject non-dictionary cache values using `ValueError("metas must be a dictionary")`.
- Reject non-string meta keys using `ValueError("metas keys must be strings")`.
- Reject non-string meta values using `ValueError("metas values must be strings")`.
- Add constructor tests for malformed direct `_metas` values and valid cached meta dictionaries.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached page metadata state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(_metas=...)` must accept `None` and real `dict[str, str]` values. |
| R2 | `Page(_metas=...)` must reject non-`None` non-dictionary values with `ValueError("metas must be a dictionary")`. |
| R3 | `Page(_metas=...)` must reject non-string keys with `ValueError("metas keys must be strings")` and non-string values with `ValueError("metas values must be strings")`. |
| R4 | Valid cached meta dictionaries must be returned by `page.metas` without triggering meta acquisition. |
| R5 | Valid page construction, lazy meta acquisition, public `Page.metas = ...` assignment validation, `Page.set_metadata`, publish metadata handling, page source/revision/file/vote behavior, and adjacent page/site workflows must remain unchanged. |
| R6 | This slice must not change meta fetch request construction, meta response parsing, live request behavior, parser selectors, write-path metadata semantics, nullable page metadata fields, or unrelated constructor fields. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, constructor tests, adjacent page workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None` and valid cached meta dictionaries remain accepted. | `TestPageInit.test_init_accepts_valid_optional_metas` passed before and after validation was added, preserving `_metas=None`, preserving a valid cached dictionary, and returning it through `page.metas`. | Rejecting missing cached metas, coercing a valid dictionary, or changing cached dictionary contents rejects this local completion claim. | `Page` constructor cached metas state | `tests/unit/test_page_constructor.py` |
| R2 | Malformed optional cached meta values fail at the constructor boundary when the cache itself is not a dictionary. | `TestPageInit.test_init_rejects_non_dict_optional_metas` failed RED for 4 malformed non-dictionary values because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, strings, list pairs, arbitrary objects, or silently coercing malformed values rejects this local completion claim. | `Page` constructor cached metas state | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Malformed meta key and value shapes fail at the constructor boundary. | `TestPageInit.test_init_rejects_non_string_optional_meta_keys` failed RED for 2 malformed dictionaries and `TestPageInit.test_init_rejects_non_string_optional_meta_values` failed RED for 3 malformed dictionaries, then both passed GREEN after validation was added. | Accepting non-string keys, accepting non-string values, or silently stringifying keys or values rejects this local completion claim. | `Page` constructor cached metas state | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R4 | Valid cached meta access remains a cache hit. | The valid-cache test asserts `page_with_metas._metas == metas` and `page_with_metas.metas == metas`, while `_metas=None` remains valid for the no-cache case. | Calling meta acquisition for a valid preloaded dictionary, clearing `_metas`, replacing the cached dictionary, or treating a valid dictionary as missing rejects this local completion claim. | `Page.metas` cache access | `tests/unit/test_page_constructor.py` |
| R5 | Existing page and adjacent workflows remain green. | `tests/unit/test_page_constructor.py` passed 147 tests, adjacent page/source/revision/file/vote/site tests passed 890 tests, and the full unit suite passed 2288 tests. | Regressing lazy meta acquisition, public `Page.metas` setter validation, `set_metadata`, publish metadata handling, page source/revision/file/vote behavior, site workflows, or parser-created pages rejects this local completion claim. | Page and adjacent workflows | `tests/unit` |
| R6 | Broader meta read/write semantics remain outside scope. | Existing getter, setter, set_metadata, publish, parser, page, and adjacent tests remain green; this slice only validates direct constructor cache type integrity. | Changing request construction, parser conversion, response diagnostics, meta tag update behavior, source text extraction, page edit behavior, live request behavior, or unrelated constructor fields rejects this local completion claim. | Page constructor scope | `src/wikidot/module/page.py`, adjacent tests |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw page source, raw page HTML, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, constructor tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `0707c96 fix(page): validate metas cache`.

- RED cache tests: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_optional_metas tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_non_dict_optional_metas tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_non_string_optional_meta_keys tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_non_string_optional_meta_values -q` failed 9 malformed `_metas` cases before the fix with `DID NOT RAISE`, while the valid cached metas case passed.
- GREEN cache tests: the same focused command passed 10 tests after optional metas-cache validation was added.
- `uv run pytest tests/unit/test_page_constructor.py -q` passed 147 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 890 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py` left both files unchanged.
- `uv run ruff format --check src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 2 files already formatted.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed.
- `uv run mypy src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2288 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page(_metas=None)` remains valid and lazy meta acquisition remains available.
- `Page(_metas={"description": "cached description", "og:title": "Cached title"})` remains valid and `page.metas` returns the cached dictionary.
- `Page(_metas=True)`, `Page(_metas="cached metas")`, `Page(_metas=[("description", "cached")])`, and `Page(_metas=object())` raise `ValueError("metas must be a dictionary")` when every other constructor field is valid.
- `Page(_metas={3: "description"})` and `Page(_metas={None: "description"})` raise `ValueError("metas keys must be strings")` when every other constructor field is valid.
- `Page(_metas={"description": 3})`, `Page(_metas={"description": None})`, and `Page(_metas={"description": object()})` raise `ValueError("metas values must be strings")` when every other constructor field is valid.
- Existing parser-created pages, direct page fixtures, lazy `Page.metas`, public `Page.metas = ...` assignment validation, `Page.set_metadata`, publish metadata behavior, page source/revision/file/vote behavior, and adjacent page/site workflows remain green.
- The new tests use unit-level code only and do not validate meta response contents, parser selectors, live Wikidot, credentials, cookies, auth JSON, private page data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Constructor validation could be confused with meta fetch response validation. Mitigation: the validator checks cache object shape only; response parsing and fetch diagnostics remain outside scope and existing tests stay green.
- Risk: Valid cached meta dictionaries could accidentally trigger acquisition. Mitigation: the valid-cache test returns the constructor-seeded dictionary through `page.metas`.
- Risk: Public setter behavior could diverge from constructor behavior. Mitigation: the constructor reuses the same `_validate_metas` helper already used by public meta write paths for non-`None` values.
