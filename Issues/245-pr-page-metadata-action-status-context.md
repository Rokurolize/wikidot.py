# PR Draft: Validate Page Metadata Action Status Before Local State Updates

## Summary

`Page.set_metadata(...)` batches tag, parent, and meta-tag mutations for browser-free publishing workflows. Earlier local slices added this helper, wrapped it in `site.page.publish(...)`, moved source verification before metadata writes, and hardened adjacent page write responses such as edit locks, save status, and rating action results. One adjacent action-response gap remained: `set_metadata(...)` sent the AMC batch and then updated local `tags`, `parent_fullname`, and `_metas` without checking each returned action response. If Wikidot returned a malformed non-empty response without `status`, wikidot.py could update local state from an unclassified mutation result.

This follow-up keeps request construction and successful metadata updates unchanged, but validates each returned action response before local state is updated. A missing `status` now raises `NoElementException` with site, page, page ID, event, and field context. Explicit non-`ok` statuses are routed through `WikidotStatusCodeException`. The local page metadata cache remains unchanged on malformed responses.

## Related Issue

Builds on [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [226-pr-publish-visibility-404-context.md](226-pr-publish-visibility-404-context.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), and [244-pr-page-rating-points-context.md](244-pr-page-rating-points-context.md). Those drafts established metadata batching as a practical publish-adjacent workflow and established the adjacent diagnostic pattern for action responses whose required fields are missing or malformed.

No upstream issue was filed from this local workspace.

## Changes

- Add a small `Page.set_metadata(...)` action-status validator.
- Validate each returned metadata action response before updating local `tags`, `parent_fullname`, or `_metas`.
- Convert missing metadata action `status` into `NoElementException` with site, page, page ID, event, and field context.
- Route explicit non-`ok` metadata action statuses through `WikidotStatusCodeException`.
- Add a focused public-interface regression proving malformed `saveTags` response status does not update local metadata state.
- Preserve metadata request body construction, batching, parent clearing, meta diffing, login checks, publish metadata delegation, and successful local state updates on valid responses.

## Type Of Change

- Bug fix / diagnostics improvement
- Page metadata action response validation
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A metadata action response missing `status` fails with wikidot.py's contextual parser exception rather than silently updating local state. | `TestPageWriteMethods.test_set_metadata_missing_action_status_does_not_update_local_state` returns `{"body": ""}` for the `saveTags` action response and asserts `NoElementException`. | No exception, a raw `KeyError`, fabricated success status, or generic failure rejects this local completion claim. |
| The malformed metadata action error identifies site, page, page ID, event, and missing field. | The focused regression asserts `Page metadata action response is malformed for site: test-site, page: test-page (id=12345, event=saveTags, field=status)`. | Omitting site, page fullname, page ID, event, or field context makes the failure ambiguous and rejects this local completion claim. |
| Malformed metadata action responses do not update local page metadata. | The focused regression asserts existing `tags`, `parent_fullname`, and `_metas` remain unchanged after the exception. | Updating any local metadata field after malformed response parsing rejects this local completion claim. |
| Successful `set_metadata(...)` behavior remains unchanged. | `TestPageWriteMethods.test_set_metadata_batches_tags_parent_and_metas` and `test_set_metadata_can_clear_parent` pass with `status: ok` responses. | Regressions in request ordering, batched request bodies, parent clearing, meta diffing, or successful local state updates reject this local completion claim. |
| Publish-adjacent metadata workflows remain unchanged. | `TestSitePageAccessor.test_publish_edits_existing_page_sets_metadata_and_verifies_source` and `test_publish_skips_metadata_when_source_verification_fails` pass. | Calling metadata too early, skipping metadata after a valid publish, or running metadata after failed source verification rejects this local completion claim. |
| Adjacent page write and publish behavior remains green. | `uv run pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_site.py::TestSitePageAccessor -q` passed 41 tests. | Regressions in page write helpers, publish result fields, metadata delegation, source verification, or visibility handling reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `13fc978 fix(page): guard metadata action status`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_missing_action_status_does_not_update_local_state -q` failed before the fix because `Page.set_metadata(...)` returned without raising and updated local metadata state.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_missing_action_status_does_not_update_local_state -q` passed 1 test after metadata action status validation was added.
- `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_batches_tags_parent_and_metas tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_missing_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_can_clear_parent -q` passed 3 tests.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_edits_existing_page_sets_metadata_and_verifies_source tests/unit/test_site.py::TestSitePageAccessor::test_publish_skips_metadata_when_source_verification_fails -q` passed 2 tests.
- `uv run pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_site.py::TestSitePageAccessor -q` passed 41 tests.
- `uv run pytest tests/unit -q` passed 794 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A `Page.set_metadata(...)` action response missing `status` raises `NoElementException`.
- The malformed metadata action message includes the site `unix_name`, page fullname, page ID, action event, and missing field.
- Local page metadata fields remain unchanged after malformed action response parsing.
- Successful tag, parent, and meta batching still sends the same request bodies and updates local state after valid `status: ok` responses.
- `site.page.publish(...)` continues to call or skip metadata at the same workflow points as before.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Browser-free publishing commonly saves source first, then applies tags, parent, and meta tags. Callers need local page state to reflect confirmed metadata action results, not merely that an AMC batch returned some non-empty response. If Wikidot emits a malformed metadata action response, wikidot.py should fail with an event-specific diagnostic and leave local metadata caches untouched, so a caller can retry or inspect the failure without relying on stale optimistic state.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified browser-free publishing as a practical workflow surface and added `Page.set_metadata(...)` specifically to replace hand-built tag, parent, and meta request batches.
- Adjacent action-response slices showed that field-aware `NoElementException` messages improve resumable plain-text diagnostics without changing successful request bodies or live Wikidot semantics.
- The refreshed complexity memo continues to list action/read boundaries and remaining parser messages as useful leads, and this slice addresses one narrow malformed-response boundary in the publish-adjacent metadata mutation path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, page source text, metadata values, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change login checks, retry policy, metadata request construction, tag serialization, parent clearing semantics, meta diffing, `Page.metas` setter behavior, individual `commit_tags()` or `set_parent(...)` behavior, source verification, publish result fields, or live Wikidot behavior. It only validates `Page.set_metadata(...)` action response status before local metadata state is updated.
