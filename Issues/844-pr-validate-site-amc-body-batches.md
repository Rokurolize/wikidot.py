# PR: Validate site AMC body batches

## Summary

`Site.amc_request(...)` and `Site.amc_request_with_retry(...)` should validate their site-scoped AMC request body batches before empty-batch handling, request-state validation, retry config reads, or delegation to the raw AMC client.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 401, which validates `AjaxModuleConnectorClient.request(...)` body batches at the raw AMC client boundary. This slice covers the public `Site` wrapper boundary, where malformed containers could previously be accepted as empty no-ops or reach `client.amc_client` before the raw validator could run.

## Problem Statement

The site-scoped AMC helpers are the public request boundary beneath many page, forum, member, application, recent-change, ListPages, and source workflows. Before this change, the wrappers typed `bodies` as `list[dict[str, Any]]` but used `len(bodies)` before validating the container.

That meant `None` failed with a raw `TypeError`, empty dictionaries and tuples were accepted as empty request batches, and non-empty malformed values such as `"abc"` or `[123]` could read `client.amc_client` before the raw client reported a stable body-shape error.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify `Site.amc_request(...)` and `Site.amc_request_with_retry(...)` as shared infrastructure for browser-free Wikidot reads and writes. Existing drafts covered empty site AMC batches, site AMC return-exception controls, retry controls, retry config objects, retained request state, and raw AMC body validation, but did not validate the site-wrapper `bodies` shape before wrapper-level short-circuiting and config access.

The local fix is committed as `cf79822`.

## Affected Workflows

- Direct callers of `Site.amc_request(...)` with generated or rehydrated request batches.
- Direct callers of `Site.amc_request_with_retry(...)` with generated or rehydrated request batches.
- Higher-level code that depends on the site wrapper failing before request setup when a malformed batch is supplied.
- Tests, scripts, CLI adapters, and continuation ledgers that build site-scoped AMC request batches from structured data.

## Proposed Fix

Reuse the existing raw AMC body-batch validator at the `Site` wrapper boundary. Validate after `return_exceptions` or explicit retry-control validation, but before empty-batch no-op handling, client request-state validation, retry config reads, or raw AMC delegation.

Keep valid empty list behavior unchanged: `site.amc_request([])` and `site.amc_request_with_retry([])` still return `()`.

## Tests And Verification

Local verification:

```text
uv run --extra test pytest tests/unit/test_site.py::TestSiteAmcRequest::test_amc_request_rejects_non_list_bodies_before_client_request tests/unit/test_site.py::TestSiteAmcRequest::test_amc_request_rejects_non_dict_body_entries_before_client_request tests/unit/test_site.py::TestSiteAmcRequest::test_amc_request_with_retry_rejects_non_list_bodies_before_config tests/unit/test_site.py::TestSiteAmcRequest::test_amc_request_with_retry_rejects_non_dict_body_entries_before_config -q
uv run --extra test pytest tests/unit/test_site.py::TestSiteAmcRequest -q
uv run --extra test pytest tests/unit/test_site.py -q
uv run --extra test pytest tests/unit/test_amc_client.py tests/unit/test_ajax.py tests/unit/test_requestutil.py -q
uv run --extra test pytest tests/unit -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pyright
git diff --check
```

The focused RED run failed before the fix with `TypeError`, `DID NOT RAISE`, or premature `amc_client` access. The focused GREEN run passed 12 tests after adding wrapper-level validation. Full unit verification passed 3957 tests, ruff and pyright were clean, and mypy reported only existing untyped-function notes with no issues.

## Acceptance Criteria

- `Site.amc_request(None)`, `{}`, `()`, and `"abc"` raise `ValueError("bodies must be a list of dictionaries")` before reading `client.amc_client`.
- `Site.amc_request([123])` and `Site.amc_request([{"moduleName": "Test"}, 123])` raise indexed body-entry diagnostics before reading `client.amc_client`.
- `Site.amc_request_with_retry(...)` enforces the same body-batch validation before retry config access.
- Valid empty list batches still return `()` without reading `client.amc_client` or retry config.
- Existing valid site AMC delegation, retry behavior, raw AMC validation, RequestUtil behavior, and adjacent site workflows remain green.

## Scope

This slice does not change raw AMC request execution, request-body field semantics, token handling, retry policy, URL routing, response parsing, empty-list no-op behavior, live Wikidot behavior, or upstream filing state.

## Upstream-Safe Motivation

The `Site` wrapper is a public boundary, not just a pass-through implementation detail. It should reject malformed request-batch containers before wrapper-specific behavior can reinterpret them as empty batches or touch client request state. Reusing the existing raw AMC validator keeps the accepted shape and diagnostic messages consistent across the wrapper and raw client.
