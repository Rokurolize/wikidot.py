# PR Draft: Validate Blank Page File Names

## Summary

`PageFileCollection.acquire(page)` and batched page-file parsing already reject file rows whose rendered attachment name is empty, and earlier direct constructor/search validation rejects malformed non-string file-name values. One adjacent public boundary remained: direct `PageFile(name="")` and `PageFileCollection.find_by_name("")` accepted blank and whitespace-only names as valid string values.

This change rejects blank and whitespace-only file names at the direct `PageFile(...)` constructor boundary and at the loaded-collection `find_by_name(...)` lookup boundary. Both raise `ValueError("name must not be empty")` after the existing string-type check. Blank `url` and `mime_type` strings remain valid for existing fixture and rehydrated-record compatibility; this slice only treats the file name as the required attachment identity. Existing parser-side file-name, href, MIME, size, row-ID, response-body, collection, cache, direct acquisition, batched acquisition, and lazy `Page.files` behavior remains unchanged.

## Outcome

Direct page-file records and loaded-collection file-name searches now fail deterministically for missing attachment names, matching the existing parser-side invariant that a real attachment row must have a non-empty displayed name.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free attachment inventories, generated file ledgers, asset audits, migration records, publication checks, direct `PageFile(...)` rehydration, or loaded `PageFileCollection.find_by_name(...)` lookups.

## Current Evidence

Local page-file drafts repeatedly identify attachment data as a practical workflow surface. Existing drafts [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [224-pr-page-file-batch-response-body-context.md](224-pr-page-file-batch-response-body-context.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [383-pr-validate-page-file-find-by-name.md](383-pr-validate-page-file-find-by-name.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md), [545-pr-validate-page-file-acquire-page.md](545-pr-validate-page-file-acquire-page.md), [589-pr-validate-page-file-collection-page-ownership.md](589-pr-validate-page-file-collection-page-ownership.md), and [599-pr-validate-page-files-cache-ownership.md](599-pr-validate-page-files-cache-ownership.md) establish page-file reads, parser diagnostics, response diagnostics, lookup validation, direct constructor type validation, parent-state validation, ownership checks, and cache coherence as active operational boundaries.

This is not a duplicate of Issue 277, which rejects empty rendered names in parser-produced file rows before `PageFile` objects are constructed. It is not a duplicate of Issue 383, which validates only the type of `find_by_name(...)` inputs. It is not a duplicate of Issue 468, which validates direct `PageFile` scalar/text types and explicitly does not require non-empty strings. This slice covers the remaining blank-name content boundary for direct files and loaded-collection lookups.

No upstream issue was filed from this local workspace.

## Changes

- Add a name-specific validator that first preserves the existing `ValueError("name must be a string")` diagnostic for non-string values.
- Reject blank and whitespace-only `PageFile.name` values during direct `PageFile(...)` construction.
- Reject blank and whitespace-only `PageFileCollection.find_by_name(...)` search names before collection scanning.
- Preserve blank `url` and `mime_type` strings as valid direct `PageFile(...)` values for existing fixture and rehydrated-record compatibility.
- Preserve valid file-name matching, valid not-found behavior, parser-side diagnostics, direct and batched acquisition, cache reuse, ownership validation, and lazy `Page.files`.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageFile(name="")` and whitespace-only variants must raise `ValueError("name must not be empty")` after the existing string-type check. |
| R2 | `PageFileCollection.find_by_name("")` and whitespace-only variants must raise `ValueError("name must not be empty")` before scanning stored files. |
| R3 | Non-string file-name diagnostics must remain `ValueError("name must be a string")`. |
| R4 | Blank `PageFile.url` and blank `PageFile.mime_type` must remain valid direct values; this slice must not broaden into URL or MIME syntax validation. |
| R5 | Existing valid file-name lookup, valid missing-name lookup, parser-side file-name/href/MIME/size diagnostics, direct and batched file acquisition, cache reuse, ownership validation, and lazy `Page.files` must remain unchanged. |
| R6 | Focused RED/GREEN, page-file tests, adjacent page/site tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, upstream PRs, private file URLs, private attachment names, or private page content. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Blank direct `PageFile.name` values fail during construction. | `TestPageFile.test_init_rejects_blank_names` failed RED for `""` and `"   "` with `DID NOT RAISE`, then passed GREEN after name validation was added. | Accepting blank direct names, checking blankness before type checks, coercing values, stripping and storing modified names, or rejecting blank URL/MIME fields rejects this local completion claim. | PageFile constructor | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | Blank loaded-collection search names fail before scanning. | `TestPageFileCollection.test_find_by_name_rejects_blank_names` failed RED for `""` and `"   "` with `DID NOT RAISE`, then passed GREEN after `find_by_name(...)` reused the name validator. | Treating blank names as ordinary misses, scanning stored files with blank keys, coercing values, or changing valid not-found behavior rejects this local completion claim. | PageFileCollection lookup | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R3 | Type diagnostics stay stable. | Existing `test_init_rejects_malformed_text_fields` and `test_find_by_name_rejects_non_string_names` stayed green after the fix. | Raising `must not be empty` for non-strings, changing `name must be a string`, or weakening URL/MIME type validation rejects this local completion claim. | Validation precedence | `tests/unit/test_page_file.py` |
| R4 | Blank URL and MIME direct values stay compatible. | `TestPageFile.test_init_allows_blank_url_and_mime_type` passed in the RED run and after the fix. | Rejecting blank URLs, rejecting blank MIME types, adding URL syntax validation, adding MIME syntax validation, or changing stored URL/MIME values rejects this local completion claim. | Direct PageFile compatibility | `tests/unit/test_page_file.py` |
| R5 | Existing page-file workflows remain green. | `tests/unit/test_page_file.py` passed 95 tests; adjacent page/page-file/page-revision/page-votes/site coverage passed 851 tests. | Regressing file acquisition, batched acquisition, parser diagnostics, cache reuse, duplicate page-file reuse, collection ownership, file cache ownership, valid `find_by_name(...)`, `find(...)`, or lazy `Page.files` rejects this local completion claim. | Page-file and adjacent workflows | `tests/unit` |
| R6 | Repository quality gates pass in the local dependency environment. | Full unit passed 2842 tests; full `ruff check`, `ruff format --check`, `mypy`, `pyright`, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | verification commands below |
| R7 | No live site state or private material is needed to prove the behavior. | The regressions use unit-level synthetic file names only; this draft contains no credentials, cookies, auth JSON, raw rollout paths, private account names, raw file responses, private file URLs, private attachment names, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private account data, raw file URLs, attachment names from private pages, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `b5bef18 fix(page_file): validate blank file names`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFile::test_init_rejects_blank_names tests/unit/test_page_file.py::TestPageFile::test_init_allows_blank_url_and_mime_type tests/unit/test_page_file.py::TestPageFileCollection::test_find_by_name_rejects_blank_names -q` failed 4 blank direct-constructor and loaded-collection lookup cases with `DID NOT RAISE`; the blank URL/MIME compatibility guard passed in the same run.
- GREEN focused: the same command passed 5 tests after name blank-string validation was added.
- Page-file coverage: `uv run pytest tests/unit/test_page_file.py -q` passed 95 tests.
- Adjacent coverage: `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 851 tests.
- `uv run ruff format src/wikidot/module/page_file.py tests/unit/test_page_file.py` left 2 files unchanged.
- `uv run pytest tests/unit -q` passed 2842 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageFile(page=..., id=1, name="", url="", mime_type="", size=0)` and whitespace-only name variants raise `ValueError("name must not be empty")`.
- `PageFileCollection.find_by_name("")` and whitespace-only search-name variants raise `ValueError("name must not be empty")`.
- Non-string direct names and search names still raise `ValueError("name must be a string")`.
- Direct `PageFile(url="", mime_type="")` remains valid and stores those strings unchanged when the name is non-empty.
- Valid `find_by_name("document.pdf")` still returns the matching file, and valid absent names still return `None`.
- Existing parser-side missing-name, missing-href, MIME-title, size, row-ID, response-body, direct acquisition, batched acquisition, duplicate-cache, ownership, lazy `Page.files`, live Wikidot semantics, upstream Issues, upstream PRs, pushes, credentials, cookies, auth JSON, and raw response bodies remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

Attachment names are the stable caller-visible identity used by asset inventories, migration ledgers, publication checks, and loaded collection lookup. Parser-produced file rows already treat an empty displayed name as malformed. Direct files and direct lookup names should follow that same invariant so generated or rehydrated data cannot silently store or search for a missing attachment identity.

## Local Evidence, Not For Upstream Paste

- Issue 277 covered parser-side empty rendered file names, proving blank attachment names are not useful for real `files/PageFilesModule` rows.
- Issue 383 covered non-string loaded-collection search names but intentionally left valid string content untouched.
- Issue 468 covered direct `PageFile` scalar/text types and explicitly did not require non-empty strings.
- The focused RED run showed direct `PageFile(name="")`, direct whitespace-only names, `find_by_name("")`, and whitespace-only lookup names were still accepted.
- This slice only validates file-name blankness. It does not validate URL syntax, MIME syntax, positive size semantics, attachment URL ownership, file contents, parser selectors, live site behavior, or valid non-empty file names.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw file response bodies, raw file URLs, attachment names from private pages, page source text from real sites, private page content, and private site data out of upstream discussion.

## Additional Notes

The new validator does not strip or normalize stored non-empty names. It rejects strings whose stripped form is empty and preserves existing behavior for all non-empty names, including names with leading or trailing whitespace.
