# PR Draft: Validate Page Edit Site

## Summary

`Page.edit()` already validates explicit title, source, comment, and force-edit inputs before write work, and earlier slices made unauthenticated edits fail before current-source reads. One adjacent action-time state boundary still trusted `page.site` after construction: if a caller, fixture, or rehydrated page object replaced `page.site` with a mock, dictionary-like object, or other non-`Site` value, `edit()` could reach login checks, delegate into `Page.create_or_edit(...)`, and mutate local title/source/revision cache state before reporting the parent-site problem.

This change revalidates `self.site` at the start of `Page.edit()` after explicit edit-input validation and before login or create/edit delegation. Malformed action-time page sites now raise `ValueError("site must be a Site")` before login checks, current-source reads, save delegation, revision-cache invalidation, revision-count sync, or local source/title mutation. Valid edits, default title/source/comment handling, forced unlocks, empty source saves, invalid input precedence, unauthenticated login behavior, local cache sync, and revision-count handling remain unchanged.

## Outcome

`Page.edit()` now has an explicit action-time parent-site preflight consistent with the page constructor and the adjacent page write action guards.

## Current Evidence

Existing drafts [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [259-pr-page-edit-local-cache-sync.md](259-pr-page-edit-local-cache-sync.md), [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md), [262-pr-page-edit-revision-count-sync.md](262-pr-page-edit-revision-count-sync.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), and [563-pr-validate-page-set-metadata-site.md](563-pr-validate-page-set-metadata-site.md) establish edit login ordering, local edit cache behavior, edit input validation, constructor site validation, and adjacent page action-time site validation. This slice covers mutated `Page.site` at `Page.edit()` time, not direct page construction, explicit edit input shape, direct `Page.create_or_edit(...)` arguments, or save-response shape.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.site` at the start of `Page.edit()` after explicit edit input validation.
- Use the validated site for `login_check()` and `Page.create_or_edit(...)` delegation.
- Add a regression for a mutated non-`Site` `page.site` that asserts no login check, no create/edit delegation, and no local title/source/revision mutation.
- Preserve valid edit behavior, forced unlocks, empty source saves, unauthenticated login behavior, invalid input precedence, local source/title sync, revision-cache invalidation, and revision-count sync.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.edit()` must reject a mutated non-`Site` `page.site` with `ValueError("site must be a Site")` before login checks, current-source reads, create/edit delegation, revision-cache invalidation, revision-count sync, or local source/title mutation. |
| R2 | Invalid title, source, comment, and force-edit input validation must retain precedence over site validation. |
| R3 | Valid edits, forced unlocks, empty source saves, default field handling, unauthenticated login behavior, local cache sync, and revision-count handling must remain stable. |
| R4 | Full page module tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A mutated non-`Site` parent fails before edit side-effect surfaces. | `TestPageEdit.test_edit_rejects_malformed_site_before_login_or_delegation` failed RED with `DID NOT RAISE` while the mocked login/delegation path mutated local state, then passed GREEN with `ValueError("site must be a Site")`. | Calling `login_check()`, calling `Page.create_or_edit(...)`, accepting dictionaries/mocks as sites, mutating `title`, mutating `_source`, mutating `_revisions`, changing `revisions_count`, or leaking delegated save behavior rejects this local completion claim. | `Page.edit()` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Malformed edit inputs still fail before parent-site validation. | Existing invalid title/source/comment/force-edit tests stayed green in the focused GREEN run, the full page module run, and the full unit suite. | Checking malformed sites first, accepting non-string edit text, accepting non-string source, accepting non-bool force-edit controls, or reaching login/request/delegation for invalid inputs rejects this local completion claim. | Edit input validation | `tests/unit/test_page.py` |
| R3 | Successful and existing edit workflows remain stable. | Focused edit tests for valid edit, forced unlock, local cache sync, revision-cache invalidation, revision-count sync, stale revision-count preservation, empty source, and unauthenticated login behavior passed, as did the full page module and full unit suite. | Changing request shape, default-source behavior, empty-source behavior, login ordering, local title/source sync, revision-cache invalidation, or revision-count sync rejects this local completion claim. | Valid edit paths | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Existing repository quality gates remain green. | Focused edit tests passed 13 tests, full page module tests passed 288 tests, full unit passed 2659 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live auth material or private state is needed to prove the behavior. | The regression uses a synthetic mutated site and mocked unit-level page state; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, or live account details. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `dde03dd fix(page): validate edit site`.

- RED action-time site validation: `uv run pytest tests/unit/test_page.py::TestPageEdit::test_edit_rejects_malformed_site_before_login_or_delegation -q` failed before the fix with `DID NOT RAISE`; the malformed site reached the mocked login/delegation path and local edit state was mutated instead of raising `ValueError("site must be a Site")`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageEdit::test_edit_rejects_malformed_site_before_login_or_delegation tests/unit/test_page.py::TestPageEdit::test_edit_not_logged_in_does_not_fetch_current_source tests/unit/test_page.py::TestPageEdit::test_edit_existing_page tests/unit/test_page.py::TestPageEdit::test_edit_force_unlock tests/unit/test_page.py::TestPageEdit::test_edit_updates_local_title_and_source_cache tests/unit/test_page.py::TestPageEdit::test_edit_invalidates_local_revision_cache tests/unit/test_page.py::TestPageEdit::test_edit_updates_local_revisions_count_from_result tests/unit/test_page.py::TestPageEdit::test_edit_keeps_local_revisions_count_when_result_is_stale tests/unit/test_page.py::TestPageEdit::test_edit_allows_empty_source tests/unit/test_page.py::TestPageEdit::test_edit_rejects_non_string_source_before_request tests/unit/test_page.py::TestPageEdit::test_edit_rejects_non_bool_force_edit_before_request tests/unit/test_page.py::TestPageEdit::test_edit_rejects_non_string_text_inputs_before_request -q` passed 13 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 288 tests.
- `uv run pytest tests/unit -q` passed 2659 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.edit()` rejects a mutated malformed `page.site` with `ValueError("site must be a Site")` before login checks, current-source reads, create/edit delegation, revision-cache invalidation, revision-count sync, or local title/source mutation.
- Invalid edit inputs still fail before site validation and before request work.
- Valid edit behavior, forced unlocks, empty source saves, unauthenticated login behavior, local cache sync, and revision-count handling remain intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed invalid mutated parent state reaching mocked login/delegation and local edit mutation before validation.
- This slice only validates mutated `Page.site` before `Page.edit()`. It does not change page construction, direct `Page.create_or_edit(...)`, publish workflows, metadata writes, response validation, edit input validation, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private-message content, and live Wikidot account details out of upstream discussion.
