# PR Draft: Validate Commit Tags Retained Page ID

## Summary

`Page.commit_tags()` already validates mutable `Page.tags` state and retained `page.site` before saving tags, and the public `Page.id` getter already validates malformed cached IDs when reached. One action-boundary gap remained: if a valid `Page` was later mutated, fixture-loaded, or rehydrated with a malformed or negative cached `_id`, `commit_tags()` called `login_check()` before the retained page-ID error surfaced through `self.id`.

This change validates a present retained `_id` with `_validate_retained_page_id(self)` after tag-state and site validation and before login checks, AMC request construction, response handling, or local tag-save acceptance. Missing `_id is None` still preserves the existing login-before-lazy-ID-lookup behavior.

## Outcome

Direct tag saves can no longer authenticate or build tag-save work through corrupted retained page-ID state. Valid loaded page IDs still produce the same `saveTags` payload, and unloaded pages still acquire IDs only after the entry login succeeds.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page metadata cleanup, generated page ledgers, migration fixtures, local tag maintenance scripts, or serialized and rehydrated `Page` records before calling `Page.commit_tags()`.

## Current Evidence

Local rollout-backed drafts repeatedly identify direct and batched page metadata/tag writes as practical workflow surfaces. Existing drafts [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), [246-pr-page-direct-metadata-action-status-context.md](246-pr-page-direct-metadata-action-status-context.md), [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), [532-pr-validate-commit-tags-state.md](532-pr-validate-commit-tags-state.md), [558-pr-validate-page-commit-tags-site.md](558-pr-validate-page-commit-tags-site.md), [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md), [664-pr-validate-page-collection-retained-page-id-state.md](664-pr-validate-page-collection-retained-page-id-state.md), and [787-pr-validate-page-edit-retained-page-id.md](787-pr-validate-page-edit-retained-page-id.md) establish direct metadata writes, page-ID validation, current tag-state validation, commit-tags retained site validation, getter retained-ID validation, collection retained-ID validation, and edit-path retained-ID validation.

This slice is not a duplicate of those drafts. Issue 532 validates `Page.tags` before direct tag saves. Issue 558 validates retained `page.site` before direct tag saves. Issues 413 and 658 validate public setter/getter page-ID behavior, but `Page.commit_tags()` had its own earlier login boundary before reaching the getter. Issue 664 validates retained IDs during collection acquisition. Issue 787 validates the `Page.edit(...)` write path, not direct `saveTags`.

Memory recall for the retained page-ID pattern found the prior Issue787 decision (`mem_mq8hw96g_31fa349972c3`) as the relevant non-duplicate precedent; no separate commit-tags retained-ID memory appeared.

No upstream issue was filed from this local workspace.

## Changes

- Validate present retained `self._id` at the start of `Page.commit_tags()` with `_validate_retained_page_id(self)`.
- Run retained-ID validation before `login_check()`.
- Preserve missing-ID behavior by calling `self.id` after login only when retained `_id is None`.
- Use the validated or lazily acquired local `page_id` value in the `saveTags` request.
- Add focused regressions for malformed and negative retained page IDs that previously reached login before failing.

## Type Of Change

- State validation
- Direct tag-save hardening
- Retained identity integrity
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.commit_tags()` must reject retained malformed `_id` values such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("page.id must be an integer")`. |
| R2 | `Page.commit_tags()` must reject retained negative `_id=-1` with `ValueError("page.id must be non-negative")`. |
| R3 | Retained-ID rejection must happen before `login_check()`, AMC request construction, response handling, or local tag-save acceptance. |
| R4 | Missing `_id is None` must preserve the existing login-before-lazy-ID-lookup behavior. |
| R5 | Current tag-state validation, retained site validation, valid direct tag saves, valid logged-out behavior, metadata action-status diagnostics, and existing page-ID boundaries must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, commit-tags coverage, write-method coverage, adjacent page/source/site coverage, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct tag saves reject malformed retained page IDs before authentication. | `TestPageWriteMethods.test_commit_tags_rejects_malformed_retained_page_ids_before_login` failed RED for five malformed values because `login_check()` had already been called, then passed GREEN after retained-ID validation moved before login. | Accepting booleans/floats, coercing values, authenticating, sending AMC requests, or delaying diagnosis to the public getter rejects this local completion claim. | `Page.commit_tags()` retained page-ID preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Direct tag saves reject negative retained page IDs before authentication. | `TestPageWriteMethods.test_commit_tags_rejects_negative_retained_page_id_before_login` failed RED because `login_check()` had already been called, then passed GREEN with the non-negative diagnostic before login. | Treating a negative retained ID as a request ID, authenticating before the local state error, or changing the diagnostic rejects this local completion claim. | `Page.commit_tags()` retained page-ID preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Validation is side-effect free for corrupted retained IDs. | The regressions assert `login_check()` and `site.amc_request(...)` are not called, and that valid local tags remain unchanged. | Calling login, constructing or sending `saveTags`, parsing responses, or mutating tag state rejects this local completion claim. | Direct tag-save preflight | focused tests |
| R4 | Missing IDs still defer lookup until after login. | The implementation stores `page_id = _validate_retained_page_id(self)` and only calls `self.id` after login when `page_id is None`; existing commit-tags success and logged-out tests remain green. | Calling `PageCollection.get_page_ids()` before login for `_id is None` would change the existing authentication boundary. | Direct tag-save missing-ID flow | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Existing adjacent validation boundaries remain stable. | Commit-tags focused coverage passed 8 tests, `TestPageWriteMethods` passed 77 tests, adjacent page/source/revision/file/vote/site coverage passed 1394 tests, and full unit coverage passed 3820 tests. | Regressing tag-state validation, retained site validation, valid tag serialization, logged-out behavior, status diagnostics, page ID setter/getter behavior, or adjacent page workflows rejects this local completion claim. | Page write and adjacent workflows | `tests/unit` |
| R6 | The local proof stays unit-level and private-data-free. | All regressions use synthetic local fixtures and mocks. | Using live Wikidot, credentials, cookies, auth JSON, raw private page source, raw rollout paths, private site names, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `e670224 fix(page): validate commit tags page id`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_rejects_malformed_retained_page_ids_before_login tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_rejects_negative_retained_page_id_before_login -q --tb=short` failed six retained page-ID cases before the fix because `login_check.assert_not_called()` observed one login call.
- GREEN focused: the same focused command passed 6 tests after the fix.
- Commit-tags neighborhood: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_success tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_not_logged_in tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_rejects_malformed_site_before_login tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_rejects_invalid_tags_before_request tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_missing_action_status_includes_site_page_event_and_field_context -q` passed 8 tests.
- Write-method coverage: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 77 tests.
- Adjacent page coverage: `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1394 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3820 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Page.commit_tags()` raises `ValueError("page.id must be an integer")` when retained `_id` is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- The same method raises `ValueError("page.id must be non-negative")` when retained `_id` is `-1`.
- The retained-ID failure occurs before login checks, AMC request construction, response handling, or local tag-save acceptance.
- Failed retained-ID preflight does not coerce or rewrite the corrupted retained `_id`.
- `_id is None` still follows the existing authenticated lazy lookup path.
- Malformed current tags still fail before site and ID validation.
- Malformed retained `page.site` still fails before retained ID validation can call login or AMC request work.
- Valid `Page.commit_tags()` behavior, valid logged-out behavior, and `saveTags` action-status diagnostics remain intact.
- Existing page-ID constructor, setter, getter, create/edit argument validation, collection retained-ID validation, and edit-path retained-ID validation remain unchanged.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Callers with mutated or rehydrated malformed `Page._id` values now fail before tag-save work. Mitigation: constructor, setter, getter, direct create/edit, collection, and edit-path validation already define those values as invalid page identity state.
- Risk: This could regress unloaded pages that need authentication before lazy page-ID lookup. Mitigation: `_id is None` is still not acquired until after `login_check()` succeeds; the preflight only validates present retained state.
- Risk: This could be mistaken for current tag-state validation. Mitigation: Issue 532 remains the tag container/entry boundary; this slice covers valid tags with corrupted retained page identity.

## Dependencies

- Existing `_validate_retained_page_id(...)` remains the canonical optional retained page-ID validator.
- Existing `Page.id` getter validation remains unchanged.
- Existing `Page.commit_tags()` tag-state validation, retained site validation, request shape, status diagnostics, and return behavior remain unchanged for valid values.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, cache ownership boundaries, result ergonomics, or complexity candidates outside this now-covered direct tag-save retained-page-ID path.

## Upstream-Safe Motivation

`Page.commit_tags()` is the direct low-level tag-save primitive. A present retained page ID should satisfy the same integer and non-negative contract as direct `Page.id` and `Page.edit(...)` before authentication or `saveTags` request work can happen. Validating present retained IDs locally keeps corrupted fixture or rehydrated state from becoming a tag-save identifier while preserving valid loaded IDs and authenticated lazy lookup for unloaded pages.

## Local Evidence

- Local rollout-backed work established direct metadata and tag writes as practical workflows through metadata batching, direct tag saves, response-status diagnostics, current tag-state validation, retained site validation, and page-ID state validation.
- Existing local drafts covered direct `Page.commit_tags()` tag-state validation, retained commit-tags site validation, direct `Page.id` setter/getter validation, collection retained page-ID validation, and page edit retained page-ID validation; they did not cover present malformed retained `_id` state used by `Page.commit_tags()` before its entry login.
- The focused RED failure showed malformed and negative retained page-ID state could call `login_check()` before failing.
- This slice only validates present retained page IDs used by `Page.commit_tags()` calls. It does not change tag syntax, tag normalization, metadata batching, page-ID acquisition URLs, page-ID parser behavior, source/edit behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw page source text, rendered page content, private page content, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates present retained IDs without calling `Page.id` before login. That preserves the existing unauthenticated direct tag-save behavior for missing IDs while making corrupted non-`None` retained identity state fail deterministically at the `commit_tags()` boundary.
