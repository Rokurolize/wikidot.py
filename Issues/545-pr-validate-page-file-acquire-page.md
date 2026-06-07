# PR Draft: Validate PageFile Direct Acquire Page Input

## Summary

`PageFileCollection.acquire(page)`, also exposed through lazy `Page.files`, is the browser-free direct attachment-list read boundary for a single Wikidot page. Earlier local slices validated retry-aware direct file acquisition, cache reuse, response-body diagnostics, parser diagnostics, file collection state, direct `PageFile.page` record state, and empty collection parent behavior. One adjacent public read-input gap remained: direct calls such as `PageFileCollection.acquire(None)`, booleans, strings, dictionaries, or arbitrary objects reached `page.site` and leaked raw `AttributeError`.

This change reuses the existing `_validate_file_page(...)` helper at the `PageFileCollection.acquire(...)` entry point before cache or request work. Malformed direct `page` arguments now raise `ValueError("page must be a Page")` deterministically, while cached page-file reuse, valid direct acquisition, request payloads, retry-exhausted diagnostics, response-body diagnostics, parser diagnostics, returned file parent state, and adjacent page workflows remain unchanged.

## Outcome

Direct page-file callers now get deterministic input validation before cache or request work instead of incidental attribute errors from malformed page-like values.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call `PageFileCollection.acquire(page)` directly, use `Page.files`, or build generated attachment inventories where a malformed deserialized or fixture-provided page should fail before file-list request construction.

## Current Evidence

Local rollout-backed drafts repeatedly identify page-file reads as practical workflow surfaces. Existing drafts [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [151-pr-page-file-failure-context.md](151-pr-page-file-failure-context.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [224-pr-page-file-batch-response-body-context.md](224-pr-page-file-batch-response-body-context.md), [230-pr-cache-direct-page-file-acquisition.md](230-pr-cache-direct-page-file-acquisition.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md), [471-pr-validate-page-file-collection-page-field.md](471-pr-validate-page-file-collection-page-field.md), [493-pr-validate-page-constructor-files-cache.md](493-pr-validate-page-constructor-files-cache.md), and [536-pr-preserve-empty-page-file-parent.md](536-pr-preserve-empty-page-file-parent.md) establish page-file acquisition, cache behavior, parser diagnostics, response diagnostics, direct record state, collection state, and page cache state as active operational boundaries.

This is not a duplicate of Issue 443. Issue 443 validates the `PageFile(page=...)` field after an attachment record already exists or is manually rehydrated. This slice validates the caller-provided `page` argument to the static `PageFileCollection.acquire(page)` read helper before cache or request work.

This is not a duplicate of Issue 471. Issue 471 validates explicit `PageFileCollection(page=...)` constructor parent state while preserving empty parentless collections. This slice validates that the object passed to the direct acquisition helper is a real `Page` before the helper can read `_files`, `site`, or `id`.

This is not a duplicate of Issue 493. Issue 493 validates the cached `Page._files` constructor state. This slice validates the direct acquisition helper input before any cache or request access.

No upstream issue was filed from this local workspace.

## Changes

- Add a focused regression for malformed direct `PageFileCollection.acquire(page=...)` inputs.
- Reuse `_validate_file_page(...)` before cache or request work.
- Preserve cached page-file reuse, valid direct acquisition, request payloads, retry-exhausted diagnostics, response-body diagnostics, parser diagnostics, returned file parent state, and adjacent page workflows.

## Type Of Change

- Input validation
- Public read-boundary hardening
- Page-file acquisition preflight
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageFileCollection.acquire(None)`, `True`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` must raise `ValueError("page must be a Page")` before cache or request work. |
| R2 | Cached valid page-file collections must still be returned without request work. |
| R3 | Valid direct page-file acquisition, request payloads, retry-exhausted diagnostics, response-body diagnostics, parser diagnostics, and returned `PageFile.page` parent state must remain unchanged. |
| R4 | Page-file, adjacent page, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct page-file acquisition inputs fail at the public read boundary. | `TestPageFileCollectionAcquire.test_acquire_rejects_malformed_page_before_fetch` failed RED for all 5 malformed values with raw `AttributeError`, then passed GREEN after validation was added. | Reaching `page.site`, accepting page-like dictionaries, building requests, or leaking raw attribute errors rejects this local completion claim. | `PageFileCollection.acquire(...)` | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | Cached valid page-file collections remain a no-request path. | Focused GREEN included `test_acquire_skips_cached_page_files`. | Re-fetching cached page files or changing cache identity rejects this local completion claim. | Page-file cache reuse | `tests/unit/test_page_file.py` |
| R3 | Valid direct page-file behavior remains stable. | Focused GREEN included `test_acquire_uses_retry_aware_amc` and `test_acquire_populates_page_files_cache`; the full page-file file passed 88 tests. | Changing request module names, retry behavior, parser output, response diagnostics, returned file parent state, or cache population rejects this local completion claim. | Direct page-file reads | `tests/unit/test_page_file.py` |
| R4 | Existing repository quality gates remain green. | Adjacent page/site/revision/vote tests passed 711 tests, full unit tests passed 2583 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic state; this draft contains no credentials, cookies, auth JSON, raw response bodies, private page content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw page HTML, page source text, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `ca9ede8 fix(page_file): validate direct acquire page`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_rejects_malformed_page_before_fetch -q` failed 5 tests before the fix because malformed pages reached `page.site` and leaked raw `AttributeError`.
- GREEN focused: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_rejects_malformed_page_before_fetch tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_skips_cached_page_files tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_uses_retry_aware_amc tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_populates_page_files_cache -q` passed 8 tests.
- `uv run pytest tests/unit/test_page_file.py -q` passed 88 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py -q` passed 711 tests.
- `uv run pytest tests/unit -q` passed 2583 tests.
- `uv run ruff check src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed.
- `uv run ruff format --check src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy .` passed with no issues in 87 source files.
- `uv run pyright .` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Malformed direct `PageFileCollection.acquire(page=...)` inputs raise `ValueError("page must be a Page")`.
- Cached valid page-file collections remain a no-request path.
- Valid direct page-file reads, request payloads, response diagnostics, parser diagnostics, cache population, and returned file parent state stay unchanged.
- Adjacent page, site, page-revision, and page-vote workflows stay green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private page data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: The new validation could disturb cached page-file reuse. Mitigation: validation accepts real `Page` objects and focused GREEN includes the cached no-request path.
- Risk: The direct acquisition diagnostic could be confused with collection constructor parent validation. Mitigation: both surfaces intentionally use the same required parent message, `ValueError("page must be a Page")`, while constructor behavior still preserves empty parentless collections when `page=None`.

## Dependencies

- Existing `Page` remains the canonical parent type for direct page-file reads.
- Existing `PageFileCollection` constructor and `PageFile` validators remain responsible for file containers, file entries, individual file fields, and parent file state.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`PageFileCollection.acquire(...)` is the direct read entry point behind browser-free attachment inventories. Validating the supplied page object before cache or request work gives generated callers and fixtures deterministic errors for malformed inputs without changing live Wikidot behavior, request shape, retries, parsing, diagnostics, cache reuse, or downstream page traversal.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed malformed direct `page` arguments crossing the public static read boundary and leaking `AttributeError` from `page.site`.
- This slice only validates the `PageFileCollection.acquire(...)` caller-provided parent type. It does not change direct page-file acquisition, parser selectors, response-body diagnostics, file ID/name/link/MIME/size parsing, cache reuse, direct file field validation, lazy `Page.files`, page source/revision/vote behavior, live site behavior, or client authentication.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw page HTML, page source text, private messages, and private site data out of upstream discussion.
