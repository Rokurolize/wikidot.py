# PR Draft: Validate Page Constructor Discussion Cache

## Summary

`Page._discussion` is the optional cached `ForumThread` behind the public `Page.discussion` property, and `_discussion_checked` records whether the page discussion lookup has already been performed. These fields are populated by lazy discussion acquisition, no-discussion cache checks, destroy cache invalidation, local fixtures, generated adapters, and serialized or rehydrated page records. Earlier local slices validated page discussion retry behavior, exhausted-fetch diagnostics, missing and malformed response bodies, malformed discussion thread IDs, page destroy cache invalidation, direct page scalar fields, page constructor source/revisions/votes/files/metas caches, and forum-thread record state, but direct `Page(..., _discussion=..., _discussion_checked=...)` construction still accepted malformed cached discussion values and truthy or falsey non-boolean checked flags.

This change validates the direct constructor's optional discussion cache during `Page.__post_init__`. `_discussion=None` remains valid for pages that have not acquired discussion state or that have checked and found no discussion, real `ForumThread` objects remain valid, and malformed non-null values now raise `ValueError("page.discussion must be ForumThread or None")`. `_discussion_checked` now accepts only real booleans and rejects values such as `None`, strings, integers, lists, and arbitrary objects with `ValueError("page.discussion_checked must be a boolean")`.

## Outcome

Directly constructed `Page` objects now fail early when optional discussion cache state or checked-state flags are malformed, while preserving lazy discussion acquisition for the default unchecked state, preserving checked no-discussion state, and preserving valid cached `ForumThread` objects.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free page inventories, page-to-discussion ledgers, discussion migration tooling, local fixtures, generated adapters, or serialized and rehydrated `Page` records.

## Current Evidence

Page discussion drafts [045-pr-retry-page-discussion-fetch.md](045-pr-retry-page-discussion-fetch.md), [192-pr-page-auxiliary-fetch-site-context.md](192-pr-page-auxiliary-fetch-site-context.md), [219-pr-page-auxiliary-response-body-context.md](219-pr-page-auxiliary-response-body-context.md), [309-pr-page-discussion-thread-id-context.md](309-pr-page-discussion-thread-id-context.md), and [335-pr-page-auxiliary-response-body-type-context.md](335-pr-page-auxiliary-response-body-type-context.md) establish `Page.discussion` as a retry-aware auxiliary page read with explicit diagnostics for exhausted fetches, missing bodies, malformed body types, and malformed generated thread IDs. [267-pr-page-destroy-cache-invalidation.md](267-pr-page-destroy-cache-invalidation.md) establishes `_discussion` and `_discussion_checked` as local cache state that must be reset after destructive page actions.

Constructor and state-integrity drafts [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md) through [489-pr-validate-page-constructor-id-field.md](489-pr-validate-page-constructor-id-field.md), [490-pr-validate-page-constructor-source-field.md](490-pr-validate-page-constructor-source-field.md), [491-pr-validate-page-constructor-revisions-cache.md](491-pr-validate-page-constructor-revisions-cache.md), [492-pr-validate-page-constructor-votes-cache.md](492-pr-validate-page-constructor-votes-cache.md), [493-pr-validate-page-constructor-files-cache.md](493-pr-validate-page-constructor-files-cache.md), and [511-pr-validate-page-constructor-metas-cache.md](511-pr-validate-page-constructor-metas-cache.md) establish the local pattern for validating direct page record and cache state instead of relying only on parser-created objects or public property paths.

Forum-thread drafts [503-pr-validate-forum-thread-site-field.md](503-pr-validate-forum-thread-site-field.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), [456-pr-validate-forum-thread-text-fields.md](456-pr-validate-forum-thread-text-fields.md), [457-pr-validate-forum-thread-post-count-field.md](457-pr-validate-forum-thread-post-count-field.md), and [458-pr-validate-forum-thread-creator-time-fields.md](458-pr-validate-forum-thread-creator-time-fields.md) establish `ForumThread` itself as the validated discussion record type.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 045, 192, 219, 309, or 335. Those slices validate lazy discussion acquisition, retry/exhaustion behavior, response-body handling, and generated thread-ID parsing; this slice validates constructor-seeded local discussion cache state before lazy acquisition is invoked.

This is not a duplicate of Issue 267. Issue 267 clears discussion caches after a successful destroy action; this slice validates the shape of direct initial cache state.

This is not a duplicate of Issue 511. Issue 511 validates the separate `_metas` cache; this slice validates `_discussion` and `_discussion_checked`.

This is not a duplicate of Issues 490 through 493. Those slices validate page `_source`, `_revisions`, `_votes`, and `_files` constructor caches; this slice validates the page discussion cache and checked flag.

This is not a duplicate of Issue 503 or adjacent forum-thread field slices. Those slices validate `ForumThread` records themselves; this slice validates whether a `Page` discussion cache slot contains a `ForumThread`.

No upstream issue was filed from this local workspace.

## Changes

- Add optional cached discussion validation for direct `Page(...)` construction.
- Preserve `_discussion=None` for pages that should lazily acquire discussion or have checked and found no discussion.
- Preserve valid cached `ForumThread` objects without coercion.
- Reject non-`ForumThread` discussion cache values using `ValueError("page.discussion must be ForumThread or None")`.
- Validate `_discussion_checked` accepts only real booleans.
- Reject malformed checked flags using `ValueError("page.discussion_checked must be a boolean")`.
- Add constructor tests for malformed direct `_discussion` values, malformed `_discussion_checked` values, valid cached discussion threads, and checked no-discussion state.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached page discussion state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(_discussion=...)` must accept `None` and real `ForumThread` objects. |
| R2 | `Page(_discussion=...)` must reject non-`None` non-`ForumThread` values with `ValueError("page.discussion must be ForumThread or None")`. |
| R3 | `Page(_discussion_checked=...)` must accept only real booleans and reject malformed values with `ValueError("page.discussion_checked must be a boolean")`. |
| R4 | A valid cached checked discussion must be returned by `page.discussion`, and checked no-discussion state must return `None` without fetching. |
| R5 | Valid default construction, lazy discussion acquisition, no-discussion checked-state behavior, page discussion retry/response diagnostics, page destroy cache invalidation, page source/revision/file/vote/metas behavior, and adjacent page/site workflows must remain unchanged. |
| R6 | This slice must not change discussion request construction, retry behavior, response parsing, generated thread-ID parsing, live request behavior, forum-thread parsing, no-discussion semantics, or unrelated constructor fields. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page data, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, constructor tests, adjacent page workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None` and valid cached `ForumThread` objects remain accepted. | `TestPageInit.test_init_accepts_valid_optional_discussion` passed before and after validation was added for default unchecked state, checked no-discussion state, and a checked cached `ForumThread`. | Rejecting missing cached discussion, rejecting a real `ForumThread`, or coercing discussion objects rejects this local completion claim. | `Page` constructor cached discussion state | `tests/unit/test_page_constructor.py` |
| R2 | Malformed optional cached discussion values fail at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_optional_discussion` failed RED for 4 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, strings, dictionaries, arbitrary objects, or silently coercing malformed values rejects this local completion claim. | `Page` constructor cached discussion state | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Malformed checked flags fail at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_discussion_checked` failed RED for 6 malformed values because constructors did not raise, then passed GREEN after strict boolean validation was added. | Accepting `None`, strings, `0`, `1`, lists, arbitrary objects, or truthiness-based coercion rejects this local completion claim. | `Page` constructor discussion checked flag | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R4 | Valid cached discussion access remains a cache hit, and checked no-discussion state remains valid. | The valid-cache test asserts `page_with_discussion.discussion == discussion` and `page_without_thread.discussion is None` when `_discussion_checked=True`. | Fetching for a checked valid cache, clearing `_discussion`, replacing the cached thread, or treating checked no-discussion as malformed rejects this local completion claim. | `Page.discussion` cache access | `tests/unit/test_page_constructor.py` |
| R5 | Existing page and adjacent workflows remain green. | `tests/unit/test_page_constructor.py` passed 158 tests, adjacent page/source/revision/file/vote/site tests passed 901 tests, and the full unit suite passed 2299 tests. | Regressing lazy discussion acquisition, no-discussion checked-state behavior, discussion response diagnostics, destroy cache invalidation, page source/revision/file/vote/metas behavior, site workflows, or parser-created pages rejects this local completion claim. | Page and adjacent workflows | `tests/unit` |
| R6 | Broader discussion read semantics remain outside scope. | Existing discussion getter, parser, response-body, page, and adjacent tests remain green; this slice only validates direct constructor cache type integrity and checked-flag type. | Changing request construction, retry policy, response diagnostics, thread-ID parsing, forum-thread acquisition, live request behavior, or unrelated constructor fields rejects this local completion claim. | Page constructor scope | `src/wikidot/module/page.py`, adjacent tests |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw page source, raw page HTML, private messages, or private forum/site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, constructor tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `5099201 fix(page): validate discussion cache`.

- RED cache tests: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_optional_discussion tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_optional_discussion tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_discussion_checked -q` failed 10 malformed `_discussion` and `_discussion_checked` cases before the fix with `DID NOT RAISE`, while the valid cached discussion case passed.
- GREEN cache tests: the same focused command passed 11 tests after optional discussion-cache and checked-flag validation were added.
- `uv run pytest tests/unit/test_page_constructor.py -q` passed 158 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 901 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py` reformatted the test file and left the source file unchanged.
- `uv run ruff format --check src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 2 files already formatted.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed.
- `uv run mypy src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2299 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page(_discussion=None, _discussion_checked=False)` remains valid and lazy discussion acquisition remains available.
- `Page(_discussion=None, _discussion_checked=True)` remains valid and `page.discussion` returns `None` as checked no-discussion state.
- `Page(_discussion=ForumThread(...), _discussion_checked=True)` remains valid and `page.discussion` returns the cached thread.
- `Page(_discussion=True)`, `Page(_discussion="cached discussion")`, `Page(_discussion={"id": 3001})`, and `Page(_discussion=object())` raise `ValueError("page.discussion must be ForumThread or None")` when every other constructor field is valid.
- `Page(_discussion_checked=None)`, `"true"`, `1`, `0`, `[]`, and `object()` raise `ValueError("page.discussion_checked must be a boolean")` when every other constructor field is valid.
- Existing parser-created pages, direct page fixtures, lazy `Page.discussion`, page discussion retry and response diagnostics, checked no-discussion behavior, page destroy cache invalidation, page source/revision/file/vote/metas behavior, and adjacent page/site workflows remain green.
- The new tests use unit-level code only and do not validate discussion response contents, generated thread-ID parser details, live Wikidot, credentials, cookies, auth JSON, private page data, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Constructor validation could be confused with page discussion response validation. Mitigation: the validator checks cache object type and checked-flag type only; response parsing and fetch diagnostics remain outside scope and existing tests stay green.
- Risk: Checked no-discussion state could be rejected accidentally. Mitigation: the valid-cache test covers `_discussion=None` with `_discussion_checked=True` and expects `page.discussion is None`.
- Risk: Public lazy behavior could be bypassed for default pages. Mitigation: `_discussion=None` with `_discussion_checked=False` remains valid and keeps lazy acquisition available.
