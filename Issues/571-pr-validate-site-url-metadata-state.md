# PR Draft: Validate Site URL Metadata State

## Summary

`Site.url` derives the canonical site URL from stored `domain` and `ssl_supported` metadata. Existing local slices validate `Site(...)` scalar metadata at construction, site lookup UNIX-name inputs before fetch work, and URL-generation state on `Page.get_url()`. One adjacent retained-state boundary still trusted mutable `Site.domain` and `Site.ssl_supported` after construction: if a caller, fixture, or rehydrated site object replaced those fields with malformed values, `Site.url` could fabricate `https://None`, `https://True`, or a truthy-string HTTPS URL instead of reporting the site metadata problem. That malformed URL can then flow into page URLs through `Page.get_url()` and into page-ID request URL construction.

This change revalidates `self.ssl_supported` and `self.domain` inside `Site.url()` before formatting. Malformed URL-time site metadata now raises `ValueError("domain must be a string")` or `ValueError("ssl_supported must be a boolean")`. Valid `Site.url`, site construction, page URL generation, accessors, site workflows, and page workflows remain unchanged.

## Outcome

Site URL generation now has explicit retained-state preflight for the scalar metadata that controls scheme and host.

## Current Evidence

Existing drafts [310-pr-site-id-context.md](310-pr-site-id-context.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [359-pr-validate-site-lookup-unix-names.md](359-pr-validate-site-lookup-unix-names.md), [480-pr-validate-site-constructor-metadata.md](480-pr-validate-site-constructor-metadata.md), [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), [569-pr-validate-page-url-site.md](569-pr-validate-page-url-site.md), and [570-pr-validate-page-url-fullname.md](570-pr-validate-page-url-fullname.md) establish site identity, lookup, constructor metadata, page parent-site validation, and page URL retained-state validation as practical workflow surfaces. This slice covers mutated `Site.domain` and `Site.ssl_supported` at URL-generation time, not constructor input validation, site lookup fetching, URL syntax validation, page fullname validation, page-site validation, or live Wikidot request behavior.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.ssl_supported` inside `Site.url`.
- Revalidate `self.domain` inside `Site.url`.
- Add regressions for mutated `domain` and `ssl_supported` values that previously produced malformed URLs.
- Preserve valid HTTPS URL generation and adjacent site/page workflows.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.url` must reject mutated non-string `domain` values with `ValueError("domain must be a string")` before formatting a URL. |
| R2 | `Site.url` must reject mutated non-boolean `ssl_supported` values with `ValueError("ssl_supported must be a boolean")` before choosing a URL scheme. |
| R3 | Valid `Site.url` output must remain `http://<domain>` or `https://<domain>` according to a boolean `ssl_supported`. |
| R4 | Adjacent site constructor, site accessor, site member/application, page URL, and page workflows must remain stable. |
| R5 | Focused URL metadata tests, adjacent site/page tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A mutated non-string stored domain fails before URL generation accepts malformed host state. | `TestSiteInit.test_url_rejects_mutated_metadata` failed RED for `domain=None` and `domain=True` with `DID NOT RAISE`, then passed GREEN with `ValueError("domain must be a string")`. | Returning `https://None`, returning `https://True`, coercing malformed domains with `str(...)`, or deferring failure to page/request execution rejects this local completion claim. | `Site.url` | `src/wikidot/module/site.py`, `tests/unit/test_site_constructor.py` |
| R2 | A mutated non-boolean stored SSL flag fails before URL generation chooses a scheme. | The same regression failed RED for `ssl_supported=1` and `ssl_supported="true"` with `DID NOT RAISE`, then passed GREEN with `ValueError("ssl_supported must be a boolean")`. | Treating truthy/falsy non-booleans as scheme controls, returning an HTTPS URL for `"true"`, or deferring failure to request execution rejects this local completion claim. | `Site.url` | `src/wikidot/module/site.py`, `tests/unit/test_site_constructor.py` |
| R3 | Valid site URL output remains unchanged. | `TestSiteInit.test_init_accepts_valid_metadata` now asserts `https://test-site.wikidot.com`, and the full adjacent site/page run stayed green. | Changing valid scheme selection, changing separators, modifying domains, or normalizing hosts rejects this local completion claim. | Site URL generation | `src/wikidot/module/site.py`, `tests/unit/test_site_constructor.py` |
| R4 | Adjacent workflows remain stable. | Adjacent site constructor/site/accessor/member/application/page run passed 733 tests, and the full unit suite passed 2669 tests. | Regressing site construction, accessors, member/application behavior, `Page.get_url()`, page-ID URL construction, or page workflows rejects this local completion claim. | Site and page workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Focused site constructor tests passed 26 tests, adjacent site/page tests passed 733 tests, full unit passed 2669 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regressions use synthetic mutated metadata on an existing unit fixture; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private metadata values, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `c4c09d6 fix(site): validate url metadata state`.

- RED URL metadata validation: `uv run pytest tests/unit/test_site_constructor.py::TestSiteInit::test_url_rejects_mutated_metadata -q` failed before the fix with 4 `DID NOT RAISE` cases for mutated `domain` and `ssl_supported`.
- GREEN focused: `uv run pytest tests/unit/test_site_constructor.py -q` passed 26 tests.
- Adjacent site/page: `uv run pytest tests/unit/test_site_constructor.py tests/unit/test_site.py tests/unit/test_site_accessors.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_page.py -q` passed 733 tests.
- `uv run pytest tests/unit -q` passed 2669 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Site.url` rejects mutated malformed `domain` values with `ValueError("domain must be a string")` before building a URL.
- `Site.url` rejects mutated malformed `ssl_supported` values with `ValueError("ssl_supported must be a boolean")` before choosing a scheme.
- Valid `Site.url` output remains unchanged.
- Adjacent site/page behavior remains intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed mutated retained site metadata was accepted by `Site.url` instead of producing explicit metadata diagnostics.
- This slice only validates mutated `Site.domain` and `Site.ssl_supported` before site URL generation. It does not change site construction, site lookup fetching, URL syntax, page fullname validation, page-site validation, page-ID response parsing, request retry behavior, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, and live Wikidot account details out of upstream discussion.
