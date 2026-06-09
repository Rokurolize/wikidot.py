# PR Draft: Validate Page File Collection Retained ID State

## Summary

`PageFileCollection.find(id)` validates malformed caller-provided search-key types before scanning stored files, but the scan still compared each retained `file.id` directly against the search ID. After local fixture, serialized, or rehydrated file state has been mutated incorrectly, booleans and floats can satisfy Python equality against integer file IDs, while `None`, strings, lists, and negative IDs are treated as ordinary not-found misses instead of corrupted retained file-ID state.

This change validates each stored file's retained ID with the existing `_validate_file_id(...)` helper before comparing it to the caller search ID. Malformed retained file IDs now raise `ValueError("id must be an integer")`, negative retained file IDs now raise `ValueError("id must be non-negative")`, valid zero-ID lookup remains accepted, existing absent integer lookup behavior remains unchanged, and no page-file fetch, parser, cache, or live Wikidot behavior changes.

## Outcome

Loaded page-file collections can no longer return a file by Python's loose numeric equality or hide corrupted retained file IDs behind an ordinary not-found result.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free attachment inventories, asset audits, migration ledgers, publication checks, duplicate cached page-file lists, local fixtures, or serialized and rehydrated `PageFileCollection` objects.

## Current Evidence

Local rollout-backed drafts already established page-file reads and attachment identity as practical boundaries. [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [224-pr-page-file-batch-response-body-context.md](224-pr-page-file-batch-response-body-context.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md), [589-pr-validate-page-file-collection-page-ownership.md](589-pr-validate-page-file-collection-page-ownership.md), and [640-pr-validate-non-negative-page-file-ids.md](640-pr-validate-non-negative-page-file-ids.md) cover page-file acquisition, retry behavior, parser diagnostics, response diagnostics, lookup search-key type validation, collection shape, direct scalar types, page ownership, and direct ID range validation.

This slice is not a duplicate of those drafts. Issue 375 validates caller-provided `PageFileCollection.find(id=...)` search-key types before scanning stored files, but it does not validate retained IDs already stored inside the collection. Issues 468 and 640 validate direct `PageFile(id=...)` construction, but they cannot cover a valid file whose ID is corrupted after construction and then reused in a collection. Issue 589 validates retained page ownership in collection entries, not stored file identity values. Issue 640 explicitly left `PageFileCollection.find(...)` lookup semantics unchanged.

## Related Issue / Non-Duplicate Analysis

Builds directly on [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md), [589-pr-validate-page-file-collection-page-ownership.md](589-pr-validate-page-file-collection-page-ownership.md), and [640-pr-validate-non-negative-page-file-ids.md](640-pr-validate-non-negative-page-file-ids.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate each stored `PageFile.id` before `PageFileCollection.find(id)` compares it to the search key.
- Reject retained stored file IDs such as `None`, `True`, `False`, `"1001"`, `1001.0`, and `[]` with `ValueError("id must be an integer")`.
- Reject retained stored file IDs such as `-1` with `ValueError("id must be non-negative")`.
- Preserve valid zero-ID lookup, valid matching lookup, existing absent integer lookup behavior, malformed caller search-key type diagnostics, collection page ownership, direct and batched acquisition, parser diagnostics, cached file collections, and lazy `Page.files`.
- Do not add caller search-key range validation in this slice.

## Type Of Change

- Input validation
- Retained page-file ID hardening
- Loaded collection lookup integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageFileCollection.find(id)` must reject retained stored `file.id` values such as `None`, `True`, `False`, `"1001"`, `1001.0`, and `[]` with `ValueError("id must be an integer")` before comparison. |
| R2 | `PageFileCollection.find(id)` must reject retained stored `file.id=-1` with `ValueError("id must be non-negative")` before comparison. |
| R3 | Valid lookup where the stored file ID and search ID are both `0` must remain accepted. |
| R4 | Existing caller search-key type validation, valid matching lookup, existing absent integer lookup behavior, collection initialization, collection page ownership, direct and batched acquisition, parser diagnostics, cached file collections, lazy `Page.files`, and adjacent page workflows must remain green. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private file data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, page-file module coverage, adjacent page/site coverage, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained stored file IDs fail before lookup comparison. | `test_find_rejects_file_with_malformed_retained_ids` failed RED for six malformed values: booleans and `1001.0` could be accepted through Python equality, while `None`, `"1001"`, and `[]` returned ordinary misses. The test passed GREEN after stored file ID validation. | Accepting booleans/floats, returning ordinary `None` misses for corrupted IDs, coercing values, or returning a file from corrupted retained ID state rejects this local completion claim. | Stored `PageFile.id` during collection lookup | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | Negative retained stored file IDs fail before lookup comparison. | `test_find_rejects_file_with_negative_retained_id` failed RED with an ordinary not-found result, then passed GREEN after stored file ID range validation. | Treating negative stored IDs as ordinary misses, accepting them, matching them, or coercing them rejects this local completion claim. | Stored `PageFile.id` during collection lookup | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R3 | Zero remains a valid retained file ID for lookup. | `test_find_accepts_file_with_zero_retained_id` passed RED and GREEN. | Rejecting `0`, treating it as missing, coercing it to false, or changing returned file identity rejects this local completion claim. | Page-file collection lookup semantics | `tests/unit/test_page_file.py` |
| R4 | Existing compatible behavior remains compatible. | Focused GREEN coverage passed 8 tests, `tests/unit/test_page_file.py` passed 109 tests, adjacent page/site coverage passed 1010 tests, and full unit passed 3189 tests. | Regressing caller search-key type validation, valid matching lookup, existing absent integer lookup behavior, collection initialization, collection page ownership, direct acquisition, batched acquisition, parser diagnostics, cached file collections, lazy `Page.files`, page source/revision/vote behavior, site workflows, or any unit test rejects this local completion claim. | Page-file collection and adjacent page workflows | `tests/unit/test_page_file.py`, `tests/unit/test_page.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic page-file objects and local unit helpers only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw file-list HTML, raw file URLs, attachment names from private pages, private page content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, temporary pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `a33e62d fix(page_file): validate collection retained ids`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollection::test_find_accepts_file_with_zero_retained_id tests/unit/test_page_file.py::TestPageFileCollection::test_find_rejects_file_with_malformed_retained_ids tests/unit/test_page_file.py::TestPageFileCollection::test_find_rejects_file_with_negative_retained_id -q` collected 8 tests: 7 retained stored file-ID cases failed before the fix, and the zero-ID compatibility guard passed.
- GREEN: the same focused command passed 8 tests after stored file IDs were validated before collection lookup comparison.
- `uv run ruff format src/wikidot/module/page_file.py tests/unit/test_page_file.py` left both files unchanged.
- `uv run pytest tests/unit/test_page_file.py -q` passed 109 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1010 tests.
- `uv run pytest tests/unit -q` passed 3189 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageFileCollection.find(1001)` raises `ValueError("id must be an integer")` when a stored file's retained `file.id` is `None`, `"1001"`, or `[]`.
- `PageFileCollection.find(1)`, `find(0)`, and `find(1001)` raise `ValueError("id must be an integer")` when stored retained IDs are `True`, `False`, or `1001.0` before they can match through Python equality.
- `PageFileCollection.find(1001)` raises `ValueError("id must be non-negative")` when a stored file's retained `file.id` is `-1`.
- `PageFileCollection.find(0)` still returns a file whose retained ID is valid integer `0`.
- Existing malformed search-key type rejection, matching lookup, absent integer lookup behavior, collection initialization, collection page ownership, direct acquisition, batched acquisition, parser diagnostics, cached file collections, lazy `Page.files`, and adjacent page workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private file data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageFileCollection.find(id)` is a local lookup over already loaded page-file inventories. The caller search key already has type validation, and stored file rows should be held to the same retained-ID contract before comparison. Validating stored IDs prevents corrupted local state from matching through Python's bool/float equality rules or disappearing as an ordinary not-found result, while preserving valid zero IDs, existing absent integer behavior, and all parser/network behavior.

## Local Evidence

- Existing local drafts covered page-file fetch retry behavior, parser row scoping, response-body diagnostics, parsed field diagnostics, collection search-key type validation, collection constructor validation, collection parent-page validation, direct file scalar type validation, direct file ID range validation, non-negative file sizes, cache reuse, and duplicate file-list handling.
- None of those drafts covered malformed retained stored `PageFile.id` values inside `PageFileCollection.find(...)` because the scan still compared `file.id == id` directly.
- The focused RED failure showed booleans and floats could be accepted as stored file IDs when they compared equal to lookup integers, while `None`, strings, lists, and negative IDs could be misreported as ordinary not-found results.
- This slice only validates retained stored file IDs at the loaded collection lookup comparison boundary. It does not change direct page-file acquisition, batched page-file acquisition, file-list parser field extraction, cached file collections, lazy `Page.files`, `PageFileCollection.find_by_name(...)`, page source/revision/vote behavior, site behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw file-list HTML, file URLs from private pages, attachment names from private pages, page source text, private messages, private page content, and private site data out of upstream discussion.

## Additional Notes

The change intentionally reuses `_validate_file_id(...)` only for stored collection rows. It does not add caller search-key range validation in `PageFileCollection.find(...)`, preserving the prior lookup-surface scope from Issue 375 and the explicit Issue 640 note that direct `PageFile.id` range validation did not change collection lookup semantics.
