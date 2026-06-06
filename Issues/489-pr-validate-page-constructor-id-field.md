# PR Draft: Validate Page Constructor ID Field

## Summary

`Page._id` is the optional cached Wikidot page identifier used by `Page.id`, `Page.is_id_acquired()`, source/revision/file/vote acquisition, discussion lookup, metadata actions, publish ledgers, and generated page inventories. Public `Page.id = ...` assignment already validates required non-boolean integer IDs, and `Page.create_or_edit(..., page_id=...)` already validates write-path optional page IDs, but the dataclass constructor still accepted direct malformed `_id` values such as booleans, strings, floats, lists, and arbitrary objects.

This change validates the direct constructor's optional page-ID cache during `Page.__post_init__`. `_id=None` remains valid for pages that have not acquired an ID yet, non-boolean integers remain valid for fixtures and rehydrated page records, and malformed values now raise `ValueError("page.id must be an integer or None")` before they can poison cached-ID state.

## Outcome

Directly constructed `Page` objects now fail early when optional cached page-ID state is malformed, while preserving lazy page-ID acquisition for `_id=None` and preserving valid preloaded integer IDs.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free page inventories, source/revision/file/vote workflows, publish ledgers, local fixtures, or serialized and rehydrated `Page` objects.

## Current Evidence

[412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md) validates caller-provided `Page.create_or_edit(..., page_id=...)` values before write-side requests. [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md) validates public `Page.id = ...` assignment before mutating `_id`. [435-pr-validate-publish-result-page-ids.md](435-pr-validate-publish-result-page-ids.md) validates `PagePublishResult.page_id`. [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md) validates collection entries before page-ID acquisition work. Recent direct `Page` constructor slices validate identity, counts, rating, parent fullname, tags, site, nullable metadata, and rating-percent fields.

Those prior slices are not duplicates. Issue 412 covers a write-path argument named `page_id`, not stored page cache state. Issue 413 covers post-construction assignment through the public `Page.id` setter, not direct dataclass initialization. Issue 435 covers publish result rows, not `Page` instances. Issue 368 covers collection entry object shape, not the ID cache inside a valid `Page`. Issues 481 through 488 validate other direct `Page` constructor fields only. None validates direct `Page(_id=...)` construction before malformed cached-ID state is stored.

## Related Issue / Non-Duplicate Analysis

Builds directly on [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), [435-pr-validate-publish-result-page-ids.md](435-pr-validate-publish-result-page-ids.md), [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md), and the direct `Page` constructor hardening in [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md) through [488-pr-validate-page-constructor-rating-percent.md](488-pr-validate-page-constructor-rating-percent.md).

No upstream issue was filed from this local workspace.

## Changes

- Add optional cached page-ID validation for direct `Page(...)` construction.
- Preserve `_id=None` for pages that should lazily acquire their page ID.
- Preserve valid non-boolean integer `_id` values without coercion.
- Reject booleans and non-integer values with a stable `ValueError` diagnostic.
- Add constructor tests for valid optional IDs and malformed direct `_id` values.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached page-ID state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(_id=...)` must accept `None` and non-boolean integers. |
| R2 | `Page(_id=...)` must reject booleans and non-integer values with `ValueError("page.id must be an integer or None")`. |
| R3 | Valid page construction, lazy ID acquisition, public `Page.id` assignment validation, create/edit `page_id` validation, parser-created pages, and page source/revision/file/vote workflows must remain unchanged. |
| R4 | This slice must not validate page-ID range semantics, URL construction, page-ID parsing, create/edit write behavior, publish result rows, collection entry shape, cached source/revisions/votes/files, live request behavior, or unrelated constructor fields. |
| R5 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, constructor tests, adjacent page/site/page-file/page-vote/page-revision tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None` and valid integer cached page IDs remain accepted. | `TestPageInit.test_init_accepts_valid_optional_id` passed RED and GREEN for `_id=None` and `_id=12345`. | Rejecting missing cached IDs, triggering lazy lookup during construction, or coercing valid integer IDs rejects this local completion claim. | `Page` constructor cached-ID state | `tests/unit/test_page_constructor.py` |
| R2 | Malformed optional cached page IDs fail at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_optional_id` failed RED for 6 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, strings, floats, lists, arbitrary objects, or silently coercing malformed values rejects this local completion claim. | `Page` constructor cached-ID state | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Existing page workflows remain green. | Constructor tests passed 111 tests; adjacent page/site/page-file/page-vote/page-revision tests passed 835 tests; full unit tests passed 2093 tests. | Regressing lazy ID acquisition, `Page.id` assignment validation, create/edit ID validation, parser-created pages, page collection behavior, page source/revision/file/vote workflows, or site workflows rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_page_revision.py`, `tests/unit` |
| R4 | Broader page-ID and parser semantics remain outside scope. | Existing page-ID, parser, create/edit, publish, and adjacent tests remain green; this slice only validates direct constructor cache type integrity. | Adding range checks, changing lazy acquisition, changing request construction, changing parser conversion, or touching live request behavior rejects this local completion claim. | Page constructor scope | `src/wikidot/module/page.py`, adjacent tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `553fc50 fix(page): validate constructor page id`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_optional_id tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_optional_id -q` failed 6 malformed `_id` cases before the fix with `DID NOT RAISE`, while the 2 valid cases passed.
- GREEN: the same focused command passed 8 tests after optional cached page-ID validation was added.
- `uv run pytest tests/unit/test_page_constructor.py -q` passed 111 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_page_revision.py tests/unit/test_page_constructor.py -q` passed 835 tests.
- `uv run pytest tests/unit -q` passed 2093 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 44 existing full-tree test typing errors outside this slice, including intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client/mock typing, invalid test cookie arguments, and existing site test mock typing issues. The changed source file and touched test module pass pyright together.

## Acceptance Criteria

- `Page(_id=None)` remains valid, `page.is_id_acquired()` remains false, and lazy ID acquisition remains available.
- `Page(_id=12345)` remains valid, `page.is_id_acquired()` is true, and `page.id` returns `12345` without a lookup.
- `Page(_id=True)`, `Page(_id=False)`, `Page(_id="12345")`, `Page(_id=12345.0)`, `Page(_id=[])`, and `Page(_id=object())` raise `ValueError("page.id must be an integer or None")` when every other constructor field is valid.
- Existing parser-created pages, direct page fixtures, page collection behavior, page lookup behavior, `Page.id` setter validation, create/edit `page_id` validation, page source/revision/file/vote workflows, and site workflows remain green.
- The new tests use unit-level code only and do not validate page-ID range semantics, URL construction, live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Cached page IDs are shared by many later read and write workflows. Direct construction is useful for fixtures and rehydrated records, but malformed cached IDs should fail at construction instead of making a `Page` appear ID-acquired with unusable state.

## Local Evidence

- Local rollout evidence used page IDs in browser-free page inventories, source/revision/file/vote workflows, publish ledgers, and generated audit records.
- Existing local drafts covered lazy ID diagnostics, direct page-ID assignment, create/edit `page_id` validation, publish-result page IDs, and collection entry validation, but did not cover direct optional cached-ID construction.
- Existing unit fixtures already relied on `_id=None` being valid for lazy page-ID acquisition and integer `_id` being valid for preloaded page records, so this change validates only malformed values.
- This slice does not change parser extraction, page write behavior, collection inference behavior, query serialization, page ID/source/revision/file/vote acquisition logic, source/revision/vote/file cache semantics, live Wikidot behavior, site client internals, URL syntax validation, or unrelated constructor fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The validator rejects booleans even though `bool` is a subclass of `int`. It does not add range checks because this slice is about constructor cache-state type integrity, not remote Wikidot page-ID semantics.
