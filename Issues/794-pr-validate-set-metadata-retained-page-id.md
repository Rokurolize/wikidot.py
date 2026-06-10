# PR Draft: Validate Set Metadata Retained Page ID

## Summary

`Page.set_metadata()` already validates tag, parent, meta payload, retained `page.site`, returned metadata action status, malformed status types, and local state update ordering. One retained identity field still crossed the batched metadata authentication boundary late: if a valid `Page` was later mutated, fixture-loaded, or rehydrated with a malformed or negative cached `_id`, `set_metadata(...)` called `login_check()` before the retained page-ID error surfaced through `self.id`.

This change validates a present retained `_id` with `_validate_retained_page_id(self)` after explicit metadata input validation and site validation and before login checks, batched AMC request construction, response handling, or local tags/parent/metas mutation. Missing `_id is None` still preserves lazy lookup after login, and meta-only calls only acquire a missing ID when a meta request body is actually needed.

## Outcome

Batched page metadata updates can no longer authenticate or build `saveTags`, `setParentPage`, `deleteMetaTag`, or `saveMetaTag` request work through corrupted retained page-ID state. Valid loaded page IDs still produce the same `pageId`/`page_id` payloads, unloaded pages still acquire IDs after authentication when a request needs them, and the all-arguments-omitted no-op still avoids page-ID lookup.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free publish metadata updates, migration ledgers, generated fixtures, local metadata maintenance scripts, or serialized and rehydrated `Page` records before calling `Page.set_metadata()`.

## Current Evidence

Local rollout-backed drafts repeatedly identify batched page metadata writes, publish metadata flows, and retained page identity as practical workflow surfaces. Existing drafts [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), [246-pr-page-direct-metadata-action-status-context.md](246-pr-page-direct-metadata-action-status-context.md), [348-pr-validate-meta-tag-inputs.md](348-pr-validate-meta-tag-inputs.md), [563-pr-validate-page-set-metadata-site.md](563-pr-validate-page-set-metadata-site.md), [724-pr-validate-page-metadata-status-type.md](724-pr-validate-page-metadata-status-type.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md), [664-pr-validate-page-collection-retained-page-id-state.md](664-pr-validate-page-collection-retained-page-id-state.md), [788-pr-validate-commit-tags-retained-page-id.md](788-pr-validate-commit-tags-retained-page-id.md), [789-pr-validate-set-parent-retained-page-id.md](789-pr-validate-set-parent-retained-page-id.md), [790-pr-validate-rename-retained-page-id.md](790-pr-validate-rename-retained-page-id.md), [791-pr-validate-vote-retained-page-id.md](791-pr-validate-vote-retained-page-id.md), [792-pr-validate-cancel-vote-retained-page-id.md](792-pr-validate-cancel-vote-retained-page-id.md), and [793-pr-validate-destroy-retained-page-id.md](793-pr-validate-destroy-retained-page-id.md) establish batched metadata writes, metadata response validation, metadata input validation, retained set-metadata site validation, metadata status type validation, page-ID validation, retained getter validation, collection retained-ID validation, and adjacent write-path retained-ID validation.

This slice is not a duplicate of those drafts. Issue 563 validates retained `page.site` before batched metadata work. Issues 245 and 724 validate returned metadata action responses. Issue 348 validates explicit meta payload shape. Issues 788 and 789 validate direct single-action tag and parent APIs, not the batched helper. Issues 413 and 658 validate public setter/getter page-ID behavior, but `Page.set_metadata()` had its own earlier login boundary before reaching the getter. Issue 664 validates retained IDs during collection acquisition. Issues 790 through 793 validate adjacent non-metadata or rating/delete write paths.

No upstream issue was filed from this local workspace.

## Changes

- Validate present retained `self._id` at the start of `Page.set_metadata()` with `_validate_retained_page_id(self)` when an update argument is supplied.
- Run retained-ID validation before `login_check()`.
- Preserve all-arguments-omitted behavior by not validating or resolving page IDs for the existing no-op path.
- Preserve missing-ID behavior by calling `self.id` after login only when a request body needs a page ID.
- Pass the validated or lazily acquired page ID into batched meta request body construction.
- Add focused regressions for malformed and negative retained page IDs that previously reached login before failing.

## Type Of Change

- State validation
- Batched metadata hardening
- Retained identity integrity
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.set_metadata()` must reject retained malformed `_id` values such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("page.id must be an integer")` when metadata update arguments are supplied. |
| R2 | `Page.set_metadata()` must reject retained negative `_id=-1` with `ValueError("page.id must be non-negative")` when metadata update arguments are supplied. |
| R3 | Retained-ID rejection must happen before `login_check()`, AMC request construction, response handling, or local tags/parent/metas mutation. |
| R4 | Missing `_id is None` must preserve authenticated lazy page-ID lookup only when a request body needs an ID; the all-arguments-omitted no-op must not force a page-ID lookup. |
| R5 | Tag validation, parent validation, meta validation, retained site validation, metadata action-status diagnostics, successful state updates, and existing page-ID boundaries must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, set-metadata coverage, write-method coverage, adjacent page/source/site coverage, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Batched metadata updates reject malformed retained page IDs before authentication. | `TestPageWriteMethods.test_set_metadata_rejects_malformed_retained_page_ids_before_login` failed RED for five malformed values because `login_check()` had already been called, then passed GREEN after retained-ID validation moved before login. | Accepting booleans/floats, coercing values, authenticating, sending AMC requests, or delaying diagnosis to the public getter rejects this local completion claim. | `Page.set_metadata()` retained page-ID preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Batched metadata updates reject negative retained page IDs before authentication. | `TestPageWriteMethods.test_set_metadata_rejects_negative_retained_page_id_before_login` failed RED because `login_check()` had already been called, then passed GREEN with the non-negative diagnostic before login. | Treating a negative retained ID as a request ID, authenticating before the local state error, or changing the diagnostic rejects this local completion claim. | `Page.set_metadata()` retained page-ID preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Validation is side-effect free for corrupted retained IDs. | The regressions assert `login_check()` and `site.amc_request(...)` are not called, and that tags, parent fullname, and `_metas` remain unchanged. | Calling login, constructing or sending metadata requests, parsing responses, or mutating local metadata state rejects this local completion claim. | Batched metadata preflight | focused tests |
| R4 | Missing IDs still defer lookup until after login and only when needed. | The implementation stores `page_id = _validate_retained_page_id(self)` only for supplied update arguments, then resolves `self.id` after login for tag/parent bodies or inside meta-body construction only when a meta diff body exists. | Forcing a page-ID lookup for the all-arguments-omitted no-op or before login for `_id is None` rejects this local completion claim. | Set-metadata missing-ID/no-op flow | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Existing adjacent validation boundaries remain stable. | Focused set-metadata retained-ID tests passed 6 tests, set-metadata-focused coverage passed 18 tests, `TestPageWriteMethods` passed 113 tests, adjacent page/source/revision/file/votes/site coverage passed 1206 tests, and full unit coverage passed 3856 tests. | Regressing retained site validation, metadata status diagnostics, valid request payloads, state update timing, page ID setter/getter behavior, or adjacent page workflows rejects this local completion claim. | Page write and adjacent workflows | `tests/unit` |
| R6 | The local proof stays unit-level and private-data-free. | All regressions use synthetic local fixtures and mocks. | Using live Wikidot, credentials, cookies, auth JSON, raw private page source, raw rollout paths, private site names, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `a29d242 fix(page): validate metadata page id`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_malformed_retained_page_ids_before_login tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_negative_retained_page_id_before_login -q --tb=short` failed six retained page-ID cases before the fix because `login_check.assert_not_called()` observed one login call.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_malformed_retained_page_ids_before_login tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_negative_retained_page_id_before_login -q` passed 6 tests.
- Set-metadata-focused coverage: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -k set_metadata -q` passed 18 tests.
- Write-method coverage: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 113 tests.
- Adjacent page coverage: `uv run pytest tests/unit/test_page.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1206 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3856 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Page.set_metadata(tags=..., parent_fullname=..., metas=...)` raises `ValueError("page.id must be an integer")` when retained `_id` is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- The same method raises `ValueError("page.id must be non-negative")` when retained `_id` is `-1`.
- The retained-ID failure occurs before login checks, AMC request construction, response handling, or local tags/parent/metas mutation.
- Failed retained-ID preflight does not coerce or rewrite the corrupted retained `_id`.
- `_id is None` still follows authenticated lazy lookup only after login and only when a request body needs a page ID.
- Malformed retained `page.site` still fails before retained ID validation can call login or AMC request work.
- Valid batched metadata updates, parent clears, empty-parent normalization, tag validation, parent validation, meta validation, action-status diagnostics, and successful local state updates remain intact.
- Existing page-ID constructor, setter, getter, create/edit argument validation, collection retained-ID validation, direct tag-save retained-ID validation, direct parent-update retained-ID validation, rename/vote/cancel-vote/destroy retained-ID validation, and adjacent workflows remain unchanged.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Callers with mutated or rehydrated malformed `Page._id` values now fail before batched metadata work. Mitigation: constructor, setter, getter, collection, direct tag, direct parent, rename, vote, cancel-vote, and destroy validation already define those values as invalid page identity state.
- Risk: This could regress unloaded pages that need authentication before lazy page-ID lookup. Mitigation: `_id is None` is still not acquired until after `login_check()` succeeds and only when a request body needs an ID.
- Risk: This could be mistaken for retained site or metadata input validation. Mitigation: Issues 563 and 348 remain those boundaries; this slice covers valid sites and valid metadata inputs with corrupted retained page identity.
- Risk: This could change meta-only no-op behavior. Mitigation: meta request body construction resolves a missing ID only when a meta diff produces request bodies, preserving lazy no-body behavior.

## Dependencies

- Existing `_validate_retained_page_id(...)` remains the canonical optional retained page-ID validator.
- Existing `Page.id` getter validation remains unchanged.
- Existing `Page.set_metadata()` input validation, retained site validation, request shape, status diagnostics, local update timing, and no-op behavior remain unchanged for valid values.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, cache ownership boundaries, result ergonomics, or complexity candidates outside this now-covered batched set-metadata retained-page-ID path.

## Upstream-Safe Motivation

`Page.set_metadata()` is the batched page metadata primitive used by browser-free publish and maintenance flows. A present retained page ID should satisfy the same integer and non-negative contract as direct `Page.id`, direct tag saves, direct parent updates, renames, votes, cancel-votes, and deletes before authentication or metadata request work can happen. Validating present retained IDs locally keeps corrupted fixture or rehydrated state from becoming a metadata update identifier while preserving valid loaded IDs, authenticated lazy lookup for unloaded pages, and the all-arguments-omitted no-op path.

## Local Evidence

- Local rollout-backed work established batched metadata updates as a practical workflow through browser-free publishing, metadata action-status diagnostics, retained site validation, direct metadata input validation, and metadata status type validation.
- Existing local drafts covered batched metadata helper behavior, metadata response validation, metadata input validation, retained set-metadata site validation, direct tag/parent retained-ID validation, direct `Page.id` setter/getter validation, collection retained page-ID validation, and adjacent rename/vote/cancel-vote/destroy retained page-ID validation; they did not cover present malformed retained `_id` state used by `Page.set_metadata()` before its entry login.
- The focused RED failure showed malformed and negative retained page-ID state could call `login_check()` before failing.
- This slice only validates present retained page IDs used by supplied `Page.set_metadata(...)` update arguments. It does not change metadata value normalization, action-status parsing, page-ID acquisition URLs, page-ID parser behavior, direct metas setter behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw page source text, rendered page content, private page content, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates present retained IDs without calling `Page.id` before login. It also avoids forcing page-ID validation for the existing no-argument no-op path. That preserves the existing unauthenticated set-metadata behavior for missing IDs while making corrupted non-`None` retained identity state fail deterministically at the batched metadata boundary when an update is requested.
