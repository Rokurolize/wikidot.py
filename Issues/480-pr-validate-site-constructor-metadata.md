# PR Draft: Validate Site Constructor Metadata

## Summary

`Site` is the central site identity object used by page, forum, member, application, recent-change, source, and publish workflows. It is usually created from `Site.from_unix_name(...)`, but direct `Site(...)` construction is public and heavily used by local fixtures, generated ledgers, and rehydrated workflow state. Before this change, direct construction accepted malformed scalar metadata such as `id=None`, `title=True`, `unix_name=[]`, `domain=123456`, or `ssl_supported=1`, storing invalid state that could later leak into URLs, AMC routing, string representations, source/publish ledgers, or site-scoped diagnostics.

This change validates the scalar site metadata during `Site.__post_init__`. Malformed values now raise stable `ValueError` diagnostics: `id must be an integer`, `<field> must be a string`, and `ssl_supported must be a boolean`. Valid `Site` construction, mock-client fixture usage, `Site.url`, `Site.pages`, `Site.page`, `Site.forum`, and adjacent site/member/application workflows remain unchanged.

## Outcome

Callers cannot silently construct `Site` objects with malformed scalar identity metadata, while ordinary `Site.from_unix_name(...)` results, direct valid fixture construction, and site-scoped workflows continue to work as before.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free site lookup, page/source inventory, page publishing, forum discovery, membership administration, pending-application review, recent-change ledgers, source/publish result ledgers, local fixtures, or rehydrated `Site` objects.

## Current Evidence

Local rollout-backed drafts repeatedly identify site identity as a practical workflow surface. Site lookup and generated metadata drafts such as [310-pr-site-id-context.md](310-pr-site-id-context.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), and [359-pr-validate-site-lookup-unix-names.md](359-pr-validate-site-lookup-unix-names.md) establish site IDs, UNIX names, domains, SSL routing, and site fields as operationally important. Recent-change and site-parent drafts such as [439-pr-validate-site-change-site-field.md](439-pr-validate-site-change-site-field.md), [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md), [476-pr-validate-forum-category-collection-site-field.md](476-pr-validate-forum-category-collection-site-field.md), [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md), and [478-pr-validate-site-accessor-parent-sites.md](478-pr-validate-site-accessor-parent-sites.md) establish valid `Site` parent objects as active boundaries for collections, accessors, and change records.

Those prior slices are not duplicates. Issue 310 adds parser-side context for malformed generated `siteId` assignments, Issue 338 exports site identity in result ledgers, Issue 359 validates caller-provided lookup UNIX names before fetching site metadata, Issue 439 validates `SiteChange.site`, Issues 475 through 477 validate collection parent-site fields, and Issue 478 validates site accessor parent objects. None validates direct `Site(id=...)`, `Site(title=...)`, `Site(unix_name=...)`, `Site(domain=...)`, or `Site(ssl_supported=...)` construction before malformed scalar state is stored.

## Related Issue / Non-Duplicate Analysis

Builds directly on the site identity and parent-state surfaces documented by [310-pr-site-id-context.md](310-pr-site-id-context.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [359-pr-validate-site-lookup-unix-names.md](359-pr-validate-site-lookup-unix-names.md), [439-pr-validate-site-change-site-field.md](439-pr-validate-site-change-site-field.md), [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md), [478-pr-validate-site-accessor-parent-sites.md](478-pr-validate-site-accessor-parent-sites.md), and [479-pr-validate-client-accessor-parent-clients.md](479-pr-validate-client-accessor-parent-clients.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_site_id(...)`, `_validate_site_text_field(...)`, and `_validate_site_ssl_supported(...)` helpers.
- Validate `Site.id`, `Site.title`, `Site.unix_name`, `Site.domain`, and `Site.ssl_supported` during `Site.__post_init__` before accessors are created.
- Reject malformed scalar metadata with stable `ValueError` messages.
- Preserve valid `Site` construction, mock-client fixture usage, `Site.url`, accessor creation, and adjacent site/member/application workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Site identity-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site(id=...)` must reject `None`, booleans, strings, floats, and other non-integer values with `ValueError("id must be an integer")`. |
| R2 | `Site(title=...)`, `Site(unix_name=...)`, and `Site(domain=...)` must reject non-string values with `ValueError("<field> must be a string")`. |
| R3 | `Site(ssl_supported=...)` must accept only booleans and reject `None`, strings, integers, lists, and other non-boolean values with `ValueError("ssl_supported must be a boolean")`. |
| R4 | Valid `Site` construction, mock-client fixture construction, `Site.url`, `Site.pages`, `Site.page`, `Site.forum`, site member workflows, and site application workflows must remain unchanged. |
| R5 | This slice must not validate `Site.client`, require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, constructor tests, adjacent site/member/application tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct `Site.id` values fail at the constructor boundary. | `TestSiteInit.test_init_rejects_malformed_metadata` failed RED for 5 malformed `id` values because constructors did not raise, then passed GREEN after validation was added. | Accepting `None`, booleans, strings, floats, arbitrary non-integers, or storing malformed site IDs rejects this local completion claim. | `Site` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site_constructor.py` |
| R2 | Malformed direct text metadata fails at the constructor boundary. | The same RED/GREEN test failed and then passed for malformed `title`, `unix_name`, and `domain` values. | Accepting non-string title, UNIX-name, or domain values, or coercing malformed values silently, rejects this local completion claim. | `Site` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site_constructor.py` |
| R3 | Malformed `ssl_supported` values fail at the constructor boundary. | The same RED/GREEN test failed and then passed for malformed SSL support values. | Accepting `None`, strings, integers such as `1`, lists, or truthy/falsy coercion rejects this local completion claim. | `Site` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site_constructor.py` |
| R4 | Existing valid site workflows remain green. | `tests/unit/test_site_constructor.py` passed 22 tests; adjacent site/accessor/member/application tests passed 373 tests; full unit tests passed 1982 tests. | Regressing direct valid fixture construction, mock-client construction, `Site.url`, accessor creation, site member workflows, or site application workflows rejects this local completion claim. | Site and adjacent workflows | `tests/unit/test_site_constructor.py`, `tests/unit/test_site.py`, `tests/unit/test_site_accessors.py`, `tests/unit/test_site_member.py`, `tests/unit/test_site_application.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly keeps `Site.client` validation out of scope. | Validating `Site.client`, using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `a2e4770 fix(site): validate constructor metadata`.

- RED: `uv run pytest tests/unit/test_site_constructor.py::TestSiteInit::test_init_rejects_malformed_metadata -q` failed 21 tests before the fix; every malformed scalar metadata case reported `DID NOT RAISE`.
- GREEN: the same focused command passed 21 tests after scalar metadata validation was added.
- `uv run pytest tests/unit/test_site_constructor.py -q` passed 22 tests.
- `uv run pytest tests/unit/test_site_constructor.py tests/unit/test_site.py tests/unit/test_site_accessors.py tests/unit/test_site_member.py tests/unit/test_site_application.py -q` passed 373 tests.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site_constructor.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/site.py tests/unit/test_site_constructor.py` passed.
- `uv run mypy src/wikidot/module/site.py tests/unit/test_site_constructor.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/site.py tests/unit/test_site_constructor.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 1982 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 85 files already formatted.
- `uv run mypy src tests` passed with no issues in 85 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client/mock typing, invalid test cookie arguments, and existing site test mock typing issues. The changed source file and new constructor test module pass pyright together.

## Acceptance Criteria

- `Site(id=None)`, `Site(id=True)`, `Site(id=False)`, `Site(id="123456")`, and `Site(id=123456.0)` raise `ValueError("id must be an integer")` when every other constructor field is valid.
- `Site(title=None)`, `Site(title=True)`, `Site(title=123456)`, and `Site(title=[])` raise `ValueError("title must be a string")`.
- `Site(unix_name=None)`, `Site(unix_name=True)`, `Site(unix_name=123456)`, and `Site(unix_name=[])` raise `ValueError("unix_name must be a string")`.
- `Site(domain=None)`, `Site(domain=True)`, `Site(domain=123456)`, and `Site(domain=[])` raise `ValueError("domain must be a string")`.
- `Site(ssl_supported=None)`, `Site(ssl_supported="true")`, `Site(ssl_supported=1)`, and `Site(ssl_supported=[])` raise `ValueError("ssl_supported must be a boolean")`.
- Valid `Site` metadata is stored unchanged, and `Site.__post_init__` still creates `pages`, `page`, and `forum` accessors.
- Existing URL construction, site accessor behavior, site member workflows, and site application workflows remain green.
- The new tests use unit-level code only and do not validate `Site.client`, require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Site` objects are used as routing and identity anchors across page, forum, member, application, recent-change, source, and publish workflows. `Site.from_unix_name(...)` already parses valid scalar values from site metadata, so the change is intentionally conservative: it only prevents direct callers, fixtures, generated adapters, or rehydrated site state from storing malformed scalar metadata that later fails as less informative URL, AMC routing, cache, or diagnostic behavior.

## Local Evidence

- Local rollout evidence used site identity in site lookup, source/publish result ledgers, page/source inventory, page publishing, recent-change reports, forum discovery, member administration, and application review.
- Existing local drafts covered parser-side generated site IDs, site lookup UNIX-name inputs, result-ledger site fields, recent-change parent `Site` fields, collection parent-site fields, and site accessor parent-site validation, but did not cover direct `Site(...)` scalar metadata construction.
- Existing unit fixtures intentionally construct valid `Site` objects with mock clients to avoid HTTP. This slice preserves that pattern and does not validate `Site.client`.
- This slice only validates direct `Site` scalar metadata. It does not change site lookup fetching, parsed site metadata extraction, URL generation for valid fields, Ajax routing for valid fields, accessors for valid sites, live Wikidot behavior, or client object validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change rejects malformed scalar values rather than coercing them. In particular, booleans are rejected for `id` even though `bool` is a subclass of `int`, and integers are rejected for `ssl_supported` even when they are truthy or falsy.
