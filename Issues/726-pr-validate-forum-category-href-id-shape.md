# PR Draft: Validate Forum Category Href ID Shape

## Summary

`ForumCategoryCollection.acquire_all(...)`, exposed through `site.forum.categories`, parses category links returned by `forum/ForumStartModule` and uses the link's `c-<id>` path segment as `ForumCategory.id`. Earlier parser hardening made missing category IDs diagnosable, but the extraction still searched for any `c-<digits>` substring. A malformed generated href such as `/forum/c-1001-latest/test-category` was therefore accepted as category ID `1001`.

This change treats `c-<digits>` as a category ID only when it is a complete URL path segment, with optional query/hash/end delimiters. Digit-bearing malformed hrefs now raise `NoElementException` with site, structural row, field, and raw href context before constructing `ForumCategory`.

## Outcome

Forum category acquisition no longer fabricates category IDs from malformed generated hrefs. Valid category links such as `/forum/c-1001/test-category` still parse the same category IDs, and missing ID links keep the existing `Category ID is not found ...` diagnostic.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum category discovery, generated forum inventory ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, `site.forum.categories`, or local fixtures where category identity must come from structurally valid Wikidot category links.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum category discovery as a practical read-heavy workflow and as the entry point for category-owned thread, post, and revision traversal. Existing drafts cover retry-aware category-list fetching, nested-table scoping, title/description text fidelity, row-level parser context, response-body diagnostics, count parsing, collection initialization, direct category ID validation, retained category ID validation, and category-thread acquisition ID validation.

This slice is not a duplicate of [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [644-pr-validate-non-negative-forum-category-ids.md](644-pr-validate-non-negative-forum-category-ids.md), [670-pr-validate-forum-category-collection-retained-id-state.md](670-pr-validate-forum-category-collection-retained-id-state.md), or [681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md](681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md). Issue 157 covers missing category ID elements and row context, Issue 233 covers count-cell parsing, Issues 452 and 644 cover direct `ForumCategory(id=...)` construction, and Issues 670 and 681 cover retained category ID state after valid category objects already exist. This slice covers generated category-list href parsing before `ForumCategory` construction.

No upstream issue was filed from this local workspace.

## Changes

- Add a focused helper for forum category href ID parsing.
- Accept category IDs only from a complete `c-<digits>` URL path segment, preserving valid `/forum/c-1001/test-category` links.
- Reject digit-bearing malformed category hrefs, such as `/forum/c-1001-latest/test-category`, with `NoElementException` containing site, structural row, `field=id`, and raw href value.
- Preserve the existing missing-ID `Category ID is not found ...` diagnostic.
- Preserve successful category-list parsing, retry behavior, response-body validation, nested-table filtering, title/description text fidelity, count parsing, collection semantics, category thread reads, and create-thread behavior.

## Type Of Change

- Parser hardening
- Forum category identity validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated forum category href containing `c-<digits>` plus trailing path-segment text, such as `/forum/c-1001-latest/test-category`, must fail before constructing `ForumCategory`. |
| R2 | The malformed category-ID error must identify site, structural category row, `field=id`, and the raw href value. |
| R3 | Valid generated category hrefs must continue to parse into the same `ForumCategory.id` values. |
| R4 | Missing category-ID hrefs must keep the existing `Category ID is not found ...` diagnostic. |
| R5 | Existing category-list parser behavior, retry handling, response-body diagnostics, nested-table filtering, title/description extraction, count parsing, collection behavior, category thread reads, and create-thread behavior must remain unchanged. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum names, raw generated HTML, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `/forum/c-1001-latest/test-category` fails instead of becoming category ID `1001`. | `test_acquire_all_malformed_category_id_includes_site_context` failed RED with `DID NOT RAISE`, then passed GREEN after strict path-segment category ID parsing was added. | Returning a `ForumCategory`, extracting the first digit run, or silently dropping trailing href text rejects this local completion claim. | Forum category generated parser | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | The malformed href diagnostic includes the structural context and observed value. | The regression matches `Category ID is malformed for site: test-site (row=1, field=id, value=/forum/c-1001-latest/test-category)`. | Omitting site, row, field, or raw href value rejects this local completion claim. | Forum category ID diagnostics | `tests/unit/test_forum_category.py` |
| R3 | Valid category links still parse. | `test_acquire_all_success`, `tests/unit/test_forum_category.py`, and adjacent forum coverage passed with existing valid `/forum/c-1001/test-category` fixtures. | Rejecting valid category links or changing parsed category IDs rejects this local completion claim. | Successful category acquisition | `tests/unit/test_forum_category.py` |
| R4 | Existing missing-ID behavior remains distinct from malformed digit-bearing hrefs. | Source inspection shows hrefs without a strict `c-<digits>` segment and without a digit-bearing malformed `c-...` segment still raise `Category ID is not found ...` with the existing row context. | Reclassifying no-ID links as malformed digit-bearing links or dropping the row context rejects this local completion claim. | Existing parser diagnostic compatibility | `src/wikidot/module/forum_category.py` |
| R5 | Adjacent repository behavior stays green. | Full unit, ruff, ruff format, mypy, pyright, and `git diff --check` passed. | Any test, lint, format, type, or whitespace failure rejects this local completion claim. | Repository quality gates | `tests/unit`, `src`, `tests` |
| R6 | No private or live-site material is needed. | The regression mutates a synthetic unit fixture and uses mocks only. | Using credentials, cookies, auth JSON, live Wikidot actions, raw private generated HTML, private forum names, upstream Issues, upstream PRs, or pushes rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `1934631 fix(forum_category): validate category href ids`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_malformed_category_id_includes_site_context -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_malformed_category_id_includes_site_context tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_success tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_malformed_row_includes_site_context tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_malformed_count_includes_site_context -q` passed 5 tests.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 141 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 885 tests.
- `uv run pytest tests/unit -q` passed 3599 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumCategoryCollection.acquire_all(...)` raises `NoElementException` for a category href such as `/forum/c-1001-latest/test-category`.
- The exception includes site `unix_name`, structural category row number, `field=id`, and the raw href value.
- Valid category hrefs with a complete `c-<digits>` path segment still parse the same category IDs.
- Hrefs without any category ID keep the existing `Category ID is not found ...` parser diagnostic.
- Successful category parsing, retry behavior, empty-result behavior, response-body validation, nested category-table filtering, title and description text spacing, count parsing, collection initialization, `find(...)`, lazy `site.forum.categories`, `ForumCategory.threads`, `reload_threads(...)`, and `create_thread(...)` remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Category links may include query strings or fragments. Mitigation: the helper accepts `c-<digits>` followed by `/`, `?`, `#`, or end of string.
- Risk: Overly loose parsing could continue accepting malformed hrefs. Mitigation: the helper requires the ID marker to be a complete path segment instead of searching for any digit run.
- Risk: This could be confused with direct category ID validation. Mitigation: Issues 452, 644, 670, and 681 cover direct or retained category IDs after object construction; this slice validates generated href input before construction.

## Dependencies

- Existing `ForumCategoryCollection.acquire_all(...)` request construction, retry helper usage, response-body validation, row selection, and count parsing remain unchanged.
- Existing `ForumCategory` constructor validation remains responsible for direct local record construction.
- Existing `NoElementException` remains the generated-parser exception for malformed category-list fields.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice. Future work should continue with fresh duplicate-checked parser boundaries, public input validation, result ergonomics, or measured complexity candidates outside this forum category href ID-shape path.

## Upstream-Safe Motivation

`ForumCategory.id` is durable identity metadata for browser-free forum inventories, moderation summaries, migration checks, cached category ledgers, and category-owned thread traversal. A generated category href with trailing text in the ID segment should not be accepted merely because it contains a `c-<digits>` substring. Path-segment validation keeps malformed Wikidot module output visible while preserving valid category rows.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established forum category discovery as a practical workflow through retry-aware fetching, parser scoping, nested-table filtering, response-body validation, title/description text fidelity, direct category constructor validation, retained category ID validation, and adjacent forum traversal workflows.
- Existing local drafts covered missing category ID diagnostics, count parsing diagnostics, direct category ID type/range validation, and retained category ID validation; they did not reject digit-bearing malformed generated hrefs before construction.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated forum-start HTML, private forum names, saved page contents, and private edit comments out of upstream discussion.
