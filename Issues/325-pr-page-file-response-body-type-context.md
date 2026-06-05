# PR Draft: Report Malformed Direct Page File Response Body Types

## Summary

`PageFileCollection.acquire(page)` parses `files/PageFilesModule` AMC response `body` values as generated attachment-list HTML for a single page. Earlier local slices made direct page-file reads retry-aware, cache-aware, site/page-context-rich, parser-scoped, filename-spacing-preserving, and consistent with collection-level page file acquisition. Issue 215 validated missing direct response `body` fields, but one adjacent response-boundary gap remained: if the decoded AMC response was a dictionary with a present but non-string `body` value, the code passed that value into BeautifulSoup and leaked a low-level parser `AttributeError`.

This local slice validates present direct page-file response `body` values before HTML parsing. Non-string bodies now raise site/page-specific `NoElementException` with `field=body`, expected type, and observed type. The diagnostic reports only compact structural context and type names; it does not include raw file-list HTML, response JSON, local rollout paths, credentials, account material, attachment names, or private page content.

## Outcome

Malformed direct page-file response body types now fail at the module response boundary with actionable site/page/type context instead of BeautifulSoup internals.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free attachment inventory, asset audits, source reconciliation, or publication checks.

## Related Issue

Builds on [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [230-pr-cache-direct-page-file-acquisition.md](230-pr-cache-direct-page-file-acquisition.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), and [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md). Those drafts established direct page-file acquisition as a practical retry-aware, cached, parser-scoped, and diagnosable attachment read path while leaving present non-string response bodies as a separate parser-entry boundary.

No upstream issue was filed from this local workspace.

## Changes

- Validate direct page-file response `body` values are strings before BeautifulSoup parsing.
- Convert present non-string direct file-list body values into site/page-specific `NoElementException`.
- Preserve missing-body diagnostics, retry-exhausted behavior, cached direct acquisition, valid empty file lists, file-row parsing, URL normalization, MIME parsing, size parsing, filename spacing, lazy `Page.files`, and collection-level page file acquisition.

## Type Of Change

- Bug fix / diagnostics improvement
- Direct page-file response-body type validation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A direct page-file response with a present non-string `body` field must fail before BeautifulSoup parsing. |
| R2 | Malformed-body-type errors must identify the affected site, page, `field=body`, expected type, and observed type while omitting raw generated file content. |
| R3 | Existing missing-body diagnostics, retry handling, direct file parsing, adjacent page workflows, and repository quality gates must remain compatible. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `PageFileCollection.acquire(page)` raises contextual `NoElementException` when `files/PageFilesModule` returns a list-valued `body`. | `TestPageFileCollectionAcquire.test_acquire_malformed_response_body_type_includes_page_context` expects `Page file list response body is malformed for site: test-site, page: test-page (field=body, expected=str, actual=list)`. | Leaking BeautifulSoup `AttributeError`, silently returning an empty collection, entering file-row parsing, or populating `page._files` rejects this local completion claim. | Direct page-file reads | `tests/unit/test_page_file.py` |
| R2 | The malformed-body-type diagnostic includes only site, page, field name, expected type, and observed type. | The focused regression matches the full message shape and uses a synthetic list-valued body. | Including raw response JSON, generated file-list HTML, attachment names, credentials, local rollout paths, account names, or private page content rejects this local completion claim. | Page-file diagnostics | `src/wikidot/module/page_file.py` |
| R3 | Existing page-file and adjacent page behavior remains green. | The page-file suite passed 36 tests, the adjacent page-file/page run passed 194 tests, and the full unit suite passed 892 tests. | Regressing missing-body diagnostics, retry exhaustion, cached acquisition, empty lists, file-row parsing, URL normalization, MIME parsing, size parsing, filename spacing, lazy page-file behavior, or adjacent page workflows rejects this local completion claim. | Page attachment workflows | `tests/unit/test_page_file.py`; `tests/unit/test_page.py` |

## Testing

Implemented locally in commit `083ac8b fix(page_file): report malformed body types`.

- RED: `uv run --extra test pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_malformed_response_body_type_includes_page_context -q` failed before the fix with BeautifulSoup `AttributeError` for the list-valued direct file-list body.
- GREEN: `uv run --extra test pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_malformed_response_body_type_includes_page_context -q` passed.
- `uv run --extra test pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_malformed_response_body_type_includes_page_context tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_missing_response_body_includes_page_context tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_raises_when_retry_is_exhausted tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_success tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_uses_retry_aware_amc tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_skips_cached_page_files -q` passed 6 tests.
- `uv run --extra test pytest tests/unit/test_page_file.py -q` passed 36 tests.
- `uv run --extra test pytest tests/unit/test_page_file.py tests/unit/test_page.py -q` passed 194 tests.
- `uv run --extra test pytest tests/unit -q` passed 892 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- Direct page-file reads still request `files/PageFilesModule` with the existing page ID payload.
- Missing `body` fields still raise the existing not-found diagnostic from Issue 215.
- Present non-string `body` values raise contextual `NoElementException` before BeautifulSoup parsing.
- The malformed-body-type message includes site, page, `field=body`, expected type, and observed type.
- The malformed-body-type message does not include raw response JSON, generated file-list HTML, attachment names, credentials, local rollout paths, private page content, or private account material.
- Existing retry-exhausted behavior, cached direct acquisition, valid empty file lists, file-row parsing, URL normalization, MIME parsing, size parsing, filename spacing, lazy `Page.files`, and collection-level page file acquisition remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real file-list response body, local rollout path, account material, private page content, attachment names, or generated file-list HTML is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Type validation could treat a future bytes-like body as malformed. Mitigation: AMC JSON bodies are expected to decode generated HTML as strings; preserving only string input keeps the parser boundary explicit.
- Risk: Type validation could mask missing-body diagnostics. Mitigation: `None` remains on the existing missing-body path; only present non-string values use the malformed-type diagnostic.
- Risk: Diagnostics could expose generated file content. Mitigation: messages include site, page, and type names only.

## Dependencies

- The AMC connector already validates decoded response roots as dictionaries before normal module parsing; this slice targets the `body` field value within that dictionary.
- Page-file HTML parser behavior remains unchanged after a valid string body is supplied.

## Open Questions

None for this local slice. Remaining useful work should continue the broader response-body field-type audit across other modules rather than expanding this direct page-file change beyond its list boundary.

## Upstream-Safe Motivation

Direct page attachment inspection is a practical browser-free asset workflow. If the generated file-list response contains a present non-string `body`, wikidot.py should report the affected site, page, and type mismatch before BeautifulSoup internals obscure the failure.

## Local Evidence, Not For Upstream Paste

- The RED failure showed a list-valued direct page-file `body` leaking BeautifulSoup `AttributeError`.
- Existing Issue 215 covered missing `body` fields but intentionally left present malformed values as a separate boundary.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated file-list HTML, attachment names, and private page content out of upstream discussion.

## Additional Notes

This is a response-body field type diagnostics fix. It preserves valid direct page-file behavior while making malformed present response bodies actionable without retaining generated attachment content.
