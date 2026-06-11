# PR: Validate forum post edit-form response payload

## Summary

`ForumPost.edit(...)` should validate that the decoded pre-save edit-form response payload is a mapping before reading `body`.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 210, which covers mapping edit-form responses where `body` is missing, Issue 327, which covers present non-string `body` values, Issue 814, which covers decoded `saveEditPost` action payloads, Issue 828, which covers source-form reads through `ForumPostCollection.get_post_sources()`, and Issue 403, which covers the raw Ajax Module Connector envelope.

## Problem Statement

`ForumPost.edit(...)` fetches the current forum post edit form through `forum/sub/ForumEditPostFormModule`, parses `currentRevisionId`, and only then sends the `saveEditPost` mutation. The edit-form helper previously called `response.json().get("body")` directly.

If the decoded edit-form response payload was a list, string, or other non-mapping value, the read-before-mutation path raised a raw `AttributeError` before wikidot.py could attach site and post context. That failure also skipped the existing no-save assertions that protect local title/source state from malformed pre-save forms.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify forum post edit preflight as a practical automation surface: retry-aware edit-form fetches, direct-child `currentRevisionId` scoping, revision-ID diagnostics, edit-form body diagnostics, edit action diagnostics, cache invalidation, and retained-state validation all exist as prior local slices.

The immediate source evidence before this slice was `ForumPost._edit_form_response_body(...)` calling `response.json().get("body")` while adjacent forum post helpers already used explicit response-shape diagnostics. The RED run reproduced the gap with a list payload and failed with `AttributeError: 'list' object has no attribute 'get'`.

The local fix is committed as `5be70ed`.

## Affected Workflows

- Browser-free forum post edits through `ForumPost.edit(...)`.
- Migration and moderation tools that edit existing forum posts.
- Generated fixtures, response adapters, and recorded-response tests that return decoded module payloads to wikidot.py.

## Proposed Fix

Decode the edit-form response once, require a `dict`, and raise `NoElementException` with site, post, expected type, and actual type context when the payload root is malformed.

Keep the existing missing-`body`, non-string-`body`, retry-exhausted fetch, `currentRevisionId`, and `saveEditPost` action diagnostics unchanged.

## Implementation Notes

The patch adds a mapping guard in `ForumPost._edit_form_response_body(...)` before calling `.get("body")`.

The regression test asserts that a list payload raises:

```text
Forum post edit form response payload is malformed for site: test-site, post: 5001 (expected=dict, actual=list)
```

It also verifies that no `saveEditPost` request is sent and that local title/source state is preserved.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_malformed_form_response_payload_type_includes_site_post_and_type_context -q
uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_form_response_body_includes_site_and_post_context tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_malformed_form_response_body_type_includes_site_post_and_type_context tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_malformed_form_response_payload_type_includes_site_post_and_type_context tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_success tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_raises_when_form_fetch_retry_is_exhausted tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_current_revision_id_includes_site_and_post_context tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_save_action_status_does_not_update_local_state tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_malformed_action_response_type_preserves_local_state_and_caches -q
uv run pytest tests/unit/test_forum_post.py -q
uv run pytest tests/unit -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pyright
git diff --check
```

Observed results:

```text
focused RED: failed with AttributeError before the fix
focused GREEN: 8 passed
forum-post module: 302 passed
full unit suite: 3928 passed
ruff: passed
format check: passed
mypy: passed with existing notes only
pyright: passed
diff whitespace: passed
```

## Compatibility And Risk Notes

The change only affects malformed decoded payload roots on the forum post edit-form preflight path. Valid mapping payloads and the existing missing-`body`, malformed-`body`, retry-exhausted, revision-ID, and edit action cases retain their current behavior.

The exception type is already used for adjacent malformed module response cases. The diagnostic intentionally includes only site/post identifiers and type names, not raw response JSON, generated edit-form HTML, post source text, titles, post content, cookies, tokens, auth JSON, or account material.

## Rationale For Upstream Suitability

The patch replaces an incidental Python container error with a domain exception that includes actionable context and preserves the no-save boundary for malformed edit forms. It is narrowly scoped, covered by a regression test, and follows the existing validation style already used in adjacent forum post response helpers.

## Acceptance Criteria

- `ForumPost.edit(...)` validates that the decoded edit-form response payload is a mapping before reading `body`.
- Non-mapping decoded edit-form payloads raise `NoElementException` with site, post, expected type, and actual type context.
- No save request is sent and local title/source state is not updated after malformed edit-form payloads.
- Existing missing-`body`, non-string-`body`, retry-exhausted, `currentRevisionId`, action-payload, and successful edit behavior remains covered.
- The full unit suite and static checks pass locally.

## Local Evidence, Not For Upstream Paste

- Local code commit: `5be70ed`
- Thread workspace report records the RED/GREEN and full gate evidence for this slice.
- No raw response JSON, generated forum HTML, edit-form HTML, post source text, post titles, post content, account material, cookies, tokens, or auth JSON were captured in this draft.
