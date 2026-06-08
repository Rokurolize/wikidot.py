# PR Draft: Validate Retained Page ID Getter State

## Summary

`Page.id` already validates direct constructor IDs, public setter values, and page IDs returned through acquisition paths, but the public getter returned any retained non-`None` `_id` value without revalidating it. A corrupted or rehydrated `Page` object could therefore expose malformed cached IDs such as `True`, `"12345"`, `12345.0`, `[]`, or `-1` through `page.id`, and downstream page-detail, revision, vote, file, source, publish, and ledger code would observe that malformed identity as if it were valid.

This change reuses the existing `_validate_page_id(...)` validator at the final `Page.id` return boundary. Malformed retained values now raise `ValueError("page.id must be an integer")`, negative retained values raise `ValueError("page.id must be non-negative")`, valid cached IDs including `0` remain accepted, and the lazy page-ID lookup path remains responsible only for the missing-`None` state.

## Outcome

The public `Page.id` getter now enforces the same ID type and non-negative range invariant for retained state that constructor and setter paths already enforce, without adding a new acquisition call for malformed non-`None` cache values and without changing valid page-ID acquisition behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Page.id`, `PageCollection.get_page_ids()`, page source/revision/vote/file/detail acquisition, browser-free publishing helpers, source-result and publish-result ledgers, migration scripts, serialized page objects, or test fixtures that may reconstruct `Page` state from stored data.

## Current Evidence

Local rollout-backed drafts repeatedly establish page identity as a shared boundary. Existing drafts cover page-ID lookup batching and deduplication ([002-pr-batch-source-page-id-lookups.md](002-pr-batch-source-page-id-lookups.md), [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md), [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [132-pr-reuse-cached-duplicate-page-ids.md](132-pr-reuse-cached-duplicate-page-ids.md)), page-ID diagnostics ([186-pr-page-id-response-type-context.md](186-pr-page-id-response-type-context.md), [187-pr-page-id-property-context.md](187-pr-page-id-property-context.md), [197-pr-page-id-site-context.md](197-pr-page-id-site-context.md)), source and publish ledgers that expose page or site identity ([069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [603-pr-validate-publish-result-page-id-coherence.md](603-pr-validate-publish-result-page-id-coherence.md), [651-pr-validate-non-negative-publish-result-page-ids.md](651-pr-validate-non-negative-publish-result-page-ids.md)), and Page ID input validation ([413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), [489-pr-validate-page-constructor-id-field.md](489-pr-validate-page-constructor-id-field.md), [639-pr-validate-non-negative-page-ids.md](639-pr-validate-non-negative-page-ids.md)).

This slice is not a duplicate of those drafts. Issue 413 validates the public setter, Issue 489 validates constructor `_id` type state, and Issue 639 validates non-negative values for constructor, setter, and create/edit page IDs. None of those slices revalidated retained `_id` at the public getter boundary after object state had already been accepted or corrupted.

## Related Issue / Non-Duplicate Analysis

Builds directly on [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), [489-pr-validate-page-constructor-id-field.md](489-pr-validate-page-constructor-id-field.md), [603-pr-validate-publish-result-page-id-coherence.md](603-pr-validate-publish-result-page-id-coherence.md), [639-pr-validate-non-negative-page-ids.md](639-pr-validate-non-negative-page-ids.md), and [651-pr-validate-non-negative-publish-result-page-ids.md](651-pr-validate-non-negative-publish-result-page-ids.md).

No upstream issue was filed from this local workspace.

## Changes

- Revalidate non-`None` retained `_id` in the public `Page.id` getter with the existing `_validate_page_id(...)` helper before returning it.
- Reject malformed cached values such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with the existing integer diagnostic.
- Reject negative cached values such as `-1` with the existing non-negative diagnostic.
- Preserve valid retained IDs, including `0`, and preserve the lazy lookup path for `_id is None`.
- Preserve the existing behavior that malformed non-`None` retained cache state does not trigger a network lookup through `PageCollection.get_page_ids()`.

## Type Of Change

- Input validation
- Public property behavior hardening
- Retained state integrity
- Page identity ledger safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `page.id` must reject retained malformed cached IDs such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("page.id must be an integer")`. |
| R2 | `page.id` must reject retained negative cached IDs such as `-1` with `ValueError("page.id must be non-negative")`. |
| R3 | Malformed or negative non-`None` retained cache values must not trigger `PageCollection.get_page_ids()`. |
| R4 | Existing valid retained IDs, `id` setter validation, zero-ID compatibility, and the lazy missing-ID path must remain unchanged. |
| R5 | Existing page source, revision, vote, file, constructor, site, and adjacent unit workflows must remain green. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, page-property tests, acquisition tests, page tests, adjacent workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained cached IDs fail at the public getter boundary. | `test_id_property_rejects_malformed_cached_ids` failed RED for five malformed values with `DID NOT RAISE`, then passed GREEN after the getter return used `_validate_page_id(...)`. | Returning malformed values, coercing strings/floats, accepting booleans as integers, or changing the diagnostic rejects this local completion claim. | `Page.id` getter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Negative retained cached IDs fail at the public getter boundary. | `test_id_property_rejects_negative_cached_id` failed RED for `-1` with `DID NOT RAISE`, then passed GREEN after the getter revalidation. | Returning negative IDs, coercing them to `0`, or raising the malformed-type diagnostic for integer negatives rejects this local completion claim. | `Page.id` getter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | A malformed non-`None` retained cache is treated as invalid local state, not as a missing ID to reacquire. | The new tests patch `PageCollection.get_page_ids` and assert it is not called for malformed and negative cached IDs. | Calling page-ID lookup for corrupted retained non-`None` state rejects this local completion claim because it hides the local state error and may perform avoidable network work. | Getter control flow | `tests/unit/test_page.py` |
| R4 | Existing public `Page.id` semantics remain stable for valid and missing states. | The focused GREEN command passed `test_id_property_acquired`, setter malformed/range/zero tests, and `test_id_property_includes_page_context_when_acquire_leaves_id_missing`; `TestPageProperties` passed 67 tests. | Regressing valid cached IDs, zero-ID compatibility, setter diagnostics, or the missing-ID `NotFoundException` context rejects this local completion claim. | Page property API | `tests/unit/test_page.py` |
| R5 | Existing adjacent workflows remain green. | `TestPageCollectionAcquire` passed 66 tests, `tests/unit/test_page.py` passed 356 tests, adjacent page/site/file/vote/revision/constructor suites passed 1111 tests, and full unit passed 2998 tests. | Regressing page source, revision, vote, file, constructor, site, collection, batching, deduplication, parser, publish, or any unit workflow rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_constructor.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All tests use synthetic page objects and mocked lookup methods only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d4701c2 fix(page): validate retained page ids`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_id_property_acquired tests/unit/test_page.py::TestPageProperties::test_id_property_rejects_malformed_cached_ids tests/unit/test_page.py::TestPageProperties::test_id_property_rejects_negative_cached_id tests/unit/test_page.py::TestPageProperties::test_id_setter_rejects_invalid_ids tests/unit/test_page.py::TestPageProperties::test_id_setter_rejects_negative_ids tests/unit/test_page.py::TestPageProperties::test_id_setter_accepts_zero_id tests/unit/test_page.py::TestPageProperties::test_id_property_includes_page_context_when_acquire_leaves_id_missing -q` failed 6 retained-cache getter cases before the fix; 9 valid getter, setter, zero-ID, and lazy-missing guards passed.
- GREEN: the same focused command passed 15 tests after returning `_validate_page_id(self._id)` from the getter.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_page.py::TestPageProperties -q` passed 67 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 66 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 356 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_page_revision.py tests/unit/test_page_constructor.py -q` passed 1111 tests.
- `uv run pytest tests/unit -q` passed 2998 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `page.id` raises `ValueError("page.id must be an integer")` when retained `_id` is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- `page.id` raises `ValueError("page.id must be non-negative")` when retained `_id` is `-1`.
- `page.id` does not call `PageCollection.get_page_ids()` for malformed or negative non-`None` retained cache state.
- Valid retained IDs still return normally, including `0`.
- The public setter still validates malformed and negative values with the existing diagnostics.
- Missing `_id is None` still follows the existing lazy lookup and missing-ID error path with site/page context.
- Existing page source, revision, vote, file, constructor, site, and adjacent workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page.id` is a central identity boundary for page detail requests, collection grouping, source/revision/vote/file acquisition, source-result ledgers, publish-result ledgers, and migration or audit tooling. The constructor and setter already reject malformed and negative IDs, but the getter could still leak corrupted retained state after reconstruction or direct mutation. Revalidating at the public getter boundary keeps downstream workflows from building request payloads or ledgers around an invalid page identity.

## Local Evidence

- Existing local drafts covered page-ID request batching, duplicate page-ID reuse, parser/request diagnostics, page-ID setter validation, constructor page-ID validation, non-negative page IDs, source-result page-ID ledgers, publish-result page-ID coherence, and non-negative publish-result page IDs.
- None of those drafts covered the getter-time retained-state gap where a non-`None` `_id` already present on the object bypassed the existing validator and was returned directly.
- The focused RED failure showed malformed and negative retained `_id` values were accepted through the public `Page.id` getter. The GREEN regressions cover malformed rejection, negative rejection, no lazy lookup for corrupted non-`None` cache state, valid cached-ID compatibility, setter compatibility, zero-ID compatibility, missing-ID lazy lookup behavior, and adjacent page workflows.
- This slice only validates retained `Page.id` getter state. It does not change page-ID fetch URLs, batch grouping, deduplication, source/revision/vote/file request construction, constructor validation, setter validation, create/edit page-ID handling, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally uses the existing `_validate_page_id(...)` helper rather than adding a second validator or a getter-specific diagnostic. That keeps constructor, setter, and getter range/type semantics aligned while preserving the existing missing-ID acquisition branch.
