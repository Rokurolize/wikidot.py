# PR Draft: Validate Page Cache Owner Retained Page ID State

## Summary

`Page` cache-owner validation protects direct cache slots such as `Page._source`, `Page._revisions`, `Page._votes`, and `Page._files`, but the shared ownership helper compared retained target/candidate `page._id` values directly. That left the same retained-state gap as the source-result ownership boundary: booleans and floats could compare equal to integers, while strings, lists, or negative IDs could be misreported as ordinary cache ownership mismatches.

This change validates both retained optional page IDs before the cache-owner comparison. Malformed retained IDs on either the receiving page or the cached owner page now raise `ValueError("page.id must be an integer or None")`, negative retained IDs now raise `ValueError("page.id must be non-negative or None")`, valid loaded cache mismatches still raise the original cache-specific ownership diagnostic such as `ValueError("page.source must belong to the page")`, unloaded IDs still fall back to `fullname`, and zero-ID same-logical-page ownership remains valid.

## Outcome

Direct source-cache construction and assignment can no longer accept corrupted retained page identity or mask corrupted retained IDs as ordinary wrong-page cache ownership state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free source inventories, page source ledgers, duplicate page-detail caches, generated migration records, publication verification reports, local fixtures, adapters, or serialized and rehydrated `Page` objects.

## Current Evidence

Local rollout-backed drafts already established `Page` cache ownership as a practical boundary. [414-pr-validate-page-source-assignments.md](414-pr-validate-page-source-assignments.md), [490-pr-validate-page-constructor-source-field.md](490-pr-validate-page-constructor-source-field.md), [597-pr-validate-page-revisions-cache-ownership.md](597-pr-validate-page-revisions-cache-ownership.md), [598-pr-validate-page-votes-cache-ownership.md](598-pr-validate-page-votes-cache-ownership.md), [599-pr-validate-page-files-cache-ownership.md](599-pr-validate-page-files-cache-ownership.md), and [600-pr-validate-page-source-cache-ownership.md](600-pr-validate-page-source-cache-ownership.md) cover direct source/cache shape and valid-ID wrong-owner checks. [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md), [660-pr-validate-publish-result-retained-page-id-state.md](660-pr-validate-publish-result-retained-page-id-state.md), and [661-pr-validate-source-result-retained-owner-page-id-state.md](661-pr-validate-source-result-retained-owner-page-id-state.md) establish retained-ID validation at adjacent public getter, publish-result, and source-result ownership boundaries.

This slice is not a duplicate of those drafts. Issue 600 validates source cache ownership when retained IDs are already comparable as valid integers or when the fallback fullname differs, but it does not validate malformed retained target/source `Page._id` values inside the shared cache-owner comparison. Issue 658 validates the public `Page.id` getter, but cache-owner validation intentionally uses retained optional IDs so unloaded pages can still fall back to `fullname` without forcing a page-ID lookup. Issues 660 and 661 validate adjacent result objects, not direct `Page` cache slots.

## Related Issue / Non-Duplicate Analysis

Builds directly on [600-pr-validate-page-source-cache-ownership.md](600-pr-validate-page-source-cache-ownership.md), [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md), and [661-pr-validate-source-result-retained-owner-page-id-state.md](661-pr-validate-source-result-retained-owner-page-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained receiving-page and cached-owner `page._id` values before comparing cache owner IDs.
- Reject malformed retained IDs such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("page.id must be an integer or None")`.
- Reject negative retained IDs such as `-1` with `ValueError("page.id must be non-negative or None")`.
- Preserve the cache-specific wrong-owner diagnostics for valid loaded mismatches, including `page.source must belong to the page`.
- Preserve `_source=None`, valid same-page source caches, zero-ID compatibility, unloaded fullname fallback, existing malformed-cache diagnostics, lazy source acquisition, explicit source refresh, duplicate cached source reuse, source iterators, publish verification, and adjacent page workflows.

## Type Of Change

- Input validation
- Retained page-ID hardening
- Cached page source ownership integrity
- Shared page cache-owner validation
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(_source=PageSource(source_page, ...))` must reject malformed retained `source_page._id` values such as `True`, `False`, `"371"`, `371.0`, and `[]` with `ValueError("page.id must be an integer or None")` before source-cache ownership comparison. |
| R2 | `page.source = PageSource(source_page, ...)` must reject malformed retained receiving-page IDs such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with the same diagnostic before replacing the previous source cache. |
| R3 | `page.source = PageSource(source_page, ...)` must reject malformed retained source-page IDs such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with the same diagnostic before replacing the previous source cache. |
| R4 | Constructor and setter paths must reject negative retained receiving-page or source-page IDs such as `-1` with `ValueError("page.id must be non-negative or None")`. |
| R5 | Malformed and negative retained source-cache ownership checks must not call `Page.id`, page-ID lookup, AMC request helpers, or live Wikidot. |
| R6 | Existing same-logical-page ownership, zero IDs, valid wrong-owner diagnostics, malformed source-cache shape diagnostics, lazy source acquisition, source refresh, duplicate cache reuse, source iterators, publish verification, page constructor/property behavior, and adjacent page/source workflows must remain green. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, page constructor/property tests, page/source tests, adjacent workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Constructor source-cache owner IDs fail before ownership comparison. | `test_init_rejects_source_cache_with_malformed_retained_source_page_ids` failed RED for five malformed source-page values: booleans and `371.0` were accepted, while `"371"` and `[]` raised the generic source-cache mismatch; the test passed GREEN after retained source-page ID validation. | Accepting boolean retained source IDs, accepting float equality, coercing strings/lists, or returning the generic ownership diagnostic rejects this local completion claim. | `Page.__post_init__` source-cache validation | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Setter target IDs fail before ownership comparison and cache replacement. | `test_source_setter_rejects_malformed_retained_target_page_ids` failed RED for five malformed receiving-page values with the same accepted or generic-mismatch behavior, then passed GREEN after retained target-page ID validation. | Replacing the previous cache, accepting malformed target IDs, or using Python numeric equality to prove cache ownership rejects this local completion claim. | `Page.source` setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Setter source IDs fail before ownership comparison and cache replacement. | `test_source_setter_rejects_malformed_retained_source_page_ids` failed RED for five malformed source-page values, then passed GREEN after retained source-page ID validation. | Accepting malformed source IDs, coercing them, or surfacing generic wrong-owner diagnostics rejects this local completion claim. | `Page.source` setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Negative retained target/source IDs fail before ownership comparison. | `test_init_rejects_source_cache_with_negative_retained_source_page_id`, `test_source_setter_rejects_negative_retained_target_page_id`, and `test_source_setter_rejects_negative_retained_source_page_id` failed RED with generic mismatch diagnostics, then passed GREEN after retained ID validation. | Accepting negative retained IDs or classifying them as ordinary wrong-page source cache ownership rejects this local completion claim. | Page cache-owner preflight | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py` |
| R5 | Validation remains side-effect-free. | Setter regressions seed a prior valid cache, replace AMC helpers with mocks, and assert no AMC calls; constructor regressions use synthetic `Page` and `PageSource` objects only. | Calling `Page.id`, performing page-ID lookup, mutating retained IDs, clearing a prior valid cache, or performing AMC work rejects this local completion claim. | Page source-cache validation | `tests/unit/test_page.py`, `tests/unit/test_page_constructor.py` |
| R6 | Existing source-cache and adjacent workflows remain green. | Focused GREEN coverage passed 32 tests, `TestPageInit` passed 190 tests, `TestPageProperties` passed 80 tests, direct page constructor/page/page-source coverage passed 565 tests, adjacent page/page-constructor/page-revision/page-file/page-source/page-votes/site coverage passed 1163 tests, and full unit passed 3044 tests. | Regressing valid source caches, zero IDs, wrong-owner diagnostics, malformed source shape diagnostics, lazy source acquisition, source refresh, duplicate cache reuse, page revisions/votes/files, site accessors, or any unit test rejects this local completion claim. | Page cache and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_page_source.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic objects only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `24ace2a fix(page): validate cache owner retained page ids`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_optional_source tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_optional_source tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_source_cache_from_different_page tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_source_cache_with_malformed_retained_source_page_ids tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_source_cache_with_negative_retained_source_page_id tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_source_cache_with_zero_retained_page_ids tests/unit/test_page.py::TestPageProperties::test_source_setter_rejects_invalid_sources tests/unit/test_page.py::TestPageProperties::test_source_setter_rejects_source_from_different_page tests/unit/test_page.py::TestPageProperties::test_source_setter_rejects_malformed_retained_target_page_ids tests/unit/test_page.py::TestPageProperties::test_source_setter_rejects_negative_retained_target_page_id tests/unit/test_page.py::TestPageProperties::test_source_setter_rejects_malformed_retained_source_page_ids tests/unit/test_page.py::TestPageProperties::test_source_setter_rejects_negative_retained_source_page_id tests/unit/test_page.py::TestPageProperties::test_source_setter_accepts_zero_retained_page_ids -q` failed 18 retained source-cache owner cases before the fix; 14 source-cache shape, wrong-owner, and zero-ID guards passed.
- GREEN: the same focused command passed 32 tests after validating retained target/source page IDs before cache-owner comparison.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py tests/unit/test_page.py` left 3 files unchanged.
- `uv run pytest tests/unit/test_page_constructor.py::TestPageInit -q` passed 190 tests.
- `uv run pytest tests/unit/test_page.py::TestPageProperties -q` passed 80 tests.
- `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_source.py -q` passed 565 tests.
- `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_source.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1163 tests.
- `uv run pytest tests/unit -q` passed 3044 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page(_source=PageSource(source_page, ...))` raises `ValueError("page.id must be an integer or None")` when the retained source-page `_id` is `True`, `False`, `"371"`, `371.0`, or `[]`.
- The same constructor raises `ValueError("page.id must be non-negative or None")` when the retained source-page `_id` is `-1`.
- `page.source = PageSource(source_page, ...)` raises `ValueError("page.id must be an integer or None")` when either the receiving page or the source page has retained `_id` values such as `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- The setter raises `ValueError("page.id must be non-negative or None")` when either retained `_id` value is `-1`.
- Malformed and negative retained source-cache ownership checks do not call `PageCollection.get_page_ids()`, AMC helpers, or live Wikidot, and failed setter attempts preserve the previous valid cache.
- Same-logical-page source wrappers with both retained IDs equal to `0` remain valid.
- Valid loaded cross-page source wrappers still raise `ValueError("page.source must belong to the page")`.
- Existing `_source=None`, malformed `_source` object rejection, malformed `page.source` assignment rejection, lazy source acquisition, explicit source refresh, duplicate cached source reuse, source iterator behavior, publish verification, page constructor/property behavior, and adjacent page/source workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page` cache-owner validation is a side-effect-free integrity boundary for preloaded caches, generated fixtures, duplicate cache reuse, and rehydrated page records. It should not call `Page.id`, but it also should not use corrupted retained page identity to prove ownership. Validating retained optional IDs before comparison preserves unloaded fullname fallback while making impossible retained page identity fail deterministically.

## Local Evidence

- Existing local drafts covered source acquisition, parser diagnostics, response diagnostics, optional `_source` cache shape, public source assignment shape, wrong-owner source-cache rejection for plausible IDs, adjacent page detail cache ownership, public retained `Page.id` getter validation, and source-result retained owner validation.
- None of those drafts covered malformed retained target/source `page._id` values inside the shared `Page` cache-owner helper because that helper bypasses `Page.id` to preserve unloaded-page fallback behavior.
- The focused RED failure showed booleans and floats could be accepted as retained owner IDs when they compared equal to explicit integers, while strings, lists, and negative IDs could be misreported as ordinary source-cache ownership mismatches. The GREEN regressions cover malformed rejection on both sides, negative rejection on both sides, no lazy lookup, no AMC work, prior-cache preservation, zero-ID compatibility, valid same-logical-page compatibility, valid cross-page mismatch diagnostics, and adjacent page workflows.
- This slice only validates retained optional page IDs at the shared `Page` cache-owner boundary. It does not change `Page.id`, page-ID acquisition URLs, source fetching, source parsing, source text validation, page writes, publish result behavior, source-result behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates the retained optional IDs instead of calling `Page.id`. Unloaded cache ownership checks still fall back to `fullname`, which preserves the previous same-logical-page reconstruction behavior without introducing network lookup.
