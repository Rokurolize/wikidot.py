# PR: Validate page metadata action response counts

## Summary

`Page.metas = {...}` and `Page.set_metadata(...)` both send direct page metadata AMC batches, then pair request bodies with returned responses to validate each action status. Before this change, a connector, mock, or adapter that returned too few or too many responses leaked Python's raw `ValueError("zip() argument 2 is shorter than argument 1")` from `zip(..., strict=True)`.

This change validates direct page metadata action response counts before any individual response is parsed. A mismatch now raises `UnexpectedException("Page metadata action response count mismatch ...")` with site, page, page ID, expected count, and actual count. Existing request construction, login checks, retained page-ID validation, metadata action payload/status validation, local state update ordering, and successful valid metadata writes remain unchanged.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issues 245, 249, 724, and 811, which validate metadata action response payload roots and status fields after one response has been selected for one request body. This slice validates the returned batch arity before positional pairing begins.

This is distinct from local Issue 846, which validates `Site.amc_request_with_retry(...)` response counts for retry-aware site reads. `Page.metas = {...}` and `Page.set_metadata(...)` use direct `site.amc_request(...)` metadata writes, so they needed a page-level direct batch guard.

## Problem Statement

Direct page metadata writes depend on one returned response per submitted metadata action. If `Page.metas = {...}` sends delete/add/update actions and receives one response, the old code parsed the first response and then raised a raw `ValueError` when strict zip detected the shorter response sequence. `Page.set_metadata(...)` had the same issue for mixed tag, parent, and meta batches.

That failure was both late and low-context: the first response could be parsed before the batch contract was known, and callers saw a Python pairing error instead of a wikidot.py diagnostic identifying the site, page, and expected response count.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free page metadata writes as practical infrastructure for publish helpers, generated maintenance scripts, migration ledgers, and fixture-backed tests. Existing local slices added batched metadata writes, direct meta setter batching, retained page-ID validation, retained site/client validation, metadata action payload validation, metadata action status validation, and retry response-count validation on adjacent helpers. They did not validate direct metadata action batch arity before `Page.metas = {...}` and `Page.set_metadata(...)` paired returned responses to request bodies.

The local fix is committed as `f484bc5`.

## Affected Workflows

- Browser-free publish flows that update tags, parent, and meta tags through `Page.set_metadata(...)`.
- Direct meta tag maintenance through `Page.metas = {...}`.
- Generated metadata migration scripts, local fixtures, tests, or adapters that mock or wrap `site.amc_request(...)`.
- Debugging malformed connector behavior where response count, not action payload shape, is the first broken contract.

## Proposed Fix

Add a small page metadata action response-count guard. Validate that direct metadata action responses are a list or tuple with exactly one entry per request body before iterating with `zip(..., strict=True)`. Raise `UnexpectedException` with site/page context and expected/actual counts on mismatch.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_rejects_action_response_count_mismatch_before_parsing tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_action_response_count_mismatch_before_parsing -q --tb=short
uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q
uv run pytest tests/unit/test_page.py -q --tb=short
uv run pytest tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py -q --tb=short
uv run pytest tests/unit -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pyright src tests
git diff --check
```

The focused RED run failed before the fix because both new regressions leaked raw `ValueError` from strict zip. The focused GREEN run passed after adding the count guard. Full unit verification passed 3962 tests, ruff and pyright were clean, mypy reported only existing untyped-function notes with no issues, and whitespace checks passed.

## Acceptance Criteria

- `Page.metas = {...}` raises `UnexpectedException` with site, page, page ID, expected count, and actual count when direct metadata action response count differs from request count.
- `Page.set_metadata(...)` raises the same contextual response-count mismatch before parsing any individual returned response.
- Mismatched response-count failures do not update local `tags`, `parent_fullname`, or cached `_metas`.
- Valid metadata writes still send the same request bodies and update local state after every returned action status is confirmed successful.
- Existing metadata payload/status diagnostics remain unchanged for one-response-per-request malformed payloads.
- The diagnostic does not include raw generated module bodies, raw response JSON, credentials, cookies, auth JSON, local rollout paths, or account material.

## Scope

This slice does not change retry policy, direct `site.amc_request(...)` behavior, metadata request construction, tag serialization, parent clear semantics, meta diffing, metadata action status parsing, successful local state updates, live Wikidot behavior, or upstream filing state.

## Upstream-Safe Motivation

Direct page metadata writes rely on positional correspondence between submitted action bodies and returned action responses. When that correspondence is broken, wikidot.py should report the metadata batch contract failure directly instead of leaking a raw Python zip error after partially parsing returned responses.
