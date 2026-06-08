# PR Draft: Validate Non-Negative Page IDs

## Summary

`Page._id`, the public `Page.id` setter, and `Page.create_or_edit(..., page_id=...)` all represent Wikidot page identity. Existing local drafts validated these boundaries as non-boolean integers or `None`, but range semantics remained open, so direct constructors, property assignment, and create/edit inputs still accepted negative integers such as `-1`. Generated page-ID acquisition already parses digit-only values, so this gap is limited to direct page state and explicit write-path inputs.

This change validates page IDs as non-negative integers at the direct constructor, public setter, and create/edit argument boundaries. It preserves `0` as a non-negative value instead of introducing a stronger positive-ID requirement.

## Outcome

Direct and write-path page ID inputs can no longer store or submit negative page IDs, while lazy ID acquisition, zero-ID compatibility, malformed-type diagnostics, generated page-ID parsing, source/revision/vote/file workflows, create/edit behavior for valid IDs, and adjacent site workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page inventories, source/revision/vote/file workflows, publish ledgers, generated page queues, local fixtures, or serialized and rehydrated `Page` records.

## Current Evidence

[412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md) validates malformed `Page.create_or_edit(..., page_id=...)` types before write-side requests. [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md) validates malformed public `Page.id = ...` assignment types. [489-pr-validate-page-constructor-id-field.md](489-pr-validate-page-constructor-id-field.md) validates malformed constructor `_id` types. [586-pr-validate-page-batch-target-site.md](586-pr-validate-page-batch-target-site.md) and adjacent source/revision/vote/file drafts establish page IDs as request grouping and cache identity state.

This slice is not a duplicate of Issues 412, 413, or 489. Those drafts reject booleans, strings, floats, and arbitrary objects, but they still accept negative integers. This slice closes the separate numeric range boundary and leaves generated parser/acquisition behavior untouched.

## Related Issue / Non-Duplicate Analysis

Builds directly on [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), [489-pr-validate-page-constructor-id-field.md](489-pr-validate-page-constructor-id-field.md), and [586-pr-validate-page-batch-target-site.md](586-pr-validate-page-batch-target-site.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject direct `Page(_id=-1)` with `ValueError("page.id must be non-negative or None")`.
- Reject `page.id = -1` with `ValueError("page.id must be non-negative")` before mutating a cached valid ID.
- Reject `Page.create_or_edit(..., page_id=-1)` with `ValueError("page_id must be non-negative or None")` before login or AMC work.
- Preserve existing malformed-type diagnostics for constructor, setter, and create/edit page IDs.
- Preserve `0` as a valid direct constructor and setter value.

## Type Of Change

- Input validation
- Public constructor and property behavior hardening
- Page write preflight hardening
- Page identity state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `Page(_id=-1)` must raise `ValueError("page.id must be non-negative or None")`. |
| R2 | Direct `page.id = -1` must raise `ValueError("page.id must be non-negative")` and preserve the previous cached ID. |
| R3 | `Page.create_or_edit(..., page_id=-1)` must raise `ValueError("page_id must be non-negative or None")` before login or AMC request work. |
| R4 | Direct `Page(_id=0)` and `page.id = 0` must remain valid. |
| R5 | Existing malformed direct type diagnostics must remain stable. |
| R6 | Generated page-ID acquisition, source/revision/vote/file workflows, create/edit behavior for valid IDs, and adjacent site workflows must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, page constructor/page tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct constructor cached page IDs cannot be negative. | `TestPageInit.test_init_rejects_negative_optional_id` failed RED with `DID NOT RAISE`, then passed GREEN after `_validate_optional_page_constructor_id(...)` rejected values below zero. | Accepting `_id=-1`, coercing it to `0`, or changing malformed-type behavior rejects this local completion claim. | Page constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Public setter assignments cannot corrupt cached page IDs with negative values. | `TestPageProperties.test_id_setter_rejects_negative_ids` failed RED with `DID NOT RAISE`, then passed GREEN and asserted the previous ID remained `12345`. | Mutating `_id` before raising, clearing the cached ID, or treating negative IDs as normal request IDs rejects this local completion claim. | Page ID setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Create/edit rejects negative page IDs before side effects. | `TestPageCreateOrEdit.test_create_or_edit_rejects_negative_page_id_before_login` failed RED after reaching lock handling, then passed GREEN with no login or AMC request call. | Calling login, taking a page lock, submitting a save, or raising a later lock/save diagnostic rejects this local completion claim. | Page write preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Zero remains valid for direct stored page IDs. | `TestPageInit.test_init_accepts_valid_optional_id` passed with `_id=0`, and `TestPageProperties.test_id_setter_accepts_zero_id` passed with `page.id = 0`. | Requiring positive-only page IDs without separate evidence rejects this local completion claim. | Constructor and setter compatibility | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py` |
| R5 | Existing malformed direct type diagnostics remain stable. | Existing malformed constructor, setter, and create/edit page-ID tests passed in focused RED and GREEN commands. | Changing `page.id must be an integer or None`, `page.id must be an integer`, or `page_id must be an integer or None` rejects this local completion claim. | Page ID type validation | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py` |
| R6 | Existing page workflows remain green. | Page constructor/page suites passed 493 tests, and the full unit suite passed 2888 tests. | Regressing generated page-ID acquisition, source/revision/vote/file acquisition, create/edit for valid IDs, page collection batching, or site workflows rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regression coverage uses unit-level synthetic objects and mocks only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, page suites, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `476e4cf fix(page): validate non-negative page ids`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_optional_id tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_optional_id tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_negative_optional_id tests/unit/test_page.py::TestPageProperties::test_id_setter_rejects_invalid_ids tests/unit/test_page.py::TestPageProperties::test_id_setter_rejects_negative_ids tests/unit/test_page.py::TestPageProperties::test_id_setter_accepts_zero_id tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_rejects_invalid_page_id_before_login tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_rejects_negative_page_id_before_login -q` failed 3 new negative page-ID cases before the fix; 19 malformed-type and zero-ID guard cases stayed green.
- GREEN: the same focused command passed 22 tests after page-ID range validation was added.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py tests/unit/test_page.py` left 3 files unchanged.
- `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py -q` passed 493 tests.
- `uv run pytest tests/unit -q` passed 2888 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page(_id=-1)` raises `ValueError("page.id must be non-negative or None")`.
- `page.id = -1` raises `ValueError("page.id must be non-negative")` and leaves a previous cached ID unchanged.
- `Page.create_or_edit(site, "page", page_id=-1, ...)` raises `ValueError("page_id must be non-negative or None")` before login or AMC request work.
- `Page(_id=0)` and `page.id = 0` remain accepted.
- Existing malformed type diagnostics for constructor `_id`, setter `id`, and create/edit `page_id` remain unchanged.
- Generated page-ID acquisition, page source/revision/vote/file workflows, valid create/edit page IDs, and adjacent site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Page IDs drive request grouping, lazy acquisition, source/revision/vote/file fetches, and write-side edit targeting. Negative IDs can look like valid integers in fixtures or generated ledgers but are not useful page identity state. Non-negative validation catches the problem at the boundary while avoiding stronger positive-only semantics.

## Local Evidence

- Local rollout evidence uses page IDs in browser-free page inventories, source/revision/vote/file workflows, publish ledgers, generated page queues, local fixtures, and serialized records.
- Existing local drafts covered malformed page-ID types for create/edit, public assignment, and direct construction, but did not cover negative integer IDs.
- The focused RED failures showed negative page IDs were accepted at direct and write preflight boundaries. The GREEN regressions cover invalid values, zero compatibility, existing malformed type validation, no-login/no-AMC preflight behavior, and full page workflow compatibility.
- This slice only validates non-negative page-ID semantics. It does not change generated page-ID parsing, URL construction, lazy acquisition, page collection entry validation, publish result rows, source/revision/vote/file cache semantics, live Wikidot behavior, or upstream actions.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

This change intentionally validates non-negative page IDs only. It does not require positive IDs and does not change generated page-ID acquisition because that path already extracts digit-only values from page lookup responses.
