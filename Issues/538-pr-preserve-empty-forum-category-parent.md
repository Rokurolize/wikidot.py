# PR Draft: Preserve Empty Forum Category Collection Parent State

## Summary

`ForumCategoryCollection(site=None, categories=[])` and the default `ForumCategoryCollection()` constructor were left with an incidental first-entry lookup after the earlier constructor-validation and explicit-parent-validation slices. Direct callers, fixture builders, generated forum category ledgers, migration audits, cached category-list setup, and downstream rehydration paths could hit `IndexError: list index out of range` before receiving a usable empty collection.

This change makes the empty no-parent state explicit by storing `self.site = None` and typing the collection parent as `Site | None`. Valid explicit `Site` parents, first-category parent inference, empty site-supplied collections, ID lookup, category-list acquisition, lazy site forum categories, category thread creation, thread-cache behavior, parser diagnostics, direct `ForumCategory` validation, and adjacent forum workflows remain unchanged.

## Outcome

Empty no-parent forum-category collections now expose the readable `site is None` sentinel instead of leaking a constructor-time `IndexError`.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum category inventories, generated forum migration ledgers, moderation or audit scripts, cached category inventories, lazy site forum categories, category-owned thread reads, or local tests that construct `ForumCategoryCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum category discovery and category-owned thread workflows as practical surfaces. Existing drafts [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-context.md](233-pr-forum-category-count-context.md), [326-pr-forum-category-response-body-type-context.md](326-pr-forum-category-response-body-type-context.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [407-pr-validate-forum-thread-create-result-id.md](407-pr-validate-forum-thread-create-result-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [434-pr-validate-forum-category-threads-assignments.md](434-pr-validate-forum-category-threads-assignments.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [453-pr-validate-forum-category-count-fields.md](453-pr-validate-forum-category-count-fields.md), [454-pr-validate-forum-category-text-fields.md](454-pr-validate-forum-category-text-fields.md), [476-pr-validate-forum-category-collection-site-field.md](476-pr-validate-forum-category-collection-site-field.md), [502-pr-validate-forum-category-site-field.md](502-pr-validate-forum-category-site-field.md), and [505-pr-validate-forum-category-threads-cache.md](505-pr-validate-forum-category-threads-cache.md) establish category discovery, parser diagnostics, response diagnostics, count parsing, lookup validation, collection entry validation, create-thread result handling, thread-cache validation, direct category field validation, explicit collection parent validation, direct category parent validation, and cached threads validation as active operational boundaries.

This is not a duplicate of Issue 476. Issue 476 validates non-`None` explicit collection parents and preserves `site=None` inference plus explicit-site empty construction, but it did not assert that an empty no-parent collection can be constructed and exposes a readable `site is None` sentinel. This slice repairs that direct-state gap without changing explicit parent validation, category-entry validation, category lookup, category acquisition, lazy cache behavior, or live Wikidot behavior.

No upstream issue was filed from this local workspace.

## Changes

- Assign `self.site = None` when `ForumCategoryCollection` is constructed with no site and no categories.
- Type the collection parent as `Site | None` to match supported constructor semantics.
- Preserve valid explicit parents, first-category parent inference, empty site-supplied collections, ID lookup, category-list acquisition, lazy forum categories, category thread creation, thread-cache behavior, parser diagnostics, direct category validation, and adjacent forum workflows.

## Type Of Change

- Contract repair
- Public collection constructor state hardening
- Forum category parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategoryCollection(site=None, categories=[])` and `ForumCategoryCollection()` must expose `site is None` and length 0 instead of raising `IndexError`. |
| R2 | `ForumCategoryCollection(site=<valid Site>, categories=[])` and `ForumCategoryCollection(site=<valid Site>, categories=[valid_category])` must remain valid. |
| R3 | `ForumCategoryCollection(site=None, categories=[valid_category])` must still infer the parent from the first category. |
| R4 | Existing malformed explicit parent validation from Issue 476 must continue to reject non-`Site` values with `ValueError("site must be a Site")`. |
| R5 | Category-list acquisition, lazy site forum categories, category thread creation, thread-cache behavior, parser diagnostics, lookup helpers, and adjacent forum workflows must remain unchanged. |
| R6 | Forum-category tests, adjacent forum workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Empty no-parent construction leaves a readable `site is None` state. | `test_init_empty_without_site_exposes_none_site` failed RED before the fix with `IndexError: list index out of range`, then passed GREEN after the constructor assigned `None`. | Raising `IndexError`, rejecting omitted input, missing `site`, or changing the empty collection length rejects this local completion claim. | ForumCategoryCollection constructor | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Explicit valid parent paths remain stable. | The focused constructor GREEN command covered existing explicit-site empty and populated construction tests. | Losing the explicit parent, changing valid empty-list behavior, or changing valid category-list construction rejects this local completion claim. | ForumCategoryCollection constructor | `tests/unit/test_forum_category.py` |
| R3 | First-category parent inference remains available. | Existing inference and adjacent category workflows stayed green through module, adjacent forum, and full unit coverage. | Rejecting omitted parents with non-empty categories or failing to preserve inferred parent state rejects this local completion claim. | ForumCategoryCollection constructor | `tests/unit/test_forum_category.py` |
| R4 | Existing malformed explicit parent preflight remains intact. | The focused constructor GREEN command covered malformed explicit parent cases, all still raising `ValueError("site must be a Site")`. | Accepting booleans, strings, dictionaries, arbitrary objects, or emitting malformed explicit parent state rejects this local completion claim. | Constructor validation | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R5 | Existing forum-category and adjacent forum workflows remain stable. | `tests/unit/test_forum_category.py` passed 91 tests and adjacent forum workflow tests passed 493 tests. | Regressing category-list acquisition, lazy site forum categories, create-thread behavior, thread-cache behavior, category lookup, parser diagnostics, forum thread/post behavior, or forum post revision workflows rejects this local completion claim. | Forum category and adjacent forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py` |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-category module passed, adjacent forum workflows passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic state and local mocks; this draft contains no credentials, cookies, auth JSON, raw response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, forum source text, private messages, page source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `6c102a5 fix(forum_category): preserve empty collection parent`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionInit::test_init_empty_without_site_exposes_none_site -q` failed before the fix with `IndexError: list index out of range`.
- GREEN focused constructor coverage: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionInit -q` passed 22 tests.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 91 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 493 tests.
- `uv run pytest tests/unit -q` passed 2556 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumCategoryCollection(site=None, categories=[])` and `ForumCategoryCollection()` return an empty collection with `collection.site is None`.
- `ForumCategoryCollection(site=<valid Site>, categories=[])` keeps that explicit parent.
- `ForumCategoryCollection(site=<valid Site>, categories=[valid_category])` remains valid.
- `ForumCategoryCollection(site=None, categories=[valid_category])` still infers the parent from the first valid category.
- Malformed explicit parent values from Issue 476 still raise `ValueError("site must be a Site")`.
- Existing valid `ForumCategory` lists, iteration, `find(...)`, category-list acquisition, lazy site forum categories, category thread creation, thread-cache behavior, parser-side category diagnostics, direct `ForumCategory` field validation, and adjacent forum workflows remain green.
- The tests use local synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, private forum data, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be mistaken for a broader collection consistency change. Mitigation: this slice only makes the default empty no-parent constructor readable and leaves acquisition behavior unchanged.
- Risk: Optional parent typing could be read as permission to use a parentless collection for remote category or thread operations. Mitigation: acquisition paths still construct collections with real sites, and this slice does not change request construction.
- Risk: This could be confused with Issue 476. Mitigation: Issue 476 validates malformed explicit non-`None` parent sites; this slice fixes the preserved empty no-parent branch.

## Out Of Scope

Changing category-list parsing, comparing collection parent identity with each contained category, coercing dictionaries into sites, rejecting `site=None`, changing direct acquisition, changing lazy forum-category behavior, changing live Wikidot behavior, changing forum thread/post contracts, and creating upstream Issues or PRs are outside this slice.

## Why This Matters

The empty no-parent state is useful for local fixtures, category ledgers, migration audits, and generated workflows that may construct a category collection before a concrete `Site` owner is attached. A readable `site is None` sentinel is easier to reason about than a default constructor that crashes before returning a collection.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used browser-free forum category acquisition, cached category inventories, category-owned thread reads, category ledgers, and tests that seed category collections directly.
- Issue 476 preserved `site=None` inference and explicit-site empty construction, but the fully empty no-parent constructor branch was not covered by an assertion and still indexed `self[0]`.
- The focused RED failure reproduced the constructor crash without live Wikidot access. The GREEN regression now proves the empty collection exposes the documented sentinel while the broader forum and repository gates prove adjacent behavior remains stable.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, forum source text, private messages, page source text, private content, private site data, and source text from real sites out of upstream discussion.
