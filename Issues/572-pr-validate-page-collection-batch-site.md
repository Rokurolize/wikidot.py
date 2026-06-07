# PR Draft: Validate Page Collection Batch Site State

## Summary

`PageCollection` validates explicit parent `site` values at construction and preserves empty parentless collections as no-op batch targets. One retained-state boundary still trusted the stored collection parent after construction: if a caller, fixture, or rehydrated collection replaced `collection.site` with a malformed non-`Site` object, batch helpers such as `get_page_ids()` could enter request construction with a bogus parent instead of reporting the collection-state problem.

This change revalidates non-`None` `PageCollection.site` inside `_get_site_for_batch()` before batch acquisition starts. Populated parentless collections still raise `ValueError("site must be a Site")`, empty parentless collections still return `self` without request work, and valid page ID/source/revision/vote/file acquisition remains unchanged.

## Outcome

Page collection batch acquisition now has an explicit retained-parent preflight before request work can use collection-level site state.

## Current Evidence

Existing drafts [002-pr-batch-source-page-id-lookups.md](002-pr-batch-source-page-id-lookups.md), [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md), [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md), [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md), and [540-pr-preserve-empty-page-collection-parent.md](540-pr-preserve-empty-page-collection-parent.md) establish page collections as practical batch-acquisition surfaces and validate constructor-time parent or entry state.

This slice is not a duplicate of those issues. Issue 477 validates explicit non-`None` parent sites at construction time. Issue 540 preserves empty parentless no-op behavior. Issue 368 validates collection entries before acquisition. This slice covers mutated retained `PageCollection.site` at batch-acquisition time, not constructor input validation, page-entry validation, empty parentless behavior, or live Wikidot request behavior.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate non-`None` `PageCollection.site` inside `_get_site_for_batch()`.
- Preserve the existing populated parentless collection error.
- Preserve empty parentless batch methods as no-ops.
- Add a regression proving mutated malformed retained site state is rejected before page-ID request work.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Batch acquisition must reject a mutated non-`Site` `PageCollection.site` with `ValueError("site must be a Site")` before request work. |
| R2 | Empty parentless `PageCollection()` batch accessors must continue to return `self` without request work. |
| R3 | Populated collections with `site=None` must continue to raise `ValueError("site must be a Site")` before request work. |
| R4 | Valid page ID/source/revision/vote/file acquisition and adjacent page/site workflows must remain stable. |
| R5 | Focused RED/GREEN, constructor/acquisition tests, adjacent page/site tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Mutated retained collection parent state fails before request construction. | `TestPageCollectionAcquire.test_acquire_rejects_mutated_site_before_fetch` failed RED with `DID NOT RAISE`, then passed GREEN after `_get_site_for_batch()` revalidated non-`None` `self.site`. | Calling `RequestUtil.request`, using a mock parent client, returning silently, or deferring the failure to lower request/parsing layers rejects this local completion claim. | `PageCollection._get_site_for_batch()` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Empty parentless batch no-ops remain unchanged. | `TestPageCollectionInit.test_init_empty_without_site_exposes_none_site` stayed green in focused constructor coverage. | Rejecting empty parentless collections, issuing requests for empty collections, or returning a different object rejects this local completion claim. | PageCollection constructor and batch accessors | `tests/unit/test_page.py` |
| R3 | Populated parentless collections still fail with the existing collection-site diagnostic. | The `_get_site_for_batch()` branch still raises `ValueError("site must be a Site")` when `self.site is None` and the collection is non-empty; acquisition coverage stayed green. | Allowing populated parentless acquisition or changing the error message rejects this local completion claim. | PageCollection batch accessors | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Adjacent workflows remain stable. | `tests/unit/test_page.py` passed 295 tests, adjacent page/site workflow tests passed 825 tests, and the full unit suite passed 2670 tests. | Regressing ListPages parsing, search pagination, page ID/source/revision/vote/file acquisition, duplicate cache reuse, lazy page properties, page write helpers, or site/page accessors rejects this local completion claim. | Page and site workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Focused constructor/acquisition tests passed 87 tests, full page tests passed 295 tests, adjacent page/site tests passed 825 tests, full unit passed 2670 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regression uses synthetic mutated collection state and local mocks; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private metadata values, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `5660d78 fix(page): validate batch collection site`.

- RED batch-site validation: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_rejects_mutated_site_before_fetch -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused regression: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_rejects_mutated_site_before_fetch -q` passed.
- Focused adjacent constructor invariants: `uv run pytest tests/unit/test_page.py::TestPageCollectionInit::test_init_empty_without_site_exposes_none_site tests/unit/test_page.py::TestPageCollectionInit::test_init_rejects_malformed_sites -q` passed 5 tests.
- Focused constructor/acquisition coverage: `uv run pytest tests/unit/test_page.py::TestPageCollectionInit tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 87 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 295 tests.
- Adjacent page/site: `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_source.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 825 tests.
- `uv run pytest tests/unit -q` passed 2670 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Mutated non-`Site` `PageCollection.site` values are rejected before batch request work.
- Empty parentless page collections continue to expose `site is None` and keep batch accessors chainable no-ops.
- Populated parentless page collections continue to fail before request work.
- Valid page ID/source/revision/vote/file acquisition remains unchanged.
- Adjacent page/site behavior remains intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed mutated retained `PageCollection.site` state was accepted by `get_page_ids()` instead of producing the existing collection-site diagnostic.
- This slice only validates retained collection parent state before batch acquisition. It does not change `PageCollection` constructor validation, empty parentless collection semantics, page entry validation, ListPages parsing, search request planning, page ID/source/revision/vote/file response parsing, duplicate cache reuse, retry behavior, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, and live Wikidot account details out of upstream discussion.
