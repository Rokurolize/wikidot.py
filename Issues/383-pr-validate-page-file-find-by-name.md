# PR Draft: Validate PageFileCollection Name Searches

## Summary

`PageFileCollection.find_by_name(name)` documents `name` as a string, but malformed caller-provided search keys were not rejected at the public loaded-collection lookup boundary. Values such as `None`, booleans, integers, and floats were treated as ordinary misses instead of stable caller errors.

This change validates the search key before scanning stored page files. Malformed `name` values now raise `ValueError("name must be a string")`. Existing valid lookup behavior and valid not-found behavior remain unchanged for string file names.

## Outcome

Page file collection callers now get deterministic Python-side preflight validation for malformed file-name search keys instead of silent misses that can hide generated-ledger, JSON, CLI, or spreadsheet input bugs.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free attachment inventories, asset audits, source reconciliation, publication checks, content migration, archival indexing, or page review workflows that need stable file-name lookup behavior.

## Current Evidence

Local rollout-backed drafts repeatedly identify page attachments and page-file inventory as practical read surfaces. Existing drafts [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [224-pr-page-file-batch-response-body-context.md](224-pr-page-file-batch-response-body-context.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), and [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md) cover file fetching, retry behavior, duplicate response reuse, row parsing, cached/direct workflows, response diagnostics, parsed file-field diagnostics, and ID-based loaded collection lookup validation. Adjacent loaded-collection search preflight drafts [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [381-pr-validate-private-message-find-id.md](381-pr-validate-private-message-find-id.md), and [382-pr-validate-page-collection-find-fullname.md](382-pr-validate-page-collection-find-fullname.md) establish the local pattern for validating lookup keys before scanning already loaded objects.

Those prior slices are not duplicates. They fetch, parse, cache, diagnose, validate stored file records, or validate ID/fullname lookup keys. Issue 375 explicitly preserved `find_by_name(...)`, but it did not validate the caller-provided `name` argument to `PageFileCollection.find_by_name(...)` before scanning stored files.

## Related Issue

Builds directly on page-file acquisition and parser hardening drafts [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), and the adjacent `find(...)` preflight pattern from [382-pr-validate-page-collection-find-fullname.md](382-pr-validate-page-collection-find-fullname.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `PageFileCollection.find_by_name(name=...)` accepts only strings before scanning stored files.
- Preserve valid `collection.find_by_name("document.pdf")` behavior when a matching file exists.
- Preserve valid unknown string behavior: a well-formed absent filename still returns `None`.
- Preserve ID-based `find(...)`, direct and batched file acquisition, page-file row parsing, cached file collections, and lazy `Page.files` semantics.

## Type Of Change

- Input validation
- Public API behavior hardening
- Page file name lookup preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageFileCollection.find_by_name(name=...)` must reject `None`, booleans, integers, floats, and other non-string values with `ValueError("name must be a string")` before scanning files. |
| R2 | Valid lookup must remain unchanged for string names that match stored file names. |
| R3 | Valid not-found behavior must remain unchanged for string names that are absent from the collection. |
| R4 | Existing ID lookup, direct file acquisition, batch file acquisition, page-file row parsing, cached collection reuse, and lazy `Page.files` behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private file data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, page-file tests, adjacent page/site tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed file names fail before collection iteration can compare them with stored file names. | `TestPageFileCollection.test_find_by_name_rejects_non_string_names` failed RED before the fix for `None`, `True`, `123`, and `1.0`, then passed GREEN after validation was added. | Treating malformed names as ordinary misses, coercing values, or scanning files with non-string keys rejects this local completion claim. | Page file name search preflight | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | Matching string search keys still return the stored `PageFile`. | Existing `test_find_by_name_existing` passed after validation was added. | Changing returned file identity, rejecting valid string names, or comparing unrelated fields rejects this local completion claim. | Page file collection lookup | `tests/unit/test_page_file.py` |
| R3 | Missing string search keys still return `None`. | Existing `test_find_by_name_nonexistent` passed after validation was added. | Raising for a valid but absent string name or changing not-found behavior rejects this local completion claim. | Page file collection lookup | `tests/unit/test_page_file.py` |
| R4 | Adjacent page-file behavior remains green. | `tests/unit/test_page_file.py` passed 44 tests, adjacent page/page-file/site tests passed 365 tests, and full unit tests passed 1106 tests. | Regressing ID lookup, direct acquisition, batch acquisition, parser diagnostics, cached files, direct file fetches, batch file fetches, or lazy `Page.files` rejects this local completion claim. | Page file workflow | affected page-file, page, and site tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw file URLs, attachment names from private pages, response bodies, private page content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, page-file tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `c70de13 fix(page_file): validate file search names`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_page_file.py::TestPageFileCollection::test_find_by_name_rejects_non_string_names` failed 4 parameterized cases before the fix because malformed names did not raise.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_page_file.py::TestPageFileCollection::test_find_by_name_rejects_non_string_names` passed 4 tests after adding search-name preflight.
- `.venv/bin/python -m pytest -q tests/unit/test_page_file.py` passed 44 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_page_file.py tests/unit/test_page.py tests/unit/test_site.py` passed 365 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1106 tests.
- `.venv/bin/ruff check src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed.
- `.venv/bin/ruff format src/wikidot/module/page_file.py tests/unit/test_page_file.py` left 2 files unchanged.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `collection.find_by_name(None)`, `collection.find_by_name(True)`, `collection.find_by_name(123)`, and `collection.find_by_name(1.0)` raise `ValueError("name must be a string")`.
- A well-formed string name matching an existing file still returns that file.
- A well-formed string name that is absent from the collection still returns `None`.
- Existing `find(id=...)`, direct acquisition, batch acquisition, file row parsing, cached file collections, and lazy `Page.files` behavior remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private file data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting non-string file-name search keys can expose caller bugs that previously looked like ordinary misses. Mitigation: the documented API type is a string filename; deterministic preflight is safer than silently hiding malformed generated input.
- Risk: The change could be confused with file-name parser validation. Mitigation: parser diagnostics for generated file rows remain unchanged; this slice only validates caller-provided loaded-collection search keys.
- Risk: Diagnostics could expose private file context. Mitigation: the new error message contains only the input-field name and expected type, not filenames, URLs, response bodies, page content, site names, or account details.

## Dependencies

- Existing `PageFileCollection` storage and iteration semantics remain authoritative for valid string names.
- Existing ID lookup, direct and batched file acquisition code remains unchanged.
- Existing page-file parser diagnostics remain unchanged.
- The validation is local to `src/wikidot/module/page_file.py` and does not affect page lookup, page votes, site search, file acquisition, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered page file find-by-name validation path.

## Upstream-Safe Motivation

File-name lookup is often fed by generated attachment inventories, audit scripts, migration ledgers, publication checks, or archival indexes. Since `find_by_name(...)` compares supplied values against stored file names, malformed search keys should fail deterministically before collection scanning rather than producing misleading misses.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established page-file data as a practical workflow through file-list acquisition, direct file fetches, batched file fetches, parser diagnostics, response-body diagnostics, parsed-field diagnostics, cache reuse, duplicate fetch reduction, and loaded collection lookup helpers.
- Existing page-file drafts covered fetching, parsing, response diagnostics, cached/direct acquisition, parsed file fields, and ID search validation; they did not validate the caller-provided `PageFileCollection.find_by_name(name=...)` search key.
- This slice only validates `PageFileCollection.find_by_name(...)` inputs. It does not change `find(id=...)`, direct file acquisition, batch file acquisition, page-file parser field extraction, cached file collections, lazy `Page.files`, page source/revision caches, page vote behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw file response bodies, raw file URLs, attachment names from private pages, source text from real sites, private page content, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed search names instead of coercing them. Callers that load file search targets from JSON, YAML, CLI flags, spreadsheets, generated structures, or audit ledgers should resolve them into strings before calling `PageFileCollection.find_by_name(...)`.
