# PR Draft: Validate Page File List Response Payloads

## Summary

`PageFileCollection.acquire(page)` fetches direct page attachment lists through `files/PageFilesModule`, validates the returned `body`, parses the file table, and caches the resulting `PageFileCollection` on the page. The direct page-file path already converted retry exhaustion, missing `body`, and present non-string `body` values into contextual wikidot.py exceptions, but it still assumed `response.json()` returned a mapping before calling `.get("body")`.

This change validates the decoded direct page-file list response payload root before reading `body`. A non-mapping payload now raises `NoElementException` with site, page, expected root type, and observed type. Existing missing-body and malformed-body diagnostics remain distinct, and malformed payloads do not seed `page._files` or enter file-table parsing.

## Related Issue

Builds on [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [224-pr-page-file-batch-response-body-context.md](224-pr-page-file-batch-response-body-context.md), and [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md).

This is not a duplicate of Issue 215 because that draft covered mapping responses with missing `body`. It is not a duplicate of Issue 325 because that draft covered mapping responses whose present `body` value had the wrong type. It is not a duplicate of Issues 224 or 334 because those drafts covered batched page-file acquisition through `PageCollection.get_page_files(...)`, not direct `PageFileCollection.acquire(page)`.

No upstream issue was filed from this local workspace.

## Changes

- Validate that the direct page-file list response payload returned by `response.json()` is a mapping before reading `body`.
- Raise site/page-specific `NoElementException` for non-mapping direct page-file payload roots.
- Add a focused direct acquisition regression for a list-valued payload root.
- Preserve existing retry exhaustion, missing-body, non-string-body, parser, cache, direct acquisition, and batched acquisition behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Page-file direct response payload validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A non-mapping direct page-file list response payload fails before body extraction or file parsing. | `TestPageFileCollectionAcquire.test_acquire_malformed_response_payload_type_includes_page_context` returns `["not", "a", "mapping"]` from `files/PageFilesModule` and expects `NoElementException`. | Leaking `AttributeError`, parsing file rows, returning an empty collection, seeding `page._files`, or omitting site/page/type context rejects this local completion claim. |
| Existing missing-body and malformed-body diagnostics remain distinct. | Focused GREEN included `test_acquire_missing_response_body_includes_page_context` and `test_acquire_malformed_response_body_type_includes_page_context`. | Reclassifying `{}` or `{"body": ["not", "html"]}` as a payload-root error, dropping `field=body`, or changing the existing messages rejects this local completion claim. |
| Existing direct page-file behavior remains compatible. | `uv run pytest tests/unit/test_page_file.py -q` passed 125 tests. | Regressing retry exhaustion, request payloads, file parsing, file-size parsing, URL normalization, cache reuse, collection behavior, or `PageFile` construction rejects this local completion claim. |
| Broad unit and static gates remain green. | `uv run pytest tests/unit -q` passed 3921 tests; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `uv run pyright`; `git diff --check`. | Any failed unit, lint, format, type, pyright, or whitespace gate rejects this local completion claim. |
| Diagnostics remain privacy-preserving. | The new message includes only site unix name, page fullname, expected root type, and observed type. | Including raw response JSON, generated file-list HTML, file names, file URLs, credentials, cookies, auth JSON, local rollout paths, account material, or private site data rejects this local completion claim. |

## Testing

Implemented locally in commit `d0daa1f fix(page_file): validate list response payload`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_malformed_response_payload_type_includes_page_context -q` failed before the fix with `AttributeError: 'list' object has no attribute 'get'`.
- GREEN: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_missing_response_body_includes_page_context tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_malformed_response_body_type_includes_page_context tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_malformed_response_payload_type_includes_page_context -q` passed 3 tests.
- `uv run pytest tests/unit/test_page_file.py -q` passed 125 tests.
- `uv run pytest tests/unit -q` passed 3921 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src tests` passed with existing notes about unchecked untyped function bodies and the unused `pyproject.toml` lxml module section.
- `uv run pyright`.
- `git diff --check`.

## Acceptance Criteria

- `PageFileCollection.acquire(page)` still uses the same `files/PageFilesModule` request payload.
- A list-valued decoded response payload for a direct page-file list raises `NoElementException` matching `Page file list response payload is malformed for site: test-site, page: test-page (expected=dict, actual=list)`.
- Mapping payloads without `body` still raise the existing missing-body message.
- Mapping payloads with non-string `body` still raise the existing malformed-body message with `field=body`, `expected=str`, and the observed body type.
- Successful file parsing, retry exhaustion handling, cache assignment, cache reuse, file field parsing, collection lookup behavior, and adjacent batched page-file acquisition remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Direct page-file acquisition cannot safely parse the attachment table unless the AMC JSON root is a mapping with a `body` field. Rejecting non-mapping roots at the response boundary keeps caller diagnostics compact and actionable while avoiding raw file-list content or response payload disclosure.

## Local Evidence, Not For Upstream Paste

- Issue 215 established missing direct page-file response-body context.
- Issue 325 established present non-string direct page-file response-body context.
- Issues 224 and 334 established the adjacent batched page-file response-body diagnostics.
- The broader response-payload series applied the same boundary distinction to action responses and list/read responses across private messages, site applications, forum categories, site members, and forum post revisions.
- Complexity scanning reported no obvious hotspots in `src/wikidot/module/page_file.py`; this slice did not introduce a new abstraction or alter acquisition control flow.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw response JSON, generated file-list HTML, file names, file URLs, and private site content out of upstream discussion.

## Additional Notes

This slice intentionally does not change page validation, request payloads, retry policy, successful file parsing, cache assignment, cached collection reuse, file field validation, batched page-file acquisition, live Wikidot behavior, or upstream filing state. It only validates the decoded direct page-file list response payload root before the existing `body` validation.
