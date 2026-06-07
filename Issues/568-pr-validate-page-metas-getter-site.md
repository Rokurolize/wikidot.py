# PR Draft: Validate Page Metas Getter Site

## Summary

`Page.metas` lazily retrieves `edit/EditMetaModule`, validates the generated response body, parses meta tags, and caches the resulting `dict[str, str]`. Existing metadata work already covers retry-aware meta reads, exhausted retry diagnostics, missing and malformed response bodies, robust meta parsing, constructor meta-cache validation, explicit meta input validation, metadata write status validation, and the direct `Page.metas = ...` setter site guard. One adjacent read-time state boundary still trusted `page.site` after construction: if a caller, fixture, or rehydrated page object replaced `page.site` with a mock, dictionary-like object, or other non-`Site` value, the getter could reach the mutated object's AMC request path and parser diagnostics before reporting the parent-site problem.

This change revalidates `self.site` at the start of the uncached `Page.metas` read before AMC request work, generated response parsing, or `_metas` cache mutation. Malformed read-time page sites now raise `ValueError("site must be a Site")` and leave the metadata cache untouched. Valid cached meta reads, retry behavior, response diagnostics, flexible escaped/literal meta parsing, and the direct setter remain unchanged.

## Outcome

The page metadata getter now has an explicit read-time parent-site preflight consistent with the page constructor, `Page.discussion`, `Page.refresh_source()`, and the adjacent metadata write guards.

## Current Evidence

Existing drafts [011-pr-robust-meta-tag-parsing.md](011-pr-robust-meta-tag-parsing.md), [046-pr-retry-page-meta-fetch.md](046-pr-retry-page-meta-fetch.md), [192-pr-page-auxiliary-fetch-site-context.md](192-pr-page-auxiliary-fetch-site-context.md), [219-pr-page-auxiliary-response-body-context.md](219-pr-page-auxiliary-response-body-context.md), [335-pr-page-auxiliary-response-body-type-context.md](335-pr-page-auxiliary-response-body-type-context.md), [511-pr-validate-page-constructor-metas-cache.md](511-pr-validate-page-constructor-metas-cache.md), [565-pr-validate-page-metas-setter-site.md](565-pr-validate-page-metas-setter-site.md), and [567-pr-validate-page-discussion-site.md](567-pr-validate-page-discussion-site.md) establish robust meta parsing, retry behavior, auxiliary site/page diagnostics, response-body validation, constructor meta-cache validation, direct meta setter site validation, and adjacent auxiliary read-time site validation. This slice covers mutated `Page.site` at uncached `Page.metas` read time, not meta response parsing, constructor cache validation, meta input shape, or direct metadata writes.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.site` at the start of the uncached `Page.metas` getter.
- Use the validated site for the metadata AMC request and diagnostics.
- Add a regression for a mutated non-`Site` `page.site` that asserts no AMC request work and no `_metas` cache mutation.
- Preserve valid meta getter retries, exhausted retry diagnostics, missing/malformed response body diagnostics, flexible meta parsing, and the direct metas setter guard.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Uncached `Page.metas` must reject a mutated non-`Site` `page.site` with `ValueError("site must be a Site")` before AMC request work, response parsing, or `_metas` cache mutation. |
| R2 | A malformed read-time site must leave `_metas` as `None`. |
| R3 | Valid meta getter retry behavior, exhausted retry diagnostics, response-body diagnostics, flexible meta parsing, and adjacent setter validation must remain stable. |
| R4 | Focused meta getter tests, full page module tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A mutated non-`Site` parent fails before meta getter request surfaces. | `TestPageWriteMethods.test_metas_getter_rejects_malformed_site_before_request` failed RED by reaching the mocked `amc_request_with_retry(...)` path and surfacing a mock-derived malformed-body diagnostic, then passed GREEN with `ValueError("site must be a Site")`. | Calling `amc_request(...)`, calling `amc_request_with_retry(...)`, accepting dictionaries/mocks as sites, parsing generated meta markup, or storing `_metas` rejects this local completion claim. | `Page.metas` getter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | A malformed parent site preserves the missing metadata cache state. | The new regression mutates `page.site`, calls `page.metas`, and asserts `_metas is None`. | Setting `_metas` to an empty dictionary, preserving a mock-derived parsed value, or replacing the cache before parent-site validation rejects this local completion claim. | Page metadata cache state | `tests/unit/test_page.py` |
| R3 | Existing metadata getter and adjacent setter behavior remains stable. | Focused GREEN included malformed getter site, flexible parsing, transient retry, exhausted retry, missing body, malformed body type, and adjacent metas setter malformed-site tests; the full page module run and full unit suite stayed green. | Changing request payloads, retry behavior, exhausted retry exception shape, response diagnostics, flexible parsing, cache timing, or setter site validation rejects this local completion claim. | Page metadata behavior | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Existing repository quality gates remain green. | Focused metadata tests passed 7 tests, full page module tests passed 292 tests, full unit passed 2663 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live auth material or private state is needed to prove the behavior. | The regression uses a synthetic mutated site and mocked unit-level page state; this draft contains no credentials, cookies, auth JSON, raw response bodies, private metadata values, private site data, or live account details. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private metadata values, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `c83a856 fix(page): validate metas getter site`.

- RED read-time site validation: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_rejects_malformed_site_before_request -q` failed before the fix because mutated `page.site` reached the mocked `amc_request_with_retry(...)` path and surfaced `Page metas response body is malformed for site: <MagicMock ...>, page: test-page (id=12345, field=body, expected=str, actual=MagicMock)` instead of `ValueError("site must be a Site")`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_rejects_malformed_site_before_request tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_parses_decoded_flexible_markup tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_retries_transient_fetch_failures tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_raises_when_retry_is_exhausted tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_missing_response_body_includes_page_context tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_malformed_response_body_type_includes_page_context tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_rejects_malformed_site_before_login -q` passed 7 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 292 tests.
- `uv run pytest tests/unit -q` passed 2663 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Uncached `Page.metas` rejects a mutated malformed `page.site` with `ValueError("site must be a Site")` before AMC request work, response parsing, or `_metas` cache mutation.
- `_metas` remains `None` after malformed parent-site validation.
- Valid metadata getter retry behavior, exhausted retry diagnostics, response-body diagnostics, flexible meta parsing, and adjacent setter validation remain intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed invalid mutated parent state reaching mocked metadata request work and producing a mock-derived generated-body diagnostic instead of an explicit parent-site diagnostic.
- This slice only validates mutated `Page.site` before the uncached `Page.metas` getter. It does not change page construction, metadata response parsing, metadata input validation, direct metadata writes, discussion/source/file/revision/vote behavior, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, and live Wikidot account details out of upstream discussion.
