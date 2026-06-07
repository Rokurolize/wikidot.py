# PR Draft: Validate Page Revision Collection Page Ownership

## Summary

`PageRevisionCollection` validates its optional collection parent `page`, and each `PageRevision` validates its own retained `page`, but source/HTML acquisition still trusted that every contained revision belonged to the collection page used for request routing. A caller could construct or rehydrate `PageRevisionCollection(page_a, [revision_from_page_b])`; `get_sources()` and `get_htmls()` would then request the target revision through `page_a.site` and apply source/HTML data using the collection page context even though the target revision retained another page.

This change validates revision entry ownership at the shared `PageRevisionCollection._generic_acquire()` boundary before cached duplicate reuse, request grouping, AMC retry work, response parsing, `PageSource` assignment, or HTML cache mutation. Revisions whose retained `revision.page` is not the collection page now raise `ValueError("revisions must belong to the collection page")`. Empty collections, valid same-page source and HTML acquisition, duplicate revision-ID reuse, cached duplicate reuse, retry-exhausted handling, response diagnostics, lazy `PageRevision.source`, lazy `PageRevision.html`, and adjacent page workflows remain unchanged.

## Outcome

Page revision source and HTML reads now reject different-page target revisions before one collection page can drive request routing or cache mutation for revisions retained from another page.

## Current Evidence

Existing drafts [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [200-pr-page-revision-source-parse-site-context.md](200-pr-page-revision-source-parse-site-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [472-pr-validate-page-revision-collection-page-field.md](472-pr-validate-page-revision-collection-page-field.md), and [586-pr-validate-page-batch-target-site.md](586-pr-validate-page-batch-target-site.md) establish page revision source/HTML acquisition, cached duplicate reuse, collection-entry validation, collection parent validation, and target ownership hardening as practical workflow surfaces.

This slice is not a duplicate of those issues. Issue 472 validates the explicit `PageRevisionCollection.page` field type, Issue 442 validates each `PageRevision.page` field type, Issue 365 validates entries are `PageRevision` instances, and the source/HTML response drafts cover retry, deduplication, and parser diagnostics. None validates a valid `PageRevision` entry whose retained `revision.page` is individually valid but does not match the collection page that will be used for source/HTML acquisition.

No upstream issue was filed from this local workspace.

## Changes

- Add a shared page-revision ownership preflight for source/HTML acquisition targets.
- Apply the preflight in `PageRevisionCollection._generic_acquire()` after entry type validation and before cached duplicate grouping or AMC request work.
- Add public regressions for `get_sources()` and `get_htmls()` with a valid revision retained from a different page on the same site.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevisionCollection(page_a, [revision_from_page_b]).get_sources()` must reject the different-page revision with `ValueError("revisions must belong to the collection page")` before AMC request work or source cache mutation. |
| R2 | `PageRevisionCollection(page_a, [revision_from_page_b]).get_htmls()` must reject the different-page revision with the same diagnostic before AMC request work or HTML cache mutation. |
| R3 | The shared preflight must preserve existing non-revision entry validation, empty no-parent behavior, valid same-page source/HTML acquisition, duplicate revision-ID reuse, cached duplicate reuse, retry-exhausted handling, response diagnostics, and lazy revision accessors. |
| R4 | Focused RED/GREEN, page revision collection coverage, full page revision module, adjacent page/page-file/page-vote/site tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Different-page revision source targets fail before request work. | `TestPageRevisionCollection.test_get_sources_rejects_revision_from_different_page_before_fetch` failed RED with `DID NOT RAISE`, then passed GREEN with `ValueError("revisions must belong to the collection page")`, no `amc_request_with_retry` call, and no `_source` mutation. | Calling `amc_request_with_retry`, accepting a different-page revision, mutating `_source`, or deferring failure to response diagnostics rejects this local completion claim. | `PageRevisionCollection.get_sources()` and `_generic_acquire()` | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Different-page revision HTML targets fail before request work. | `TestPageRevisionCollection.test_get_htmls_rejects_revision_from_different_page_before_fetch` passed after the shared preflight with the same diagnostic, no `amc_request_with_retry` call, and no `_html` mutation. | Calling `amc_request_with_retry`, accepting a different-page revision, mutating `_html`, or deferring failure to response diagnostics rejects this local completion claim. | `PageRevisionCollection.get_htmls()` and `_generic_acquire()` | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R3 | Existing page revision collection behavior remains stable. | `TestPageRevisionCollection` passed 52 tests, and `tests/unit/test_page_revision.py` passed 112 tests. | Regressing page-required errors, non-revision entry validation, valid source/HTML parsing, duplicate revision-ID deduplication, cached duplicate reuse, retry-exhausted handling, direct source/html setter validation, or lazy source/HTML behavior rejects this local completion claim. | Page revision workflows | `tests/unit/test_page_revision.py` |
| R4 | Adjacent workflows and repository quality gates remain green. | Adjacent page/page-revision/page-file/page-vote/site tests passed 822 tests, the full unit suite passed 2690 tests, ruff check passed, ruff format check passed with 87 files already formatted, mypy passed with no issues in 87 source files, pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live auth material or private state is needed to prove the behavior. | The regressions use synthetic valid `Page` and `PageRevision` objects; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private forum content, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `bc702e0 fix(page_revision): validate revision collection page ownership`.

- RED target-page source ownership: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_rejects_revision_from_different_page_before_fetch -q` failed before the fix with `DID NOT RAISE` after the different-page revision reached source acquisition.
- GREEN focused source regression: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_rejects_revision_from_different_page_before_fetch -q` passed 1 test.
- Focused source/HTML ownership coverage: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_rejects_revision_from_different_page_before_fetch tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_rejects_revision_from_different_page_before_fetch -q` passed 2 tests.
- Page revision collection coverage: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection -q` passed 52 tests.
- Full page revision module: `uv run pytest tests/unit/test_page_revision.py -q` passed 112 tests.
- Adjacent page/page-revision/page-file/page-vote/site tests: `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 822 tests.
- `uv run pytest tests/unit -q` passed 2690 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageRevisionCollection(page_a, [revision_from_page_b]).get_sources()` raises `ValueError("revisions must belong to the collection page")` before AMC retry work or `_source` mutation.
- `PageRevisionCollection(page_a, [revision_from_page_b]).get_htmls()` raises the same diagnostic before AMC retry work or `_html` mutation.
- The shared acquisition helper still accepts valid same-page revision batches and preserves duplicate revision-ID deduplication, cached duplicate reuse, retry-exhausted handling, source/HTML response diagnostics, and lazy revision accessors.
- Adjacent page/page-file/page-vote/site behavior remains intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed a valid revision from another page reaching `get_sources()` without ownership rejection, proving the shared source/HTML acquisition helper did not validate target revision ownership relative to the collection page.
- This slice only validates page-revision collection target-page ownership before source/HTML acquisition work. It does not change revision-list acquisition, parser-created revisions, direct revision constructor validation, response parsing, duplicate source/HTML deduplication, cached duplicate reuse, lazy revision properties for valid same-page revisions, live site behavior, or authentication semantics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, page source text from real sites, and live Wikidot account details out of upstream discussion.
