# PR: Validate page edit-lock response payloads

## Summary

`Page.create_or_edit(...)` should validate that decoded `edit/PageEditModule` edit-lock response payloads are mappings before reading lock fields or sending `savePage`.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 242, which covers mapping edit-lock responses missing `lock_id` or `lock_secret`. It is also distinct from Issues 653 through 656, which cover present malformed `page_revision_id` and `locked` fields, Issue 714, which covers present non-string `savePage` statuses, and Issue 808, which covers non-mapping `savePage` response payloads.

## Problem Statement

`Page.create_or_edit(...)` first acquires a Wikidot page edit lock through `edit/PageEditModule`. It then inspects lock-state fields, validates an optional `page_revision_id`, requires `lock_id` and `lock_secret`, and only then sends the `savePage` action.

If the decoded edit-lock response payload is a list, string, or other non-mapping value, the existing code can reach raw container operations such as `.get("other_locks")` or string-key indexing on a list. That leaks incidental Python errors before wikidot.py can report which site/page edit-lock boundary produced malformed module data, and before the existing field-specific edit-lock diagnostics can run.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free page creation, editing, publishing, edit-lock acquisition, source verification, metadata updates, and publish ledgers as practical workflows. Existing local drafts already hardened page edit locks, lock token fields, edit-lock revision IDs, locked-state typing, save response status handling, save response payload roots, page source/text inputs, and page ID preflight validation.

The immediate source evidence before this slice was `Page.create_or_edit(...)` assigning `page_lock_response_data = page_lock_response.json()` and then reading `page_lock_response_data.get("other_locks")` before any root-shape validation. The RED run reproduced the gap with a list-valued decoded edit-lock response and failed with raw `AttributeError: 'list' object has no attribute 'get'` before any contextual edit-lock response error could run.

The local fix is committed as `9f6f8aa`.

## Affected Workflows

- Browser-free page creation through `Page.create_or_edit(...)`.
- Browser-free page editing through `Page.edit(...)`, which delegates to `Page.create_or_edit(...)`.
- Site publish helpers that use create/edit, post-save lookup, source verification, metadata updates, and publish result ledgers.
- Migration, translation, fixture generation, and recorded-response adapters that synthesize edit-lock module payloads.

## Proposed Fix

Decode the edit-lock response once, require a `dict`, and raise `NoElementException` with site, page, module name, expected type, and actual type context when the payload root is malformed.

Keep the existing page-write semantics: login checks, edit-lock request construction, forced-lock payloads, lock-conflict handling, `other_locks` handling, `page_revision_id` validation, `raise_on_exists`, missing page ID behavior, `lock_id` and `lock_secret` validation, `savePage` request construction, save status handling, stale ListPages fallback, local page/source cache updates, and successful create/edit behavior remain unchanged for valid mapping payloads.

## Implementation Notes

The patch adds `_require_page_edit_lock_response_data(...)` beside the existing edit-lock field validators. `Page.create_or_edit(...)` now routes `page_lock_response.json()` through that helper before checking `locked`, `other_locks`, `page_revision_id`, `lock_id`, or `lock_secret`.

The regression test configures `Page.create_or_edit(...)` with a mocked edit-lock response whose `json()` value is a list. It asserts that the public API raises:

```text
Page edit lock response is malformed for site: test-site, page: new-page (module=edit/PageEditModule, expected=dict, actual=list)
```

It also asserts that the edit-lock response is decoded once and that `savePage` is not sent.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_malformed_lock_response_payload_type_fails_before_save -q
uv run pytest tests/unit/test_page.py -q -k "create_or_edit_malformed_lock_response_payload_type or create_or_edit_malformed_locked_field_value or create_or_edit_missing_lock_field or create_or_edit_malformed_lock_field_value or create_or_edit_blank_lock_field_value or create_or_edit_malformed_page_revision_id or create_or_edit_negative_page_revision_id or create_or_edit_accepts_zero_page_revision_id or create_or_edit_missing_save_status or create_or_edit_malformed_save_response_type or create_or_edit_malformed_save_status_type or create_new_page or edit_existing_page_stale_search_preserves_page_id or edit_without_page_id or edit_raise_on_exists"
uv run pytest tests/unit/test_page.py -q
uv run pytest tests/unit -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pyright
git diff --check
```

Observed results:

```text
RED: failed with AttributeError before the fix
focused GREEN: 51 passed
page module: 491 passed
full unit suite: 3941 passed
ruff: passed
format check: passed
mypy: passed with existing notes only
pyright: passed
diff whitespace: passed
```

The complexity scan reported only pre-existing hotspots outside the changed edit-lock root-shape guard.

## Compatibility And Risk Notes

The change only affects malformed decoded edit-lock payload roots on `Page.create_or_edit(...)`. Valid mapping payloads and existing missing-lock-field, blank-lock-field, malformed-lock-field, malformed `locked`, malformed `page_revision_id`, lock-conflict, `other_locks`, save-response, stale-search fallback, and successful create/edit behavior retain their current behavior.

The diagnostic intentionally includes only site/page/module identifiers and type names. It does not include raw response JSON, lock IDs, lock secrets, page source text, page titles, edit comments, account material, cookies, tokens, passwords, secrets, or auth JSON.

## Rationale For Upstream Suitability

The patch replaces incidental Python container errors with a domain exception at the page edit-lock boundary. It follows the existing response-shape validation style already used for page save responses and generated read-module payloads, preserves public API behavior for valid responses, and is covered by a regression through the public `Page.create_or_edit(...)` API.

## Acceptance Criteria

- `Page.create_or_edit(...)` validates that decoded `edit/PageEditModule` payloads are mappings before reading `locked`, `other_locks`, `page_revision_id`, `lock_id`, or `lock_secret`.
- Non-mapping payloads raise `NoElementException` with site, page, module name, expected type, and actual type context.
- Malformed edit-lock payloads fail before sending `savePage`.
- Existing edit-lock field validation, save response validation, stale-search fallback, local cache updates, and successful create/edit behavior remain covered.
- The full unit suite and static checks pass locally.

## Local Evidence, Not For Upstream Paste

- Local code commit: `9f6f8aa`
- Thread workspace report records the RED/GREEN and full gate evidence for this slice.
- Clawpatch provenance was checked against local fork `d89ca91`, provider `codex`, state `missing`, `codex-cli 0.139.0`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.
- No raw response JSON, lock IDs, lock secrets, page source text, page titles, edit comments, account material, cookies, tokens, passwords, secrets, or auth JSON were captured in this draft.
