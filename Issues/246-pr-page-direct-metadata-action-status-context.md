# PR Draft: Validate Direct Page Metadata Action Status

## Summary

`Page.commit_tags()` and `Page.set_parent(...)` are the direct single-action counterparts to the batched `Page.set_metadata(...)` helper. The batched helper now validates each returned metadata action status before changing local state, but these direct APIs still sent `saveTags` or `setParentPage` and treated any returned response object as success. That meant malformed responses without `status`, or explicit non-`ok` statuses, could be hidden from callers; in the parent case, local `parent_fullname` could also be updated from an unclassified mutation result.

This follow-up routes the direct tag and parent actions through the same metadata action status validator used by `set_metadata(...)`. Missing `status` now raises `NoElementException` with site, page, page ID, event, and field context. Explicit non-`ok` statuses raise `WikidotStatusCodeException`. Successful `status: ok` direct tag commits and parent changes keep their existing request bodies and return semantics.

## Related Issue

Builds on [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), [244-pr-page-rating-points-context.md](244-pr-page-rating-points-context.md), and [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md). Those drafts established browser-free metadata writes as a practical workflow and established the adjacent action-response diagnostic pattern.

No upstream issue was filed from this local workspace.

## Changes

- Validate the single `saveTags` action response returned by `Page.commit_tags()`.
- Validate the single `setParentPage` action response returned by `Page.set_parent(...)` before updating `parent_fullname`.
- Convert missing direct metadata action `status` into `NoElementException` with site, page, page ID, event, and field context.
- Preserve explicit non-`ok` status handling through `WikidotStatusCodeException`.
- Add focused public-interface regressions for malformed direct tag and parent action responses.
- Preserve request construction, login checks, successful tag commits, parent setting, parent clearing, and method chaining.

## Type Of Change

- Bug fix / diagnostics improvement
- Direct page metadata action response validation
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A direct tag save response missing `status` fails with contextual `NoElementException`. | `TestPageWriteMethods.test_commit_tags_missing_action_status_includes_site_page_event_and_field_context` returns `{"body": ""}` for the `saveTags` response and asserts `NoElementException`. | Returning success, raising a raw `KeyError`, fabricating success, or omitting action context rejects this local completion claim. |
| A direct parent action response missing `status` fails with contextual `NoElementException`. | `TestPageWriteMethods.test_set_parent_missing_action_status_does_not_update_local_state` returns `{"body": ""}` for the `setParentPage` response and asserts `NoElementException`. | Returning success, raising a raw `KeyError`, fabricating success, or omitting action context rejects this local completion claim. |
| The malformed direct metadata action messages identify site, page, page ID, event, and missing field. | The focused regressions assert messages ending in `(id=12345, event=saveTags, field=status)` and `(id=12345, event=setParentPage, field=status)`. | Omitting site, page fullname, page ID, event, or field context makes the failure ambiguous and rejects this local completion claim. |
| A malformed parent action does not update local page state. | The parent regression starts with `parent_fullname == "old-parent"` and asserts it remains unchanged after the exception. | Updating `parent_fullname` before validating the response rejects this local completion claim. |
| Successful direct tag and parent writes remain unchanged. | Existing `test_commit_tags_success`, `test_set_parent_success`, and `test_set_parent_clear` pass with `status: ok` fixtures. | Regressions in request bodies, parent clearing, method chaining, or successful local parent updates reject this local completion claim. |
| Batched metadata and publish-adjacent behavior remain unchanged. | `TestPageWriteMethods` and `TestSitePageAccessor` pass together. | Regressions in `set_metadata(...)`, publish metadata delegation, source verification ordering, or publish result behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `8cb2e42 fix(page): guard direct metadata action status`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_missing_action_status_does_not_update_local_state -q` failed before the fix because `Page.set_parent(...)` returned without raising and would update local `parent_fullname`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_missing_action_status_does_not_update_local_state -q` passed 1 test after direct parent action status validation was added.
- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_missing_action_status_includes_site_page_event_and_field_context -q` failed before the fix because `Page.commit_tags()` returned without raising.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_missing_action_status_includes_site_page_event_and_field_context tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_missing_action_status_does_not_update_local_state -q` passed 2 tests.
- `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_success tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_missing_action_status_includes_site_page_event_and_field_context tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_success tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_clear tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_missing_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_batches_tags_parent_and_metas tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_missing_action_status_does_not_update_local_state -q` passed 7 tests.
- `uv run pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_site.py::TestSitePageAccessor -q` passed 43 tests.
- `uv run pytest tests/unit -q` passed 796 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Page.commit_tags()` raises `NoElementException` when the direct `saveTags` response lacks `status`.
- `Page.set_parent(...)` raises `NoElementException` when the direct `setParentPage` response lacks `status`.
- Both malformed-response messages include site `unix_name`, page fullname, page ID, action event, and missing field.
- `Page.set_parent(...)` does not update `parent_fullname` after a malformed direct parent response.
- Successful direct tag and parent actions keep the existing request bodies and return behavior.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Direct tag and parent setters are small APIs, but they are still write actions. A caller should not have to guess whether the returned AMC response actually confirmed the action. Validating direct metadata action status makes these APIs consistent with `Page.set_metadata(...)`, prevents optimistic local parent state updates after malformed responses, and produces event-specific diagnostics for retry or manual inspection.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established browser-free publishing and metadata batching as practical local workflows, not speculative feature ideas.
- Recent adjacent slices hardened edit-lock fields, save status, rating action points, and batched metadata action status before local state updates.
- The refreshed complexity memo still lists action/read boundaries and remaining parser messages as useful leads; this slice closes the direct tag/parent action-response boundary outside the already-covered batched metadata helper.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, page source text, metadata values, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not retry direct metadata write actions, change tag serialization, change parent clearing semantics, alter `Page.set_metadata(...)`, modify `Page.metas` setter behavior, add per-action result objects, or touch live Wikidot behavior. It only validates direct `commit_tags()` and `set_parent(...)` action response status before treating those writes as successful.
