# PR: Validate page single-action response counts

## Problem Statement

`Page.destroy()`, `Page.commit_tags()`, `Page.set_parent(...)`, `Page.rename(...)`, `Page.vote(...)`, and `Page.cancel_vote()` each send one direct AMC action request and then immediately index the first returned response. Before this change, a connector, mock, or adapter that returned zero responses leaked Python's raw `IndexError("list index out of range")` before wikidot.py could explain which site, page, and action broke the direct response-count contract.

This was a low-context failure at the browser-free page lifecycle, metadata, rename, and rating action boundary. It also bypassed the existing action diagnostics that preserve local state until the returned action payload, status, and rating points are confirmed.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free page cleanup, tagging, parent management, renaming, and voting as practical infrastructure for page migration, generated maintenance scripts, moderation helpers, local tests, publish-result ledgers, and fixture-backed workflows. Existing local slices hardened these methods around retained site/client/page ID state, action payload shape, missing action status, malformed action status type, explicit non-ok status mapping, rating points parsing, and metadata response counts. They did not validate the direct one-action response count before indexing the returned response sequence.

The local fix is committed as `9928a87`.

## Affected Workflows

- Browser-free page deletion through `Page.destroy()`.
- Direct page tag saves through `Page.commit_tags()`.
- Direct page parent changes through `Page.set_parent(...)`.
- Direct page rename workflows through `Page.rename(...)`.
- Direct page vote and vote-cancel workflows through `Page.vote(...)` and `Page.cancel_vote()`.
- Generated cleanup, migration, moderation, publishing, or maintenance scripts that wrap or mock `site.amc_request(...)`.
- Fixture-backed tests where a malformed adapter returns the wrong number of direct page action responses.
- Debugging malformed connector behavior where response count, not payload shape, is the first broken contract.

## Proposed Fix

Add a small page action response-count guard. Validate that each direct single-action response sequence has exactly one entry before indexing and parsing it. Raise `UnexpectedException` with site, page, page ID, event, expected count, and actual count on mismatch.

## Implementation Notes

The change adds `_require_page_action_response_count(...)` next to the existing page write and action-status helpers. `destroy`, `commit_tags`, `set_parent`, `rename`, `vote`, and `cancel_vote` now pass their raw `site.amc_request(...)` result through that guard before selecting response zero.

The guard intentionally stays local to direct page action handling instead of adding a generic `Site.amc_request(...)` response-count policy. Direct action callers already have domain-specific diagnostics, and a broad site-level guard could preempt more useful page/forum/member/application context.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_single_action_write_methods_reject_response_count_mismatch_before_parsing -q --tb=short
uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q --tb=short
uv run pytest tests/unit/test_page.py -q --tb=short
uv run pytest tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py -q --tb=short
uv run pytest tests/unit -q --tb=short
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pyright
git diff --check
```

The focused RED run failed before the fix because all six new regression parameters leaked raw `IndexError` from indexing an empty response list. The focused GREEN run passed after adding the count guard. `TestPageWriteMethods` passed 139 tests, `tests/unit/test_page.py` passed 501 tests, adjacent page/site coverage passed 1262 tests, full unit verification passed 3975 tests, ruff and pyright were clean, mypy reported only existing untyped-function notes with no issues, and whitespace checks passed.

## Compatibility And Risk Notes

- Valid direct page actions still send the same request bodies and parse the same returned payloads.
- Existing delete/rename action diagnostics, metadata action diagnostics, rating action diagnostics, rating-points parsing, local state update ordering, and cache invalidation after valid success remain unchanged.
- Mismatched response-count failures occur before payload parsing, status handling, rating mutation, parent/name/tag mutation, or cache invalidation.
- The diagnostic does not include raw generated module bodies, raw response JSON, credentials, cookies, auth JSON, private source text, local rollout paths, or account material.

## Rationale For Upstream Suitability

Direct page actions rely on positional correspondence between each submitted one-request batch and its returned response. When that correspondence is broken, wikidot.py should report the page action response-count failure directly instead of leaking a raw Python indexing error.

## Scope

This slice does not change retry policy, direct `site.amc_request(...)` behavior, request construction, action status parsing, rating-points parsing, valid local state updates, metadata batching, page create/edit behavior, live Wikidot behavior, or upstream filing state.
