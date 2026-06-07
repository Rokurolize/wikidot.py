# PR Draft: Validate ForumCategoryCollection Acquire Site Argument

## Summary

`ForumCategoryCollection.acquire_all(site)`, also exposed through `site.forum.categories`, is the browser-free forum category inventory read boundary. Earlier local slices validated category-list retries, nested-table scoping, title and description spacing, parser context, exhausted-retry diagnostics, response-body diagnostics, count parsing, collection construction, collection parent state, direct `ForumCategory.site`, and empty collection parent state. One adjacent public read-input gap remained: direct calls such as `ForumCategoryCollection.acquire_all(None)`, `"test-site"`, dictionaries, booleans, or arbitrary objects reached `site.amc_request_with_retry(...)` and leaked raw `AttributeError`.

This change reuses the existing `_validate_forum_category_site(...)` helper at the `ForumCategoryCollection.acquire_all(...)` entry point before any category-list request work. Malformed direct `site` arguments now raise `ValueError("site must be a Site")` deterministically, while valid category acquisition, request payloads, retry-exhausted diagnostics, response-body diagnostics, parser diagnostics, returned category parent state, and adjacent forum workflows remain unchanged.

## Outcome

Direct forum-category inventory callers now get the same deterministic parent-site preflight used by stored forum-category records and explicit category-collection parents, instead of incidental attribute errors from malformed call inputs.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call `ForumCategoryCollection.acquire_all(site)` directly, use `site.forum.categories`, or build generated forum inventories where a malformed deserialized or fixture-provided parent site should fail before AMC request construction.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum category discovery as a practical workflow surface and as the starting point for category-owned thread, post, and revision traversal. Existing drafts [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [476-pr-validate-forum-category-collection-site-field.md](476-pr-validate-forum-category-collection-site-field.md), [502-pr-validate-forum-category-site-field.md](502-pr-validate-forum-category-site-field.md), [505-pr-validate-forum-category-threads-cache.md](505-pr-validate-forum-category-threads-cache.md), and [538-pr-preserve-empty-forum-category-parent.md](538-pr-preserve-empty-forum-category-parent.md) establish category-list acquisition, parser diagnostics, response diagnostics, direct record state, cache state, collection state, and empty parent behavior as active operational boundaries.

This is not a duplicate of Issue 502. Issue 502 validates direct `ForumCategory(site=...)` construction after category records already exist or are manually rehydrated. This slice validates the caller-provided `site` argument to the static `ForumCategoryCollection.acquire_all(site)` read helper before request work.

No upstream issue was filed from this local workspace.

## Changes

- Add a focused regression for malformed direct `ForumCategoryCollection.acquire_all(site=...)` inputs.
- Validate the `site` argument with `_validate_forum_category_site(...)` before `amc_request_with_retry(...)`.
- Preserve valid category-list request payloads, retry-exhausted diagnostics, response-body diagnostics, parser diagnostics, returned category parent state, `site.forum.categories`, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public read-boundary hardening
- Forum category inventory preflight
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategoryCollection.acquire_all(None)`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` must raise `ValueError("site must be a Site")` before category-list request work. |
| R2 | Valid `ForumCategoryCollection.acquire_all(site)` acquisition, request payloads, retry-exhausted diagnostics, response-body diagnostics, parser diagnostics, and returned `ForumCategory.site` parent state must remain unchanged. |
| R3 | `site.forum.categories`, category collection construction, direct `ForumCategory` construction, thread-cache behavior, and adjacent forum thread/post/revision workflows must remain unchanged. |
| R4 | Forum category, adjacent forum, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct category-list `site` inputs fail at the public read boundary. | `TestForumCategoryCollectionAcquireAll.test_acquire_all_rejects_malformed_site_before_request` failed RED for all 5 malformed values with raw `AttributeError`, then passed GREEN after validation was added. | Reaching `site.amc_request_with_retry`, accepting site-like dictionaries, returning an empty collection, or leaking raw attribute errors rejects this local completion claim. | `ForumCategoryCollection.acquire_all(...)` | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Valid category-list acquisition remains stable. | Focused GREEN included `test_acquire_all_success`; the full forum-category test file passed 96 tests. | Changing request module names, retry behavior, parser output, response diagnostics, or returned category parent state rejects this local completion claim. | Forum category list reads | `tests/unit/test_forum_category.py` |
| R3 | Adjacent forum workflows remain stable. | Adjacent forum category/thread/post/revision tests passed 499 tests. | Regressing `site.forum.categories`, category-owned thread reads, post reads, revision reads, collection construction, record construction, or cache behavior rejects this local completion claim. | Forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py` |
| R4 | Existing repository quality gates remain green. | Full unit tests passed 2568 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, and full pyright passed with 0 errors, 0 warnings, and 0 informations. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic state; this draft contains no credentials, cookies, auth JSON, raw response bodies, private forum content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, forum source text, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `64b928a fix(forum_category): validate category list site`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_rejects_malformed_site_before_request -q` failed 5 tests before the fix because malformed sites reached `site.amc_request_with_retry(...)` and leaked raw `AttributeError`.
- GREEN focused: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_rejects_malformed_site_before_request tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_success -q` passed 6 tests.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 96 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 499 tests.
- `uv run pytest tests/unit -q` passed 2568 tests.
- `uv run ruff check src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed.
- `uv run ruff format --check src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy .` passed with no issues in 87 source files.
- `uv run pyright .` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- Malformed direct `ForumCategoryCollection.acquire_all(site=...)` inputs raise `ValueError("site must be a Site")`.
- Valid category-list reads, request payloads, retry-exhausted diagnostics, response diagnostics, parser diagnostics, and returned category parent state stay unchanged.
- Adjacent forum category/thread/post/revision workflows stay green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: The new validation could reject existing valid test fixtures if the helper accepted structural site-like mocks. Mitigation: existing valid fixtures use real `Site` instances, and focused plus full forum-category tests passed.
- Risk: This could obscure response or parser diagnostics. Mitigation: validation only runs before request work for malformed parent objects; valid-site response and parser diagnostics remain covered by the existing category acquisition tests.

## Dependencies

- Existing `_validate_forum_category_site(...)` remains the canonical local parent-site validator.
- Existing `Site` constructor validation remains responsible for site scalar fields such as `id`, `title`, `unix_name`, `domain`, and `ssl_supported`.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`ForumCategoryCollection.acquire_all(...)` is the direct read entry point behind browser-free forum category discovery. Validating the supplied parent `Site` before request work gives generated callers and fixtures deterministic errors for malformed inputs without changing live Wikidot behavior, request shape, retries, parsing, diagnostics, or downstream forum traversal.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed malformed direct `site` arguments crossing the public static read boundary and leaking `AttributeError` from `site.amc_request_with_retry`.
- This slice only validates the `ForumCategoryCollection.acquire_all(...)` caller-provided parent type. It does not change category-list acquisition, parser selectors, response-body diagnostics, category ID/title/description/count parsing, collection initialization, direct category field validation, lazy `site.forum.categories`, `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, forum thread/post/revision behavior, live site behavior, or client authentication.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, forum source text, private messages, and private site data out of upstream discussion.
