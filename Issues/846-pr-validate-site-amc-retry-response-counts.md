# PR: Validate site AMC retry response counts

## Summary

`Site.amc_request_with_retry(...)` expects each lower-level `site.amc_request(..., return_exceptions=True)` call to return one result for each requested body. Before this change, a lower-level connector, mock, or adapter that returned too few initial or retry results could silently shorten the helper output or leave stale failed slots as `None`.

This change validates the result count after the initial site AMC batch request and after each retry request. A mismatch now raises `UnexpectedException("Site AMC retry response count mismatch ...")` with expected count, actual count, batch start, and attempt number. Existing retry controls, empty-batch behavior, partial-success semantics, exhausted retry handling, request-body validation, and raw AMC delegation remain unchanged.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 394, which validates `Site.amc_request_with_retry(...)` retry control inputs such as `batch_size` and `max_retries`. This slice validates the lower-level response arity contract after a valid request has been issued.

This is distinct from local Issue 844, which validates the `Site.amc_request(...)` body batch shape before delegating to the raw AMC client. This slice validates the count of returned AMC result objects before `amc_request_with_retry(...)` maps them back to request positions.

This is adjacent to local Issue 845, which validates the same response-count contract in the private-message-specific retry helper. This slice covers the shared site retry helper used by page, forum, member, application, recent-change, and ListPages workflows.

## Problem Statement

`Site.amc_request_with_retry(...)` preserves partial successes by tracking failed response positions and retrying only failed request bodies. That retry mapping depends on positional correspondence between the attempted request slice and the returned result sequence.

If the initial call returned one response for two requested bodies, the helper returned a one-entry tuple for a two-body request. If a retry call returned one response for two failed bodies, the helper updated only the first failed slot and returned the second slot as `None`, making a malformed lower-level response look like an exhausted retry for a different request.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify `Site.amc_request_with_retry(...)` as shared infrastructure for browser-free site reads and writes. Existing drafts covered retry-aware page source, file, vote, revision, forum, member, application, recent-changes, and ListPages workflows, plus retry control validation and body-batch validation. They did not validate that each site AMC request attempt returned one result per request body.

The local fix is committed as `3257ba6`.

## Affected Workflows

- Page collection source, file, vote, revision, metadata, auxiliary, and ListPages reads that rely on `Site.amc_request_with_retry(...)`.
- Forum category, thread, post, and revision workflows that rely on site retry batching.
- Site member, site application, recent changes, and other site-scoped retry-aware reads.
- Tests, stubs, generated adapters, or connector changes that return malformed result sequences from `site.amc_request(..., return_exceptions=True)`.

## Proposed Fix

Add a small site AMC retry response-count guard. Validate that each initial batch response and each retry response is a list or tuple with the expected number of entries before indexing or extending results by request position. Raise `UnexpectedException` with compact batch context if the contract is violated.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_site.py::TestSiteAmcRequest::test_amc_request_with_retry_rejects_initial_response_count_mismatch tests/unit/test_site.py::TestSiteAmcRequest::test_amc_request_with_retry_rejects_retry_response_count_mismatch -q --tb=short
uv run pytest tests/unit/test_site.py::TestSiteAmcRequest -q --tb=short
uv run pytest tests/unit/test_site.py -q --tb=short
uv run pytest tests/unit/test_amc_client.py tests/unit/test_ajax.py tests/unit/test_requestutil.py -q --tb=short
uv run pytest tests/unit -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pyright src tests
git diff --check
```

The focused RED run failed before the fix because neither the initial nor retry response-count mismatch raised `UnexpectedException`. The focused GREEN run passed after adding the count guard. Full unit verification passed 3960 tests, ruff and pyright were clean, mypy reported only existing untyped-function notes with no issues, and whitespace checks passed.

## Acceptance Criteria

- An initial site AMC batch response sequence with fewer or more entries than the request batch raises `UnexpectedException` with expected count, actual count, batch start, and attempt `0`.
- A retry response sequence with fewer or more entries than the failed request slice raises `UnexpectedException` with expected count, actual count, batch start, and retry attempt.
- Valid site AMC retry behavior still retries transient failures, preserves successful sibling responses, and returns `None` for genuinely exhausted failures.
- Existing empty-batch, retry-control, body-shape, raw AMC delegation, site workflow, and connector-adjacent tests remain green.
- The diagnostic does not include raw generated module bodies, raw response JSON, credentials, cookies, auth JSON, local rollout paths, or account material.

## Scope

This slice does not change retry policy, retry control validation, request body construction, response payload parsing, partial-success semantics, exhausted retry behavior, raw AMC behavior, live Wikidot behavior, or upstream filing state.

## Upstream-Safe Motivation

Shared site retry handling relies on positional correspondence between requested AMC bodies and returned results. When that correspondence is broken, wikidot.py should report the contract failure directly instead of returning shortened result tuples or misclassifying malformed retry output as an exhausted request.
