# PR Draft: Validate Page Metas Setter Retained Page ID

## Summary

`Page.metas = {...}` already validates explicit meta payloads, retained `page.site`, returned metadata action status, malformed status types, and local `_metas` update ordering. One retained identity field still crossed the direct meta setter authentication boundary late: if a valid `Page` was later mutated, fixture-loaded, or rehydrated with a malformed or negative cached `_id`, the setter called `login_check()` before the retained page-ID error surfaced through `self.id`.

This change validates a present retained `_id` with `_validate_retained_page_id(self)` after explicit meta input validation and site validation and before login checks, meta diff request construction, response handling, or local `_metas` mutation. Missing `_id is None` still preserves lazy lookup after login, and meta-only no-diff writes still avoid page-ID lookup when cached metas make no request body necessary.

## Outcome

Direct meta-tag updates can no longer authenticate or build `deleteMetaTag` or `saveMetaTag` request work through corrupted retained page-ID state. Valid loaded page IDs still produce the same `pageId` payloads, and unloaded pages still acquire IDs after authentication only when a meta request body needs an ID.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use direct meta-tag maintenance, browser-free publish metadata helpers, migration ledgers, generated fixtures, local metadata cleanup scripts, or serialized and rehydrated `Page` records before assigning `Page.metas`.

## Current Evidence

Local rollout-backed drafts repeatedly identify page metadata writes, direct meta-tag setters, publish metadata flows, and retained page identity as practical workflow surfaces. Existing drafts [007-pr-batch-meta-tag-updates.md](007-pr-batch-meta-tag-updates.md), [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [249-pr-page-metas-setter-action-status-context.md](249-pr-page-metas-setter-action-status-context.md), [348-pr-validate-meta-tag-inputs.md](348-pr-validate-meta-tag-inputs.md), [565-pr-validate-page-metas-setter-site.md](565-pr-validate-page-metas-setter-site.md), [724-pr-validate-page-metadata-status-type.md](724-pr-validate-page-metadata-status-type.md), [794-pr-validate-set-metadata-retained-page-id.md](794-pr-validate-set-metadata-retained-page-id.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md), [664-pr-validate-page-collection-retained-page-id-state.md](664-pr-validate-page-collection-retained-page-id-state.md), [787-pr-validate-page-edit-retained-page-id.md](787-pr-validate-page-edit-retained-page-id.md), [788-pr-validate-commit-tags-retained-page-id.md](788-pr-validate-commit-tags-retained-page-id.md), [789-pr-validate-set-parent-retained-page-id.md](789-pr-validate-set-parent-retained-page-id.md), [790-pr-validate-rename-retained-page-id.md](790-pr-validate-rename-retained-page-id.md), [791-pr-validate-vote-retained-page-id.md](791-pr-validate-vote-retained-page-id.md), [792-pr-validate-cancel-vote-retained-page-id.md](792-pr-validate-cancel-vote-retained-page-id.md), and [793-pr-validate-destroy-retained-page-id.md](793-pr-validate-destroy-retained-page-id.md) establish meta batching, batched metadata writes, direct meta setter response validation, metadata input validation, retained direct metas-site validation, metadata status type validation, batched set-metadata retained-ID validation, page-ID validation, retained getter validation, collection retained-ID validation, and adjacent write-path retained-ID validation.

This slice is not a duplicate of those drafts. Issue 565 validates retained `page.site` before direct meta setter work. Issues 249 and 724 validate returned metadata action responses. Issue 348 validates explicit meta payload shape. Issue 794 validates the batched `Page.set_metadata(...)` helper and explicitly leaves the direct `Page.metas` setter outside its scope. Issues 788 and 789 validate direct tag and parent APIs, not direct meta-tag assignment. Issues 413 and 658 validate public setter/getter page-ID behavior, but `Page.metas = ...` had its own earlier login boundary before reaching the getter. Issue 664 validates retained IDs during collection acquisition. Issues 787 through 793 validate adjacent edit/tag/parent/rename/rating/delete write paths.

No upstream issue was filed from this local workspace.

## Changes

- Validate present retained `self._id` at the start of the `Page.metas` setter with `_validate_retained_page_id(self)`.
- Run retained-ID validation before `login_check()`.
- Pass the validated or lazily resolved page ID into shared meta request body construction.
- Preserve missing-ID behavior by calling `self.id` after login only when a meta diff request body needs a page ID.
- Add focused regressions for malformed and negative retained page IDs that previously reached login before failing.

## Type Of Change

- State validation
- Direct meta setter hardening
- Retained identity integrity
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.metas = ...` must reject retained malformed `_id` values such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("page.id must be an integer")`. |
| R2 | `Page.metas = ...` must reject retained negative `_id=-1` with `ValueError("page.id must be non-negative")`. |
| R3 | Retained-ID rejection must happen before `login_check()`, AMC request construction, response handling, or local `_metas` mutation. |
| R4 | Missing `_id is None` must preserve authenticated lazy page-ID lookup only when a meta request body needs an ID. |
| R5 | Meta input validation, retained site validation, metadata action-status diagnostics, successful cache updates, and existing page-ID boundaries must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, metas-setter coverage, write-method coverage, adjacent page/source/site coverage, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct meta setter updates reject malformed retained page IDs before authentication. | `TestPageWriteMethods.test_metas_setter_rejects_malformed_retained_page_ids_before_login` failed RED for five malformed values because `login_check()` had already been called, then passed GREEN after retained-ID validation moved before login. | Accepting booleans/floats, coercing values, authenticating, sending AMC requests, or delaying diagnosis to the public getter rejects this local completion claim. | `Page.metas` setter retained page-ID preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Direct meta setter updates reject negative retained page IDs before authentication. | `TestPageWriteMethods.test_metas_setter_rejects_negative_retained_page_id_before_login` failed RED because `login_check()` had already been called, then passed GREEN with the non-negative diagnostic before login. | Treating a negative retained ID as a request ID, authenticating before the local state error, or changing the diagnostic rejects this local completion claim. | `Page.metas` setter retained page-ID preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Validation is side-effect free for corrupted retained IDs. | The regressions assert `login_check()` and `site.amc_request(...)` are not called, and that `_id` and `_metas` remain unchanged. | Calling login, constructing or sending metadata requests, parsing responses, coercing retained IDs, or mutating local metadata state rejects this local completion claim. | Direct metas setter preflight | focused tests |
| R4 | Missing IDs still defer lookup until after login and only when needed. | The implementation stores `page_id = _validate_retained_page_id(self)`, calls login, and passes that value to `_meta_update_request_bodies(...)`; the helper resolves `self.id` only inside request-body loops when `page_id is None`. | Forcing a page-ID lookup before login for `_id is None` or for cached no-diff meta assignments rejects this local completion claim. | Direct metas missing-ID/no-diff flow | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Existing adjacent validation boundaries remain stable. | Focused metas setter retained-ID tests passed 6 tests, metas-setter-focused coverage passed 11 tests, `TestPageWriteMethods` passed 119 tests, adjacent page/source/revision/file/votes/site coverage passed 1212 tests, and full unit coverage passed 3862 tests. | Regressing retained site validation, metadata status diagnostics, valid request payloads, state update timing, page ID setter/getter behavior, or adjacent page workflows rejects this local completion claim. | Page write and adjacent workflows | `tests/unit` |
| R6 | The local proof stays unit-level and private-data-free. | All regressions use synthetic local fixtures and mocks. | Using live Wikidot, credentials, cookies, auth JSON, raw private page source, raw rollout paths, private site names, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the docs commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `3e79344 fix(page): validate metas setter page id`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_rejects_malformed_retained_page_ids_before_login tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_rejects_negative_retained_page_id_before_login -q --tb=short` failed six retained page-ID cases before the fix because `login_check.assert_not_called()` observed one login call.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_rejects_malformed_retained_page_ids_before_login tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_rejects_negative_retained_page_id_before_login -q --tb=short` passed 6 tests.
- Metas-setter-focused coverage: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -k metas_setter -q --tb=short` passed 11 tests.
- Write-method coverage: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q --tb=short` passed 119 tests.
- Adjacent page coverage: `uv run pytest tests/unit/test_page.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q --tb=short` passed 1212 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3862 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Page.metas = ...` raises `ValueError("page.id must be an integer")` when retained `_id` is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- The same setter raises `ValueError("page.id must be non-negative")` when retained `_id` is `-1`.
- The retained-ID failure occurs before login checks, AMC request construction, response handling, or local `_metas` mutation.
- Failed retained-ID preflight does not coerce or rewrite the corrupted retained `_id`.
- `_id is None` still follows authenticated lazy lookup only after login and only when a meta request body needs a page ID.
- Malformed retained `page.site` still fails before retained ID validation can call login or AMC request work.
- Invalid meta payloads still fail before site validation, retained-ID validation, login checks, or request work.
- Valid batched meta deletes, adds, updates, response diagnostics, status type diagnostics, and successful local cache replacement remain intact.
- Existing page-ID constructor, setter, getter, create/edit argument validation, collection retained-ID validation, edit-path retained-ID validation, commit-tags retained-ID validation, set-parent retained-ID validation, rename/vote/cancel-vote/destroy retained-ID validation, and batched set-metadata retained-ID validation remain unchanged.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Callers with mutated or rehydrated malformed `Page._id` values now fail before direct meta-tag write work. Mitigation: constructor, setter, getter, collection, edit, direct tag, direct parent, rename, vote, cancel-vote, destroy, and batched set-metadata validation already define those values as invalid page identity state.
- Risk: This could regress unloaded pages that need authentication before lazy page-ID lookup. Mitigation: `_id is None` is still not acquired until after `login_check()` succeeds and only when a meta request body needs an ID.
- Risk: This could be mistaken for retained site, metadata input, or metadata response validation. Mitigation: Issues 565, 348, 249, and 724 remain those boundaries; this slice covers valid sites and valid metadata inputs with corrupted retained page identity before direct setter authentication.
- Risk: This could change meta-only no-diff behavior. Mitigation: meta request body construction resolves a missing ID only when a meta diff produces request bodies, preserving cached no-body behavior.

## Dependencies

- Existing `_validate_retained_page_id(...)` remains the canonical optional retained page-ID validator.
- Existing `Page.id` getter validation remains unchanged.
- Existing `Page.metas` input validation, retained site validation, request shape, status diagnostics, local update timing, and no-diff behavior remain unchanged for valid values.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, cache ownership boundaries, result ergonomics, or complexity candidates outside this now-covered direct metas-setter retained-page-ID path.

## Upstream-Safe Motivation

`Page.metas = ...` remains the direct public meta-tag mutation API and is still used by lower-level metadata maintenance code even though batched `Page.set_metadata(...)` exists. A present retained page ID should satisfy the same integer and non-negative contract as direct `Page.id`, `Page.edit(...)`, `Page.commit_tags()`, `Page.set_parent()`, `Page.rename()`, `Page.vote()`, `Page.cancel_vote()`, `Page.destroy()`, and `Page.set_metadata(...)` before authentication or metadata request work can happen. Validating present retained IDs locally keeps corrupted fixture or rehydrated state from becoming a meta-tag update identifier while preserving valid loaded IDs and authenticated lazy lookup for unloaded pages.

## Local Evidence

- Local rollout-backed work established direct meta-tag writes as a practical workflow through batched meta updates, browser-free publishing, metadata action-status diagnostics, retained site validation, direct metadata input validation, and metadata status type validation.
- Existing local drafts covered direct metas batching, direct metas response validation, direct metas site validation, metadata input validation, batched set-metadata retained-ID validation, direct `Page.id` setter/getter validation, collection retained page-ID validation, and adjacent edit/commit-tags/set-parent/rename/vote/cancel-vote/destroy retained page-ID validation; they did not cover present malformed retained `_id` state used by `Page.metas = ...` before its entry login.
- The focused RED failure showed malformed and negative retained page-ID state could call `login_check()` before failing.
- This slice only validates present retained page IDs used by direct `Page.metas = ...` assignment. It does not change metadata value normalization, action-status parsing, page-ID acquisition URLs, page-ID parser behavior, batched `Page.set_metadata(...)` behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw page source text, rendered page content, private page content, private metadata values, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates present retained IDs without calling `Page.id` before login. That preserves the existing unauthenticated direct meta setter behavior for missing IDs while making corrupted non-`None` retained identity state fail deterministically at the `Page.metas` setter boundary.
