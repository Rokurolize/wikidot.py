# PR Draft: Validate Cancel Vote Retained Page ID

## Summary

`Page.cancel_vote()` already validates retained `page.site`, returned `cancelVote` action status, returned rating points, and successful vote-cache invalidation ordering. One retained identity field still crossed the action authentication boundary late: if a valid `Page` was later mutated, fixture-loaded, or rehydrated with a malformed or negative cached `_id`, `cancel_vote()` called `login_check()` before the retained page-ID error surfaced through `self.id`.

This change validates a present retained `_id` with `_validate_retained_page_id(self)` after site validation and before login checks, AMC request construction, response handling, local rating mutation, or vote-cache invalidation. Missing `_id is None` still preserves the existing login-before-lazy-ID-lookup behavior.

## Outcome

Page vote cancellations can no longer authenticate or build `cancelVote` request work through corrupted retained page-ID state. Valid loaded page IDs still produce the same integer `pageId` payload, and unloaded pages still acquire IDs only after the entry login succeeds.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page vote cleanup, rating audits, moderation helpers, generated page ledgers, migration fixtures, or serialized and rehydrated `Page` records before calling `Page.cancel_vote()`.

## Current Evidence

Local rollout-backed drafts repeatedly identify page vote cancellation, rating state, and retained page identity as practical workflow surfaces. Existing drafts [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [562-pr-validate-page-cancel-vote-site.md](562-pr-validate-page-cancel-vote-site.md), [723-pr-validate-page-rating-status-type.md](723-pr-validate-page-rating-status-type.md), [773-pr-validate-rating-points-ascii-shape.md](773-pr-validate-rating-points-ascii-shape.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md), [664-pr-validate-page-collection-retained-page-id-state.md](664-pr-validate-page-collection-retained-page-id-state.md), [787-pr-validate-page-edit-retained-page-id.md](787-pr-validate-page-edit-retained-page-id.md), [788-pr-validate-commit-tags-retained-page-id.md](788-pr-validate-commit-tags-retained-page-id.md), [789-pr-validate-set-parent-retained-page-id.md](789-pr-validate-set-parent-retained-page-id.md), [790-pr-validate-rename-retained-page-id.md](790-pr-validate-rename-retained-page-id.md), and [791-pr-validate-vote-retained-page-id.md](791-pr-validate-vote-retained-page-id.md) establish vote-cache invalidation, rating action-status validation, retained cancel-vote site validation, rating status type validation, returned points validation, page-ID validation, retained getter validation, collection retained-ID validation, and adjacent write-path retained-ID validation.

This slice is not a duplicate of those drafts. Issue 562 validates retained `page.site` before cancel-vote work. Issues 337, 723, and 773 validate remote rating responses and returned point shape. Issue 261 validates `_votes` invalidation after successful cancel-vote work. Issues 413 and 658 validate public setter/getter page-ID behavior, but `Page.cancel_vote()` had its own earlier login boundary before reaching the getter. Issue 664 validates retained IDs during collection acquisition. Issues 787, 788, 789, 790, and 791 validate adjacent write paths, not direct `cancelVote`.

No upstream issue was filed from this local workspace.

## Changes

- Validate present retained `self._id` at the start of `Page.cancel_vote()` with `_validate_retained_page_id(self)`.
- Run retained-ID validation before `login_check()`.
- Preserve missing-ID behavior by calling `self.id` after login only when retained `_id is None`.
- Use the validated or lazily acquired local `page_id` value in the `cancelVote` request payload.
- Add focused regressions for malformed and negative retained page IDs that previously reached login before failing.

## Type Of Change

- State validation
- Page cancel-vote hardening
- Retained identity integrity
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.cancel_vote()` must reject retained malformed `_id` values such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("page.id must be an integer")`. |
| R2 | `Page.cancel_vote()` must reject retained negative `_id=-1` with `ValueError("page.id must be non-negative")`. |
| R3 | Retained-ID rejection must happen before `login_check()`, AMC request construction, response handling, local rating mutation, or vote-cache invalidation. |
| R4 | Missing `_id is None` must preserve the existing login-before-lazy-ID-lookup behavior. |
| R5 | Retained site validation, successful vote cancellations, action-status diagnostics, rating-points diagnostics, vote-cache invalidation, and existing page-ID boundaries must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, cancel-vote coverage, write-method coverage, adjacent page/source/site coverage, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Vote cancellations reject malformed retained page IDs before authentication. | `TestPageWriteMethods.test_cancel_vote_rejects_malformed_retained_page_ids_before_login` failed RED for five malformed values because `login_check()` had already been called, then passed GREEN after retained-ID validation moved before login. | Accepting booleans/floats, coercing values, authenticating, sending AMC requests, or delaying diagnosis to the public getter rejects this local completion claim. | `Page.cancel_vote()` retained page-ID preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Vote cancellations reject negative retained page IDs before authentication. | `TestPageWriteMethods.test_cancel_vote_rejects_negative_retained_page_id_before_login` failed RED because `login_check()` had already been called, then passed GREEN with the non-negative diagnostic before login. | Treating a negative retained ID as a request ID, authenticating before the local state error, or changing the diagnostic rejects this local completion claim. | `Page.cancel_vote()` retained page-ID preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Validation is side-effect free for corrupted retained IDs. | The regressions assert `login_check()` and `site.amc_request(...)` are not called, and that `rating` and `_votes` remain unchanged. | Calling login, constructing or sending `cancelVote`, parsing responses, mutating rating, or clearing `_votes` rejects this local completion claim. | Cancel-vote preflight | focused tests |
| R4 | Missing IDs still defer lookup until after login. | The implementation stores `page_id = _validate_retained_page_id(self)` and only calls `self.id` after login when `page_id is None`; existing cancel-vote success and logged-out paths remain covered by write-method and adjacent suites. | Calling `PageCollection.get_page_ids()` before login for `_id is None` would change the existing authentication boundary. | Cancel-vote missing-ID flow | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Existing adjacent validation boundaries remain stable. | Focused cancel-vote retained-ID tests passed 6 tests, cancel-vote-focused coverage passed 12 tests, `TestPageWriteMethods` passed 101 tests, adjacent page/source/revision/file/votes/site coverage passed 1194 tests, and full unit coverage passed 3844 tests. | Regressing retained site validation, action-status diagnostics, rating-points diagnostics, vote-cache invalidation, valid cancel-vote payloads, page ID setter/getter behavior, or adjacent page workflows rejects this local completion claim. | Page write and adjacent workflows | `tests/unit` |
| R6 | The local proof stays unit-level and private-data-free. | All regressions use synthetic local fixtures and mocks. | Using live Wikidot, credentials, cookies, auth JSON, raw private page source, raw rollout paths, private site names, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `afa62a3 fix(page): validate cancel vote page id`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_rejects_malformed_retained_page_ids_before_login tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_rejects_negative_retained_page_id_before_login -q --tb=short` failed six retained page-ID cases before the fix because `login_check.assert_not_called()` observed one login call.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_rejects_malformed_retained_page_ids_before_login tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_rejects_negative_retained_page_id_before_login -q` passed 6 tests.
- Cancel-vote-focused coverage: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -k cancel_vote -q` passed 12 tests.
- Write-method coverage: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 101 tests.
- Adjacent page coverage: `uv run pytest tests/unit/test_page.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1194 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3844 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Page.cancel_vote()` raises `ValueError("page.id must be an integer")` when retained `_id` is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- The same method raises `ValueError("page.id must be non-negative")` when retained `_id` is `-1`.
- The retained-ID failure occurs before login checks, AMC request construction, response handling, local rating mutation, or vote-cache invalidation.
- Failed retained-ID preflight does not coerce or rewrite the corrupted retained `_id`.
- `_id is None` still follows the existing authenticated lazy lookup path.
- Malformed retained `page.site` still fails before retained ID validation can call login or AMC request work.
- Valid vote cancellations, malformed action-status diagnostics, explicit non-`ok` status diagnostics, rating-points diagnostics, and successful `_votes` invalidation remain intact.
- Existing page-ID constructor, setter, getter, create/edit argument validation, collection retained-ID validation, edit-path retained-ID validation, commit-tags retained-ID validation, set-parent retained-ID validation, rename retained-ID validation, and vote retained-ID validation remain unchanged.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Callers with mutated or rehydrated malformed `Page._id` values now fail before cancel-vote work. Mitigation: constructor, setter, getter, direct create/edit, collection, edit-path, commit-tags, set-parent, rename, and vote validation already define those values as invalid page identity state.
- Risk: This could regress unloaded pages that need authentication before lazy page-ID lookup. Mitigation: `_id is None` is still not acquired until after `login_check()` succeeds; the preflight only validates present retained state.
- Risk: This could be mistaken for retained site validation. Mitigation: Issue 562 remains the cancel-vote site boundary; this slice covers valid sites with corrupted retained page identity.
- Risk: This could be mistaken for response/cache ordering. Mitigation: Issues 337, 723, 773, and 261 remain the action-status, points, and vote-cache boundaries; this slice only changes the pre-auth retained-ID boundary.

## Dependencies

- Existing `_validate_retained_page_id(...)` remains the canonical optional retained page-ID validator.
- Existing `Page.id` getter validation remains unchanged.
- Existing `Page.cancel_vote()` retained site validation, request shape, status diagnostics, points parsing, local rating update timing, and `_votes` invalidation remain unchanged for valid values.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, cache ownership boundaries, result ergonomics, or complexity candidates outside this now-covered direct cancel-vote retained-page-ID path.

## Upstream-Safe Motivation

`Page.cancel_vote()` is the direct low-level page rating cancellation primitive and also mutates local rating and vote-cache state. A present retained page ID should satisfy the same integer and non-negative contract as direct `Page.id`, `Page.edit(...)`, `Page.commit_tags()`, `Page.set_parent()`, `Page.rename()`, and `Page.vote()` before authentication or `cancelVote` request work can happen. Validating present retained IDs locally keeps corrupted fixture or rehydrated state from becoming a cancel-vote identifier while preserving valid loaded IDs and authenticated lazy lookup for unloaded pages.

## Local Evidence

- Local rollout-backed work established page vote cancellation as a practical workflow through action-status diagnostics, rating-points diagnostics, retained site validation, local rating preservation on failure, and vote-cache invalidation after success.
- Existing local drafts covered retained cancel-vote site validation, rating action-status validation, returned rating-points validation, vote-cache invalidation, direct `Page.id` setter/getter validation, collection retained page-ID validation, and adjacent edit/commit-tags/set-parent/rename/vote retained page-ID validation; they did not cover present malformed retained `_id` state used by `Page.cancel_vote()` before its entry login.
- The focused RED failure showed malformed and negative retained page-ID state could call `login_check()` before failing.
- This slice only validates present retained page IDs used by `Page.cancel_vote()` calls. It does not change rate action status parsing, points parsing, `_votes` invalidation timing, page-ID acquisition URLs, page-ID parser behavior, vote behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw page source text, rendered page content, private page content, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates present retained IDs without calling `Page.id` before login. That preserves the existing unauthenticated cancel-vote behavior for missing IDs while making corrupted non-`None` retained identity state fail deterministically at the `cancel_vote()` boundary.
