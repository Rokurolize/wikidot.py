# PR Draft: Validate Page Revision Source Cache Retained Page ID State

## Summary

`PageRevision.source` cache ownership validates that a retained `PageSource` belongs to the revision's `Page`, but the ownership check compared retained revision-page and source-page `page._id` values directly. That left the same retained-state gap as the `Page` cache-owner and source-result ownership boundaries: booleans and floats could compare equal to integers, while strings, lists, or negative IDs could be misreported as ordinary revision/source ownership mismatches.

This change validates both retained optional page IDs before the `PageRevision` source-cache ownership comparison. Malformed retained IDs on either the revision page or the source page now raise `ValueError("page.id must be an integer or None")`, negative retained IDs now raise `ValueError("page.id must be non-negative or None")`, valid loaded wrong-owner source caches still raise `ValueError("revision.source must belong to the revision page")`, unloaded IDs still fall back to `fullname`, and zero-ID same-logical-page ownership remains valid.

## Outcome

Direct `PageRevision(_source=...)` construction and `revision.source = ...` assignment can no longer accept corrupted retained page identity or mask corrupted retained IDs as ordinary wrong-page revision source-cache ownership state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free revision source inventories, historical source ledgers, duplicate revision-source caches, generated migration records, publication verification reports, local fixtures, adapters, or serialized and rehydrated `PageRevision` objects.

## Current Evidence

Local rollout-backed drafts already established `PageRevision.source` cache ownership as a practical boundary. [431-pr-validate-page-revision-source-assignments.md](431-pr-validate-page-revision-source-assignments.md), [509-pr-validate-page-revision-source-cache.md](509-pr-validate-page-revision-source-cache.md), [601-pr-validate-page-revision-source-cache-ownership.md](601-pr-validate-page-revision-source-cache-ownership.md), [430-pr-validate-page-source-wiki-text.md](430-pr-validate-page-source-wiki-text.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), and [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md) cover source assignment shape, constructor cache shape, valid-ID wrong-owner checks, source text shape, and duplicate cached revision source reuse. [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md), [661-pr-validate-source-result-retained-owner-page-id-state.md](661-pr-validate-source-result-retained-owner-page-id-state.md), and [662-pr-validate-page-cache-owner-retained-page-id-state.md](662-pr-validate-page-cache-owner-retained-page-id-state.md) establish retained-ID validation at adjacent public getter, source-result, and page cache-owner boundaries.

This slice is not a duplicate of those drafts. Issue 601 validates `PageRevision` source-cache ownership when retained IDs are already comparable as valid integers or when the fallback fullname differs, but it does not validate malformed retained revision/source `Page._id` values inside the ownership comparison. Issue 658 validates the public `Page.id` getter, but revision source-cache validation intentionally uses retained optional IDs so unloaded pages can still fall back to `fullname` without forcing a page-ID lookup. Issues 661 and 662 validate adjacent result and `Page` cache-owner objects, not direct `PageRevision.source` cache slots.

## Related Issue / Non-Duplicate Analysis

Builds directly on [601-pr-validate-page-revision-source-cache-ownership.md](601-pr-validate-page-revision-source-cache-ownership.md), [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md), [661-pr-validate-source-result-retained-owner-page-id-state.md](661-pr-validate-source-result-retained-owner-page-id-state.md), and [662-pr-validate-page-cache-owner-retained-page-id-state.md](662-pr-validate-page-cache-owner-retained-page-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained revision-page and source-page `page._id` values before comparing `PageRevision.source` cache owner IDs.
- Reject malformed retained IDs such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("page.id must be an integer or None")`.
- Reject negative retained IDs such as `-1` with `ValueError("page.id must be non-negative or None")`.
- Preserve the original wrong-owner diagnostic for valid loaded mismatches: `revision.source must belong to the revision page`.
- Preserve `_source=None`, valid same-page source caches, zero-ID compatibility, unloaded fullname fallback, existing malformed-cache diagnostics, lazy revision source acquisition, duplicate cached revision source reuse, revision HTML behavior, page source behavior, and adjacent page workflows.

## Type Of Change

- Input validation
- Retained page-ID hardening
- Cached page revision source ownership integrity
- Public dataclass constructor behavior hardening
- Public property setter behavior hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevision(_source=PageSource(source_page, ...))` must reject malformed retained `source_page._id` values such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("page.id must be an integer or None")` before source-cache ownership comparison. |
| R2 | `revision.source = PageSource(source_page, ...)` must reject malformed retained revision-page IDs such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with the same diagnostic before replacing the previous source cache. |
| R3 | `revision.source = PageSource(source_page, ...)` must reject malformed retained source-page IDs such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with the same diagnostic before replacing the previous source cache. |
| R4 | Constructor and setter paths must reject negative retained revision-page or source-page IDs such as `-1` with `ValueError("page.id must be non-negative or None")`. |
| R5 | Malformed and negative retained source-cache ownership checks must not call `Page.id`, page-ID lookup, AMC request helpers, or live Wikidot. |
| R6 | Existing same-logical-page ownership, zero IDs, valid wrong-owner diagnostics, malformed source-cache shape diagnostics, lazy revision source acquisition, duplicate cached revision source reuse, revision HTML behavior, page source behavior, and adjacent page/source workflows must remain green. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, PageRevision class/module tests, direct revision/source tests, adjacent workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Constructor source-cache owner IDs fail before ownership comparison. | `test_init_rejects_source_cache_with_malformed_retained_source_page_ids` failed RED for five malformed source-page values: booleans and `12345.0` were accepted, while `"12345"` and `[]` raised the generic revision source ownership mismatch; the test passed GREEN after retained source-page ID validation. | Accepting boolean retained source IDs, accepting float equality, coercing strings/lists, or returning the generic ownership diagnostic rejects this local completion claim. | `PageRevision.__post_init__` source-cache validation | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Setter target IDs fail before ownership comparison and cache replacement. | `test_source_setter_rejects_malformed_retained_target_page_ids` failed RED for five malformed receiving-page values with the same accepted or generic-mismatch behavior, then passed GREEN after retained target-page ID validation. | Replacing the previous cache, accepting malformed target IDs, or using Python numeric equality to prove revision source ownership rejects this local completion claim. | `PageRevision.source` setter | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R3 | Setter source IDs fail before ownership comparison and cache replacement. | `test_source_setter_rejects_malformed_retained_source_page_ids` failed RED for five malformed source-page values, then passed GREEN after retained source-page ID validation. | Accepting malformed source IDs, coercing them, or surfacing generic wrong-owner diagnostics rejects this local completion claim. | `PageRevision.source` setter | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R4 | Negative retained target/source IDs fail before ownership comparison. | `test_init_rejects_source_cache_with_negative_retained_source_page_id`, `test_source_setter_rejects_negative_retained_target_page_id`, and `test_source_setter_rejects_negative_retained_source_page_id` failed RED with accepted or generic mismatch behavior, then passed GREEN after retained ID validation. | Accepting negative retained IDs or classifying them as ordinary wrong-page revision source cache ownership rejects this local completion claim. | PageRevision source-cache preflight | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R5 | Validation remains side-effect-free. | Setter regressions seed a prior valid cache, use mock AMC helpers, and assert no AMC calls; constructor regressions use synthetic `Page`, `PageRevision`, and `PageSource` objects only. | Calling `Page.id`, performing page-ID lookup, mutating retained IDs, clearing a prior valid cache, or performing AMC work rejects this local completion claim. | Revision source-cache validation | `tests/unit/test_page_revision.py` |
| R6 | Existing source-cache and adjacent workflows remain green. | Focused GREEN coverage passed 28 tests, `TestPageRevision` passed 88 tests, full PageRevision coverage passed 140 tests, direct revision/source coverage passed 146 tests, adjacent page/page-constructor/page-revision/page-file/page-source/page-votes/site coverage passed 1183 tests, and full unit passed 3064 tests. | Regressing valid revision source caches, zero IDs, wrong-owner diagnostics, malformed source shape diagnostics, lazy revision source acquisition, duplicate cached revision source reuse, revision HTML, page source behavior, site accessors, or any unit test rejects this local completion claim. | Page revision cache and adjacent workflows | `tests/unit/test_page_revision.py`, `tests/unit/test_page_source.py`, `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic objects only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `e61765d fix(page_revision): validate source cache retained page ids`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_init_accepts_valid_source_cache tests/unit/test_page_revision.py::TestPageRevision::test_init_accepts_source_cache_from_same_logical_page tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_source_cache_from_different_page tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_source_cache_with_malformed_retained_source_page_ids tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_source_cache_with_negative_retained_source_page_id tests/unit/test_page_revision.py::TestPageRevision::test_init_accepts_source_cache_with_zero_retained_page_ids tests/unit/test_page_revision.py::TestPageRevision::test_source_setter_rejects_invalid_sources tests/unit/test_page_revision.py::TestPageRevision::test_source_setter_rejects_source_from_different_page tests/unit/test_page_revision.py::TestPageRevision::test_source_setter_rejects_malformed_retained_target_page_ids tests/unit/test_page_revision.py::TestPageRevision::test_source_setter_rejects_negative_retained_target_page_id tests/unit/test_page_revision.py::TestPageRevision::test_source_setter_rejects_malformed_retained_source_page_ids tests/unit/test_page_revision.py::TestPageRevision::test_source_setter_rejects_negative_retained_source_page_id tests/unit/test_page_revision.py::TestPageRevision::test_source_setter_accepts_zero_retained_page_ids -q` failed 18 retained revision source-cache owner cases before the fix; 10 source-cache shape, wrong-owner, and zero-ID guards passed.
- GREEN: the same focused command passed 28 tests after validating retained target/source page IDs before `PageRevision.source` ownership comparison.
- `uv run ruff format src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_page_revision.py::TestPageRevision -q` passed 88 tests.
- `uv run pytest tests/unit/test_page_revision.py -q` passed 140 tests.
- `uv run pytest tests/unit/test_page_revision.py tests/unit/test_page_source.py -q` passed 146 tests.
- `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_source.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1183 tests.
- `uv run pytest tests/unit -q` passed 3064 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageRevision(_source=PageSource(source_page, ...))` raises `ValueError("page.id must be an integer or None")` when the retained source-page `_id` is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- The same constructor raises `ValueError("page.id must be non-negative or None")` when the retained source-page `_id` is `-1`.
- `revision.source = PageSource(source_page, ...)` raises `ValueError("page.id must be an integer or None")` when either the receiving revision page or the source page has retained `_id` values such as `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- The setter raises `ValueError("page.id must be non-negative or None")` when either retained `_id` value is `-1`.
- Malformed and negative retained revision source-cache ownership checks do not call `PageCollection.get_page_ids()`, AMC helpers, or live Wikidot, and failed setter attempts preserve the previous valid cache.
- Same-logical-page source wrappers with both retained IDs equal to `0` remain valid.
- Valid loaded cross-page source wrappers still raise `ValueError("revision.source must belong to the revision page")`.
- Existing `_source=None`, malformed `_source` object rejection, malformed `revision.source` assignment rejection, lazy revision source acquisition, duplicate cached revision source reuse, revision HTML behavior, page source behavior, and adjacent page/source workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageRevision.source` cache ownership is a side-effect-free integrity boundary for preloaded revision source caches, duplicate cache reuse, historical source ledgers, generated fixtures, and rehydrated revision records. It should not call `Page.id`, but it also should not use corrupted retained page identity to prove ownership. Validating retained optional IDs before comparison preserves unloaded fullname fallback while making impossible retained page identity fail deterministically.

## Local Evidence

- Existing local drafts covered revision source acquisition, parser diagnostics, response diagnostics, optional `_source` cache shape, public source assignment shape, wrong-owner revision source-cache rejection for plausible IDs, public retained `Page.id` getter validation, source-result retained owner validation, and page cache-owner retained ID validation.
- None of those drafts covered malformed retained target/source `page._id` values inside the `PageRevision.source` ownership helper because that helper bypasses `Page.id` to preserve unloaded-page fallback behavior.
- The focused RED failure showed booleans and floats could be accepted as retained owner IDs when they compared equal to explicit integers, while strings, lists, and negative IDs could be misreported as ordinary revision source-cache ownership mismatches. The GREEN regressions cover malformed rejection on both sides, negative rejection on both sides, no lazy lookup, no AMC work, prior-cache preservation, zero-ID compatibility, valid same-logical-page compatibility, valid cross-page mismatch diagnostics, and adjacent page workflows.
- This slice only validates retained optional page IDs at the `PageRevision.source` cache-owner boundary. It does not change `Page.id`, page-ID acquisition URLs, revision source fetching, source parsing, source text validation, revision HTML behavior, page source behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates retained optional IDs instead of calling `Page.id`. Unloaded revision source-cache ownership checks still fall back to `fullname`, which preserves the previous same-logical-page reconstruction behavior without introducing network lookup.
