# PR Draft: Validate Forum Category Create Response Payload

## Summary

`ForumCategory.create_thread(...)` now validates that decoded `newThread` action responses are dictionaries before reading `threadId` or `status`. Non-mapping payloads such as `["not-ok"]` raise contextual `NoElementException` with site, category ID, event, expected type, and actual type context instead of leaking a raw list `AttributeError`.

The change is intentionally narrow: valid `{"threadId": ..., "status": "ok"}` creates, missing or malformed `threadId` diagnostics, missing `status` diagnostics, non-string `status` diagnostics, explicit non-ok string status handling, cache invalidation, and created-thread lookup remain unchanged.

## Problem Statement

Forum thread creation treats the decoded `newThread` response as a result object: it first validates `threadId`, then validates action `status`, clears the cached category thread list, and fetches the created thread. Earlier local slices covered missing and malformed `threadId` fields, valid-ID responses missing `status`, explicit non-ok string statuses, present non-string statuses such as `{"threadId": 3001, "status": ["not-ok"]}`, retained category IDs, and retained site/client boundaries. One response-shape gap remained: if `response.json()` returned a non-dictionary payload, `create_thread(...)` attempted `response.get("threadId")` and leaked raw `AttributeError`.

That failure gives callers neither the create-thread action context nor a stable wikidot.py data-shape exception. Generated fixtures, response adapters, recorded traffic, or mocked responses should be classified before field access, and failed create responses must not clear cached threads or fetch a created thread.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free forum thread creation, discussion migration, moderation tooling, generated forum ledgers, local fixtures, and recorded-response tests as practical automation surfaces: [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [167-pr-forum-thread-create-result-context.md](167-pr-forum-thread-create-result-context.md), [252-pr-forum-category-create-thread-action-status-context.md](252-pr-forum-category-create-thread-action-status-context.md), [264-pr-forum-category-create-thread-cache-invalidation.md](264-pr-forum-category-create-thread-cache-invalidation.md), [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md), [652-pr-validate-non-negative-create-thread-result-ids.md](652-pr-validate-non-negative-create-thread-result-ids.md), [719-pr-validate-forum-category-create-thread-status-type.md](719-pr-validate-forum-category-create-thread-status-type.md), [796-pr-validate-create-thread-retained-category-id.md](796-pr-validate-create-thread-retained-category-id.md), and [802-pr-validate-forum-action-site-clients.md](802-pr-validate-forum-action-site-clients.md).

This slice is not a duplicate of [167-pr-forum-thread-create-result-context.md](167-pr-forum-thread-create-result-context.md), [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md), or [652-pr-validate-non-negative-create-thread-result-ids.md](652-pr-validate-non-negative-create-thread-result-ids.md). Those issues cover mapping responses where `threadId` is missing, typed incorrectly, boolean, or negative.

This slice is not a duplicate of [252-pr-forum-category-create-thread-action-status-context.md](252-pr-forum-category-create-thread-action-status-context.md). Issue 252 covered mapping responses with a valid integer `threadId` but missing `status` or explicit non-ok string statuses.

This slice is not a duplicate of [719-pr-validate-forum-category-create-thread-status-type.md](719-pr-validate-forum-category-create-thread-status-type.md). Issue 719 covered a present non-string `status` field inside a mapping, such as `{"threadId": 3001, "status": ["not-ok"]}`. This slice covers the decoded `newThread` response payload not being a mapping before `threadId` extraction and status lookup.

Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) covers the raw Ajax Module Connector response envelope before module-level action payload handling.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free forum thread creation through `ForumCategory.create_thread(...)`.
- Discussion migration tools that create threads and immediately fetch the created thread.
- Generated forum ledgers, moderation tooling, fixtures, and recorded-response tests that decode action responses before returning them to wikidot.py module code.

## Proposed Fix

- Validate the decoded `newThread` response payload as a dictionary immediately after JSON decode.
- Reject non-dictionary payloads with `NoElementException` before `threadId` extraction or status lookup.
- Include only structural context and type names in the diagnostic, not raw response data.
- Preserve existing dictionary `threadId` validation order and status handling.

## Implementation Notes

Implemented locally in commit `0d4ad1a fix(forum_category): validate create response payload`.

The implementation adds one preflight guard in `src/wikidot/module/forum_category.py`:

```python
if not isinstance(response, dict):
    raise NoElementException(
        f"Forum category action response is malformed for site: {site.unix_name}, "
        f"category: {category_id} (event=newThread, expected=dict, actual={type(response).__name__})"
    )
```

The RED regression mocked `ForumCategory.create_thread(...)`'s `newThread` response as `["not-ok"]`. Before the fix, the method leaked `AttributeError: 'list' object has no attribute 'get'`. After the fix, the same case raises contextual `NoElementException`, decodes the response once, preserves the cached thread collection, and does not fetch a created thread.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Non-dictionary create-thread payloads fail before `threadId` extraction. | `test_create_thread_malformed_action_response_type_preserves_cache_and_does_not_fetch_created_thread` failed RED with raw `AttributeError`, then passed GREEN. | Reaching `.get`, leaking `AttributeError`, coercing the payload, or treating a list as a create result rejects this claim. |
| Missing or malformed `threadId` in a dictionary keeps the existing Issue 167/407/652 diagnostics. | Focused GREEN included missing/invalid, boolean, and negative `threadId` regressions. | Reporting action-status or payload-type errors for dictionary `threadId` failures rejects this claim. |
| Missing `status` in a dictionary with valid `threadId` keeps the existing Issue 252 diagnostic. | Focused GREEN included `test_create_thread_missing_action_status_does_not_fetch_created_thread`. | Reclassifying `{"threadId": 3001}` as the payload-type branch or dropping `field=status` rejects this claim. |
| Present non-string `status` keeps the existing Issue 719 diagnostic. | Focused GREEN included `test_create_thread_malformed_action_status_type_preserves_cache_and_does_not_fetch_created_thread`. | Reclassifying `{"threadId": 3001, "status": ["not-ok"]}` as a payload-type error rejects this claim. |
| Explicit non-ok string statuses still use `WikidotStatusCodeException`. | Focused GREEN included `test_create_thread_explicit_non_ok_action_status_preserves_cache_and_does_not_fetch_created_thread`. | Reclassifying non-ok strings as malformed response shape rejects this claim. |
| Failed create payloads do not clear cached threads or fetch the created thread. | The new regression asserts one AMC request and preserved `_threads`. | Clearing cached threads or issuing a second detail fetch before confirmed success rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3909 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `0d4ad1a fix(forum_category): validate create response payload`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_malformed_action_response_type_preserves_cache_and_does_not_fetch_created_thread -q --tb=short` failed before the fix with raw `AttributeError: 'list' object has no attribute 'get'`.
- GREEN focused: the same new regression passed after the payload guard.
- Create-thread response coverage: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_missing_or_invalid_thread_id_raises tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_malformed_action_response_type_preserves_cache_and_does_not_fetch_created_thread tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_boolean_thread_id_is_malformed_and_preserves_cache tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_negative_thread_id_is_malformed_and_preserves_cache tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_missing_action_status_does_not_fetch_created_thread tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_malformed_action_status_type_preserves_cache_and_does_not_fetch_created_thread tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_explicit_non_ok_action_status_preserves_cache_and_does_not_fetch_created_thread tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_success_invalidates_cached_threads -q --tb=short` passed 10 tests.
- Forum category module coverage: `uv run pytest tests/unit/test_forum_category.py -q --tb=short` passed 159 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3909 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `ForumCategory.create_thread(...)` with `response.json()` returning `["not-ok"]` raises `NoElementException` matching `Forum category action response is malformed for site: test-site, category: 1001 (event=newThread, expected=dict, actual=list)`.
- `{}` and `{"threadId": "3001"}` still raise the existing missing/invalid thread-ID diagnostic.
- `{"threadId": True, "status": "ok"}` and negative thread IDs remain rejected before status handling.
- `{"threadId": 3001}` still raises the existing missing-status message with `field=status`.
- `{"threadId": 3001, "status": ["not-ok"]}` still raises the existing malformed status-type message with `expected=str, actual=list`.
- Explicit non-ok string statuses still raise `WikidotStatusCodeException`.
- The malformed payload branch decodes the response JSON once, preserves cached threads, does not fetch the created thread, and does not include raw response data.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: A caller may have relied on raw `AttributeError` from malformed synthetic responses. Mitigation: the public module expects a result object, and repo validation style consistently routes malformed generated response shape through contextual `NoElementException`.
- Risk: This could be confused with returned `threadId` validation. Mitigation: dictionary payloads still follow the existing thread-ID-first guard before action-status validation.
- Risk: This could hide raw payload details useful for debugging. Mitigation: the diagnostic includes site, category ID, event, expected type, and actual type while avoiding raw response data that could contain private forum content or account material.

## Dependencies

- Forum category create responses remain expected to decode as JSON objects with a non-negative integer `threadId` and string `status`.
- Returned `threadId` validation remains responsible for identity fields after payload shape is confirmed.
- `WikidotStatusCodeException` remains responsible for explicit non-ok string statuses.
- `NoElementException` remains the parser/data-shape exception for malformed module response payloads.

## Open Questions

None for this local slice. Similar non-mapping action-payload guards may be useful on forum reply/edit, site-invitation, site-application, and site-member mutation helpers, but each surface should receive its own duplicate check against the existing action-status and status-type issue series before implementation.

## Rationale for Upstream Suitability

The patch is small, local, and consistent with existing wikidot.py response-shape diagnostics. It improves failure classification for malformed forum create-thread responses without changing successful creates, returned `threadId` validation, cache invalidation timing, created-thread lookup, or existing status-code behavior.

## Local Evidence

- Local rollout-backed forum drafts established thread creation, thread detail lookup, category thread caches, discussion migration, moderation tooling, generated forum ledgers, and fixtures as practical consumers of forum category behavior.
- Existing local drafts covered returned `threadId` context, missing create-thread action status, present non-string create-thread action status values, raw connector envelope status typing, create-thread cache invalidation, retained category IDs, and retained site/client state. They did not cover a decoded `newThread` response payload that is not a mapping before `threadId` extraction.
- This slice only validates forum category create-thread payload shape. It does not change request construction, login checks, retry behavior, forum reply/edit handling, site administration handling, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw forum content, raw response bodies, private site data, and private source text out of upstream discussion.
