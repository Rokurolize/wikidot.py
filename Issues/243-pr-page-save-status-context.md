# PR Draft: Include Context In Malformed Page Save Status Errors

## Summary

`Page.create_or_edit(...)` sends Wikidot's `savePage` action after acquiring an edit lock. Earlier local slices established this browser-free page write path as a practical workflow surface by hardening create/edit fallback behavior, save-response decoding, edit-lock secret masking, publish orchestration, source verification, post-save visibility polling, and malformed edit-lock required fields. One adjacent malformed-response gap remained: if `savePage` returned a decoded response object without a `status` field, wikidot.py accessed the dictionary field directly and leaked a raw Python `KeyError` after the write action returned.

This follow-up keeps successful page creation and editing unchanged, and keeps non-`ok` save statuses routed through `WikidotStatusCodeException`. It only routes the required save response status through a small validation helper. Missing `status` now raises `NoElementException` with site, page, and field context before any post-save `ListPages` lookup or fallback page fabrication happens.

## Related Issue

Builds on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [226-pr-publish-visibility-404-context.md](226-pr-publish-visibility-404-context.md), and [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md). Those drafts established browser-free page writes, save response reuse, privacy-safe diagnostics, action/read boundaries, and required edit-lock field validation as practical rollout-backed surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Add a small required-status helper for `savePage` response data.
- Convert a missing `status` field into `NoElementException` with site, page, and field context.
- Add a focused public `Page.create_or_edit(...)` regression for a malformed save response missing `status`.
- Preserve login checks, edit-lock request payloads, edit-lock required field handling, lock/other-lock handling, `raise_on_exists`, existing-page `page_id` validation, successful `savePage` request payloads, non-`ok` save status handling, stale `ListPages` fallback behavior, `Page.edit(...)`, `site.page.publish(...)`, and live Wikidot behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Browser-free page save response validation
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A malformed save response missing `status` fails with wikidot.py's contextual parser exception rather than raw dictionary access. | `TestPageCreateOrEdit.test_create_or_edit_missing_save_status_includes_site_page_and_field_context` returns `{}` from the save response and asserts `NoElementException`. | A raw `KeyError`, fabricated success status, generic error, or swallowed failure rejects this local completion claim. |
| The malformed save response error identifies the affected site, page, and missing field. | The focused regression asserts `Page save response is malformed for site: test-site, page: new-page (field=status)`. | Omitting site, page, or field context rejects this local completion claim. |
| Malformed save responses do not proceed into post-save lookup or fallback construction. | The focused regression asserts the site's AMC request method is called exactly twice: edit lock and save. | Any third AMC call that attempts `ListPages`, or any fabricated returned page after the malformed save response, rejects this local completion claim. |
| Non-`ok` save statuses remain `WikidotStatusCodeException`. | `TestPageCreateOrEdit.test_create_or_edit_save_failure_decodes_response_once` remains green. | Converting explicit non-`ok` statuses into `NoElementException`, changing the status code value, or decoding the response repeatedly rejects this local completion claim. |
| Successful create/edit and publish workflows remain unchanged. | `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageEdit tests/unit/test_site.py::TestSitePageAccessor -q` passed 33 tests. | Regressions in lock handling, force edit, empty source, save failures, stale search fallback, publish create/edit, metadata, source verification, or visibility retry reject this local completion claim. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 208 tests. | Regressions in page reads, page writes, site page accessors, source/revision/vote/file helpers, or recent changes reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `ff9f26d fix(page): report malformed save status`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_missing_save_status_includes_site_page_and_field_context -q` failed before the fix with raw `KeyError: 'status'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_missing_save_status_includes_site_page_and_field_context -q` passed 1 test after the helper was added.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` reformatted 1 file and left 1 file unchanged.
- `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_missing_save_status_includes_site_page_and_field_context tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_save_failure_decodes_response_once tests/unit/test_page.py::TestPageCreateOrEdit::test_create_new_page tests/unit/test_page.py::TestPageEdit::test_edit_existing_page tests/unit/test_page.py::TestPageEdit::test_edit_allows_empty_source -q` passed 5 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageEdit tests/unit/test_site.py::TestSitePageAccessor -q` passed 33 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 208 tests.
- `uv run pytest tests/unit -q` passed 791 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A present but malformed save response missing `status` raises `NoElementException`.
- The malformed save response message includes the site `unix_name`, page fullname, and missing field name.
- The malformed save response path does not proceed to post-save `ListPages` lookup.
- Explicit non-`ok` save statuses continue to raise `WikidotStatusCodeException`.
- Successful page creation, existing-page editing, forced edit lock release, explicit empty source handling, save failure handling, stale `ListPages` fallback behavior, `Page.edit(...)`, and `site.page.publish(...)` remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Browser-free publishing and page editing depend on `savePage` returning a status before wikidot.py can classify the mutation outcome or build a returned page object. If Wikidot emits a malformed save response, wikidot.py should identify the site, page, and missing field for plain-text logs instead of surfacing an unhelpful raw Python exception. This keeps the write action unchanged while making the post-write failure boundary explicit.

## Local Evidence, Not For Upstream Paste

- Local drafts repeatedly identified browser-free page publishing as a practical workflow surface by wrapping create/edit, source verification, metadata updates, visibility retry, and audit result fields.
- Earlier edit-lock and save-path slices improved privacy masking, duplicate save-response decoding, and required edit-lock field validation without changing the write request path.
- The refreshed complexity memo continues to list action/read boundaries and remaining parser messages as useful leads, and this slice addresses one narrow malformed-response boundary in the page write path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, stored session material, lock secrets, source text, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change login checks, retry policy, edit-lock request construction, edit-lock required field validation, lock conflict classification, `raise_on_exists`, page-ID validation, save request construction, non-`ok` save status handling, stale lookup fallback behavior, metadata writes, source verification, post-save visibility polling, or live Wikidot behavior. It only converts a missing required save response status into a contextual parser error before post-save lookup.
