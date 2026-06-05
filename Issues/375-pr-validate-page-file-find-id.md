# PR Draft: Validate PageFileCollection.find ID Input

## Summary

`PageFileCollection.find(id)` documents `id` as `int`, but malformed caller-provided search keys were not rejected at the public search boundary. Values such as `None`, `"123"`, and `123.0` were treated as ordinary not-found misses, while `True` could match file ID `1` because `bool` is an `int` subclass.

This change validates the search key before scanning the file collection. Non-integer and boolean values now raise `ValueError("id must be an integer")`. Existing valid lookup behavior and valid not-found behavior remain unchanged for non-boolean integer IDs.

## Outcome

Page file collection callers now get deterministic Python-side preflight validation for malformed file search IDs instead of misleading not-found misses or accidental boolean ID matches.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free attachment inventories, asset audits, source reconciliation, publication checks, content migration, archival indexing, or page review workflows that need stable file lookup behavior.

## Current Evidence

Local rollout-backed drafts repeatedly identify page attachments and page-file inventory as practical read surfaces. Existing drafts [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [224-pr-page-file-batch-response-body-context.md](224-pr-page-file-batch-response-body-context.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), and [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md) cover file fetching, retry behavior, duplicate response reuse, row parsing, cached/direct workflows, response diagnostics, and parsed file-field diagnostics. Adjacent validation drafts [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md) and [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md) cover collection entries and page vote search users.

Those prior slices are not duplicates. They fetch, parse, cache, diagnose, or validate stored file records and adjacent collection/search surfaces, but they do not validate the caller-provided `id` argument to `PageFileCollection.find(...)` before scanning stored files.

## Related Issue

Builds directly on page-file acquisition and parser hardening drafts [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), and the adjacent `find(...)` preflight pattern from [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `PageFileCollection.find(id=...)` accepts only non-boolean integer IDs before scanning stored files.
- Preserve valid `collection.find(123)` behavior when a matching file exists.
- Preserve valid unknown integer behavior: a well-formed integer ID that is absent from the collection still returns `None`.
- Preserve `find_by_name(...)`, direct and batched file acquisition, page-file row parsing, cached file collections, and lazy `Page.files` semantics.

## Type Of Change

- Input validation
- Public API behavior hardening
- Page file lookup preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageFileCollection.find(id=...)` must reject `None`, booleans, strings, floats, and other non-integer values with `ValueError("id must be an integer")` before scanning files. |
| R2 | Valid lookup must remain unchanged for well-formed non-boolean integer IDs that match stored file IDs. |
| R3 | Valid not-found behavior must remain unchanged for well-formed non-boolean integer IDs that are absent from the collection. |
| R4 | Existing `find_by_name(...)`, direct file acquisition, batch file acquisition, page-file row parsing, cached collection reuse, and lazy `Page.files` behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private file data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, page-file collection tests, adjacent page/site tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed search IDs fail before collection iteration can compare them with stored file IDs. | `TestPageFileCollection.test_find_rejects_non_integer_ids` failed RED before the fix for `None`, `True`, `"123"`, and `123.0`, then passed GREEN after validation was added. | Treating malformed IDs as ordinary misses, coercing values, scanning files, or matching `True` to file ID `1` rejects this local completion claim. | Page file search preflight | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | Matching non-boolean integer IDs still return the stored `PageFile`. | Existing page-file collection tests passed after validation was added. | Changing returned file identity, requiring string IDs, or rejecting valid integer IDs rejects this local completion claim. | Page file collection lookup | `tests/unit/test_page_file.py` |
| R3 | Missing non-boolean integer IDs still return `None`. | Existing page-file collection tests passed after validation was added. | Raising for a valid but absent integer ID or changing not-found behavior rejects this local completion claim. | Page file collection lookup | `tests/unit/test_page_file.py` |
| R4 | Adjacent page-file behavior remains green. | `tests/unit/test_page_file.py` passed 40 tests, and adjacent page/page-file/site tests passed 284 tests. | Regressing `find_by_name(...)`, file acquisition, parser diagnostics, cached files, direct file fetches, batch file fetches, or lazy `Page.files` rejects this local completion claim. | Page file workflow | affected page-file, page, and site tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw file URLs, attachment names from private pages, response bodies, private page content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, page-file tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `1e24516 fix(page_file): validate file search ids`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_page_file.py::TestPageFileCollection::test_find_rejects_non_integer_ids` failed 4 parameterized cases before the fix: malformed IDs did not raise, and `True` could match stored file ID `1`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_page_file.py::TestPageFileCollection::test_find_rejects_non_integer_ids` passed 4 tests after adding search-ID preflight.
- `.venv/bin/python -m pytest -q tests/unit/test_page_file.py` passed 40 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_page_file.py tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_page.py::TestPageProperties tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_site.py` passed 284 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1070 tests.
- `.venv/bin/ruff check src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed.
- `.venv/bin/ruff format src/wikidot/module/page_file.py tests/unit/test_page_file.py` left 2 files unchanged.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `collection.find(None)`, `collection.find(True)`, `collection.find("123")`, and `collection.find(123.0)` raise `ValueError("id must be an integer")`.
- A well-formed integer ID matching an existing file still returns that file.
- A well-formed integer ID that is absent from the collection still returns `None`.
- Existing `find_by_name(...)`, direct acquisition, batch acquisition, file row parsing, cached file collections, and lazy `Page.files` behavior remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private file data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `True` tightens behavior for a value that could previously match file ID `1`. Mitigation: `bool` is not a meaningful file ID even though it is an `int` subclass, and accepting it can hide caller payload bugs.
- Risk: Rejecting string or float IDs can expose upstream caller bugs. Mitigation: the documented API type is `int`; callers loading IDs from JSON, CLI flags, spreadsheets, or generated ledgers should normalize to non-boolean integers before calling `find(...)`.
- Risk: Diagnostics could expose private file context. Mitigation: the new error message contains only the input-field name and expected type, not filenames, URLs, response bodies, page content, site names, or account details.

## Dependencies

- Existing `PageFileCollection` storage and iteration semantics remain authoritative for valid integer IDs.
- Existing direct and batched file acquisition code remains unchanged.
- Existing page-file parser diagnostics remain unchanged.
- The validation is local to `src/wikidot/module/page_file.py` and does not affect page lookup, page votes, site search, or file acquisition.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered page file find-ID validation path.

## Upstream-Safe Motivation

File lookup is often fed by generated attachment inventories, audit scripts, migration ledgers, publication checks, or archival indexes. Since `find(...)` compares the supplied ID against stored file IDs, malformed search keys should fail deterministically before collection scanning rather than producing misleading misses or accidentally matching a boolean ID to integer ID `1`.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established page-file data as a practical workflow through file-list acquisition, direct file fetches, batched file fetches, parser diagnostics, response-body diagnostics, parsed-field diagnostics, cache reuse, and duplicate fetch reduction.
- Existing page-file drafts covered fetching, parsing, response diagnostics, cached/direct acquisition, and parsed file fields; they did not validate the caller-provided `PageFileCollection.find(id=...)` search key.
- This slice only validates `PageFileCollection.find(...)` inputs. It does not change `find_by_name(...)`, direct file acquisition, batch file acquisition, page-file parser field extraction, cached file collections, lazy `Page.files`, page source/revision caches, page vote behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw file response bodies, raw file URLs, attachment names from private pages, source text from real sites, private page content, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed search IDs instead of coercing them. Callers that load file search targets from JSON, YAML, CLI flags, spreadsheets, generated structures, or audit ledgers should resolve them into non-boolean integers before calling `PageFileCollection.find(...)`.
