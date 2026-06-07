# PR Draft: Validate Page Metas Setter Site

## Summary

`Page.metas = {...}` already validates explicit meta payloads before write work, batches delete/save meta actions, validates every returned metadata action status before updating `_metas`, and preserves local metadata state on malformed action responses. One adjacent action-time state boundary still trusted `page.site` after construction: if a caller, fixture, or rehydrated page object replaced `page.site` with a mock, dictionary-like object, or other non-`Site` value, the setter could reach login checks, AMC request construction, and response-pairing failures before reporting the parent-site problem.

This change revalidates `self.site` at the start of the `Page.metas` setter after explicit meta payload validation and before login or request work. Malformed action-time page sites now raise `ValueError("site must be a Site")` before login checks, meta lazy reads, metadata AMC requests, response handling, or local `_metas` mutation. Valid batched meta deletes/adds/updates, invalid meta input precedence, metadata action-status diagnostics, and local cache updates remain unchanged.

## Outcome

The direct `Page.metas = ...` metadata write path now has an explicit action-time parent-site preflight consistent with the page constructor, `Page.set_metadata()`, and the adjacent direct metadata action guards.

## Current Evidence

Existing drafts [007-pr-batch-meta-tag-updates.md](007-pr-batch-meta-tag-updates.md), [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [249-pr-page-metas-setter-action-status-context.md](249-pr-page-metas-setter-action-status-context.md), [348-pr-validate-meta-tag-inputs.md](348-pr-validate-meta-tag-inputs.md), [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), and [563-pr-validate-page-set-metadata-site.md](563-pr-validate-page-set-metadata-site.md) establish batched meta writes, meta setter response validation, explicit meta input validation, page constructor site validation, and adjacent batched metadata action-time site validation. This slice covers mutated `Page.site` at `Page.metas = ...` time, not metadata input shape, metadata response shape, or batched `Page.set_metadata(...)`.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.site` at the start of the `Page.metas` setter after explicit meta payload validation.
- Use the validated site for `login_check()`, batched `amc_request(...)`, and metadata action-status diagnostics.
- Add a regression for a mutated non-`Site` `page.site` that asserts no login check, no AMC request, no meta lazy fetch, and no local `_metas` mutation.
- Preserve valid batched meta changes, invalid input precedence, action-status diagnostics, and successful local cache updates.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.metas = ...` must reject a mutated non-`Site` `page.site` with `ValueError("site must be a Site")` before login checks, meta lazy reads, metadata AMC requests, response handling, or local `_metas` mutation. |
| R2 | Invalid meta payload validation must retain precedence over site validation. |
| R3 | Valid batched meta deletes/adds/updates and metadata action-status diagnostics must remain stable. |
| R4 | Focused metas setter tests, full page module tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A mutated non-`Site` parent fails before direct meta setter side-effect surfaces. | `TestPageWriteMethods.test_metas_setter_rejects_malformed_site_before_login` failed RED by reaching mocked login/request work and then raising `ValueError("zip() argument 2 is shorter than argument 1")`, then passed GREEN with `ValueError("site must be a Site")`. | Calling `login_check()`, calling `amc_request(...)`, calling `amc_request_with_retry(...)`, accepting dictionaries/mocks as sites, mutating `_metas`, or leaking response-pairing errors rejects this local completion claim. | `Page.metas` setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Malformed meta payloads still fail before parent-site validation. | Existing invalid metas setter tests stayed green in the focused GREEN run, the full page module run, and the full unit suite. | Checking malformed sites first, accepting non-dictionary metas, accepting non-string meta keys, accepting non-string meta values, or reaching login/request work for invalid metas rejects this local completion claim. | Meta input validation | `tests/unit/test_page.py` |
| R3 | Successful valid meta writes and response diagnostics remain stable. | `test_metas_setter_batches_changes`, `test_metas_setter_missing_action_status_does_not_update_local_state`, and adjacent `Page.set_metadata()` tests passed in the focused GREEN run, the full page module run, and the full unit suite. | Changing request shape, diff behavior, local update timing, malformed response diagnostics, or successful `_metas` cache replacement rejects this local completion claim. | Direct meta write paths | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Existing repository quality gates remain green. | Focused metadata tests passed 6 tests, full page module tests passed 289 tests, full unit passed 2660 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live auth material or private state is needed to prove the behavior. | The regression uses a synthetic mutated site and mocked unit-level page state; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, or live account details. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `7103a78 fix(page): validate metas setter site`.

- RED action-time site validation: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_rejects_malformed_site_before_login -q` failed before the fix because mutated `page.site` reached mocked login/request work and then raised `ValueError("zip() argument 2 is shorter than argument 1")` instead of `ValueError("site must be a Site")`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_rejects_malformed_site_before_login tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_batches_changes tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_missing_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_rejects_invalid_metas_before_request tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_malformed_site_before_login tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_batches_tags_parent_and_metas -q` passed 6 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 289 tests.
- `uv run pytest tests/unit -q` passed 2660 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.metas = ...` rejects a mutated malformed `page.site` with `ValueError("site must be a Site")` before login checks, meta lazy reads, metadata AMC requests, returned-status handling, or local `_metas` mutation.
- Invalid meta payloads still fail before site validation and before request work.
- Valid batched meta writes, response diagnostics, and local cache updates remain intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed invalid mutated parent state reaching mocked login/request work before validation.
- This slice only validates mutated `Page.site` before the direct `Page.metas` setter. It does not change page construction, lookup, create/edit behavior, `Page.set_metadata(...)`, direct tag/parent APIs, response validation, metadata input validation, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private-message content, and live Wikidot account details out of upstream discussion.
