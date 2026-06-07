# PR Draft: Validate Page Batch Target Site Ownership

## Summary

`PageCollection` validates its retained batch parent `site`, but batch helpers still trusted every contained `Page` to belong to that same site. A caller could construct or rehydrate `PageCollection(site_a, [page_from_site_b])`; `get_page_ids()` would then use the collection site's client while building request URLs from the target page's own site, and source/revision/vote/file helpers could later route site-specific AMC requests through the wrong collection site after page-ID acquisition.

This change validates page entry site ownership at the shared `PageCollection._get_site_for_batch()` boundary before page-ID lookup, source fetches, revision fetches, vote fetches, file fetches, cache reuse, parser work, or local cache mutation. Pages whose retained `page.site` is not the collection site now raise `ValueError("pages must belong to the collection site")`. Empty parentless collections, valid same-site page batches, malformed-entry validation, retained collection-site validation, duplicate/cache reuse, response diagnostics, lazy page accessors, and adjacent page/site workflows remain unchanged.

## Outcome

Page batch reads now reject different-site target pages before one collection site can drive direct page-ID requests or AMC requests for page records retained from another site.

## Current Evidence

Existing drafts [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [095-pr-deduplicate-page-source-fetches.md](095-pr-deduplicate-page-source-fetches.md), [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [430-pr-validate-page-source-wiki-text.md](430-pr-validate-page-source-wiki-text.md), [566-pr-validate-page-refresh-source-site.md](566-pr-validate-page-refresh-source-site.md), and [572-pr-validate-page-collection-batch-site.md](572-pr-validate-page-collection-batch-site.md) establish page batch reads, cache reuse, retained site validation, and collection-entry validation as practical workflow surfaces.

This slice is not a duplicate of those issues. Issue 572 validates the retained `PageCollection.site` field itself after mutation. Issue 368 validates that entries are `Page` objects. Earlier source/revision/vote/file drafts cover duplicate/cache behavior and response diagnostics. This slice covers a valid `Page` entry whose retained `page.site` is individually valid but does not match the collection site that will be used for direct request routing.

No upstream issue was filed from this local workspace.

## Changes

- Add a shared page batch ownership preflight for collection entries.
- Apply the preflight in `PageCollection._get_site_for_batch()` after retained collection-site validation and before every public batch accessor delegates to ID/source/revision/vote/file acquisition.
- Add a public regression for `get_page_ids()` with a valid page retained from a different `Site`.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageCollection(site_a, [page_from_site_b]).get_page_ids()` must reject the different-site page with `ValueError("pages must belong to the collection site")` before `RequestUtil.request` or cache mutation. |
| R2 | The shared batch preflight must preserve existing retained collection-site and non-page entry validation across `get_page_ids()`, `get_page_sources()`, `get_page_revisions()`, `get_page_votes()`, and `get_page_files()`. |
| R3 | Valid same-site page ID/source/revision/vote/file acquisition, duplicate/cache reuse, response diagnostics, lazy page accessors, and adjacent page/site behavior must remain stable. |
| R4 | Focused RED/GREEN, page acquisition coverage, full page module, adjacent page/site tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Different-site page entries fail before direct page-ID request work. | `TestPageCollectionAcquire.test_get_page_ids_rejects_page_from_different_site_before_fetch` failed RED with `DID NOT RAISE`, then passed GREEN with `ValueError("pages must belong to the collection site")` and no `RequestUtil.request` call. | Calling `RequestUtil.request`, accepting a different-site page, mutating `_id`, or deferring failure to request/response diagnostics rejects this local completion claim. | `PageCollection.get_page_ids()` and `_get_site_for_batch()` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Existing batch preflights remain stable. | `TestPageCollectionAcquire` passed 65 tests, including retained collection-site mutation, non-page entry rejection across all batch accessors, empty/cached behavior, duplicate ID/source/revision/vote/file reuse, and response diagnostics. | Reordering validation so malformed collection sites or malformed entries can reach request work rejects this local completion claim. | PageCollection batch preflight | `tests/unit/test_page.py` |
| R3 | Adjacent workflows remain stable. | `tests/unit/test_page.py` passed 296 tests, adjacent page/site workflow tests passed 826 tests, and the full unit suite passed 2688 tests. | Regressing ListPages parsing, page ID/source/revision/vote/file acquisition, lazy page properties, page write helpers, page source/revision/file/vote models, or site/page accessors rejects this local completion claim. | Page and site workflows | `tests/unit` |
| R4 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live auth material or private state is needed to prove the behavior. | The regression uses synthetic valid `Site` and `Page` objects; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private forum content, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `ed737bc fix(page): validate batch page site ownership`.

- RED target-site ownership: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_get_page_ids_rejects_page_from_different_site_before_fetch -q` failed before the fix with `DID NOT RAISE` after the different-site page reached the patched direct request path.
- GREEN focused regression: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_get_page_ids_rejects_page_from_different_site_before_fetch -q` passed 1 test.
- Page acquisition coverage: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 65 tests.
- Full page module: `uv run pytest tests/unit/test_page.py -q` passed 296 tests.
- Adjacent page/site: `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_source.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 826 tests.
- `uv run pytest tests/unit -q` passed 2688 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageCollection(site_a, [page_from_site_b]).get_page_ids()` raises `ValueError("pages must belong to the collection site")` before direct request work or `_id` mutation.
- The shared batch preflight protects `get_page_ids()`, `get_page_sources()`, `get_page_revisions()`, `get_page_votes()`, and `get_page_files()` without weakening existing retained-site or non-page entry validation.
- Valid same-site page ID/source/revision/vote/file acquisition, duplicate/cache behavior, lazy page accessors, and response diagnostics remain unchanged.
- Adjacent page/site behavior remains intact.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed a valid page from another site reaching `get_page_ids()` without any ownership rejection, proving the retained collection-site preflight did not validate entry ownership.
- This slice only validates page batch target-site ownership relative to the collection site. It does not change ListPages search behavior, same-site batch acquisition, source/revision/vote/file response parsing, lazy page accessors, page write actions, live site behavior, or authentication semantics for valid same-site pages.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, page source text from real sites, and live Wikidot account details out of upstream discussion.
