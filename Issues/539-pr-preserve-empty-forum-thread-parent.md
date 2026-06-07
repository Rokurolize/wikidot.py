# PR Draft: Preserve Empty Forum Thread Collection Parent State

## Summary

`ForumThreadCollection(site=None, threads=[])` and the default `ForumThreadCollection()` constructor were left with an incidental first-entry lookup after the earlier constructor-validation and explicit-parent-validation slices. Direct callers, fixture builders, generated forum thread ledgers, migration audits, cached thread-list setup, and downstream rehydration paths could hit `IndexError: list index out of range` before receiving a usable empty collection.

This change makes the empty no-parent state explicit by storing `self.site = None` and typing the collection parent as `Site | None`. Valid explicit `Site` parents, first-thread parent inference, empty site-supplied collections, ID lookup, category thread-list acquisition, direct thread-detail acquisition, lazy category threads, reply/create workflows, parser diagnostics, direct `ForumThread` validation, and adjacent forum workflows remain unchanged.

## Outcome

Empty no-parent forum-thread collections now expose the readable `site is None` sentinel instead of leaking a constructor-time `IndexError`.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum thread inventories, generated discussion migration ledgers, moderation or audit scripts, cached thread inventories, lazy category threads, direct thread lookups, or local tests that construct `ForumThreadCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum thread list and direct thread-detail workflows as practical surfaces. Existing drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [170-pr-forum-thread-detail-fetch-failure-context.md](170-pr-forum-thread-detail-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [292-pr-forum-thread-list-user-context.md](292-pr-forum-thread-list-user-context.md), [323-pr-forum-thread-list-response-body-type-context.md](323-pr-forum-thread-list-response-body-type-context.md), [324-pr-forum-thread-detail-response-body-type-context.md](324-pr-forum-thread-detail-response-body-type-context.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), [456-pr-validate-forum-thread-text-fields.md](456-pr-validate-forum-thread-text-fields.md), [457-pr-validate-forum-thread-post-count.md](457-pr-validate-forum-thread-post-count.md), [458-pr-validate-forum-thread-creator-timestamp.md](458-pr-validate-forum-thread-creator-timestamp.md), [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md), [503-pr-validate-forum-thread-site-field.md](503-pr-validate-forum-thread-site-field.md), and [504-pr-validate-forum-thread-posts-cache.md](504-pr-validate-forum-thread-posts-cache.md) establish thread-list reads, direct detail reads, parser diagnostics, response diagnostics, duplicate cache reuse, lookup validation, collection entry validation, direct thread field validation, explicit collection parent validation, direct thread parent validation, and cached posts validation as active operational boundaries.

This is not a duplicate of Issue 475. Issue 475 validates non-`None` explicit collection parents and preserves `site=None` inference plus explicit-site empty construction, but it did not assert that an empty no-parent collection can be constructed and exposes a readable `site is None` sentinel. This slice repairs that direct-state gap without changing explicit parent validation, thread-entry validation, thread lookup, acquisition, lazy cache behavior, or live Wikidot behavior.

No upstream issue was filed from this local workspace.

## Changes

- Assign `self.site = None` when `ForumThreadCollection` is constructed with no site and no threads.
- Type the collection parent as `Site | None` to match supported constructor semantics.
- Preserve valid explicit parents, first-thread parent inference, empty site-supplied collections, ID lookup, category thread-list acquisition, direct thread-detail acquisition, lazy category threads, reply/create workflows, parser diagnostics, direct thread validation, and adjacent forum workflows.

## Type Of Change

- Contract repair
- Public collection constructor state hardening
- Forum thread parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThreadCollection(site=None, threads=[])` and `ForumThreadCollection()` must expose `site is None` and length 0 instead of raising `IndexError`. |
| R2 | `ForumThreadCollection(site=<valid Site>, threads=[])` and `ForumThreadCollection(site=<valid Site>, threads=[valid_thread])` must remain valid. |
| R3 | `ForumThreadCollection(site=None, threads=[valid_thread])` must still infer the parent from the first thread. |
| R4 | Existing malformed explicit parent validation from Issue 475 must continue to reject non-`Site` values with `ValueError("site must be a Site")`. |
| R5 | Category thread-list acquisition, direct thread-detail acquisition, lazy category threads, reply/create behavior, parser diagnostics, lookup helpers, and adjacent forum workflows must remain unchanged. |
| R6 | Forum-thread tests, adjacent forum workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Empty no-parent construction leaves a readable `site is None` state. | `test_init_empty_without_site_exposes_none_site` failed RED before the fix with `IndexError: list index out of range`, then passed GREEN after the constructor assigned `None`. | Raising `IndexError`, rejecting omitted input, missing `site`, or changing the empty collection length rejects this local completion claim. | ForumThreadCollection constructor | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Explicit valid parent paths remain stable. | The focused constructor GREEN command covered existing explicit-site empty and populated construction tests. | Losing the explicit parent, changing valid empty-list behavior, or changing valid thread-list construction rejects this local completion claim. | ForumThreadCollection constructor | `tests/unit/test_forum_thread.py` |
| R3 | First-thread parent inference remains available. | The focused constructor GREEN command covered `test_init_infers_site_from_threads`. | Rejecting omitted parents with non-empty threads or failing to preserve inferred parent state rejects this local completion claim. | ForumThreadCollection constructor | `tests/unit/test_forum_thread.py` |
| R4 | Existing malformed explicit parent preflight remains intact. | The focused constructor GREEN command covered malformed explicit parent cases, all still raising `ValueError("site must be a Site")`. | Accepting booleans, strings, dictionaries, arbitrary objects, or emitting malformed explicit parent state rejects this local completion claim. | Constructor validation | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R5 | Existing forum-thread and adjacent forum workflows remain stable. | `tests/unit/test_forum_thread.py` passed 133 tests and adjacent forum workflow tests passed 494 tests. | Regressing category thread-list acquisition, direct thread-detail acquisition, lazy category threads, reply/create behavior, thread lookup, parser diagnostics, forum category/post behavior, or forum post revision workflows rejects this local completion claim. | Forum thread and adjacent forum workflows | `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py` |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-thread module passed, adjacent forum workflows passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic state and local mocks; this draft contains no credentials, cookies, auth JSON, raw response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, forum source text, private messages, page source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `7ce2be9 fix(forum_thread): preserve empty collection parent`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_init_empty_without_site_exposes_none_site -q` failed before the fix with `IndexError: list index out of range`.
- GREEN focused constructor coverage: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionInit -q` passed 23 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 133 tests.
- `uv run pytest tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 494 tests.
- `uv run pytest tests/unit -q` passed 2557 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThreadCollection(site=None, threads=[])` and `ForumThreadCollection()` return an empty collection with `collection.site is None`.
- `ForumThreadCollection(site=<valid Site>, threads=[])` keeps that explicit parent.
- `ForumThreadCollection(site=<valid Site>, threads=[valid_thread])` remains valid.
- `ForumThreadCollection(site=None, threads=[valid_thread])` still infers the parent from the first valid thread.
- Malformed explicit parent values from Issue 475 still raise `ValueError("site must be a Site")`.
- Existing valid `ForumThread` lists, iteration, `find(...)`, category thread-list acquisition, direct thread-detail acquisition, lazy category threads, reply/create behavior, parser-side thread diagnostics, direct `ForumThread` field validation, and adjacent forum workflows remain green.
- The tests use local synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, private forum data, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be mistaken for a broader collection consistency change. Mitigation: this slice only makes the default empty no-parent constructor readable and leaves acquisition behavior unchanged.
- Risk: Optional parent typing could be read as permission to use a parentless collection for remote thread or post operations. Mitigation: acquisition paths still construct collections with real sites, and this slice does not change request construction.
- Risk: This could be confused with Issue 475. Mitigation: Issue 475 validates malformed explicit non-`None` parent sites; this slice fixes the preserved empty no-parent branch.

## Out Of Scope

Changing thread-list parsing, comparing collection parent identity with each contained thread, coercing dictionaries into sites, rejecting `site=None`, changing direct acquisition, changing lazy category-thread behavior, changing live Wikidot behavior, changing forum category/post contracts, and creating upstream Issues or PRs are outside this slice.

## Why This Matters

The empty no-parent state is useful for local fixtures, thread ledgers, migration audits, and generated workflows that may construct a thread collection before a concrete `Site` owner is attached. A readable `site is None` sentinel is easier to reason about than a default constructor that crashes before returning a collection.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used browser-free forum thread-list acquisition, direct thread-detail reads, cached thread inventories, category-owned thread reads, thread ledgers, and tests that seed thread collections directly.
- Issue 475 preserved `site=None` inference and explicit-site empty construction, but the fully empty no-parent constructor branch was not covered by an assertion and still indexed `self[0]`.
- The focused RED failure reproduced the constructor crash without live Wikidot access. The GREEN regression now proves the empty collection exposes the documented sentinel while the broader forum and repository gates prove adjacent behavior remains stable.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, forum source text, private messages, page source text, private content, private site data, and source text from real sites out of upstream discussion.
