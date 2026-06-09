# PR Draft: Validate Page File Link Href Routes

## Summary

`PageFileCollection.acquire(page)` and `PageCollection.get_page_files()` parse generated `files/PageFilesModule` rows into `PageFile.url` values. Issue [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md) made missing or blank attachment link `href` values fail with context instead of resolving to the site root, but a present malformed href was still passed through `urljoin(...)`. As a result, `javascript:alert(1)`, `mailto:file@example.com`, `http:file.txt`, `/`, `#file.txt`, and `?file=file.txt` could become stored attachment URLs on a structurally valid file row.

This change validates generated attachment href route shape before constructing `PageFile` records. Valid relative file URLs and valid absolute HTTP(S) file URLs remain compatible, while malformed present hrefs raise contextual `NoElementException`.

## Outcome

Browser-free page-file inventories no longer store non-download schemes, hostless HTTP strings, site-root URLs, query-only routes, or fragment-only routes as attachment download URLs. Existing relative `local--files` links and absolute HTTP(S) links continue to parse as before.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use attached-file reads for browser-free asset inventories, generated attachment ledgers, migration audits, publication checks, file download reconciliation, cached page-file reuse, local fixtures, or `Page.files` lazy reads.

## Current Evidence

Local rollout-backed drafts repeatedly identify page attachments as a practical read surface. [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [224-pr-page-file-batch-response-body-context.md](224-pr-page-file-batch-response-body-context.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [383-pr-validate-page-file-find-by-name.md](383-pr-validate-page-file-find-by-name.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md), [471-pr-validate-page-file-collection-page-field.md](471-pr-validate-page-file-collection-page-field.md), [589-pr-validate-page-file-collection-page-ownership.md](589-pr-validate-page-file-collection-page-ownership.md), [599-pr-validate-page-files-cache-ownership.md](599-pr-validate-page-files-cache-ownership.md), [632-pr-validate-non-negative-page-file-sizes.md](632-pr-validate-non-negative-page-file-sizes.md), [671-pr-validate-page-file-collection-retained-id-state.md](671-pr-validate-page-file-collection-retained-id-state.md), and [708-pr-validate-page-file-collection-retained-names.md](708-pr-validate-page-file-collection-retained-names.md) establish file fetches, parser diagnostics, response diagnostics, duplicate cache reuse, lookup validation, direct field validation, retained-state validation, and cache ownership as active operational boundaries.

This slice is not a duplicate of Issue 276, which rejects missing or blank link hrefs. It is not a duplicate of Issue 468, which validates direct `PageFile.url` type but intentionally keeps blank direct URLs compatible for existing fixtures. It is not a duplicate of response-body, row-ID, name, MIME, size, collection, or cache-ownership drafts, because this slice validates present generated attachment href route shape before `PageFile.url` is stored.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), and the page-file record/cache drafts listed in Current Evidence.

## Changes

- Add a generated file-list href parser using `urlsplit(...)` and `urljoin(...)`.
- Reject non-HTTP(S) schemes such as `javascript:` and `mailto:`.
- Reject `http` or `https` hrefs that do not include a host, such as `http:file.txt`.
- Reject hrefs that resolve to a URL with no path segment, including `/`, `#file.txt`, and `?file=file.txt`.
- Preserve relative attachment href normalization through the site URL.
- Preserve absolute HTTP(S) attachment hrefs such as `https://cdn.example.com/file.txt`.
- Preserve existing missing/blank href diagnostics, filename text extraction, MIME title parsing, size parsing, row-ID validation, nested-row scoping, direct acquisition, batched acquisition, cached duplicate reuse, lazy `Page.files`, and direct `PageFile` constructor compatibility.

## Type Of Change

- Bug fix
- Page-file parser route-shape validation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated page-file link href with a non-download scheme such as `javascript:` or `mailto:` must fail before constructing `PageFile`. |
| R2 | An `http` or `https` href without a host must fail before constructing `PageFile`. |
| R3 | A root, query-only, or fragment-only href must fail before constructing `PageFile`. |
| R4 | Malformed href diagnostics must include site unix name, page fullname, file name, file ID, `field=href`, and the observed href value. |
| R5 | Valid relative attachment hrefs must still normalize against the site URL. |
| R6 | Valid absolute HTTP(S) attachment hrefs must remain preserved. |
| R7 | Existing missing/blank href errors, file name, MIME, size, row-ID, nested-row, direct acquisition, batched acquisition, duplicate cache, lazy page-file, and adjacent page workflows must remain compatible. |
| R8 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw page-file bodies, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, full page-file tests, adjacent page/file/source/revision/vote/site tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `javascript:alert(1)` and `mailto:file@example.com` raise `NoElementException` before `PageFile` construction. | The focused RED failed with `DID NOT RAISE`; focused GREEN passed after href parsing. | Storing a non-HTTP(S) scheme in `PageFile.url` rejects this local completion claim. | Page-file parser | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | `http:file.txt` raises the contextual malformed-href error. | The parametrized malformed-route regression covers hostless HTTP. | Treating hostless HTTP text as a relative file URL rejects this local completion claim. | Page-file parser | page-file tests |
| R3 | `/`, `#file.txt`, and `?file=file.txt` raise the contextual malformed-href error. | The parametrized malformed-route regression covers root, fragment-only, and query-only hrefs. | Returning the site root URL, site-root fragment URL, or site-root query URL as an attachment URL rejects this local completion claim. | Page-file parser | page-file tests |
| R4 | The malformed-href diagnostic includes site, page, file name, file ID, field, and raw href value. | The regression matches `Page file link href is malformed for site: test-site, page: test-page, file: file.txt (id=100, field=href, value=<href>)`. | Omitting the file row location or observed href rejects this local completion claim. | Parser diagnostics | page-file tests |
| R5 | `/local--files/test-page/image.png` still becomes a site absolute URL. | Existing `test_acquire_success` passed in focused and full page-file coverage. | Rejecting valid relative attachment links or changing normalized file URLs rejects this local completion claim. | Relative file URL compatibility | page-file tests |
| R6 | `https://cdn.example.com/file.txt` remains exactly preserved. | Existing `test_acquire_preserves_absolute_file_url` passed in focused and full page-file coverage. | Rewriting or rejecting valid absolute HTTP(S) file URLs rejects this local completion claim. | Absolute file URL compatibility | page-file tests |
| R7 | Existing page-file and adjacent workflows remain green. | Focused nearby tests, full `test_page_file.py`, adjacent page/file/source/revision/vote/site tests, and full unit tests passed. | Regressing missing href diagnostics, MIME/size parsing, row scoping, direct/batched acquisition, cached duplicate reuse, lazy `Page.files`, or adjacent page/source/revision/vote/site behavior rejects this local completion claim. | Page-file workflow | `tests/unit` |
| R8 | No live site state or private material is needed. | All regressions use synthetic generated file-list HTML and mocked AMC responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private attachment names, private file URLs, page source, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, page-file tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `282a52f fix(page_file): validate file link href routes`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_rejects_malformed_file_link_href_routes -q` failed before the fix with 6 `DID NOT RAISE` malformed-route cases.
- GREEN focused: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_rejects_malformed_file_link_href_routes tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_success tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_preserves_absolute_file_url tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_requires_file_link_href tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_multiple_files tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_ignores_nested_file_rows -q` passed 11 tests.
- `uv run pytest tests/unit/test_page_file.py -q` passed 122 tests.
- `uv run pytest tests/unit/test_page_file.py tests/unit/test_page.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1125 tests.
- `uv run pytest tests/unit -q` passed 3722 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageFileCollection.acquire(page)` raises a contextual `NoElementException` for `javascript:alert(1)`.
- `PageFileCollection.acquire(page)` raises the same diagnostic family for `mailto:file@example.com`.
- `PageFileCollection.acquire(page)` raises the same diagnostic family for `http:file.txt`.
- `PageFileCollection.acquire(page)` raises the same diagnostic family for `/`.
- `PageFileCollection.acquire(page)` raises the same diagnostic family for `#file.txt`.
- `PageFileCollection.acquire(page)` raises the same diagnostic family for `?file=file.txt`.
- The malformed-href error includes site unix name, page fullname, file name, file ID, `field=href`, and the raw href value.
- Valid relative file links such as `/local--files/test-page/image.png` still normalize against the site URL.
- Valid absolute HTTP(S) file links such as `https://cdn.example.com/file.txt` are still preserved.
- Existing missing or blank link href behavior remains on the `Page file link href is not found ...` path.
- Existing filename, MIME, size, row-ID, nested-row, direct acquisition, batched acquisition, cached duplicate, lazy page-file, and adjacent page workflows remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw real page-file HTML, local rollout path, private attachment name, private file URL, page source, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Tightening file href route parsing could reject an unusual but valid generated download link. Mitigation: relative file links remain supported, absolute HTTP(S) links remain supported, and the validation only rejects non-download schemes, hostless HTTP(S), and links that resolve to no path segment.
- Risk: This could be confused with direct `PageFile.url` validation. Mitigation: direct `PageFile(url="")` fixture compatibility is unchanged; this slice validates only generated file-list hrefs that are already required to be present and non-blank.
- Risk: This could blur previous missing-href diagnostics. Mitigation: missing or blank href values still use `Page file link href is not found ...`; only present malformed route shapes use `Page file link href is malformed ...`.
- Risk: Diagnostics could expose raw file-list HTML. Mitigation: the new diagnostic reports only the scalar href value plus site/page/file/field context, not full response bodies, credentials, cookies, local paths, page source, private attachment content, or private site data.

## Dependencies

- `files/PageFilesModule` continues to represent attachment links as relative or absolute HTTP(S) hrefs.
- `PageFile.url` remains a stored download URL string; direct constructor type compatibility is unchanged.
- `PageFileCollection._parse_file_fields_from_html(...)` remains the shared parser for direct and batched file acquisition.

## Open Questions

None for this local slice. Future page-file parser changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

`PageFile.url` is the download URL that downstream callers use for attachment inventories, asset audits, migration ledgers, and publication checks. A JavaScript URL, mailto URL, hostless HTTP string, site-root URL, query-only route, or fragment-only route is not an attached-file download URL. Validating generated href route shape keeps malformed module output visible while preserving normal relative and absolute HTTP(S) attachment links.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: six malformed present hrefs did not raise and were accepted as stored attachment URLs.
- Existing local drafts covered page-file fetch retry, duplicate request reduction, shared parser reuse, row scoping, missing hrefs, filename/MIME/size/row-ID diagnostics, response-body typing, direct record fields, collection construction, retained state, and cache ownership; they did not validate present generated attachment href route shape.
- This slice does not change request payloads, retry policy, file row selectors, filename text extraction, MIME title extraction, size parsing, direct `PageFile` constructor rules, direct `PageFileCollection` constructor rules, `Page.files` cache invalidation, live Wikidot behavior, upstream filing state, or valid relative/absolute HTTP(S) file output.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated file-list HTML from real sites, page source, private attachment names, private file URLs, private file contents, and private site data out of upstream discussion.
