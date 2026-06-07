# PR Draft: Validate ForumCategory Site Field

## Summary

`ForumCategory` records carry the parent `Site` used by browser-free forum category discovery, lazy category thread reads, `reload_threads(...)`, `create_thread(...)`, returned-status diagnostics, generated forum inventory ledgers, and local fixtures. Earlier local slices validated category-list fetch retries, parser scoping, response-body diagnostics, loaded-collection lookup, collection entries, collection parent sites, direct category ID/count/text fields, thread-cache assignment, and forum-thread parent category fields. One direct record-state gap remained: `ForumCategory(..., site=...)` still accepted arbitrary non-`Site` values such as `None`, booleans, strings, dictionaries, and arbitrary objects.

This change validates `ForumCategory.site` at initialization. Malformed parent-site values now raise `ValueError("site must be a Site")` before invalid category state can be stored. Valid `Site` parents, category-list parsing, collection construction, category-owned thread reads, `reload_threads(...)`, `create_thread(...)`, forum thread/post/revision behavior, and adjacent site/forum workflows remain unchanged.

## Outcome

Callers cannot silently construct forum-category records with malformed parent-site state, while parser-created categories and valid direct `ForumCategory(...)` construction keep the existing category inventory, thread-read, and thread-create behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum category discovery, `site.forum.categories`, category-owned thread reads, forum migration checks, generated forum inventory ledgers, moderation tooling, translation review tooling, local fixtures, or serialized and rehydrated forum category records.

## Current Evidence

Forum-category drafts [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [434-pr-validate-forum-category-threads-assignments.md](434-pr-validate-forum-category-threads-assignments.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [453-pr-validate-forum-category-count-fields.md](453-pr-validate-forum-category-count-fields.md), and [454-pr-validate-forum-category-text-fields.md](454-pr-validate-forum-category-text-fields.md) establish forum category acquisition, parser diagnostics, response diagnostics, write-input validation, loaded-collection lookup, collection state, thread-cache assignment, and direct category scalar fields as practical operational boundaries.

Adjacent parent-state drafts [439-pr-validate-site-change-site-field.md](439-pr-validate-site-change-site-field.md), [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md), [476-pr-validate-forum-category-collection-site-field.md](476-pr-validate-forum-category-collection-site-field.md), [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md), [478-pr-validate-site-accessor-parent-sites.md](478-pr-validate-site-accessor-parent-sites.md), [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md), and [501-pr-validate-site-member-site-field.md](501-pr-validate-site-member-site-field.md) establish the local pattern for validating direct parent-site fields instead of relying only on parser boundaries or mocks.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 476. Issue 476 validates only `ForumCategoryCollection(site=...)` explicit parent sites while preserving inference from category entries. This slice validates the separate parent `Site` object stored on each `ForumCategory` record.

This is not a duplicate of Issues 452, 453, or 454. Those slices validate direct category ID, count, title, and description fields. This slice validates the parent-site field that supplies client routing, site diagnostics, lazy thread acquisition, and thread creation context.

This is not a duplicate of Issue 478. Issue 478 validates `SitePagesAccessor`, `SitePageAccessor`, and `SiteForumAccessor` parent sites, not forum-category records returned by the forum accessor.

This is not a duplicate of Issues 500 or 501. Those slices validate site application and site member parent records. This change applies the same parent-state pattern to forum category records.

No upstream issue was filed from this local workspace.

## Changes

- Rename the internal forum-category site validator so it can be reused by both `ForumCategoryCollection` and `ForumCategory`.
- Update `ForumCategory.__post_init__` to reject non-`Site` parent objects.
- Preserve valid `ForumCategoryCollection(site=...)` behavior through the same validator.
- Add focused constructor regressions for malformed category parent-site values.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum-category parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategory(site=None)`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` must raise `ValueError("site must be a Site")` when every other constructor field is valid. |
| R2 | Valid `Site` parents must remain valid constructor inputs, and parser-created `ForumCategory` rows must retain the original parent site. |
| R3 | Existing `ForumCategoryCollection` explicit-site validation must keep the same error message and valid-site behavior. |
| R4 | Existing category-list parsing, collection initialization, loaded-collection lookup, lazy `site.forum.categories`, category-owned thread reads, `reload_threads(...)`, `create_thread(...)`, forum thread/post/revision behavior, and adjacent site/forum workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-category tests, adjacent forum tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor site values fail at the public dataclass boundary. | `TestForumCategoryBasic.test_init_rejects_malformed_sites` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after validation was added. | Accepting missing values, booleans, site names, dictionaries, arbitrary objects, or emitting category rows with non-`Site` parent state rejects this local completion claim. | ForumCategory constructor | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Valid parent-site semantics stay green. | Existing category parser and constructor tests passed with valid `Site` fixtures. | Rejecting valid `Site` objects, losing the parent site during `ForumCategoryCollection.acquire_all(...)`, or changing stored ID/count/text fields rejects this local completion claim. | Parser-created and manually created categories | `tests/unit/test_forum_category.py` |
| R3 | Collection explicit-site validation keeps its contract. | `TestForumCategoryCollectionInit.test_init_rejects_malformed_sites` remained green after the collection and category constructor shared the validator. | Weakening collection parent-site validation, changing diagnostics, or accepting malformed explicit collection sites rejects this local completion claim. | ForumCategoryCollection constructor | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R4 | Existing adjacent forum workflows remain green. | `tests/unit/test_forum_category.py` passed 80 tests, adjacent forum tests passed 449 tests, and the full unit suite passed 2224 tests. | Regressing category-list acquisition, parser diagnostics, response-body diagnostics, collection initialization, loaded-collection lookup, lazy category thread reads, `reload_threads(...)`, `create_thread(...)`, forum thread parent-category behavior, forum post behavior, or forum post revision behavior rejects this local completion claim. | Forum category and adjacent forum workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Full ruff, format, mypy, pyright, unit, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4c7f7b7 fix(forum_category): validate category site`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_malformed_sites -q` failed 5 tests before the fix; every malformed `site` value reported `DID NOT RAISE`.
- GREEN constructor: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_malformed_sites -q` passed 5 tests.
- Adjacent constructor checks: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionInit::test_init_rejects_malformed_sites tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_integer_category_id tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_integer_threads_count tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_integer_posts_count tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_string_title tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_string_description -q` passed 24 tests.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 80 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 449 tests.
- `uv run ruff check src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed.
- `uv run ruff format --check src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2224 tests.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumCategory(site=None)`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` raise `ValueError("site must be a Site")`.
- Valid `Site` instances remain valid as `ForumCategory.site`.
- Parser-created rows from `ForumCategoryCollection.acquire_all(site)` retain the original valid `Site` parent.
- Existing `ForumCategoryCollection(site=...)` explicit-site validation remains unchanged.
- Existing category-list parsing, response diagnostics, direct category ID/count/text validation, collection initialization, loaded-collection lookup, lazy `site.forum.categories`, category-owned thread reads, `reload_threads(...)`, `create_thread(...)`, forum thread/post/revision behavior, and adjacent site/forum workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Reusing the collection validator could accidentally weaken collection-site validation. Mitigation: the existing collection malformed-site test stayed green, and the helper still raises `ValueError("site must be a Site")`.
- Risk: Constructor validation could be confused with live-site validation. Mitigation: this change only checks the local parent object type and does not contact Wikidot, validate permissions, or change authentication behavior.
- Risk: Tests could drift back to arbitrary site-like mocks. Mitigation: valid category tests already use real `Site` fixtures, and malformed cases are explicit unit-level invalid inputs.

## Dependencies

- Valid category-list parser output continues to be created from a real `Site` object supplied to `ForumCategoryCollection.acquire_all(site)`.
- Existing `Site` constructor validation remains responsible for site scalar fields such as `id`, `title`, `unix_name`, `domain`, and `ssl_supported`.
- Existing forum write-input validation remains responsible for `create_thread(...)` title, description, and source strings.

## Open Questions

None for this local slice. Post-construction mutation revalidation remains outside scope, matching adjacent constructor-only record-field validations such as `Page.site`.

## Upstream-Safe Motivation

`ForumCategory.site` is the parent object behind browser-free category inventories, lazy thread reads, thread creation, diagnostics, and generated forum ledgers. Parser paths already pass a real `Site` object into created category rows. Constructor validation keeps malformed local parent state out of manually constructed or rehydrated records without changing category acquisition, parser selectors, thread reads, thread creation payloads, returned-status handling, cache behavior, or live Wikidot interactions.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work repeatedly used browser-free forum category discovery, cached category inventories, category-owned thread reads, thread creation drafts, generated forum inventory ledgers, forum migration checks, moderation tooling, and tests that construct `ForumCategory` records directly.
- Existing local drafts covered forum-category fetch retry behavior, parser row scoping, response-body diagnostics, parser count diagnostics, write-input validation, collection search-key validation, collection constructor validation, collection parent-site validation, thread-cache assignment validation, direct category ID/count/text validation, and forum-thread category validation, but did not cover direct `ForumCategory(site=...)` construction.
- The focused RED failures showed invalid constructor site values were accepted as dataclass state. The GREEN regressions cover missing, boolean, string, dictionary, and arbitrary object values.
- This slice only validates stored forum-category parent type at construction. It does not change category-list acquisition, parser selectors, response-body diagnostics, ID parsing, title parsing, description parsing, count parsing, collection initialization, `find(...)`, lazy `site.forum.categories`, `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, forum thread/post/revision behavior, live site behavior, or client authentication.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, forum source text, page source text, private messages, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed parent objects instead of accepting site-like mocks or dictionaries. Tests and downstream callers should construct a real `Site` object and stub network-facing request methods when unit-level isolation is needed.
