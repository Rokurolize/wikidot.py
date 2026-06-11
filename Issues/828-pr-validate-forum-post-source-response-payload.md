# PR: Validate forum post source response payload

## Summary

`ForumPostCollection.get_post_sources()` should validate that the decoded `forum/sub/ForumEditPostFormModule` response payload is a mapping before reading `body`.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 209, which covers mapping responses where `body` is missing, Issue 327, which covers present non-string `body` values, Issue 827, which covers forum post list payload roots, and Issue 814, which covers edit mutation action payloads.

## Problem Statement

The source-form helper previously called `response.json().get("body")` directly. If the decoded response payload was a list, string, or other non-mapping value, the read path raised a raw `AttributeError` before wikidot.py could attach site and post context.

That made `ForumPost.source` and `ForumPostCollection.get_post_sources()` harder to diagnose when the API returned a malformed source-form envelope.

## Rollout Evidence

Local TDD reproduced the failure with a list payload. The RED run failed with `AttributeError: 'list' object has no attribute 'get'` in `_source_response_body`.

The local fix is committed as `72451a9`.

## Affected Workflows

The affected workflow is any caller that reads forum post source through `ForumPost.source` or `ForumPostCollection.get_post_sources()`.

The malformed response comes from the source-form request path using `forum/sub/ForumEditPostFormModule`.

## Proposed Fix

Decode the response once, require a `dict`, and raise `NoElementException` with site, post, expected type, and actual type context when the payload root is malformed.

Keep the existing missing-`body` and non-string-`body` diagnostics unchanged.

## Implementation Notes

The patch adds a mapping guard in `ForumPostCollection._source_response_body(...)` before calling `.get("body")`.

The regression test asserts that a list payload raises:

```text
Forum post source response payload is malformed for site: test-site, post: 5001 (expected=dict, actual=list)
```

It also verifies that `_source` remains unset and the direct non-retry request path is not used.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_malformed_response_payload_type_includes_site_post_and_type_context -q
uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_missing_response_body_includes_site_and_post_context tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_malformed_response_body_type_includes_site_post_and_type_context tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_malformed_response_payload_type_includes_site_post_and_type_context tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_success tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_skips_failed_retry_response tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_missing_direct_source_textarea_includes_context -q
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
focused GREEN: 6 passed
forum-post module: 301 passed
full unit suite: 3927 passed
ruff: passed
format check: passed
mypy: passed
pyright: passed
diff whitespace: passed
```

## Compatibility And Risk Notes

The change only affects malformed decoded payload roots on the forum post source-form read path. Valid mapping payloads and the existing missing-`body` and malformed-`body` cases retain their current behavior.

The exception type is already used for adjacent malformed response cases, so callers that handle wikidot.py read failures through `NoElementException` receive a more consistent error surface.

## Rationale For Upstream Suitability

The patch replaces an incidental Python container error with a domain exception that includes actionable context. It is narrowly scoped, covered by a regression test, and follows the existing validation style already used in adjacent forum post response helpers.

## Acceptance Criteria

- `ForumPostCollection.get_post_sources()` validates that the decoded source-form response payload is a mapping before reading `body`.
- Non-mapping decoded payloads raise `NoElementException` with site, post, expected type, and actual type context.
- Existing missing-`body`, non-string-`body`, retry, source textarea, and success behavior remains covered.
- The full unit suite and static checks pass locally.

## Local Evidence, Not For Upstream Paste

- Local code commit: `72451a9`
- Thread workspace report records the RED/GREEN and full gate evidence for this slice.
- No raw response JSON, generated forum HTML, source text, forum titles, account material, cookies, tokens, or auth JSON were captured in this draft.
