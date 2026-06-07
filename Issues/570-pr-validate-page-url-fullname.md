# PR Draft: Validate Page URL Fullname

## Summary

`Page.get_url()` builds the canonical page URL used by direct callers, publish-result URL ledgers, integration helpers, and `PageCollection._acquire_page_ids(...)` request URL construction. Existing local slices validate `Page(fullname=...)` at construction, page fullname inputs before lookup/write work, rename targets before mutation, and mutated `page.site` before URL generation. One adjacent stored-identity boundary still trusted `page.fullname` after construction: if a caller, fixture, or rehydrated page object replaced `page.fullname` with a mock, dictionary-like object, or other non-string value, `get_url()` could fabricate a URL from malformed page identity instead of reporting the identity problem before page-ID request construction.

This change revalidates `self.fullname` inside `Page.get_url()` before building the URL. Malformed URL-time page fullnames now raise `ValueError("fullname must be a string")`. Valid URL generation, page-ID acquisition, publish-result URL export, constructor identity validation, and fullname input validation remain unchanged.

## Outcome

Page URL generation now has explicit preflight for both parent-site state and stored page fullname state before canonical URLs or page-ID request URLs are built.

## Current Evidence

Existing drafts [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [132-pr-reuse-cached-duplicate-page-ids.md](132-pr-reuse-cached-duplicate-page-ids.md), [186-pr-page-id-response-type-context.md](186-pr-page-id-response-type-context.md), [197-pr-page-id-site-context.md](197-pr-page-id-site-context.md), [231-pr-publish-result-url.md](231-pr-publish-result-url.md), [352-pr-validate-page-rename-fullname-input.md](352-pr-validate-page-rename-fullname-input.md), [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md), [533-pr-validate-page-fullname-inputs.md](533-pr-validate-page-fullname-inputs.md), and [569-pr-validate-page-url-site.md](569-pr-validate-page-url-site.md) establish page-ID URL batching, cached duplicate ID reuse, page-ID diagnostics, publish URL ledger export, rename target validation, constructor identity validation, public fullname input validation, and URL-time parent-site validation. This slice covers mutated stored `Page.fullname` at URL-generation time, not constructor input validation, lookup/write arguments, URL syntax validation, page-site validation, page-ID response parsing, or live Wikidot request behavior.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.fullname` inside `Page.get_url()`.
- Use the validated fullname when constructing the URL.
- Add a regression for a mutated non-string `page.fullname` that asserts URL generation raises `ValueError("fullname must be a string")`.
- Preserve valid URL generation, adjacent URL-site validation, and page-ID property behavior.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.get_url()` must reject a mutated non-string `page.fullname` with `ValueError("fullname must be a string")` before building a canonical URL. |
| R2 | Valid `Page.get_url()` output must remain `"<site.url>/<page.fullname>"`. |
| R3 | Adjacent URL-time site validation and page-ID acquisition behavior must remain stable because `_acquire_page_ids(...)` builds request URLs through `page.get_url()`. |
| R4 | Focused URL/page-ID tests, full page module tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A mutated non-string stored fullname fails before URL generation accepts malformed page identity. | `TestPageProperties.test_get_url_rejects_malformed_fullname` failed RED with `DID NOT RAISE <class 'ValueError'>`, then passed GREEN with `ValueError("fullname must be a string")`. | Reading a mock/dict/object as fullname, returning a mock-derived URL, coercing malformed identity with `str(...)`, or deferring failure to request execution rejects this local completion claim. | `Page.get_url()` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Valid page URL output remains unchanged. | Focused GREEN included `TestPageProperties.test_get_url`, which still returns `https://test-site.wikidot.com/test-page`. | Changing URL separators, adding `norender` or `noredirect`, normalizing page names, stripping categories, or changing valid output rejects this local completion claim. | Page URL generation | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Adjacent URL-time site validation and page-ID property behavior remain stable. | Focused GREEN included malformed URL site, acquired-ID, and missing-ID context tests, and full page/full unit suites stayed green. | Changing parent-site validation, page-ID cache behavior, page-ID lookup diagnostics, page collection routing, duplicate URL reuse, or request payload construction for valid pages rejects this local completion claim. | Page ID lookup URL construction | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Existing repository quality gates remain green. | Focused URL/page-ID tests passed 5 tests, full page module tests passed 294 tests, full unit passed 2665 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live auth material or private state is needed to prove the behavior. | The regression uses a synthetic mutated fullname on an existing unit fixture; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private metadata values, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `9085c00 fix(page): validate page url fullname`.

- RED URL-time fullname validation: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_get_url_rejects_malformed_fullname -q` failed before the fix with `Failed: DID NOT RAISE <class 'ValueError'>`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_get_url tests/unit/test_page.py::TestPageProperties::test_get_url_rejects_malformed_site tests/unit/test_page.py::TestPageProperties::test_get_url_rejects_malformed_fullname tests/unit/test_page.py::TestPageProperties::test_id_property_acquired tests/unit/test_page.py::TestPageProperties::test_id_property_includes_page_context_when_acquire_leaves_id_missing -q` passed 5 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 294 tests.
- `uv run pytest tests/unit -q` passed 2665 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.get_url()` rejects a mutated malformed `page.fullname` with `ValueError("fullname must be a string")` before building a canonical URL.
- Valid URL generation remains unchanged.
- Adjacent URL-time parent-site validation and page-ID property/lookup behavior remain intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed mutated stored page identity was accepted by `Page.get_url()` instead of producing an explicit fullname diagnostic.
- This slice only validates mutated `Page.fullname` before page URL generation. It does not change page construction, lookup/write argument validation, URL syntax, page-site validation, page-ID response parsing, request retry behavior, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, and live Wikidot account details out of upstream discussion.
