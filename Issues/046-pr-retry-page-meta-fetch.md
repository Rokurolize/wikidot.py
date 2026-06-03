# PR Draft: Retry Page Meta Tag Fetch

## Summary

`Page.metas` fetches `edit/EditMetaModule` to lazily load page meta tags before parsing them into a `dict[str, str]`. That fetch is read-only, but it still used plain `site.amc_request(...)`. A transient AMC failure could therefore be treated as a response and fail with an attribute/parsing error before the existing retry mechanism could run.

The fix routes only the meta-tag getter's module lookup through `site.amc_request_with_retry(...)`. If the retry succeeds, `Page.metas` preserves the existing behavior: it parses decoded and literal meta markup, caches the resulting dictionary, and leaves the existing setter and `set_metadata(...)` write behavior unchanged. If retries are exhausted, it raises `UnexpectedException("Cannot retrieve page metas: <fullname>")` and leaves `_metas` unset so a later access can retry.

## Related Issue

Complements [007-pr-batch-meta-tag-updates.md](007-pr-batch-meta-tag-updates.md), which optimized meta-tag writes, and [011-pr-robust-meta-tag-parsing.md](011-pr-robust-meta-tag-parsing.md), which hardened meta-tag parsing. It also follows the read-path retry pattern from [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), and [045-pr-retry-page-discussion-fetch.md](045-pr-retry-page-discussion-fetch.md). No upstream issue filed yet.

## Changes

- Use `self.site.amc_request_with_retry(...)` for `Page.metas`'s `edit/EditMetaModule` lookup.
- Raise `UnexpectedException("Cannot retrieve page metas: <fullname>")` when the retry result is `None`.
- Preserve existing parser behavior for HTML-escaped and literal `<meta>` tags.
- Preserve the `_metas` cache on successful reads.
- Leave meta write mutations, page tags, parent changes, save, rename, vote, and delete actions unchanged.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [ ] Security/privacy hardening
- [x] Reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Requirements Traceability

| Requirement | Acceptance | Verification | Negative Control |
| --- | --- | --- | --- |
| R1: Meta-tag getter is retry-aware | `Page.metas` retries transient failures while fetching `edit/EditMetaModule` | `test_metas_getter_retries_transient_fetch_failures` | The test failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` |
| R2: Exhausted meta-tag fetch fails explicitly | A `None` retry result raises `UnexpectedException` with the page fullname and does not set `_metas` | `test_metas_getter_raises_when_retry_is_exhausted` | Exhausted retry leaves the property eligible for a later retry instead of caching an empty or partial meta dictionary |
| R3: Successful parser behavior is preserved | A successful response still parses escaped and literal meta tags into decoded values | `test_metas_getter_parses_decoded_flexible_markup` | The test asserts decoded ampersands, empty values, quotes, and literal markup still parse correctly |
| R4: Adjacent page and site behavior is preserved | Page write helpers, `set_metadata(...)`, and site tests remain green | `TestPageWriteMethods`; `tests/unit/test_page.py`; `tests/unit/test_page.py tests/unit/test_site.py`; `tests/unit` | Broad unit coverage still passes after the getter retry change |

## Testing

Local implementation commit: `1918d14 fix(page): retry meta tag fetch`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_retries_transient_fetch_failures -q` failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_raises_when_retry_is_exhausted -q` passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed with 19 tests.
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 87 tests.
- [x] `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed with 134 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 599 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] Complexity scan refreshed at `/home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/artifacts/complexity_analysis_wikidot.md`

## Acceptance Criteria

- `Page.metas` uses retry-aware AMC for the read-only `EditMetaModule` lookup.
- A transient meta-tag fetch failure is retried before the response body is parsed.
- An exhausted meta-tag fetch retry raises an explicit page-fullname-specific `UnexpectedException`.
- Exhausted retry does not set `_metas`, so the next property access can try again.
- Existing meta parsing and meta write behavior remain unchanged.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Meta tags are read during page metadata workflows and before diff-based metadata updates. Retrying the read-only `EditMetaModule` lookup avoids exposing transient AMC failures as unrelated attribute/parsing errors and aligns the getter with other retry-aware page lazy properties. The change deliberately avoids retrying meta write actions because duplicate mutation semantics should be evaluated separately.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence repeatedly used `wikidot.py` for page metadata, source collection, publication support, and browser-free workflows where read-heavy AMC paths needed retry-aware behavior.
- Existing local issues [007-pr-batch-meta-tag-updates.md](007-pr-batch-meta-tag-updates.md) and [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md) show `Page.metas` participates in higher-level metadata workflows.
- Existing local issues [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), and [045-pr-retry-page-discussion-fetch.md](045-pr-retry-page-discussion-fetch.md) established that page lazy properties should not cache false negatives when acquisition retries are exhausted.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice intentionally does not retry `deleteMetaTag`, `saveMetaTag`, `set_metadata(...)` mutations, page save, rename, tag save, parent setting, vote, or delete paths. Those paths can have duplicate-action or idempotency risks and should be evaluated separately only when mutation semantics are proven safe.
