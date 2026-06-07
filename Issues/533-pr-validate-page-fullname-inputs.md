# PR Draft: Validate Page Fullname Inputs Before Lookup And Write Work

## Summary

`fullname` is the routing key for individual page lookup, direct page creation/editing, high-level site page creation, and browser-free publishing. Previous local slices already validated stored `Page(fullname=...)` identity, `PageCollection.find(fullname=...)`, and rename targets, while adjacent create/publish slices validated title, source, comment, booleans, page IDs, metadata, parent fullnames, and tags. The remaining page-boundary fullname inputs could still fail incidentally or progress into side-effect work before a stable diagnostic.

This change validates `fullname` as a string at the direct collection lookup, `Site.page.get(...)`, `Site.page.create(...)`, `Site.page.publish(...)`, and `Page.create_or_edit(...)` boundaries. Malformed fullnames now raise `ValueError("fullname must be a string")` before ListPages search, direct page-ID fallback, login checks, page-lock requests, save requests, existing-page edit delegation, publish source verification, metadata writes, or result construction.

## Outcome

Page lookup and write helpers now fail at the caller-facing fullname boundary instead of leaking raw `_split_fullname` `TypeError`, sending malformed `wiki_page` values into write requests, or relying on downstream helpers to reject values after high-level APIs have already made progress.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page lookup, creation, editing, and publishing from generated ledgers, JSON/YAML inputs, migration fixtures, local queue records, or automation that may carry malformed page identifiers.

## Current Evidence

Local rollout-backed drafts established `Site.page.get(...)`, `Page.create_or_edit(...)`, and `Site.page.publish(...)` as practical workflow surfaces for stale ListPages fallback, direct page-ID fallback, browser-free publishing, source verification, post-save visibility retries, and metadata updates. Relevant prior local drafts include [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [190-pr-site-page-get-direct-id-error-surface.md](190-pr-site-page-get-direct-id-error-surface.md), [203-pr-site-page-get-miss-site-context.md](203-pr-site-page-get-miss-site-context.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [352-pr-validate-page-rename-fullname-input.md](352-pr-validate-page-rename-fullname-input.md), [382-pr-validate-page-collection-find-fullname.md](382-pr-validate-page-collection-find-fullname.md), [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md), and [531-pr-validate-metadata-tag-inputs.md](531-pr-validate-metadata-tag-inputs.md).

Those prior slices are not duplicates. Issue 481 validates stored constructor identity fields. Issue 382 validates `PageCollection.find(...)` on an already loaded collection, not direct ListPages lookup. Issue 352 validates rename targets, not lookup or create/edit targets. Issues 349, 350, 412, and 531 validate adjacent write inputs after a valid page target has been supplied. None rejects malformed fullnames at the direct ListPages lookup, high-level site accessor, or direct create/edit boundary before lookup and write-side work. No upstream issue was filed from this local workspace.

## Changes

- Validate `PageCollection._split_fullname(...)` before category/name splitting so direct `PageCollection.get_by_fullname(...)` fails before ListPages search.
- Validate `Page.create_or_edit(fullname=...)` before login checks, page-lock requests, save requests, post-save lookup, fallback page construction, or local source-cache mutation.
- Validate `Site.page.get(fullname=...)` before ListPages lookup or direct page-ID fallback.
- Validate `Site.page.create(fullname=...)` before login checks, force-edit lookup, existing-page edit delegation, or `Page.create_or_edit(...)` delegation.
- Validate `Site.page.publish(fullname=...)` before login checks, page lookup, create/edit delegation, post-save page-ID resolution, source verification, metadata writes, or result construction.
- Preserve valid default-category and explicit-category fullname behavior.

## Type Of Change

- Input validation
- Page lookup preflight hardening
- Page write preflight hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageCollection.get_by_fullname(...)` must reject non-string fullnames with `ValueError("fullname must be a string")` before ListPages search. |
| R2 | `Site.page.get(...)` must reject non-string fullnames with the same diagnostic before ListPages lookup or direct page-ID fallback. |
| R3 | `Page.create_or_edit(...)` must reject non-string fullnames with the same diagnostic before login checks, edit-lock requests, save requests, post-save lookup, fallback page construction, or local cache mutation. |
| R4 | `Site.page.create(...)` must reject non-string fullnames with the same diagnostic before login checks, force-edit lookup, existing-page edit delegation, or direct create/edit delegation. |
| R5 | `Site.page.publish(...)` must reject non-string fullnames with the same diagnostic before login checks, page lookup, create/edit work, post-save visibility resolution, source verification, metadata writes, or result construction. |
| R6 | Valid default-category names such as `"new-page"` and explicit category names such as `"component:new-page"` must keep existing lookup, create/edit, publish, fallback, and result behavior. |
| R7 | This slice must not change fullname syntax, empty-string handling, URL construction, page title/source/comment validation, metadata validation, page-ID validation, rename validation, constructor validation, live Wikidot behavior, or response parsing. |
| R8 | Focused RED/GREEN, adjacent page/site/search tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R9 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct collection lookup validates the lookup key before any ListPages request can be constructed. | `test_get_by_fullname_rejects_non_string_fullnames_before_search` failed RED for `None`, `True`, `123`, and `1.0` with raw `_split_fullname` `TypeError`, then passed GREEN with no search call. | Calling `search_pages`, leaking `TypeError`, coercing values, or returning `None` rejects this local completion claim. | Direct page collection lookup | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Site page lookup validates the public lookup key before ListPages or direct page-ID fallback. | `test_get_rejects_non_string_fullnames_before_lookup` failed RED for the same values with raw `_split_fullname` `TypeError`, then passed GREEN with neither search nor direct lookup called. | Calling ListPages search, direct page-ID fallback, leaking `TypeError`, coercing values, or treating malformed input as not found rejects this local completion claim. | Site page lookup | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Direct create/edit validates the page target before any write-side work. | `test_create_or_edit_rejects_non_string_fullnames_before_request` failed RED because malformed values reached login and page-lock handling, then passed GREEN before login or AMC calls. | Calling login, constructing a page-lock request, sending AMC, leaking target-lock errors, coercing values, or mutating local caches rejects this local completion claim. | Direct page write helper | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | High-level create validates the target before authentication and delegation. | `test_create_rejects_non_string_fullnames_before_login` failed RED with `DID NOT RAISE` when downstream create/edit was patched, then passed GREEN before login, force-edit lookup, or delegation. | Calling login, checking an existing page, editing an existing page, delegating to `Page.create_or_edit(...)`, or accepting malformed targets rejects this local completion claim. | Site create preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R5 | High-level publish validates the target before any publish workflow side effects. | `test_publish_rejects_non_string_fullnames_before_save` failed RED with `DID NOT RAISE` when lookup and create/edit were patched, then passed GREEN before login, lookup, create/edit, page-ID resolution, source verification, metadata writes, or result construction. | Calling login, lookup, create/edit, post-save page-ID resolution, refresh, metadata updates, result construction, or accepting malformed targets rejects this local completion claim. | Site publish preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R6 | Valid lookup, create/edit, edit, and publish workflows stay green. | `TestPageCollectionInit`, `TestPageCreateOrEdit`, `TestPageEdit`, and `TestSitePageAccessor` passed 145 tests; broader page/site/search coverage passed 751 tests. | Regressing default-category lookup, explicit-category splitting, stale ListPages fallback, direct page-ID fallback, create/edit selection, publish metadata, source verification, or result fields rejects this local completion claim. | Adjacent page workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_constructor.py`, `tests/unit/test_search_pages_query.py` |
| R7 | The slice stays scoped to type preflight. | The implementation adds five existing string-field validator calls and no syntax, URL, parser, response, or live behavior changes. | Adding syntax normalization, changing empty-string behavior, modifying URL generation, altering response parsing, or changing live account behavior rejects this local completion claim. | Code scope | `src/wikidot/module/page.py`, `src/wikidot/module/site.py` |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R9 | No private material or live action is needed to prove the behavior. | All regressions use synthetic malformed values and local mocks; the draft contains no raw credentials, cookies, auth JSON, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `79d50f0 fix(page): validate page fullname inputs`.

- RED focused fullname tests: `uv run pytest tests/unit/test_page.py::TestPageCollectionInit::test_get_by_fullname_rejects_non_string_fullnames_before_search tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_rejects_non_string_fullnames_before_request tests/unit/test_site.py::TestSitePageAccessor::test_get_rejects_non_string_fullnames_before_lookup tests/unit/test_site.py::TestSitePageAccessor::test_create_rejects_non_string_fullnames_before_login tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_non_string_fullnames_before_save -q` failed 20 cases before the fix. Collection and site lookup leaked raw `_split_fullname` `TypeError`; direct create/edit reached login and page-lock response handling; high-level create and publish did not raise when downstream helpers were patched.
- GREEN focused fullname tests: the same command passed 20 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionInit tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageEdit tests/unit/test_site.py::TestSitePageAccessor -q` passed 145 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_constructor.py tests/unit/test_search_pages_query.py -q` passed 751 tests.
- `uv run pytest tests/unit -q` passed 2544 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageCollection.get_by_fullname(site, None)`, `True`, `123`, and `1.0` raise `ValueError("fullname must be a string")` before ListPages search.
- `Site.page.get(None)`, `True`, `123`, and `1.0` raise the same stable diagnostic before ListPages lookup or direct page-ID fallback.
- `Page.create_or_edit(site, None)`, `True`, `123`, and `1.0` raise the same stable diagnostic before login checks or AMC requests.
- `Site.page.create(None)`, `True`, `123`, and `1.0` raise the same stable diagnostic before login, force-edit lookup, existing-page edit delegation, or direct create/edit delegation.
- `Site.page.publish(None)`, `True`, `123`, and `1.0` raise the same stable diagnostic before login, lookup, create/edit, page-ID resolution, source verification, metadata writes, or result construction.
- Valid string fullnames keep existing default-category and explicit-category behavior.
- Existing constructor fullname validation, rename fullname validation, `PageCollection.find(...)` validation, title/source/comment validation, metadata validation, page-ID validation, direct fallback behavior, publish result behavior, and static gates remain green.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with constructor identity validation. Mitigation: constructor validation protects stored `Page` objects; this slice protects lookup and write method arguments before searches and requests.
- Risk: This could be confused with `PageCollection.find(...)` validation. Mitigation: `find(...)` scans an already loaded collection; this slice validates `get_by_fullname(...)` before ListPages query construction.
- Risk: Adding syntax validation would overreach and could break legitimate Wikidot page names. Mitigation: this slice only enforces string type and preserves existing empty-string, colon-splitting, and remote semantics.
- Risk: High-level create/publish might appear protected by `Page.create_or_edit(...)` alone. Mitigation: high-level tests patch downstream helpers and require rejection before login or delegation.

## Out Of Scope

Changing page-name syntax, rejecting empty strings, normalizing page names, changing URL construction, changing `Page` constructor fields, changing rename behavior, changing title/source/comment/page-ID/metadata validators, changing ListPages query semantics, changing direct page-ID fallback behavior, changing live Wikidot behavior, changing response parsing, and upstream Issue/PR creation are outside this slice.

## Why This Matters

Automation frequently carries page identifiers from generated ledgers, config files, or queue records into lookup and publish helpers. A malformed identifier should produce a stable local boundary error before authentication, network-oriented request construction, fallback probing, or publish workflow state begins.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used browser-free lookup, direct create/edit, and publish helpers to handle stale ListPages, direct page-ID fallback, source verification, visibility retries, metadata updates, and audit result records.
- Existing fullname-related drafts covered stored page identity, collection scans, and rename targets, but not the public lookup/write arguments that route ListPages and `wiki_page` request payloads.
- The focused RED failures showed that malformed fullnames either leaked raw Python type errors, advanced into write-side login/request handling, or passed through high-level APIs when downstream helpers were patched. The GREEN regression now proves the boundary fails before those effects.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
