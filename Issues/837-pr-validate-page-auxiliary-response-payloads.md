# PR: Validate page auxiliary response payloads

## Summary

`Page.discussion` and `Page.metas` should validate that decoded auxiliary module response payloads are mappings before reading `body`.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 219, which covers mapping auxiliary responses where `body` is missing. It is also distinct from local Issue 335, which covers present non-string `body` values, and Issues 833 through 836, which cover page source, revision-list, vote, and file payload roots.

## Problem Statement

`Page.discussion` retrieves `forum/ForumCommentsListModule` to discover the page comment thread ID, then caches the loaded forum thread or the absence of one. `Page.metas` retrieves `edit/EditMetaModule`, restores escaped tag boundaries, and parses page-owned meta name/content values.

If a decoded auxiliary response payload was a list, string, or other non-mapping value, each property raised raw `AttributeError: 'list' object has no attribute 'get'` before wikidot.py could attach site, page, page ID, and expected payload shape context. That raw failure bypassed the existing missing-`body` and non-string-`body` diagnostics and left callers without the affected auxiliary workflow context.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify page auxiliary reads as practical browser-free workflows: discussion thread lookup, no-thread caching, thread ID parsing diagnostics, metas retrieval, metas getter site validation, missing-body diagnostics, and non-string-body diagnostics all exist as prior local slices.

The immediate source evidence before this slice was `Page.discussion` and `Page.metas` each calling `response.json().get("body")` after retry handling. The RED run reproduced the gap with list-valued decoded responses and failed with raw `AttributeError` before the existing body checks could run.

The local fix is committed as `ef362f4`.

## Affected Workflows

- Browser-free page discussion lookup through `Page.discussion`.
- Browser-free page meta retrieval through `Page.metas`.
- Publication verification, archive, moderation, and migration workflows that need contextual page failures.
- Generated fixtures, response adapters, and recorded-response tests that return decoded auxiliary module payloads to wikidot.py.

## Proposed Fix

Decode each auxiliary response once, require a `dict`, and raise `NoElementException` with site, page, page ID, expected type, and actual type context when the payload root is malformed.

Keep the existing property semantics: retry-exhausted `None` responses still raise `UnexpectedException`, missing `body` responses keep their existing `NoElementException` messages, present non-string `body` values keep the existing field-specific diagnostics, no-thread discussion results still cache only after valid parsing, and successful discussion/metas parsing remains unchanged for valid mapping payloads.

## Implementation Notes

The patch adds decoded-payload type guards in `Page.discussion` and `Page.metas` before reading `body`.

The regression tests configure each property with a mocked response whose `json()` value is a list. They assert that the public properties raise:

```text
Page discussion response payload is malformed for site: test-site, page: test-page (id=12345, expected=dict, actual=list)
Page metas response payload is malformed for site: test-site, page: test-page (id=12345, expected=dict, actual=list)
```

The tests also assert that the legacy plain `amc_request` path is not used, malformed discussion payloads do not mark `_discussion_checked`, and malformed metas payloads do not populate `_metas`.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_page.py -q -k "discussion_malformed_response_payload_type or metas_getter_malformed_response_payload_type"
uv run pytest tests/unit/test_page.py -q -k "discussion_malformed_response_payload_type or discussion_missing_response_body or discussion_malformed_response_body_type or discussion_malformed_thread_id or discussion_retry_exhausted or discussion_without_thread or metas_getter_malformed_response_payload_type or metas_getter_missing_response_body or metas_getter_malformed_response_body_type or metas_getter_rejects_malformed_site_before_request or metas_getter_retry_exhausted or metas_getter_decodes"
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
RED: 2 failed with AttributeError before the fix
focused GREEN: 8 passed
page module: 490 passed
full unit suite: 3940 passed
ruff: passed
format check: passed
mypy: passed with existing notes only
pyright: passed
diff whitespace: passed
```

The complexity scan reported only pre-existing hotspots outside the changed page auxiliary paths.

## Compatibility And Risk Notes

The change only affects malformed decoded payload roots on page discussion and metas reads. Valid mapping payloads and existing missing-`body`, malformed-`body`, retry-exhausted, no-thread discussion, thread-ID parsing, meta tag parsing, and successful parsing cases retain their current behavior.

The diagnostic intentionally includes only site/page/page-ID identifiers and type names. It does not include raw response JSON, generated discussion or meta HTML, meta values, page titles, account material, cookies, tokens, passwords, secrets, or auth JSON.

## Rationale For Upstream Suitability

The patch replaces incidental Python container errors with domain exceptions that include actionable page auxiliary context. It follows the response-shape validation style already used in adjacent page helpers, preserves the public property APIs, and is covered by regressions through the public `Page.discussion` and `Page.metas` properties.

## Acceptance Criteria

- `Page.discussion` validates that decoded `forum/ForumCommentsListModule` payloads are mappings before reading `body`.
- `Page.metas` validates that decoded `edit/EditMetaModule` payloads are mappings before reading `body`.
- Non-mapping payloads raise `NoElementException` with site, page, page ID, expected type, and actual type context.
- Existing missing-`body`, non-string-`body`, retry-exhausted, no-thread discussion, thread-ID parsing, meta tag parsing, and successful parsing behavior remains covered.
- The full unit suite and static checks pass locally.

## Local Evidence, Not For Upstream Paste

- Local code commit: `ef362f4`
- Thread workspace report records the RED/GREEN and full gate evidence for this slice.
- Clawpatch provenance was checked against local fork `d89ca91`, provider `codex`, state `missing`, `codex-cli 0.139.0`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.
- No raw response JSON, generated discussion or meta HTML, meta values, page titles, account material, cookies, tokens, passwords, secrets, or auth JSON were captured in this draft.
