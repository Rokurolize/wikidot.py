# PR Draft: Validate Page ID Assignments

## Summary

`Page.id` is a public property that lazily acquires a Wikidot page ID when no ID is cached, and many page detail, source, revision, vote, file, discussion, metadata, and publish workflows use the cached value once it is present. The setter documented `value` as an integer, but it accepted any object. A caller could assign `page.id = None`, `page.id = True`, `page.id = "12345"`, or `page.id = 12345.0`, causing malformed local state to be reused by later request construction or cache grouping.

This change validates direct `Page.id` assignments as non-boolean integers. Invalid assignments now raise `ValueError("page.id must be an integer")` before mutating the cached `_id`, preserving the last valid ID when one exists.

## Outcome

Manually constructed, fixture-created, or ledger-rehydrated `Page` objects can no longer silently corrupt their cached page ID through the public property setter.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page read/write workflows, generated page ledgers, migration scripts, translation audits, page detail crawlers, or local tests that construct `Page` objects directly.

## Current Evidence

Local rollout evidence repeatedly uses page ID caching as a practical workflow boundary. Existing drafts [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [002-pr-batch-source-page-id-lookups.md](002-pr-batch-source-page-id-lookups.md), [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md), [013-pr-refresh-cached-page-source.md](013-pr-refresh-cached-page-source.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [132-pr-reuse-cached-duplicate-page-ids.md](132-pr-reuse-cached-duplicate-page-ids.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), and [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md) establish page ID state as an active operational surface.

Those prior slices are not duplicates. Issues187 and 197 improved lazy `Page.id` failure context, Issues066 and 132 improved page-ID acquisition deduplication and cached duplicate reuse, Issue225 exposed already-loaded page IDs in source-result ledgers without triggering lookup, Issue368 validated `PageCollection` entries, and Issue412 validated the optional `Page.create_or_edit(..., page_id=...)` write argument. None of them validates direct public `Page.id = ...` assignments before cached state mutation.

## Related Issue

Builds directly on [187-pr-page-id-property-context.md](187-pr-page-id-property-context.md), [197-pr-page-id-site-context.md](197-pr-page-id-site-context.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md), and [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a required page-ID validator for direct `Page.id` assignments.
- Reject `None`, booleans, strings, floats, and other non-integer values with `ValueError("page.id must be an integer")`.
- Validate before assigning `_id`, so invalid assignments preserve any previously cached valid page ID.
- Preserve valid non-boolean integer assignments and existing lazy `Page.id` acquisition behavior.
- Preserve existing page collection, source, revision, vote, file, discussion, metadata, create/edit, publish, and source-result ledger behavior for valid IDs.

## Type Of Change

- Input validation
- Public property behavior hardening
- Local cache integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `page.id = None`, `page.id = True`, and `page.id = False` must raise `ValueError("page.id must be an integer")` before mutating `_id`. |
| R2 | `page.id = "12345"` and `page.id = 12345.0` must raise the same stable diagnostic before mutating `_id`. |
| R3 | Invalid assignments after an already-cached valid page ID must preserve that previous ID. |
| R4 | Valid non-boolean integer assignments must remain allowed. |
| R5 | Lazy page-ID acquisition and valid page source, revision, vote, file, discussion, metadata, create/edit, publish, and source-result ledger workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent page/site tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Missing and boolean assignments fail before local ID mutation. | New `TestPageProperties.test_id_setter_rejects_invalid_ids` failed RED for `None`, `True`, and `False` because the setter did not raise, then passed GREEN after validation was added. | Accepting `None`, treating booleans as integer IDs, clearing `_id`, or surfacing later request/cache failures rejects this local completion claim. | Direct page ID setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | String and float assignments fail with the same stable diagnostic before local ID mutation. | The same focused regression failed RED for `"12345"` and `12345.0`, then passed GREEN after validation was added. | Coercing text or floats into IDs, storing the malformed value, or deferring failure to a later request path rejects this local completion claim. | Direct page ID setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Invalid assignments preserve the previous valid cached ID. | The focused GREEN asserts `mock_page_with_id.id == 12345` after each rejected assignment. | Mutating `_id` before raising, clearing the cached ID, or triggering lazy lookup to recover the value rejects this local completion claim. | Local page ID cache | `tests/unit/test_page.py` |
| R4 | Real integer assignments remain valid. | Existing property and page collection tests still pass, including many fixtures and duplicate-page workflows that assign real integer IDs. | Rejecting non-bool integers or changing existing direct ID assignment behavior rejects this local completion claim. | Page fixtures and cache setup | `tests/unit/test_page.py` |
| R5 | Existing page and site workflows remain green. | Page property tests passed 24 tests, page collection acquisition passed 63 tests, adjacent page/page-file/page-revision/page-vote/site tests passed 485 tests, and full unit tests passed 1463 tests. | Regressing lazy lookup, cached duplicate reuse, page source/revision/vote/file acquisition, discussion lookup, metadata updates, create/edit, publish, or result ledger behavior rejects this local completion claim. | Page and site workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent page/site tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `5204caf fix(page): validate page id assignments`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_id_setter_rejects_invalid_ids -q` failed 5 tests before the fix with `Failed: DID NOT RAISE <class 'ValueError'>`; the bad value was accepted by the setter.
- GREEN: the same focused command passed 5 tests after adding page-ID assignment validation.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left both files unchanged.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties -q` passed 24 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 63 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 485 tests.
- `uv run --extra test pytest tests/unit -q` passed 1463 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `page.id = None`, `page.id = True`, and `page.id = False` raise `ValueError("page.id must be an integer")` without changing an existing cached valid ID.
- `page.id = "12345"` and `page.id = 12345.0` raise `ValueError("page.id must be an integer")` without changing an existing cached valid ID.
- `page.id = 12345` remains valid.
- Existing lazy `Page.id` acquisition still runs when `_id` is missing and still reports site/page context if acquisition leaves `_id` unset.
- Existing page collection acquisition, cached duplicate reuse, source/revision/vote/file acquisition, discussion lookup, metadata updates, create/edit, publish, and source-result ledger behavior remains green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page.id` is shared by page detail reads, cache grouping, source/revision/vote/file acquisition, discussion lookup, metadata writes, publish helpers, and result ledgers. Direct assignment is useful for test fixtures, caller-created page objects, and data rehydrated from external ledgers, but malformed identifiers should fail at the property boundary instead of silently poisoning later request construction.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free page acquisition, source verification, metadata updates, publish helpers, and source-result ledgers that depend on cached page IDs.
- Existing local drafts covered lazy ID failure context, page-ID acquisition deduplication, cached duplicate ID reuse, source-result page ID export, page collection entry validation, and create/edit `page_id` validation, but did not cover direct `Page.id` setter mutation.
- The focused RED failures showed invalid assignments were accepted by the property setter. The GREEN regression covers missing, boolean, string, and float values and asserts the previous valid ID survives.
- This slice only validates direct page-ID assignment shape; it does not change URL construction, lazy ID acquisition, page-ID parsing, page collection entry validation, create/edit `page_id`, source/text input validation, metadata updates, publish behavior, result fields, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed page IDs instead of coercing values. Callers that load identifiers from text-based configuration or external ledgers should parse and validate those values into real integers before assigning them to `Page.id`.
