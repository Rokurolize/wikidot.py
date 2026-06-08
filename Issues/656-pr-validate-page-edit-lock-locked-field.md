# PR Draft: Validate Page Edit-Lock Locked Field

## Summary

`Page.create_or_edit(...)` uses Wikidot's `edit/PageEditModule` response to classify lock conflicts before sending `savePage`. The fixture-backed edit-lock responses show `locked` as a boolean when present, while the existing-page response may omit it. Before this fix, malformed falsey present `locked` values such as `None`, `0`, `[]`, or `{}` could be accepted and the save path could proceed, while malformed truthy values such as `1`, `"false"`, or `"true"` were misclassified as real lock conflicts and raised `TargetErrorException`.

This change validates a present edit-lock `locked` field as a real boolean before lock-conflict classification. A missing `locked` key still means unlocked for existing/new page compatibility, `locked=True` still reports a real lock conflict, and malformed present values now raise contextual `NoElementException` before `savePage`.

## Outcome

Malformed returned edit-lock lock-state data no longer reaches the save path or gets reported as a legitimate page lock. Valid `locked=True` conflicts, omitted `locked` responses, edit-lock token validation, revision-ID validation, save-status diagnostics, stale-search fallback, `Page.edit(...)`, `site.page.publish(...)`, and adjacent page workflows keep their existing behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page creation/editing, page publishing, migration scripts, fixture generators, page-write adapters, or publish ledgers where malformed edit-lock response state should be distinguished from a real page lock.

## Current Evidence

Page write drafts [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [653-pr-validate-page-edit-lock-revision-ids.md](653-pr-validate-page-edit-lock-revision-ids.md), [654-pr-validate-page-edit-lock-token-fields.md](654-pr-validate-page-edit-lock-token-fields.md), and [655-pr-validate-page-edit-lock-revision-before-page-id.md](655-pr-validate-page-edit-lock-revision-before-page-id.md) establish `Page.create_or_edit(...)`, edit locks, lock fields, revision IDs, caller page IDs, save requests, and browser-free publishing as practical mutation boundaries.

This slice is not a duplicate of those drafts. Issue 242 covers contextual handling for missing edit-lock token fields, Issue 653 covers returned `page_revision_id` value validation, Issue 654 covers present edit-lock token value validation, Issue 655 covers revision-ID validation precedence before missing caller `page_id`, and Issue 351 covers caller boolean controls. This draft covers the returned edit-lock `locked` field shape that decides whether an edit-lock response is a real lock conflict.

## Related Issue / Non-Duplicate Analysis

Builds directly on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [653-pr-validate-page-edit-lock-revision-ids.md](653-pr-validate-page-edit-lock-revision-ids.md), [654-pr-validate-page-edit-lock-token-fields.md](654-pr-validate-page-edit-lock-token-fields.md), and [655-pr-validate-page-edit-lock-revision-before-page-id.md](655-pr-validate-page-edit-lock-revision-before-page-id.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate a present returned edit-lock `locked` field as `bool` before lock-conflict classification.
- Treat a missing `locked` key as unlocked to preserve existing-page and new-page compatibility.
- Preserve `locked=True` as `TargetErrorException` lock-conflict behavior.
- Preserve edit-lock `lock_id`, `lock_secret`, and `page_revision_id` validation; save request shape; `raise_on_exists`; save-status handling; stale-search fallback; `Page.edit(...)`; `site.page.publish(...)`; live Wikidot behavior; pushes; upstream Issues; and upstream PRs.
- Leave `other_locks` shape and behavior unchanged because this slice only has fixture-backed evidence for `locked`.

## Type Of Change

- Response validation
- Page mutation-boundary hardening
- Lock-conflict diagnostic classification fix
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Present edit-lock `locked` values with falsey malformed shapes such as `None`, `0`, `[]`, or `{}` must raise contextual `NoElementException` before `savePage`. |
| R2 | Present edit-lock `locked` values with truthy malformed shapes such as `1`, `"false"`, or `"true"` must raise contextual `NoElementException`, not `TargetErrorException`. |
| R3 | A valid edit-lock response with `locked=True` must still raise the lock-conflict `TargetErrorException`. |
| R4 | A missing `locked` key must keep existing-page and new-page behavior compatible. |
| R5 | Existing edit-lock token validation, revision-ID validation, save-status diagnostics, create/edit behavior, stale-search fallback, `Page.edit(...)`, `site.page.publish(...)`, and adjacent page workflows must remain stable. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source text, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, create/edit tests, adjacent page/site/revision/source tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Falsey malformed present `locked` values fail at the edit-lock response boundary before the save path. | `test_create_or_edit_malformed_locked_field_value_fails_before_save` failed RED for `None`, `0`, `[]`, and `{}` with no expected exception, then passed GREEN after validation. | Proceeding to `savePage`, accepting falsey malformed values as unlocked, or raising a caller precondition rejects this local completion claim. | `Page.create_or_edit` edit-lock response parsing | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Truthy malformed present `locked` values fail as malformed response data rather than real lock conflicts. | The same focused test failed RED for `1`, `"false"`, and `"true"` with `TargetErrorException`, then passed GREEN with `NoElementException`. | Raising `TargetErrorException`, coercing truthy values, or treating strings/numbers as real lock state rejects this local completion claim. | `Page.create_or_edit` lock-conflict classification | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Valid `locked=True` conflict behavior stays stable. | `test_edit_locked_page` passed in the focused RED and GREEN commands and in the broader create/edit class. | Changing the exception type/message for a real lock conflict rejects this local completion claim. | Page lock conflict handling | `tests/unit/test_page.py` |
| R4 | Missing `locked` remains compatible with existing-page and new-page responses. | `test_create_new_page` and `test_edit_existing_page_stale_search_preserves_page_id` passed in the focused commands and broader create/edit class. | Requiring `locked` for existing pages, rejecting omitted `locked`, or changing new-page behavior rejects this local completion claim. | Page create/edit paths | `tests/unit/test_page.py` |
| R5 | Adjacent page workflows stay green. | The create/edit class passed 65 tests, `TestPageEdit` passed 13 tests, `TestSitePageAccessor` passed 92 tests, `tests/unit/test_page.py` passed 350 tests, adjacent page/site/page-revision/page-source suites passed 777 tests, and full unit passed 2989 tests. | Regressing lock conflicts, token validation, revision-ID validation, valid saves, `Page.edit`, publish helpers, page accessors, page revision/source behavior, save-status diagnostics, or any existing unit test rejects this local completion claim. | Page workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_source.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic edit-lock responses and mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, create/edit tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `16a7a54 fix(page): validate edit lock locked field`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_malformed_locked_field_value_fails_before_save tests/unit/test_page.py::TestPageCreateOrEdit::test_edit_locked_page tests/unit/test_page.py::TestPageCreateOrEdit::test_create_new_page tests/unit/test_page.py::TestPageCreateOrEdit::test_edit_existing_page_stale_search_preserves_page_id -q` failed 7 malformed present `locked` cases before the fix; the valid locked-page, new-page, and existing-page stale-search guards passed.
- GREEN: the same focused command passed 10 tests after the edit-lock `locked` field validation was added before conflict classification.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left both files unchanged.
- `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit -q` passed 65 tests.
- `uv run pytest tests/unit/test_page.py::TestPageEdit -q` passed 13 tests.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed 92 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 350 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_revision.py tests/unit/test_page_source.py -q` passed 777 tests.
- `uv run pytest tests/unit -q` passed 2989 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.create_or_edit(...)` rejects present edit-lock `locked=None`, `0`, `1`, `"false"`, `"true"`, `[]`, and `{}` with `NoElementException` before `savePage`.
- Malformed truthy present `locked` values are not misclassified as real lock conflicts.
- `locked=True` still raises the lock-conflict `TargetErrorException`.
- Missing `locked` remains compatible with new-page and existing-page responses.
- `other_locks` behavior remains unchanged.
- Existing edit-lock token validation, revision-ID validation, save-status diagnostics, create/edit behavior, `Page.edit(...)`, and page-accessor workflows remain unchanged.
- Live Wikidot behavior, pushes, upstream Issues, and upstream PRs remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

The edit-lock response is the source of truth for whether a page is locked before wikidot.py attempts to save. A real lock conflict should remain a `TargetErrorException`, but malformed lock-state data should be reported as malformed response data. Validating `locked` before truthiness checks keeps synthetic bad values from either reaching `savePage` or producing a misleading real-lock diagnostic.

## Local Evidence

- Local rollout-backed drafts repeatedly use browser-free page creation/editing, publishing, post-save lookup, source verification, metadata updates, and page-write audit ledgers.
- Existing local drafts covered missing lock fields, token value validation, returned revision-ID validation, revision-ID precondition precedence, caller-provided page-ID validation, save-response reuse, and save-status diagnostics, but did not cover malformed returned `locked` values being accepted or misclassified by truthiness.
- The focused RED failure showed malformed falsey present `locked` values did not raise before the save path, while malformed truthy present `locked` values raised the real lock-conflict exception.
- This slice only validates the returned edit-lock `locked` field. It does not change login behavior, edit-lock request construction, token validation, revision-ID validation, save status parsing, post-save search fallback, page URL construction, direct page or revision constructors, publish result construction, live site behavior, parser behavior, or `other_locks`.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally treats a missing `locked` key differently from a present malformed value. Missing remains compatible with existing fixtures and page flows, while present values must be real booleans before lock-conflict classification.
