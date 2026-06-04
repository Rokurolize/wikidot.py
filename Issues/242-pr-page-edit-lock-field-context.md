# PR Draft: Include Context In Malformed Page Edit Lock Field Errors

## Summary

`Page.create_or_edit(...)` acquires Wikidot's generated edit lock through `edit/PageEditModule` before sending the `savePage` action. Earlier local slices established this browser-free page write path as a practical workflow surface by hardening create/edit fallback behavior, save-response handling, lock-secret masking, publish orchestration, source verification, post-save visibility polling, and the `Page.edit(...)` login-before-read boundary. One adjacent malformed-response gap remained: if the edit-lock response was present but omitted `lock_id` or `lock_secret`, wikidot.py accessed the dictionary field directly and leaked a raw Python `KeyError` before the save request could be built.

This follow-up keeps successful page creation and editing unchanged, but routes the required edit-lock fields through a small validation helper. Missing `lock_id` or `lock_secret` now raises `NoElementException` with site, page, and field context before any `savePage` request is sent. The error names the missing field without exposing the lock secret value.

## Related Issue

Builds on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [204-pr-publish-source-verification-site-context.md](204-pr-publish-source-verification-site-context.md), and [226-pr-publish-visibility-404-context.md](226-pr-publish-visibility-404-context.md). Those drafts established browser-free page writes, edit-lock handling, privacy-safe diagnostics, source verification, and action/read boundaries as practical rollout-backed surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Add a small required-field helper for `edit/PageEditModule` lock response fields.
- Convert missing `lock_id` and missing `lock_secret` into `NoElementException` with site, page, and field context.
- Add a focused public `Page.create_or_edit(...)` regression for both required lock fields.
- Preserve login checks, edit-lock request payloads, lock/other-lock handling, `raise_on_exists`, existing-page `page_id` validation, successful `savePage` request payloads, save response handling, stale ListPages fallback behavior, `Page.edit(...)`, `site.page.publish(...)`, and live Wikidot behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Browser-free page edit-lock response validation
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Missing required edit-lock fields fail with wikidot.py's contextual parser exception rather than raw dictionary access. | `TestPageCreateOrEdit.test_create_or_edit_missing_lock_field_includes_site_page_and_field_context` removes `lock_id` and `lock_secret` from the fixture and asserts `NoElementException`. | A raw `KeyError`, fabricated lock field, silent save attempt, or generic error rejects this local completion claim. |
| The malformed edit-lock error identifies the affected site, page, and missing field without exposing secret values. | The focused regression asserts `Page edit lock response is malformed for site: test-site, page: new-page (field=lock_id)` and the analogous `lock_secret` message. | Omitting site, page, or field context, or printing a lock secret value, rejects this local completion claim. |
| Malformed edit-lock responses do not send `savePage`. | The focused regression asserts the site's AMC request method is called exactly once, for the edit-lock fetch. | Any second AMC call that attempts `savePage` after missing lock data rejects this local completion claim. |
| Successful create/edit and publish workflows remain unchanged. | `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageEdit tests/unit/test_site.py::TestSitePageAccessor -q` passed 32 tests. | Regressions in lock handling, force edit, empty source, save failures, stale search fallback, publish create/edit, metadata, source verification, or visibility retry reject this local completion claim. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 207 tests. | Regressions in page reads, page writes, site page accessors, source/revision/vote/file helpers, or recent changes reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `cd6f26a fix(page): report malformed edit lock fields`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_missing_lock_field_includes_site_page_and_field_context -q` failed before the fix with raw `KeyError: 'lock_id'` and `KeyError: 'lock_secret'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_missing_lock_field_includes_site_page_and_field_context -q` passed 2 tests after the helper was added.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` reformatted 1 file and left 1 file unchanged.
- `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_missing_lock_field_includes_site_page_and_field_context tests/unit/test_page.py::TestPageCreateOrEdit::test_create_new_page tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_save_failure_decodes_response_once tests/unit/test_page.py::TestPageEdit::test_edit_existing_page tests/unit/test_page.py::TestPageEdit::test_edit_allows_empty_source -q` passed 6 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageEdit tests/unit/test_site.py::TestSitePageAccessor -q` passed 32 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 207 tests.
- `uv run pytest tests/unit -q` passed 790 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A present but malformed edit-lock response missing `lock_id` raises `NoElementException` before saving.
- A present but malformed edit-lock response missing `lock_secret` raises `NoElementException` before saving.
- The malformed edit-lock message includes the site `unix_name`, page fullname, and missing field name.
- The malformed edit-lock message does not expose any lock secret value.
- Successful page creation, existing-page editing, forced edit lock release, explicit empty source handling, save failure handling, stale ListPages fallback behavior, `Page.edit(...)`, and `site.page.publish(...)` remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Browser-free publishing and page editing depend on the edit-lock response before they can safely send `savePage`. If Wikidot emits a malformed lock response, wikidot.py should fail before mutation and should identify the site, page, and missing field for plain-text logs. That keeps the action boundary strict while avoiding raw Python exceptions and avoiding disclosure of temporary lock secrets.

## Local Evidence, Not For Upstream Paste

- Local drafts repeatedly identified browser-free page publishing as a practical workflow surface by wrapping create/edit, source verification, metadata updates, visibility retry, and audit result fields.
- Earlier edit-lock and save-path slices improved privacy masking and duplicate save-response decoding without changing the write request path.
- The refreshed complexity memo continues to list action/read boundaries and remaining parser messages as useful leads, and this slice addresses one narrow malformed-response boundary in the page write path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, stored session material, lock secrets, source text, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change login checks, retry policy, edit-lock request construction, lock conflict classification, `raise_on_exists`, page-ID validation, save request construction, save response status handling, stale lookup fallback behavior, metadata writes, source verification, post-save visibility polling, or live Wikidot behavior. It only converts missing required edit-lock fields into contextual parser errors before mutation.
