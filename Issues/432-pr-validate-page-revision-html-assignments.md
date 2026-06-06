# PR Draft: Validate Page Revision HTML Assignments

## Summary

`PageRevision.html` is a public property that lazily acquires and caches the rendered HTML for one page revision. The setter documented `value` as `str`, but it accepted any object. A caller could assign `revision.html = None`, `revision.html = True`, `revision.html = 1`, or `revision.html = ["<p>New HTML</p>"]`, causing the public property to store malformed local revision-HTML state and defer failures to later code that expects rendered HTML text.

This change validates direct `PageRevision.html` assignments as strings. Invalid assignments now raise `ValueError("revision.html must be a string")` before mutating `_html`, preserving the last valid cached revision HTML when one exists. Existing lazy revision HTML acquisition, response-body validation, separator trimming, retry behavior, duplicate cached revision HTML reuse, direct revision source assignment validation, and adjacent page/site workflows remain unchanged.

## Outcome

Manually constructed, fixture-created, duplicate-reused, or ledger-rehydrated `PageRevision` objects can no longer silently corrupt their cached rendered revision HTML through the public property setter.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page revision HTML reads, source/HTML comparison, revision snapshot ledgers, translation audits, migration scripts, rollback tooling, publication verification, or local tests that construct `PageRevision` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page revision HTML state as a practical workflow surface. Existing drafts [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [201-pr-page-revision-lazy-site-context.md](201-pr-page-revision-lazy-site-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), and [431-pr-validate-page-revision-source-assignments.md](431-pr-validate-page-revision-source-assignments.md) establish revision HTML reads, retry behavior, deduplication, cache reuse, response diagnostics, collection-entry validation, and adjacent revision source object integrity as active operational boundaries.

Those prior slices are not duplicates. Issues015, 061, 078, 126, 145, 179, 201, 216, and 328 improved revision HTML acquisition, failure visibility, context, parsing, retry, deduplication, cached reuse, and response-body diagnostics. Issue365 validates collection entries before source/HTML acquisition, Issue415 validates direct `Page.revisions = ...` collection assignment, Issue419 validates `PageRevisionCollection(...)` initialization, and Issue431 validates direct `PageRevision.source = ...` assignment. None of them validates direct public `PageRevision.html = ...` assignment before single-revision cache mutation.

## Related Issue

Builds directly on [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), and [431-pr-validate-page-revision-source-assignments.md](431-pr-validate-page-revision-source-assignments.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a `PageRevision.html` value validator.
- Reject `None`, booleans, integers, lists, and other non-string values with `ValueError("revision.html must be a string")`.
- Validate before assigning `_html`, so invalid assignments preserve any previously cached valid revision HTML.
- Preserve valid string assignments, including empty strings.
- Preserve existing lazy revision HTML acquisition, HTML response parsing, retry behavior, duplicate cached revision HTML reuse, revision source assignment validation, and adjacent page/site workflows.

## Type Of Change

- Input validation
- Public property behavior hardening
- Local revision HTML cache integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `revision.html = None`, `revision.html = True`, `revision.html = 1`, and `revision.html = ["<p>New HTML</p>"]` must raise `ValueError("revision.html must be a string")` before mutating `_html`. |
| R2 | Invalid assignments after already-cached valid HTML must preserve that previous string. |
| R3 | Valid string assignments must remain allowed. |
| R4 | Existing lazy revision HTML acquisition, retry behavior, duplicate cached revision HTML reuse, source/HTML collection behavior, page workflows, and site workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent page revision tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed revision HTML assignments fail before local HTML cache mutation. | `TestPageRevision.test_html_setter_rejects_invalid_html` failed RED for `None`, `True`, `1`, and `["<p>New HTML</p>"]` because the setter did not raise, then passed GREEN after validation was added. | Accepting missing values, booleans, numbers, lists, arbitrary objects, or deferring failure to later HTML consumers rejects this local completion claim. | Direct page revision HTML setter | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Invalid assignments preserve the previous valid cached revision HTML. | The focused GREEN asserts `sample_revision.html == "<p>Cached HTML</p>"` after each rejected assignment. | Mutating `_html` before raising, clearing cached HTML, or triggering lazy lookup to recover the value rejects this local completion claim. | Local revision HTML cache | `tests/unit/test_page_revision.py` |
| R3 | String assignments remain valid. | `TestPageRevision.test_html_setter` assigns `"<p>New HTML</p>"` and asserts it is stored unchanged. | Rejecting valid strings, coercing non-strings to strings, or changing direct cache setup behavior rejects this local completion claim. | PageRevision fixtures and cache setup | `tests/unit/test_page_revision.py` |
| R4 | Existing adjacent revision HTML workflows remain green. | Focused setter/property/collection checks passed 11 tests, `tests/unit/test_page_revision.py tests/unit/test_page.py tests/unit/test_site.py` passed 511 tests, and full unit tests passed 1628 tests. | Regressing lazy revision HTML reads, retry exhaustion behavior, response parsing, duplicate cached revision HTML reuse, revision source reads, page source reads, site source iterators, or publish-adjacent workflows rejects this local completion claim. | Page revision, page, and site workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, source text from real sites, revision comments, revision HTML, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent revision/page/site tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `f8dcd42 fix(page_revision): validate html assignments`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_html_setter_rejects_invalid_html -q` failed 4 tests before the fix; every malformed HTML assignment reported `DID NOT RAISE`.
- GREEN: the same focused command passed 4 tests after adding setter validation.
- `uv run ruff format src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` left 2 files unchanged.
- `uv run mypy src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_html_setter tests/unit/test_page_revision.py::TestPageRevision::test_html_setter_rejects_invalid_html tests/unit/test_page_revision.py::TestPageRevision::test_html_property_uses_cache tests/unit/test_page_revision.py::TestPageRevision::test_html_property_lazy_load tests/unit/test_page_revision.py::TestPageRevision::test_html_property_raises_when_retry_is_exhausted tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_success tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_reuses_cached_duplicate_revision_html tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_deduplicates_duplicate_revision_ids -q` passed 11 tests.
- `uv run pytest tests/unit/test_page_revision.py tests/unit/test_page.py tests/unit/test_site.py -q` passed 511 tests.
- `uv run pytest tests/unit -q` passed 1628 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `revision.html = None`, `revision.html = True`, `revision.html = 1`, and `revision.html = ["<p>New HTML</p>"]` raise `ValueError("revision.html must be a string")` without changing an existing cached valid HTML string.
- `revision.html = "<p>New HTML</p>"` remains valid and stores the same string.
- Existing lazy `PageRevision.html` acquisition still runs when `_html` is missing and still reports site/page/revision context if acquisition leaves `_html` unset.
- Existing revision HTML response parsing, separator trimming, duplicate cached revision HTML reuse, source/HTML collection behavior, page source reads, source iterator rows, and site/page workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageRevision.html` is shared by lazy revision HTML reads, duplicate cached revision reuse, revision snapshot ledgers, source/HTML comparison, and tests that seed revision state directly. Direct assignment is useful for caller-created revision objects and data rehydrated from external ledgers, but malformed HTML cache objects should fail at the property boundary instead of silently poisoning later revision HTML consumers.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used revision HTML snapshots, source/HTML comparison, cached duplicate revision reuse, and tests that seed revision HTML caches directly.
- Existing local drafts covered revision HTML acquisition, retry/fallback behavior, duplicate request deduplication, parse-once reuse, lazy failure context, response-body diagnostics, `Page.revisions` assignment validation, `PageRevisionCollection` initialization validation, collection entry validation, and direct revision source assignment validation, but did not cover direct `PageRevision.html = ...` mutation.
- The focused RED failures showed invalid assignments were accepted by the property setter. The GREEN regression covers missing, boolean, integer, and list values and asserts the previous valid HTML string survives.
- This slice only validates direct page revision HTML assignment shape. It does not change lazy revision HTML acquisition, revision HTML parsing, separator trimming, revision source behavior, page source setter validation, create/edit, publish, live site behavior, or parser behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, source text from real sites, revision comments, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed revision HTML cache objects instead of coercing values. Callers that load rendered revision HTML from files, generated structures, JSON, YAML, CLI flags, spreadsheets, databases, or ledgers should normalize the rendered HTML to `str` before assigning it to `PageRevision.html`.
