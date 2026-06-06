# PR Draft: Validate ForumPost Identity And Text Fields

## Summary

`ForumPost` records carry the direct post ID, display title, and parsed HTML body text used by browser-free forum indexing, cached thread-post scans, source/revision fetches, edit workflows, migration ledgers, and moderation or translation review tooling. Earlier local slices validated parser-side post-list IDs and title spacing, direct parent-thread state, direct creator/time metadata, collection entries, collection initialization, collection search IDs, acquisition inputs, source response diagnostics, and write-side edit text inputs. The public `ForumPost(..., id=..., title=..., text=...)` dataclass constructor still accepted malformed direct values such as `None`, booleans, strings, floats, integers in text fields, and lists, letting callers create fixture, ledger, or rehydrated post records whose identity or displayed content fields were not the documented types.

This change validates `ForumPost.id`, `ForumPost.title`, and `ForumPost.text` at initialization. `id` now accepts only non-boolean integers. `title` and `text` now accept only strings through the shared `validate_text_field(...)` helper. Malformed values raise stable `ValueError` diagnostics: `id must be an integer`, `title must be a string`, and `text must be a string`. Valid post-list parsing, parser-side post ID/user/timestamp/edit-metadata diagnostics, direct thread validation, direct creator/time validation, collection validation, lazy source reads, lazy revision reads, edit behavior, and adjacent forum category/thread/revision workflows remain unchanged.

## Outcome

Callers cannot silently construct forum-post records with malformed IDs, titles, or body text, while parser-created posts and valid direct `ForumPost(...)` construction remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum indexing, discussion migration ledgers, moderation tooling, translation review tooling, cached thread-post scans, duplicate thread-post reads, `ForumThread.posts`, forum post source reads, forum post edit workflows, forum post revisions, local fixtures, or serialized/rehydrated post records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum-post reads and stored post records as practical workflow surfaces. Existing drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), [235-pr-forum-post-id-parse-context.md](235-pr-forum-post-id-parse-context.md), [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md), [296-pr-forum-post-list-timestamp-context.md](296-pr-forum-post-list-timestamp-context.md), [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md), [298-pr-forum-post-list-edit-timestamp-context.md](298-pr-forum-post-list-edit-timestamp-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), and [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md) establish forum post acquisition, retry behavior, duplicate handling, parser scoping, text fidelity, parser diagnostics, response diagnostics, source acquisition, edit preflight, public acquisition input validation, collection-entry validation, search-key validation, collection constructor integrity, parent-thread constructor validation, and creator/time constructor validation as active operational boundaries.

Those prior slices are not duplicates. Issue 235 validates malformed generated structural post IDs before parser-side `ForumPost` construction. Issue 109 preserves parser-side post title spacing. Issue 354 validates write-side source/title text passed into forum mutations. Issue 378 validates `ForumPostCollection.find(id=...)` lookup keys after a collection already exists. Issue 446 validates the separate public `ForumPost.thread` parent field. Issue 459 validates the separate public `ForumPost.created_by` and `ForumPost.created_at` metadata fields. This slice validates the separate public dataclass `ForumPost.id`, `ForumPost.title`, and `ForumPost.text` fields so malformed identity/text values cannot become stored record state in manually constructed posts, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [235-pr-forum-post-id-parse-context.md](235-pr-forum-post-id-parse-context.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), and the adjacent direct record-field patterns from [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), [456-pr-validate-forum-thread-text-fields.md](456-pr-validate-forum-thread-text-fields.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), and [454-pr-validate-forum-category-text-fields.md](454-pr-validate-forum-category-text-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumPost.id` validation at dataclass initialization.
- Add `ForumPost.title` validation at dataclass initialization.
- Add `ForumPost.text` validation at dataclass initialization.
- Reject non-integer and boolean IDs with `ValueError("id must be an integer")`.
- Reject non-string titles with `ValueError("title must be a string")`.
- Reject non-string body text with `ValueError("text must be a string")`.
- Preserve parser-created posts, direct parent-thread validation, creator/time validation, source acquisition, revision acquisition, edit behavior, and adjacent forum behavior.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum-post identity/text state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPost(id=None)`, `True`, `"5001"`, and `5001.0` must raise `ValueError("id must be an integer")` before storing record state. |
| R2 | `ForumPost(title=None)`, `True`, `5001`, and `["Test Post Title"]` must raise `ValueError("title must be a string")` before storing record state. |
| R3 | `ForumPost(text=None)`, `True`, `5001`, and `["<p>Test post content</p>"]` must raise `ValueError("text must be a string")` before storing record state. |
| R4 | Valid integer IDs and valid string title/text fields must remain valid and preserve stored values. |
| R5 | Existing post-list parsing, parser-side ID/user/timestamp/edit-metadata diagnostics, direct thread validation, direct creator/time validation, collection initialization, collection search validation, lazy source reads, lazy revision reads, edit behavior, and adjacent forum category/thread/revision workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, forum-post tests, adjacent forum tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor IDs fail at the public dataclass boundary. | `TestForumPostBasic.test_init_rejects_malformed_id` failed RED for 4 malformed values because the constructor did not raise, then passed GREEN after ID validation was added. | Accepting missing values, booleans, strings, floats, arbitrary objects, or emitting post records with non-integer IDs rejects this local completion claim. | ForumPost constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Malformed constructor titles fail at the public dataclass boundary. | `TestForumPostBasic.test_init_rejects_malformed_title` failed RED for 4 malformed values because the constructor did not raise, then passed GREEN after title validation was added. | Accepting missing values, booleans, integers, lists, arbitrary objects, or emitting post records with non-string titles rejects this local completion claim. | ForumPost constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Malformed constructor body text fails at the public dataclass boundary. | `TestForumPostBasic.test_init_rejects_malformed_text` failed RED for 4 malformed values because the constructor did not raise, then passed GREEN after text validation was added. | Accepting missing values, booleans, integers, lists, arbitrary objects, or emitting post records with non-string body text rejects this local completion claim. | ForumPost constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R4 | Valid identity/text semantics stay green. | Existing valid constructor coverage, string representation coverage, parser-created post coverage, source tests, revision tests, and edit tests passed. | Rejecting valid non-boolean integer IDs, changing stored titles, changing stored post body HTML text, or coercing values rejects this local completion claim. | Parser-created and manually created posts | `tests/unit/test_forum_post.py` |
| R5 | Existing forum-post and adjacent forum workflows remain green. | `tests/unit/test_forum_post.py` passed 121 tests, adjacent forum tests passed 398 tests, and full unit tests passed 1808 tests. | Regressing post-list parsing, parser ID/user/timestamp/edit-metadata diagnostics, source acquisition, lazy revision acquisition, edit behavior, parent-thread validation, creator/time validation, collection validation, forum category behavior, forum thread behavior, or forum post revision behavior rejects this local completion claim. | Forum post and adjacent forum workflows | `tests/unit/test_forum_post.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, post titles from real sites, post bodies from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-post tests passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `27d8c52 fix(forum_post): validate post identity fields`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_id tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_title tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_text -q` failed 12 tests before the fix; every malformed `id`, `title`, and `text` value reported `DID NOT RAISE`.
- GREEN: the same focused command passed 12 tests after ID/title/text validation was added.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 121 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 398 tests.
- `uv run pytest tests/unit -q` passed 1808 tests.
- `uv run ruff check src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed.
- `uv run ruff format --check src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed with 2 files already formatted.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed with no issues in 2 source files.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `uv run pyright src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 61 existing full-tree typing errors outside this slice, including page fixture `None` mismatches, intentional invalid-input test calls, requestutil response narrowing issues, invalid `SearchPagesQuery` parameter calls, and site test mock typing issues. The changed source file and changed forum-post test file pass pyright together.

## Acceptance Criteria

- `ForumPost(id=None)`, `True`, `"5001"`, and `5001.0` raise `ValueError("id must be an integer")`.
- `ForumPost(title=None)`, `True`, `5001`, and `["Test Post Title"]` raise `ValueError("title must be a string")`.
- `ForumPost(text=None)`, `True`, `5001`, and `["<p>Test post content</p>"]` raise `ValueError("text must be a string")`.
- Valid non-boolean integer IDs remain valid.
- Valid string titles and body text remain valid and are not normalized or coerced.
- Existing post-list parsing, parser-side ID/user/timestamp/edit-metadata diagnostics, direct parent-thread validation, direct creator/time validation, collection search validation, collection initialization, `ForumPost.source`, `ForumPost.revisions`, `ForumPost.edit(...)`, and adjacent forum category/thread/revision workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPost.id`, `ForumPost.title`, and `ForumPost.text` are durable record fields behind browser-free forum indexing, post-list reads, generated migration ledgers, moderation summaries, cached thread-post scans, duplicate thread-post reuse, source reads, edit workflows, revision traversal, and downstream forum audit tooling. Parser paths already produce integer IDs and string title/body values and report malformed generated structural IDs with context; the record constructor should apply the same invariant so fixture-created or rehydrated posts cannot carry malformed identity/text state into logs, generated ledgers, migration comparisons, display summaries, cache keys, or downstream tools.

## Local Evidence

- Local rollout evidence used browser-free forum indexing, generated moderation ledgers, translation review tooling, forum migration checks, cached thread-post scans, duplicate thread-post reads, lazy source reads, edit workflows, revision traversal, and tests that seed forum-post records directly.
- Existing local drafts covered forum post fetch retry behavior, duplicate thread-post reduction, parser scoping, parser-side ID/user/timestamp/edit-metadata diagnostics, title text fidelity, response diagnostics, public acquisition input validation, collection entry validation, collection search-key validation, collection constructor validation, direct parent-thread validation, and direct creator/time validation, but did not cover direct `ForumPost(id=..., title=..., text=...)` construction.
- The focused RED failures showed invalid constructor post ID/title/text values were accepted as dataclass state. The GREEN regressions cover missing, boolean, string, float, integer-in-text-field, and list values.
- This slice only validates stored forum-post ID/title/text types at construction. It does not change post-list acquisition, parser selectors, title parsing, body parsing, created metadata parsing, edit metadata parsing, collection initialization, `find(...)`, source acquisition, revision acquisition, edit behavior, forum category behavior, forum thread behavior, forum post revision behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, post titles from real sites, post bodies from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates type only. It does not reject empty strings, trim values, parse numeric strings into integers, require positive IDs, normalize HTML, or add source-level validation for `_source`; those would be separate behavior changes with separate parser or workflow evidence.
