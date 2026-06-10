# PR Draft: Validate Page Edit Retained Title

## Summary

`Page.edit(...)` validates explicit `title`, `source`, `comment`, `force_edit`, and retained `page.site` state before delegating to `Page.create_or_edit(...)`. One omitted-title path still copied `self.title` only after the login check. If a valid `Page` was later mutated, fixture-loaded, or rehydrated with a non-string retained title, `Page.edit(source="...")` could authenticate and delegate a malformed title into the write path before any retained-title validation occurred.

This change validates retained `self.title` when `title` is omitted, after retained site validation and before `login_check()`, current-source reads, `Page.create_or_edit(...)` delegation, local title/source mutation, revision-count sync, or revision-cache invalidation. Malformed retained titles now raise `ValueError("title must be a string")`. Valid omitted-title edits still preserve the current page title, and explicit valid title edits remain unchanged.

## Outcome

Page edits can no longer use malformed retained page-title state as the hidden title for omitted-title edits. The failure is local, deterministic, and side-effect free.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page editing, generated fixtures, migration ledgers, publication tooling, local tests, or serialized and rehydrated `Page` records before calling `Page.edit(source=...)`.

## Current Evidence

Local rollout-backed drafts repeatedly identify page editing and page title state as practical workflow surfaces. Existing drafts [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [259-pr-page-edit-local-cache-sync.md](259-pr-page-edit-local-cache-sync.md), [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md), [564-pr-validate-page-edit-site.md](564-pr-validate-page-edit-site.md), and the adjacent omitted-title forum edit draft [784-pr-validate-forum-post-edit-retained-title.md](784-pr-validate-forum-post-edit-retained-title.md) establish page edit defaulting, local cache sync, revision invalidation, explicit page write text validation, constructor title validation, edit-time retained site validation, and the analogous forum omitted-title retained-state boundary.

This slice is not a duplicate of those drafts. Issue 350 validates explicit `Page.edit(title=3)` and `Page.edit(comment=3)` inputs and intentionally preserves `Page.edit(title=None, comment=None)` defaults. Issue 481 validates `Page(title=...)` at construction, but it cannot cover post-construction mutation, fixture mutation, or rehydrated state before a later edit call. Issue 564 validates retained `page.site` at edit time, not the retained title used as the delegated write payload when explicit `title` is omitted.

The focused RED test demonstrated the gap: `mock_page_with_id.title = 3` followed by `mock_page_with_id.edit(source="Updated source")` completed without raising before the fix, reached the patched successful delegation path, and failed the regression with `DID NOT RAISE`.

## Related Issue / Non-Duplicate Analysis

Builds directly on [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md), [564-pr-validate-page-edit-site.md](564-pr-validate-page-edit-site.md), and the adjacent retained-title pattern from [784-pr-validate-forum-post-edit-retained-title.md](784-pr-validate-forum-post-edit-retained-title.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `self.title` with `_validate_page_text_field("title", self.title)` when `Page.edit(...)` is called without an explicit `title`.
- Run the retained-title validation before `login_check()`.
- Preserve explicit `title=` validation and successful local title updates from the returned edited page.
- Preserve valid omitted-title edit behavior by delegating the current retained title when it is a string.
- Add a focused regression for a mutated retained title that previously reached login/delegation and local cache mutation.

## Type Of Change

- State validation
- Page edit-path hardening
- Retained text-field integrity
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.edit(source=...)` with omitted `title` must reject a retained `page.title` that is not a string with `ValueError("title must be a string")`. |
| R2 | The retained-title rejection must happen before `login_check()`, current-source reads, `Page.create_or_edit(...)`, local title/source mutation, revision-count sync, or revision-cache invalidation. |
| R3 | Explicit malformed `title=`, `comment=`, `source=`, and malformed `force_edit` validation must remain unchanged. |
| R4 | Valid omitted-title edits, valid explicit-title edits, edit lock/save behavior, local source sync, revision-cache invalidation, and adjacent page/site workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, edit coverage, adjacent page/source/site coverage, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Omitted-title edit rejects malformed retained title state. | `TestPageEdit.test_edit_rejects_malformed_retained_title_before_login_or_delegation` failed RED with `DID NOT RAISE`, then passed GREEN after retained-title validation was added. | Accepting an integer or other non-string retained title, coercing it, or using it as the delegated write title rejects this local completion claim. | `Page.edit(...)` omitted-title preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Validation is side-effect free. | The regression asserts `login_check` and `Page.create_or_edit(...)` are not called, and that retained title, `revisions_count`, `_source`, and `_revisions` remain unchanged. | Authenticating, delegating to `Page.create_or_edit(...)`, fetching current source, updating `title`, updating `_source`, changing `revisions_count`, or clearing `_revisions` rejects this local completion claim. | Page edit preflight | focused test |
| R3 | Existing explicit edit validation remains stable. | `TestPageEdit` passed 14 tests, including non-string source, force-edit, title, and comment preflight coverage. | Regressing explicit source/title/comment/force diagnostics, login ordering, or current-source guard behavior rejects this local completion claim. | Public edit inputs | `tests/unit/test_page.py` |
| R4 | Valid edit behavior and adjacent page workflows remain green. | Adjacent page/source/revision/file/vote/site coverage passed 1381 tests; full unit passed 3807 tests. | Regressing valid omitted-title saves, explicit-title saves, edit-lock/save behavior, local source sync, revision-cache invalidation, page source/revision/file/vote workflows, site workflows, or full unit coverage rejects this local completion claim. | Page edit and adjacent workflows | `tests/unit` |
| R5 | The local proof stays unit-level and private-data-free. | All regressions use synthetic local fixtures and mocks. | Using live Wikidot, credentials, cookies, auth JSON, raw private page source, raw rollout paths, private site names, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `6948429 fix(page): validate retained edit title`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageEdit::test_edit_rejects_malformed_retained_title_before_login_or_delegation -q --tb=short` failed before the fix with `DID NOT RAISE`.
- GREEN focused: the same focused command passed 1 test after the fix.
- Edit coverage: `uv run pytest tests/unit/test_page.py::TestPageEdit -q` passed 14 tests after formatting.
- Adjacent page coverage: `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1381 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3807 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted after formatting the edited test file.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Page.edit(source=...)` raises `ValueError("title must be a string")` when the edited page's retained `title` is an integer or other non-string and the caller omits explicit `title`.
- The retained-title failure occurs before login checks, current-source reads, `Page.create_or_edit(...)`, local title/source mutation, revision-count sync, or revision-cache invalidation.
- The retained-title failure does not coerce or rewrite the corrupted retained `title`.
- Explicit invalid `title`, `comment`, `source`, and `force_edit` inputs still raise the same diagnostics before request work.
- Valid omitted-title edits still delegate the current retained string title.
- Valid explicit-title edits still update local state from the returned edited page after confirmed successful delegation.
- Existing edit lock/save behavior, local source sync, revision-cache invalidation, page source/revision/file/vote workflows, and site workflows remain green.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Callers with mutated or rehydrated malformed `Page.title` values now fail before edit work. Mitigation: constructor validation already requires strings, and corrupted retained state should be fixed before request construction rather than coerced into a page save payload.
- Risk: A valid omitted-title edit could accidentally stop preserving the current title. Mitigation: the implementation validates and reuses the retained title only when it is a string, and existing successful edit tests remain green.
- Risk: This could be mistaken for explicit page title/comment input validation. Mitigation: Issue 350 remains the explicit-input boundary; this slice only covers omitted `title=None` and corrupted retained state.

## Dependencies

- Existing `_validate_page_text_field(...)` remains the canonical page text-field validator.
- Existing `Page(title=...)` constructor validation remains unchanged.
- Existing `Page.edit(...)` source defaulting, `Page.create_or_edit(...)` delegation, local state sync, revision-count handling, revision-cache invalidation, and source-cache update behavior remains unchanged for valid values.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, cache ownership boundaries, result ergonomics, or complexity candidates outside this now-covered omitted-title edit path.

## Upstream-Safe Motivation

`Page.edit(source=...)` with omitted `title` still delegates a title to the page write helper, using the page's current retained title. That retained title should satisfy the same string contract as explicit `title=` before authentication, current-source reads, save delegation, or local cache mutation can happen. Validating it locally keeps corrupted fixture or rehydrated state from becoming a write payload while preserving valid omitted-title and explicit-title behavior.

## Local Evidence

- Local rollout-backed work established page editing as a practical workflow through login/source ordering, local title/source cache sync, revision-cache invalidation, page source input validation, explicit page title/comment validation, constructor title validation, and retained edit-site validation.
- Existing local drafts covered explicit `Page.edit(title=...)` input validation, constructor-time `Page.title` validation, retained edit parent site validation, source defaulting, edit-lock/save behavior, and cache invalidation; they did not cover post-construction malformed retained `self.title` state used by the omitted-title edit path.
- The focused RED failure showed malformed retained title state could reach a patched successful edit delegation and update local state instead of failing before login/delegation.
- This slice only validates the retained title used by omitted-title `Page.edit(...)` calls. It does not change parser field extraction, title normalization, source text contents, source acquisition internals, edit-lock handling, save response handling, metadata writes, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw page source text, rendered page content, private page content, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates type only. It does not reject empty titles, trim titles, coerce non-string values, reassign `self.title` during preflight, or change the local title update rule after successful edit delegation.
