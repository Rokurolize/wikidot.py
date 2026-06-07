# PR Draft: Validate ForumThread Site Field

## Summary

`ForumThread` records carry the parent `Site` used by browser-free category thread-list reads, direct thread-detail reads, thread URLs, reply action routing, returned-status diagnostics, downstream post/revision reads, generated forum migration ledgers, and local fixtures. Earlier local slices validated thread-list fetch retries, direct thread-detail retries, parser scoping, response-body diagnostics, loaded-collection lookup, collection entries, collection parent sites, direct thread ID/text/count/creator/time/category fields, and forum-category parent sites. One direct record-state gap remained: `ForumThread(..., site=...)` still accepted arbitrary non-`Site` values such as `None`, booleans, strings, dictionaries, and arbitrary objects.

This change validates `ForumThread.site` at initialization. Malformed parent-site values now raise `ValueError("site must be a Site")` before invalid thread state can be stored. Valid `Site` parents, category thread-list parsing, direct thread-detail parsing, collection construction, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, `ForumThread.reply(...)`, forum category/post/revision behavior, and adjacent site/forum workflows remain unchanged.

## Outcome

Callers cannot silently construct forum-thread records with malformed parent-site state, while parser-created threads and valid direct `ForumThread(...)` construction keep existing read, URL, reply, and downstream post/revision behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum thread discovery, `Site.get_thread(...)`, `Site.get_threads(...)`, `ForumThread.get_from_id(...)`, category-owned thread reads, generated forum migration ledgers, moderation tooling, translation review tooling, local fixtures, or serialized and rehydrated forum thread records.

## Current Evidence

Forum-thread drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [170-pr-forum-thread-detail-fetch-failure-context.md](170-pr-forum-thread-detail-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md), [238-pr-forum-thread-detail-count-parse-context.md](238-pr-forum-thread-detail-count-parse-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), [456-pr-validate-forum-thread-text-fields.md](456-pr-validate-forum-thread-text-fields.md), [457-pr-validate-forum-thread-post-count-field.md](457-pr-validate-forum-thread-post-count-field.md), and [458-pr-validate-forum-thread-creator-time-fields.md](458-pr-validate-forum-thread-creator-time-fields.md) establish thread-list acquisition, direct thread-detail acquisition, retry behavior, parser diagnostics, response diagnostics, cache reuse, public thread-ID input validation, collection entry validation, direct thread parent-category validation, and direct thread scalar-field validation as active operational boundaries.

Adjacent parent-state drafts [439-pr-validate-site-change-site-field.md](439-pr-validate-site-change-site-field.md), [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md), [476-pr-validate-forum-category-collection-site-field.md](476-pr-validate-forum-category-collection-site-field.md), [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md), [478-pr-validate-site-accessor-parent-sites.md](478-pr-validate-site-accessor-parent-sites.md), [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md), [501-pr-validate-site-member-site-field.md](501-pr-validate-site-member-site-field.md), and [502-pr-validate-forum-category-site-field.md](502-pr-validate-forum-category-site-field.md) establish the local pattern for validating direct parent-site fields instead of relying only on parser boundaries or mocks.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 475. Issue 475 validates only `ForumThreadCollection(site=...)` explicit parent sites while preserving inference from thread entries. This slice validates the separate parent `Site` object stored on each `ForumThread` record.

This is not a duplicate of Issue 447. Issue 447 validates `ForumThread.category`, the optional parent forum category. This slice validates the required parent `Site` object that supplies URL generation, client routing, site diagnostics, reply action routing, and downstream post acquisition context.

This is not a duplicate of Issues 455, 456, 457, or 458. Those slices validate direct thread ID, title, description, post count, creator, and timestamp fields. This slice validates the parent-site field used across thread reads, replies, diagnostics, and generated ledgers.

This is not a duplicate of Issue 502. Issue 502 validates `ForumCategory.site`; this change applies the same parent-state pattern to `ForumThread.site`.

No upstream issue was filed from this local workspace.

## Changes

- Rename the internal forum-thread site validator so it can be reused by both `ForumThreadCollection` and `ForumThread`.
- Update `ForumThread.__post_init__` to reject non-`Site` parent objects.
- Preserve valid `ForumThreadCollection(site=...)` behavior through the same validator.
- Add focused constructor regressions for malformed thread parent-site values.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum-thread parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThread(site=None)`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` must raise `ValueError("site must be a Site")` when every other constructor field is valid. |
| R2 | Valid `Site` parents must remain valid constructor inputs, and parser-created `ForumThread` rows must retain the original parent site. |
| R3 | Existing `ForumThreadCollection` explicit-site validation must keep the same error message and valid-site behavior. |
| R4 | Existing category thread-list parsing, direct thread-detail parsing, collection initialization, loaded-collection lookup, lazy `ForumCategory.threads`, direct and batched thread acquisition, lazy `ForumThread.posts`, `ForumThread.reply(...)`, forum category/post/revision behavior, and adjacent site/forum workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-thread tests, adjacent forum tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor site values fail at the public dataclass boundary. | `TestForumThreadBasic.test_init_rejects_malformed_sites` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after validation was added. | Accepting missing values, booleans, site names, dictionaries, arbitrary objects, or emitting thread rows with non-`Site` parent state rejects this local completion claim. | ForumThread constructor | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Valid parent-site semantics stay green. | Existing thread parser and constructor tests passed with valid `Site` fixtures. | Rejecting valid `Site` objects, losing the parent site during `ForumThreadCollection._parse_list_in_category(...)` or `_parse_thread_page(...)`, or changing stored ID/text/count/creator/time/category fields rejects this local completion claim. | Parser-created and manually created threads | `tests/unit/test_forum_thread.py` |
| R3 | Collection explicit-site validation keeps its contract. | `TestForumThreadCollectionInit.test_init_rejects_malformed_sites` remained green after the collection and thread constructor shared the validator. | Weakening collection parent-site validation, changing diagnostics, or accepting malformed explicit collection sites rejects this local completion claim. | ForumThreadCollection constructor | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R4 | Existing adjacent forum workflows remain green. | `tests/unit/test_forum_thread.py` passed 125 tests, adjacent forum tests passed 454 tests, and the full unit suite passed 2229 tests. | Regressing category thread-list acquisition, direct thread-detail acquisition, parser diagnostics, response-body diagnostics, collection initialization, loaded-collection lookup, lazy category thread reads, direct thread lookup, batched thread lookup, lazy post reads, reply cache synchronization, forum category behavior, forum post behavior, or forum post revision behavior rejects this local completion claim. | Forum thread and adjacent forum workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, forum source text, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Full ruff, format, mypy, pyright, unit, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `8d44327 fix(forum_thread): validate thread site`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_sites -q` failed 5 tests before the fix; every malformed `site` value reported `DID NOT RAISE`.
- GREEN constructor: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_sites -q` passed 5 tests.
- Adjacent constructor checks: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_init_rejects_malformed_sites tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_non_integer_thread_id tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_non_string_title tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_non_string_description tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_non_integer_post_count tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_created_by tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_created_at tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_categories -q` passed 34 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 125 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 454 tests.
- `uv run ruff check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed.
- `uv run ruff format --check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2229 tests.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThread(site=None)`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` raise `ValueError("site must be a Site")`.
- Valid `Site` instances remain valid as `ForumThread.site`.
- Parser-created rows from category thread lists and direct thread-detail pages retain the original valid `Site` parent.
- Existing `ForumThreadCollection(site=...)` explicit-site validation remains unchanged.
- Existing thread-list parsing, direct thread-detail parsing, response diagnostics, direct thread ID/text/count/creator/time/category validation, collection initialization, loaded-collection lookup, lazy `ForumCategory.threads`, direct and batched thread acquisition, lazy `ForumThread.posts`, `ForumThread.reply(...)`, forum category/post/revision behavior, and adjacent site/forum workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Reusing the collection validator could accidentally weaken collection-site validation. Mitigation: the existing collection malformed-site test stayed green, and the helper still raises `ValueError("site must be a Site")`.
- Risk: Constructor validation could be confused with live-site validation. Mitigation: this change only checks the local parent object type and does not contact Wikidot, validate permissions, or change authentication behavior.
- Risk: Tests could drift back to arbitrary site-like mocks. Mitigation: valid thread tests already use real `Site` fixtures, and malformed cases are explicit unit-level invalid inputs.

## Dependencies

- Valid category thread-list parser output continues to be created from a real `Site` object supplied to the parser.
- Existing `Site` constructor validation remains responsible for site scalar fields such as `id`, `title`, `unix_name`, `domain`, and `ssl_supported`.
- Existing forum write-input validation remains responsible for `ForumThread.reply(...)` source, title, and parent-post ID inputs.

## Open Questions

None for this local slice. Post-construction mutation revalidation remains outside scope, matching adjacent constructor-only record-field validations such as `Page.site` and `ForumCategory.site`.

## Upstream-Safe Motivation

`ForumThread.site` is the parent object behind browser-free thread inventories, thread URLs, direct thread-detail reads, reply action routing, diagnostics, downstream post/revision reads, and generated forum ledgers. Parser paths already pass a real `Site` object into created thread rows. Constructor validation keeps malformed local parent state out of manually constructed or rehydrated records without changing thread acquisition, parser selectors, reply payloads, returned-status handling, cache behavior, post acquisition, or live Wikidot interactions.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work repeatedly used browser-free category thread-list reads, direct thread-detail reads, cached thread inventories, reply workflows, generated forum inventory ledgers, forum migration checks, moderation tooling, and tests that construct `ForumThread` records directly.
- Existing local drafts covered forum-thread fetch retry behavior, parser row scoping, response-body diagnostics, parser count/user/timestamp diagnostics, reply input validation, collection search-key validation, collection constructor validation, collection parent-site validation, direct thread ID/text/count/creator/time/category validation, and forum-post parent-thread validation, but did not cover direct `ForumThread(site=...)` construction.
- The focused RED failures showed invalid constructor site values were accepted as dataclass state. The GREEN regressions cover missing, boolean, string, dictionary, and arbitrary object values.
- This slice only validates stored forum-thread parent type at construction. It does not change category thread-list acquisition, direct thread-detail acquisition, parser selectors, response-body diagnostics, ID parsing, title parsing, description parsing, count parsing, creator/time parsing, collection initialization, `find(...)`, lazy `ForumCategory.threads`, `ForumThread.posts`, `ForumThread.reply(...)`, forum category/post/revision behavior, live site behavior, or client authentication.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, forum source text, page source text, private messages, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed parent objects instead of accepting site-like mocks or dictionaries. Tests and downstream callers should construct a real `Site` object and stub network-facing request methods when unit-level isolation is needed.
