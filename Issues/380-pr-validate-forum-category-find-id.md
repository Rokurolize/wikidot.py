# PR Draft: Validate ForumCategoryCollection Search IDs

## Summary

`ForumCategoryCollection.find(id)` documents `id` as an integer, but malformed caller-provided search keys were not rejected at the public collection lookup boundary. Values such as `None` and strings were treated as ordinary misses, while floats could compare equal to stored integer category IDs and booleans remain a Python `int` subclass.

This change validates the search key before scanning stored forum categories. Malformed `id` values now raise `ValueError("id must be an integer")`. Existing valid lookup behavior and valid not-found behavior remain unchanged for non-boolean integer category IDs.

## Outcome

Forum category collection callers now get deterministic Python-side preflight validation for malformed category search IDs instead of misleading misses, accidental float equality matches, or boolean/int comparison surprises.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum category discovery for moderation ledgers, translation review tooling, forum migration checks, archival jobs, local indexing, generated workflows, cached category scans, thread inventory bootstrapping, or source-preserving forum transformations.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum category discovery as a practical read surface and as the entry point for downstream thread, post, and revision workflows. Existing drafts [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [252-pr-forum-category-create-thread-action-status-context.md](252-pr-forum-category-create-thread-action-status-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), and [264-pr-forum-category-create-thread-cache-invalidation.md](264-pr-forum-category-create-thread-cache-invalidation.md) cover category-list acquisition, retry behavior, structural parser boundaries, text fidelity, response diagnostics, count parser diagnostics, category-owned thread access, cache behavior, and create-thread action diagnostics. Adjacent search preflight drafts [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md) and [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md) cover nearby forum collection lookup keys.

Those prior slices are not duplicates. They fetch, parse, cache, diagnose, or mutate category-adjacent forum workflows, but they do not validate the caller-provided search key to an already loaded `ForumCategoryCollection.find(...)` before scanning stored categories.

## Related Issue

Builds directly on the forum category discovery hardening line from [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), and the adjacent `find(...)` preflight pattern from [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `ForumCategoryCollection.find(id=...)` accepts only non-boolean integer IDs before scanning stored categories.
- Preserve valid `collection.find(1001)` behavior when a matching category exists.
- Preserve valid unknown integer behavior: a well-formed absent ID still returns `None`.
- Preserve forum category-list acquisition, parser diagnostics, response diagnostics, cached category collections, lazy `site.forum.categories`, lazy `ForumCategory.threads`, `ForumCategory.reload_threads()`, and `ForumCategory.create_thread(...)` semantics.

## Type Of Change

- Input validation
- Public API behavior hardening
- Forum category lookup preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategoryCollection.find(id=...)` must reject `None`, booleans, strings, floats, and other non-integer values with `ValueError("id must be an integer")` before scanning categories. |
| R2 | Valid lookup must remain unchanged for well-formed non-boolean integer IDs that match stored categories. |
| R3 | Valid not-found behavior must remain unchanged for well-formed non-boolean integer IDs that are absent from the collection. |
| R4 | Existing category-list acquisition, parser diagnostics, response diagnostics, cached collection reuse, lazy `site.forum.categories`, lazy `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumCategory.create_thread(...)`, forum thread reads, forum post reads, and forum post revision reads must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-category tests, adjacent forum tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed category IDs fail before collection iteration can compare them with stored category IDs. | `TestForumCategoryCollectionInit.test_find_rejects_non_integer_ids` failed RED before the fix for `None`, `True`, `"1001"`, and `1001.0`, then passed GREEN after validation was added. | Treating malformed IDs as ordinary misses, coercing values, scanning categories, or matching floats/booleans as integer IDs rejects this local completion claim. | Forum category ID search preflight | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Matching non-boolean integer search keys still return the stored `ForumCategory`. | Existing `test_find_existing` passed after validation was added. | Changing returned category identity, rejecting valid integer IDs, or comparing unrelated fields rejects this local completion claim. | Forum category collection lookup | `tests/unit/test_forum_category.py` |
| R3 | Missing non-boolean integer search keys still return `None`. | Existing `test_find_nonexistent` passed after validation was added. | Raising for a valid but absent integer ID or changing not-found behavior rejects this local completion claim. | Forum category collection lookup | `tests/unit/test_forum_category.py` |
| R4 | Adjacent forum behavior remains green. | `tests/unit/test_forum_category.py` passed 32 tests, adjacent forum tests passed 260 tests, and full unit tests passed 1094 tests. | Regressing category-list acquisition, category parser diagnostics, response diagnostics, nested table filtering, title/description spacing, category-owned thread reads, create-thread behavior, forum thread reads, post reads, or revision reads rejects this local completion claim. | Forum category workflow | affected forum-category, forum-thread, forum-post, and forum-post-revision tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum source, private forum content, private comments, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-category tests passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `22ecaf9 fix(forum_category): validate category search ids`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_forum_category.py::TestForumCategoryCollectionInit::test_find_rejects_non_integer_ids` failed 4 parameterized cases before the fix: malformed IDs did not raise, and comparison was reachable for every malformed value.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_forum_category.py::TestForumCategoryCollectionInit::test_find_rejects_non_integer_ids` passed 4 tests after adding ID search preflight.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_category.py` passed 32 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py` passed 260 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1094 tests.
- `.venv/bin/ruff check src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed.
- `.venv/bin/ruff format src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` left 2 files unchanged.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `collection.find(None)`, `collection.find(True)`, `collection.find("1001")`, and `collection.find(1001.0)` raise `ValueError("id must be an integer")`.
- A well-formed integer ID matching an existing category still returns that category.
- A well-formed integer ID that is absent from the collection still returns `None`.
- Existing forum category-list acquisition, parser diagnostics, response diagnostics, cached category collections, lazy `site.forum.categories`, lazy `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumCategory.create_thread(...)`, forum thread reads, forum post reads, and forum post revision reads remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `True` tightens behavior for values that could previously compare equal to integer search keys. Mitigation: `bool` is not a meaningful forum category ID, and accepting it can hide caller payload bugs.
- Risk: Rejecting float or string search keys can expose upstream caller bugs. Mitigation: the documented API type is an integer; callers loading IDs from JSON, CLI flags, spreadsheets, or generated ledgers should normalize to non-boolean integers before calling `find(...)`.
- Risk: Diagnostics could expose private forum context. Mitigation: the new error message contains only the input-field name and expected type, not category titles, descriptions, rendered forum content, site names, or account details.

## Dependencies

- Existing `ForumCategoryCollection` storage and iteration semantics remain authoritative for valid integer search keys.
- Existing forum category-list acquisition and parser code remains unchanged.
- Existing forum category response diagnostics remain unchanged.
- The validation is local to `src/wikidot/module/forum_category.py` and does not affect category acquisition, category-owned thread acquisition, thread creation, forum post acquisition, forum post source reads, forum post revision behavior, page behavior, site search, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered forum category search-ID validation path.

## Upstream-Safe Motivation

Forum category lookup is often fed by generated forum inventories, moderation ledgers, translation tooling, migration scripts, archival indexes, or cached category scans. Since `find(...)` compares supplied values against stored category IDs, malformed search keys should fail deterministically before collection scanning rather than producing misleading misses or accidentally matching float values to integer category IDs.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established forum category data as a practical workflow through category-list acquisition, retry behavior, structural parser boundaries, text fidelity, response-body diagnostics, count parsing diagnostics, cache behavior, category-owned thread reads, and create-thread diagnostics.
- Existing forum-category drafts covered fetching, parsing, response diagnostics, cached/lazy category-adjacent reads, create-thread behavior, and parsed category fields; they did not validate caller-provided search keys to `ForumCategoryCollection.find(id=...)`.
- This slice only validates `ForumCategoryCollection` search-ID inputs. It does not change category-list acquisition, parser field extraction, cached category collections, lazy `site.forum.categories`, lazy `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumCategory.create_thread(...)`, forum thread behavior, forum post behavior, forum post revision behavior, page behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum post source, raw rendered forum content, comments from private forums, source text from real sites, private forum content, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed search IDs instead of coercing them. Callers that load forum category search targets from JSON, YAML, CLI flags, spreadsheets, generated structures, or audit ledgers should resolve them into non-boolean integers before calling `ForumCategoryCollection.find(...)`.
