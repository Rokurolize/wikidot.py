# PR Draft: Validate Blank Site Routing Metadata

## Summary

`Site(...)` already rejects malformed metadata types, `Site.from_unix_name(...)` already rejects malformed caller-provided lookup names, and `Site.url` already rejects mutated non-string URL metadata, but blank and whitespace-only routing metadata still passed. Direct `Site(unix_name="", ...)` and `Site(domain="", ...)` constructions could create unusable site identities, `Site.url` could format malformed URLs like `https://`, and parsed blank `WIKIREQUEST.info.siteUnixName` or `WIKIREQUEST.info.domain` values could return a `Site` with unusable routing metadata.

This change rejects blank and whitespace-only `unix_name` and `domain` values after the existing string-type checks. It applies during `Site.__post_init__`, during `Site.url` domain revalidation, and during `Site.from_unix_name(...)` because parsed metadata flows through the constructor before returning a site object. Blank `title` remains valid display text. Existing non-string diagnostics, caller-provided lookup-name syntax validation, valid SSL/non-SSL lookup behavior, missing metadata diagnostics, site ID parsing, site accessors, page/forum/member/application workflows, and adjacent client/Ajax workflows remain unchanged.

## Outcome

Blank site routing metadata now fails locally before unusable `Site` identities or malformed site URLs can be stored or returned, while valid non-empty routing metadata and blank display titles keep the existing behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who construct `Site` records from parsed Wikidot HTML, generated fixtures, local ledgers, sandbox setup scripts, migration records, or browser-free automation state.

## Current Evidence

Site and lookup drafts [310-pr-site-id-context.md](310-pr-site-id-context.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [359-pr-validate-site-lookup-unix-names.md](359-pr-validate-site-lookup-unix-names.md), [480-pr-validate-site-constructor-metadata.md](480-pr-validate-site-constructor-metadata.md), [525-pr-validate-site-lookup-config-object.md](525-pr-validate-site-lookup-config-object.md), [548-pr-validate-site-lookup-client.md](548-pr-validate-site-lookup-client.md), and [571-pr-validate-site-url-metadata-state.md](571-pr-validate-site-url-metadata-state.md) establish site lookup, constructor metadata, URL-time metadata, result-ledger site identity, site ID diagnostics, config-object validation, and direct lookup client validation as practical browser-free infrastructure boundaries.

Issue 359 validates caller-provided site lookup names before `Site.from_unix_name(...)` issues HTTP work, but it does not validate the returned parsed `siteUnixName` or `domain` metadata. Issue 480 validates direct constructor metadata types, but it does not reject blank string routing metadata. Issue 571 revalidates URL-time metadata types, but it does not reject blank string domains. This slice resolves that adjacent content-boundary only for blank and whitespace-only site routing strings; it does not attempt full domain syntax validation, site-name normalization, redirect policy changes, live site existence policy changes, or display-title content validation.

No upstream issue was filed from this local workspace.

## Changes

- Reject blank and whitespace-only `unix_name` values in `Site.__post_init__` after the existing string-type check.
- Reject blank and whitespace-only `domain` values in `Site.__post_init__` after the existing string-type check.
- Reuse the same routing-field validator in `Site.url` so mutated blank or whitespace-only domains fail before URL formatting.
- Let `Site.from_unix_name(...)` reject parsed blank `WIKIREQUEST.info.siteUnixName` and `WIKIREQUEST.info.domain` values through constructor validation before returning a `Site`.
- Preserve blank `title` as valid display text and preserve valid non-empty strings exactly; the validators do not strip, normalize, or rewrite stored metadata.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site(..., unix_name="")` and whitespace-only variants must raise `ValueError("unix_name must not be empty")` before accessor/cache state is initialized as a usable site record. |
| R2 | `Site(..., domain="")` and whitespace-only variants must raise `ValueError("domain must not be empty")` before accessor/cache state is initialized as a usable site record. |
| R3 | `Site.url` must reject a mutated blank or whitespace-only `domain` with `ValueError("domain must not be empty")` before formatting a URL. |
| R4 | `Site.from_unix_name(...)` must reject parsed blank `WIKIREQUEST.info.siteUnixName` and `WIKIREQUEST.info.domain` values before returning a `Site`. |
| R5 | Blank `title` must remain valid display text, and existing metadata type diagnostics must remain unchanged. |
| R6 | Valid site construction, valid SSL and non-SSL URL formatting, valid site lookup parsing, missing metadata diagnostics, malformed site ID diagnostics, site accessors, and adjacent page/forum/member/application/client/Ajax workflows must remain unchanged. |
| R7 | Focused RED/GREEN, affected site tests, adjacent workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R8 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Blank direct site UNIX names fail during construction. | `TestSiteInit.test_init_rejects_blank_routing_metadata` failed RED for `""` and `"   "` `unix_name` values with `DID NOT RAISE`, then passed GREEN after routing-field validation was added. | Accepting a blank `unix_name`, checking blankness before type checks, changing non-string diagnostics, or normalizing and continuing rejects this local completion claim. | Site constructor routing metadata | `src/wikidot/module/site.py`, `tests/unit/test_site_constructor.py` |
| R2 | Blank direct site domains fail during construction. | The same constructor test failed RED for `""` and `"   "` `domain` values with `DID NOT RAISE`, then passed GREEN after routing-field validation was added. | Accepting a blank `domain`, initializing a usable site record with blank routing metadata, changing non-string diagnostics, or normalizing and continuing rejects this local completion claim. | Site constructor routing metadata | `src/wikidot/module/site.py`, `tests/unit/test_site_constructor.py` |
| R3 | Mutated blank domains fail before URL formatting. | `TestSiteInit.test_url_rejects_mutated_metadata` failed RED for blank and whitespace-only mutated domains with `DID NOT RAISE`, then passed GREEN after `Site.url` reused the routing-field validator. | Returning `https://`, `https://   `, or any URL for blank mutated domains, or changing mutated non-string domain/SSL diagnostics, rejects this local completion claim. | Site URL revalidation | `src/wikidot/module/site.py`, `tests/unit/test_site_constructor.py` |
| R4 | Parsed blank lookup metadata fails before returning a site. | `TestSiteFromUnixName.test_from_unix_name_blank_parsed_unix_name` and `test_from_unix_name_blank_parsed_domain` failed RED with `DID NOT RAISE`, then passed GREEN through constructor validation after metadata parsing. | Returning a `Site` with blank parsed `siteUnixName` or `domain`, weakening caller lookup-name validation, or changing missing metadata/site ID diagnostics rejects this local completion claim. | Site lookup parse boundary | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R5 | Display titles and validation precedence stay stable. | `TestSiteInit.test_init_allows_blank_title` passed in the RED run and after the fix, and malformed metadata type cases continued to pass with the existing string/integer/boolean diagnostics. | Rejecting blank titles, stripping titles, changing metadata type diagnostics, or validating blankness before type checks rejects this local completion claim. | Site display metadata | `tests/unit/test_site_constructor.py` |
| R6 | Valid and adjacent site workflows remain green. | `tests/unit/test_site_constructor.py` and `tests/unit/test_site.py` passed 325 tests; adjacent site/page/forum/member/application/client/Ajax coverage passed 1555 tests. | Regressing valid SSL/non-SSL URLs, valid site lookup, missing metadata errors, malformed site ID errors, accessors, page/forum/member/application workflows, client setup, or Ajax behavior rejects this local completion claim. | Site and adjacent workflows | `tests/unit` |
| R7 | Repository quality gates pass in the local dependency environment. | Full unit passed 2837 tests; full `ruff check`, `ruff format --check`, `mypy`, `pyright`, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | verification commands below |
| R8 | No live site material or private state is needed to prove the behavior. | The regressions use synthetic site names, domains, and mocked lookup HTML only; this draft contains no credentials, cookies, auth JSON, raw rollout paths, private account names, raw response bodies, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private account data, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `5656e3c fix(site): validate blank routing metadata`.

- RED: `uv run pytest tests/unit/test_site_constructor.py::TestSiteInit::test_init_rejects_blank_routing_metadata tests/unit/test_site_constructor.py::TestSiteInit::test_url_rejects_mutated_metadata tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_blank_parsed_unix_name tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_blank_parsed_domain -q` failed 8 blank routing-metadata cases with `DID NOT RAISE`; existing non-string URL checks and blank-title preservation passed in the same focused run.
- GREEN focused: the same command passed 12 tests after routing-field blank-string validation was added.
- Site coverage: `uv run pytest tests/unit/test_site_constructor.py tests/unit/test_site.py -q` passed 325 tests.
- Adjacent coverage: `uv run pytest tests/unit/test_site_constructor.py tests/unit/test_site.py tests/unit/test_site_accessors.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_client.py tests/unit/test_ajax.py -q` passed 1555 tests.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site_constructor.py tests/unit/test_site.py` left 3 files unchanged.
- `uv run pytest tests/unit -q` passed 2837 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Site(client=..., id=1, title="Test", unix_name="", domain="test.wikidot.com", ssl_supported=True)` and whitespace-only `unix_name` variants raise `ValueError("unix_name must not be empty")`.
- `Site(client=..., id=1, title="Test", unix_name="test", domain="", ssl_supported=True)` and whitespace-only `domain` variants raise `ValueError("domain must not be empty")`.
- `Site(..., title="")` remains valid and stores `title == ""`.
- A valid `Site` whose `domain` is later set to `""` or whitespace-only raises `ValueError("domain must not be empty")` when `site.url` is read.
- `Site.from_unix_name(...)` returns no site object when mocked lookup HTML contains blank `WIKIREQUEST.info.siteUnixName` or blank `WIKIREQUEST.info.domain`.
- Non-string `unix_name`, `domain`, and `title` values still raise the existing `"... must be a string"` diagnostics, and malformed `id` / `ssl_supported` diagnostics remain unchanged.
- Valid non-empty routing metadata keeps existing site construction, valid URL formatting, valid site lookup parsing, accessors, page/forum/member/application workflows, client workflows, Ajax workflows, live Wikidot semantics, upstream Issues, upstream PRs, pushes, credentials, cookies, auth JSON, and raw response bodies outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

Site routing metadata is used to build AMC routing names, URLs, ledger site identities, lookup results, and downstream automation records. Blank strings at those boundaries usually indicate missing or malformed parsed metadata, not a useful site identity. Failing before storing or formatting blank routing fields gives deterministic local diagnostics without requiring live Wikidot traffic or exposing private site data.

## Local Evidence, Not For Upstream Paste

- Issue 359 covered caller-provided site lookup UNIX-name validation and explicitly sits before the HTTP lookup path; it does not validate parsed site metadata returned by Wikidot HTML.
- Issue 480 covered direct site constructor metadata types and did not reject blank routing strings.
- Issue 571 covered URL-time metadata type validation and did not reject blank mutated domains.
- The focused RED run showed direct site construction, URL-time mutated domain access, and parsed lookup metadata accepted blank routing strings.
- This slice only validates blank routing strings. It does not validate full domain syntax, redirect consistency, site-name syntax beyond existing lookup-name validation, title contents, live site existence, or valid non-empty metadata semantics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw response bodies, private account data, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The new routing-field validator deliberately does not strip, normalize, lowercase, punycode-convert, or rewrite non-empty metadata. It only rejects strings whose stripped form is empty, preserving existing request and URL behavior for all non-empty string inputs.
