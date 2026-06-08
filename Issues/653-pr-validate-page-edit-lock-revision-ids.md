# PR Draft: Validate Page Edit-Lock Revision IDs

## Summary

`Page.create_or_edit(...)` acquires Wikidot's `edit/PageEditModule` response, checks whether the page already exists, requires `lock_id` and `lock_secret`, and forwards an optional `page_revision_id` as `revision_id` in the later `savePage` request. Existing local drafts already cover browser-free page writes, missing edit-lock fields, save-status diagnostics, caller-provided page ID preflight/range validation, and direct page-revision ID range validation. One response-boundary gap remained: when `page_revision_id` was present but `None`, a boolean, a string, a float, or a negative integer, the value was treated as existing-page state and copied into the save request.

This change validates a present edit-lock `page_revision_id` as a non-boolean non-negative integer before `savePage`. A missing `page_revision_id` still means the new-page path, `page_revision_id=0` remains valid for compatibility, and valid positive IDs keep the same request shape.

## Outcome

Malformed or negative edit-lock revision IDs fail before `savePage`, while new-page saves, valid existing-page saves, zero-ID compatibility, lock-field diagnostics, save-status diagnostics, stale-search fallback, and adjacent page workflows keep their existing behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page creation/editing, page publishing, migration scripts, fixture generators, page-write adapters, or publish ledgers where malformed edit-lock responses should not leak into write requests.

## Current Evidence

Page write drafts [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md), [189-pr-page-create-edit-existing-search-fallback.md](189-pr-page-create-edit-existing-search-fallback.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), and [639-pr-validate-non-negative-page-ids.md](639-pr-validate-non-negative-page-ids.md) establish `Page.create_or_edit(...)`, edit locks, save requests, and browser-free publishing as practical mutation boundaries.

This slice is not a duplicate of those drafts. Issue 242 covers missing `lock_id` and `lock_secret` context, but not the optional edit-lock revision ID. Issue 243 covers the returned `savePage` status, but by then the malformed `revision_id` payload has already been sent. Issue 412 and Issue 639 cover caller-provided page IDs and direct `Page` state, not returned edit-lock revision IDs. Issue 638 covers direct page-revision record IDs, and Issue 649 covers forum-post edit-form `currentRevisionId`; neither validates `Page.create_or_edit(...)`'s edit-lock `page_revision_id` before saving a page.

## Related Issue / Non-Duplicate Analysis

Builds directly on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md), [189-pr-page-create-edit-existing-search-fallback.md](189-pr-page-create-edit-existing-search-fallback.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md), [639-pr-validate-non-negative-page-ids.md](639-pr-validate-non-negative-page-ids.md), and [649-pr-validate-non-negative-forum-post-edit-revision-ids.md](649-pr-validate-non-negative-forum-post-edit-revision-ids.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_page_edit_revision_id(...)` for `Page.create_or_edit(...)` edit-lock response data.
- Return `None` only when the `page_revision_id` key is absent, preserving the new-page path.
- Reject present non-integer and boolean values with contextual `NoElementException`.
- Reject present negative integers with contextual `NoElementException`.
- Use the validated value when constructing the `savePage` `revision_id` payload.
- Preserve valid zero and positive revision IDs.
- Preserve lock acquisition, lock conflict handling, `raise_on_exists`, save request shape for valid IDs, save-status handling, stale search fallback, `Page.edit(...)`, `site.page.publish(...)`, live Wikidot behavior, pushes, upstream Issues, and upstream PRs.

## Type Of Change

- Returned response-field validation
- Page mutation-boundary hardening
- Write-request payload integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A present edit-lock `page_revision_id` with malformed values such as `None`, booleans, strings, or floats must raise contextual `NoElementException` before `savePage`. |
| R2 | A present negative edit-lock `page_revision_id` such as `-1` or `-100` must raise contextual `NoElementException` before `savePage`. |
| R3 | A missing `page_revision_id` key must keep the new-page save path and send an empty `revision_id` value. |
| R4 | `page_revision_id=0` and valid positive integer revision IDs must remain accepted and forwarded as `revision_id`. |
| R5 | Existing missing lock-field diagnostics, save-status diagnostics, create/edit behavior, stale-search fallback, `Page.edit(...)`, `site.page.publish(...)`, and adjacent page workflows must remain stable. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source text, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, create/edit tests, adjacent page/site/revision/source tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed present edit-lock revision IDs fail at the response boundary. | `test_create_or_edit_malformed_page_revision_id_fails_before_save` failed RED for `None`, `True`, `False`, `"100"`, and `100.0` with `DID NOT RAISE`, then passed GREEN after `_validate_page_edit_revision_id(...)` rejected malformed present values. | Accepting malformed values, coercing strings/floats/bools, or sending `savePage` rejects this local completion claim. | `Page.create_or_edit` edit-lock response parsing | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Negative present edit-lock revision IDs fail at the response boundary. | `test_create_or_edit_negative_page_revision_id_fails_before_save` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after the non-negative guard rejected values below zero. | Accepting negative values, coercing them to zero, treating them as new-page state, or sending `savePage` rejects this local completion claim. | `Page.create_or_edit` edit-lock response parsing | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Missing `page_revision_id` remains the new-page path. | `test_create_new_page` passed in the focused RED and GREEN commands and continued to send an empty `revision_id` for new pages. | Requiring `page_revision_id` for new pages or changing the new-page save payload rejects this local completion claim. | Page create path | `tests/unit/test_page.py` |
| R4 | Zero and positive existing-page revision IDs remain valid. | `test_create_or_edit_accepts_zero_page_revision_id`, `test_edit_existing_page_stale_search_preserves_page_id`, and the broader create/edit class passed after the fix. | Rejecting zero, rejecting valid positive integers, or changing existing-page request payloads rejects this local completion claim. | Page edit path | `tests/unit/test_page.py` |
| R5 | Adjacent page workflows stay green. | The create/edit class passed 33 tests, `TestPageEdit` passed 13 tests, `TestSitePageAccessor` passed 92 tests, `tests/unit/test_page.py` passed 318 tests, adjacent page/site/page-revision/page-source suites passed 745 tests, and full unit passed 2957 tests. | Regressing `Page.edit`, publish helpers, page accessors, page revision/source behavior, save-status diagnostics, lock-field diagnostics, or any existing unit test rejects this local completion claim. | Page workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_source.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic edit-lock responses and mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, create/edit tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `5bcf2f2 fix(page): validate edit lock revision ids`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_missing_lock_field_includes_site_page_and_field_context tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_malformed_page_revision_id_fails_before_save tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_negative_page_revision_id_fails_before_save tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_accepts_zero_page_revision_id tests/unit/test_page.py::TestPageCreateOrEdit::test_create_new_page tests/unit/test_page.py::TestPageCreateOrEdit::test_edit_existing_page_stale_search_preserves_page_id -q` failed 7 malformed/negative edit-lock revision-ID cases before the fix; 5 missing-lock-field/new-page/stale-search/zero guards stayed green.
- GREEN: the same focused command passed 12 tests after the edit-lock revision-ID guard was added.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left both files unchanged.
- `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit -q` passed 33 tests.
- `uv run pytest tests/unit/test_page.py::TestPageEdit -q` passed 13 tests.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed 92 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 318 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_revision.py tests/unit/test_page_source.py -q` passed 745 tests.
- `uv run pytest tests/unit -q` passed 2957 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.create_or_edit(...)` rejects present edit-lock `page_revision_id=None`, booleans, strings, and floats with `NoElementException`.
- The malformed-value exception message includes the site unix name, page fullname, `field=page_revision_id`, and the malformed value.
- `Page.create_or_edit(...)` rejects present edit-lock `page_revision_id=-1` and `page_revision_id=-100` with `NoElementException`.
- The negative-value exception message includes `must be non-negative`, the site unix name, page fullname, `field=page_revision_id`, and the negative value.
- Malformed and negative edit-lock revision IDs fail before `savePage`; tests assert only the edit-lock AMC request was made.
- A missing `page_revision_id` key remains the new-page path and sends an empty `revision_id`.
- `page_revision_id=0` remains valid and is forwarded as `revision_id=0`.
- Valid positive existing-page revision IDs remain valid.
- Existing missing lock-field diagnostics and save-status diagnostics remain unchanged.
- Live Wikidot behavior, pushes, upstream Issues, and upstream PRs remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

The edit-lock response is the source of truth for whether a page save is an existing-page update and which revision ID should be sent to `savePage`. Rejecting malformed or impossible present `page_revision_id` values at that boundary prevents invalid response data from becoming write-request payload state, without requiring a stronger positive-only invariant or changing the new-page path.

## Local Evidence

- Local rollout-backed drafts repeatedly use browser-free page creation/editing, publishing, post-save lookup, source verification, metadata updates, and page-write audit ledgers.
- Existing local drafts covered missing edit-lock fields, save-status diagnostics, caller-provided page IDs, direct page-revision IDs, and forum edit-form revision IDs, but did not cover malformed or negative integer `page_revision_id` values returned by the page edit-lock response.
- The focused RED failure showed malformed and negative present edit-lock revision IDs were accepted into `savePage` before this slice.
- This slice only validates present edit-lock `page_revision_id` values. It does not change login behavior, edit-lock request construction, lock conflict handling, `lock_id`/`lock_secret` requirements, save status parsing, post-save search fallback, page URL construction, direct page or revision constructors, publish result construction, live site behavior, or parser behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

This change intentionally treats a missing `page_revision_id` key differently from a present malformed value. Missing remains the documented new-page signal, while present values must be plausible existing-page revision IDs.
