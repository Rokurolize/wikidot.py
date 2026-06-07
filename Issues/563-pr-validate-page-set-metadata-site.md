# PR Draft: Validate Page Set Metadata Site

## Summary

`Page.set_metadata()` already validates explicit tag, parent, and meta payloads before request construction, validates each returned metadata action status before local mutation, and preserves local tags, parent, and meta cache state on malformed action responses. One adjacent action-time state boundary still trusted `page.site` after construction: if a caller, fixture, or rehydrated page object replaced `page.site` with a mock, dictionary-like object, or other non-`Site` value, `set_metadata()` could reach login checks, AMC request construction, and response-pairing failures before reporting the parent-site problem.

This change revalidates `self.site` at the start of `Page.set_metadata()` after metadata input validation and before login or request work. Malformed action-time page sites now raise `ValueError("site must be a Site")` before login checks, metadata AMC requests, meta reads, response handling, or local metadata mutation. Valid batched tag/parent/meta updates, invalid input precedence, parent clearing, empty-parent normalization, action-status diagnostics, and local state updates remain unchanged.

## Outcome

`Page.set_metadata()` now has an explicit action-time parent-site preflight consistent with the page constructor and the adjacent direct metadata action guards.

## Current Evidence

Existing drafts [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), [348-pr-validate-meta-tag-inputs.md](348-pr-validate-meta-tag-inputs.md), [531-pr-validate-metadata-tag-inputs.md](531-pr-validate-metadata-tag-inputs.md), [558-pr-validate-page-commit-tags-site.md](558-pr-validate-page-commit-tags-site.md), and [559-pr-validate-page-set-parent-site.md](559-pr-validate-page-set-parent-site.md) establish the batched helper, metadata action-status validation, explicit metadata input validation, and adjacent direct metadata action-time site validation. This slice covers mutated `Page.site` at `Page.set_metadata()` time, not metadata input shape or metadata response shape.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.site` at the start of `Page.set_metadata()` after explicit metadata input validation.
- Use the validated site for `login_check()`, batched `amc_request(...)`, and metadata action-status diagnostics.
- Add a regression for a mutated non-`Site` `page.site` that asserts no login check, AMC request, or meta lazy fetch occurs and local tags, parent, and meta cache remain unchanged.
- Preserve valid batched metadata updates, invalid input precedence, parent clearing, empty-parent normalization, response diagnostics, and local state updates.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.set_metadata()` must reject a mutated non-`Site` `page.site` with `ValueError("site must be a Site")` before login checks, metadata AMC requests, meta reads, response handling, or local metadata mutation. |
| R2 | Invalid tag, parent, and meta input validation must retain precedence over site validation. |
| R3 | Valid batched tag/parent/meta updates, parent clearing, and empty-string parent clearing must remain stable. |
| R4 | Missing metadata action status diagnostics must remain unchanged and must not update local metadata state. |
| R5 | Focused set-metadata tests, full page module tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A mutated non-`Site` parent fails before metadata side-effect surfaces. | `TestPageWriteMethods.test_set_metadata_rejects_malformed_site_before_login` failed RED by reaching mocked login/request work and then raising `ValueError("zip() argument 2 is shorter than argument 1")`, then passed GREEN with `ValueError("site must be a Site")`. | Calling `login_check()`, calling `amc_request(...)`, calling `amc_request_with_retry(...)`, accepting dictionaries/mocks as sites, mutating local `tags`, mutating `parent_fullname`, mutating `_metas`, or leaking response-pairing errors rejects this local completion claim. | `Page.set_metadata()` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Malformed metadata inputs still fail before parent-site validation. | Existing invalid tag, parent, and metas tests stayed green in the focused GREEN run, the full page module run, and the full unit suite. | Checking malformed sites first, accepting invalid tag containers, accepting invalid parent values, or accepting invalid meta dictionaries rejects this local completion claim. | Metadata input validation | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Successful valid metadata updates remain stable. | `test_set_metadata_batches_tags_parent_and_metas`, `test_set_metadata_can_clear_parent`, and `test_set_metadata_empty_parent_string_clears_local_parent` passed in the focused GREEN run, the full page module run, and the full unit suite. | Changing request shape, tag serialization, parent clear normalization, meta diff request construction, return value, or local update timing rejects this local completion claim. | Valid metadata write paths | `tests/unit/test_page.py` |
| R4 | Existing response diagnostics remain stable. | `test_set_metadata_missing_action_status_does_not_update_local_state` passed in the focused GREEN run, the full page module run, and the full unit suite. | Updating local metadata from malformed responses, losing site/page/event/field diagnostics, or accepting malformed metadata action responses rejects this local completion claim. | Metadata response handling | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Existing repository quality gates remain green. | Focused set-metadata tests passed 11 tests, full page module tests passed 287 tests, full unit passed 2658 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regression uses a synthetic mutated site and mocked unit-level page state; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, or live account details. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `e888bf4 fix(page): validate set metadata site`.

- RED action-time site validation: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_malformed_site_before_login -q` failed before the fix because mutated `page.site` reached mocked login/request work and then raised `ValueError("zip() argument 2 is shorter than argument 1")` instead of `ValueError("site must be a Site")`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_malformed_site_before_login tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_batches_tags_parent_and_metas tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_missing_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_can_clear_parent tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_non_string_parent_before_request tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_invalid_tags_before_request tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_invalid_metas_before_request tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_empty_parent_string_clears_local_parent -q` passed 11 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 287 tests.
- `uv run pytest tests/unit -q` passed 2658 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.set_metadata()` rejects a mutated malformed `page.site` with `ValueError("site must be a Site")` before login checks, metadata AMC requests, meta reads, returned-status handling, or local metadata mutation.
- Invalid metadata inputs still fail before site validation and before request work.
- Valid batched metadata updates, parent clearing, response diagnostics, and local state updates remain intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed invalid mutated parent state reaching mocked login/request work before validation.
- This slice only validates mutated `Page.site` before `Page.set_metadata()`. It does not change page construction, lookup, create/edit behavior, direct tag/parent/meta APIs, response validation, metadata input validation, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private-message content, and live Wikidot account details out of upstream discussion.
