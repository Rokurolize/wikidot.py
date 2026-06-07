# PR Draft: Validate Page URL Site

## Summary

`Page.get_url()` builds the canonical page URL used by direct callers, publish-result URL ledgers, integration helpers, and `PageCollection._acquire_page_ids(...)` request URL construction. The page constructor already rejects malformed parent sites, and recent local slices validate mutated `page.site` before page write actions and auxiliary reads. One adjacent URL-generation boundary still trusted `page.site` after construction: if a caller, fixture, or rehydrated page object replaced `page.site` with a mock, dictionary-like object, or other non-`Site` value, `get_url()` could fabricate a URL from the malformed object instead of reporting the parent-site problem before page-ID request construction.

This change revalidates `self.site` inside `Page.get_url()` before reading `site.url`. Malformed URL-time page sites now raise `ValueError("site must be a Site")`. Valid URL generation, page-ID acquisition, publish-result URL export, and all cached page behaviors remain unchanged.

## Outcome

Page URL generation now has the same explicit parent-site preflight as page construction, page action-time site guards, and auxiliary read-time site guards.

## Current Evidence

Existing drafts [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [132-pr-reuse-cached-duplicate-page-ids.md](132-pr-reuse-cached-duplicate-page-ids.md), [186-pr-page-id-response-type-context.md](186-pr-page-id-response-type-context.md), [197-pr-page-id-site-context.md](197-pr-page-id-site-context.md), [231-pr-publish-result-url.md](231-pr-publish-result-url.md), [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md), [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), and [557-pr-validate-page-destroy-site.md](557-pr-validate-page-destroy-site.md) through [568-pr-validate-page-metas-getter-site.md](568-pr-validate-page-metas-getter-site.md) establish page-ID URL batching, cached duplicate ID reuse, page-ID diagnostics, publish URL ledger export, collection-site validation, constructor-site validation, and mutated page-site validation for adjacent action/read surfaces. This slice covers mutated `Page.site` at URL-generation time, not constructor input validation, URL syntax validation, page fullname validation, page-ID response parsing, or live Wikidot request behavior.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.site` inside `Page.get_url()`.
- Use the validated `Site` object when reading `url`.
- Add a regression for a mutated non-`Site` `page.site` that asserts URL generation raises `ValueError("site must be a Site")`.
- Preserve valid URL generation and adjacent page-ID property behavior.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.get_url()` must reject a mutated non-`Site` `page.site` with `ValueError("site must be a Site")` before reading `url` from the malformed object. |
| R2 | Valid `Page.get_url()` output must remain `"<site.url>/<page.fullname>"`. |
| R3 | Adjacent page-ID acquisition behavior must remain stable because `_acquire_page_ids(...)` builds request URLs through `page.get_url()`. |
| R4 | Focused URL/page-ID tests, full page module tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A mutated non-`Site` parent fails before URL generation accepts malformed object state. | `TestPageProperties.test_get_url_rejects_malformed_site` failed RED with `DID NOT RAISE <class 'ValueError'>`, then passed GREEN with `ValueError("site must be a Site")`. | Reading `url` from a mock/dict/object, accepting malformed sites, returning a mock-derived URL, coercing the site, or deferring failure to request execution rejects this local completion claim. | `Page.get_url()` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Valid page URL output remains unchanged. | Focused GREEN included `TestPageProperties.test_get_url`, which still returns `https://test-site.wikidot.com/test-page`. | Changing URL separators, adding `norender` or `noredirect`, normalizing page names, stripping categories, or changing valid output rejects this local completion claim. | Page URL generation | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Adjacent page-ID property behavior remains stable. | Focused GREEN included acquired-ID and missing-ID context tests, and full page/full unit suites stayed green. | Changing page-ID cache behavior, page-ID lookup diagnostics, page collection routing, duplicate URL reuse, or request payload construction for valid pages rejects this local completion claim. | Page ID lookup URL construction | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Existing repository quality gates remain green. | Focused URL/page-ID tests passed 4 tests, full page module tests passed 293 tests, full unit passed 2664 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live auth material or private state is needed to prove the behavior. | The regression uses a synthetic mutated site on an existing unit fixture; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private metadata values, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `94f56a4 fix(page): validate page url site`.

- RED URL-time site validation: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_get_url_rejects_malformed_site -q` failed before the fix with `Failed: DID NOT RAISE <class 'ValueError'>`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_get_url tests/unit/test_page.py::TestPageProperties::test_get_url_rejects_malformed_site tests/unit/test_page.py::TestPageProperties::test_id_property_acquired tests/unit/test_page.py::TestPageProperties::test_id_property_includes_page_context_when_acquire_leaves_id_missing -q` passed 4 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 293 tests.
- `uv run pytest tests/unit -q` passed 2664 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.get_url()` rejects a mutated malformed `page.site` with `ValueError("site must be a Site")` before reading `url` from the malformed object.
- Valid URL generation remains unchanged.
- Adjacent page-ID property and lookup behavior remains intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed mutated parent state was accepted by `Page.get_url()` instead of producing an explicit parent-site diagnostic.
- This slice only validates mutated `Page.site` before page URL generation. It does not change page construction, URL syntax, page fullname validation, page-ID response parsing, request retry behavior, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, and live Wikidot account details out of upstream discussion.
