# PR Draft: Validate Forum Post Revision Identity Fields

## Summary

`ForumPostRevision` records carry the revision ID used by HTML fetch requests and the revision number used to preserve edit-history ordering. Earlier local slices validated revision acquisition inputs, collection entries, collection initialization, loaded-collection search keys, optional HTML controls, direct `html` assignments, the parent `post` field, and parser-side revision ID/user/timestamp diagnostics. The public `ForumPostRevision(...)` constructor still accepted malformed direct `id` and `rev_no` values such as `None`, booleans, numeric strings, and floats, letting fixtures, generated ledgers, or rehydrated records carry malformed revision identity state.

This change validates `ForumPostRevision.id` and `ForumPostRevision.rev_no` at initialization. Malformed values now raise `ValueError("id must be an integer")` or `ValueError("rev_no must be an integer")`; valid non-boolean integer values remain valid. Existing revision-list parsing, parser-side revision ID diagnostics, parser-side revision user/timestamp diagnostics, lazy `ForumPost.revisions`, duplicate cached revision reuse, direct and batched revision acquisition, revision HTML behavior, collection lookup, and adjacent forum workflows remain unchanged.

## Outcome

Callers cannot silently construct forum-post revision records with malformed stored identity fields, while parser-created, fixture-created, and manually created valid revisions continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum edit-history reads, generated discussion migration ledgers, revision HTML capture, duplicate revision cache reuse, direct `ForumPostRevisionCollection.acquire_all(post)`, lazy `ForumPost.revisions`, multi-post `ForumPostRevisionCollection.acquire_all_for_posts(...)`, collection `find(...)` / `find_by_rev_no(...)`, or local tests that construct `ForumPostRevision` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post revision identity as a practical workflow surface. Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [433-pr-validate-forum-post-revision-html-assignments.md](433-pr-validate-forum-post-revision-html-assignments.md), and [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md) establish revision-list acquisition, retry behavior, duplicate request reduction, cache reuse, response diagnostics, parser diagnostics, acquisition-input validation, collection-entry validation, lookup-key validation, optional HTML controls, collection constructor integrity, HTML assignment integrity, and parent-post constructor integrity as active operational boundaries.

Those prior slices are not duplicates. Issue 283 validates malformed generated `showRevision(...)` values before parser-side `ForumPostRevision` construction. Issue 377 validates search keys passed to loaded `ForumPostRevisionCollection.find(...)` and `find_by_rev_no(...)`, not stored constructor fields. Issue 445 validates the parent `post` field and explicitly leaves revision IDs and revision numbers as separate concerns. This slice validates direct `ForumPostRevision(id=..., rev_no=...)` construction so malformed identity values cannot become stored record state in manually constructed revisions, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [433-pr-validate-forum-post-revision-html-assignments.md](433-pr-validate-forum-post-revision-html-assignments.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), and the adjacent constructor identity-field validation pattern from [435-pr-validate-publish-result-page-ids.md](435-pr-validate-publish-result-page-ids.md), [451-pr-validate-private-message-id-field.md](451-pr-validate-private-message-id-field.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), and [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumPostRevision.id` validation at dataclass initialization.
- Add `ForumPostRevision.rev_no` validation at dataclass initialization.
- Reject non-integer and boolean revision IDs with `ValueError("id must be an integer")`.
- Reject non-integer and boolean revision numbers with `ValueError("rev_no must be an integer")`.
- Preserve valid parser-created and directly constructed revisions with non-boolean integer IDs and revision numbers.
- Preserve existing revision-list parsing, lazy `ForumPost.revisions`, direct and batched acquisition, revision HTML behavior, collection lookup, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum post revision identity state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevision(id=None)`, `True`, `"9001"`, and `9001.0` must raise `ValueError("id must be an integer")` when every other revision field is valid. |
| R2 | `ForumPostRevision(rev_no=None)`, `True`, `"0"`, and `0.0` must raise `ValueError("rev_no must be an integer")` when every other revision field is valid. |
| R3 | Valid non-boolean integer `id` and `rev_no` values must remain valid and preserve existing revision fields. |
| R4 | Existing revision-list parsing, parser-side revision ID/user/timestamp diagnostics, lazy `ForumPost.revisions`, duplicate cached revision reuse, direct and batched acquisition, revision HTML behavior, collection lookup, and adjacent forum workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-post-revision tests, adjacent forum tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor revision IDs fail at the public dataclass boundary. | `TestForumPostRevisionBasic.test_init_rejects_malformed_ids` failed RED for 4 malformed values because the constructor did not raise, then passed GREEN after ID validation was added. | Accepting missing values, booleans, numeric strings, floats, arbitrary objects, or emitting revision rows with non-integer `id` state rejects this local completion claim. | ForumPostRevision constructor | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Malformed constructor revision numbers fail at the public dataclass boundary. | `TestForumPostRevisionBasic.test_init_rejects_malformed_revision_numbers` failed RED for 4 malformed values because the constructor did not raise, then passed GREEN after revision-number validation was added. | Accepting missing values, booleans, numeric strings, floats, arbitrary objects, or emitting revision rows with non-integer `rev_no` state rejects this local completion claim. | ForumPostRevision constructor | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Valid revision identity semantics stay green. | Existing string, cache, parser, collection lookup, and HTML tests passed after constructor validation was added. | Rejecting valid integer revision IDs or revision numbers, coercing numeric strings, or changing stored revision fields rejects this local completion claim. | Parser-created and manually created revisions | `tests/unit/test_forum_post_revision.py` |
| R4 | Existing adjacent forum workflows remain green. | `tests/unit/test_forum_post_revision.py` passed 98 tests, adjacent forum tests passed 418 tests, and full unit tests passed 1828 tests. | Regressing direct revision acquisition, lazy `ForumPost.revisions`, multi-post acquisition, cached direct acquisition, duplicate post-revision reuse, parser diagnostics, response diagnostics, search lookup, HTML acquisition, forum post source/edit workflows, forum category workflows, or forum thread workflows rejects this local completion claim. | Forum revision and adjacent forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum post text, revision HTML, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `80ed583 fix(forum_post_revision): validate revision identity fields`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_rejects_malformed_ids tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_rejects_malformed_revision_numbers -q` failed 8 tests before the fix; every malformed `id` or `rev_no` value reported `DID NOT RAISE`.
- GREEN: the same focused command passed 8 tests after `ForumPostRevision` identity validation was added.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 98 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 418 tests.
- `uv run pytest tests/unit -q` passed 1828 tests.
- `uv run ruff check src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed.
- `uv run ruff format --check src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed with 2 files already formatted after applying the formatter.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed with no issues in 2 source files.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `uv run pyright src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 61 existing full-tree typing errors outside this slice, including page fixture `None` mismatches, an intentional invalid cookie-name test call, intentional invalid-input test calls, requestutil response narrowing issues, invalid `SearchPagesQuery` parameter calls, client mock typing, and site test mock typing issues. The changed source file and changed forum-post-revision test file pass pyright together.

## Acceptance Criteria

- `ForumPostRevision(id=None)`, `True`, `"9001"`, and `9001.0` raise `ValueError("id must be an integer")`.
- `ForumPostRevision(rev_no=None)`, `True`, `"0"`, and `0.0` raise `ValueError("rev_no must be an integer")`.
- Valid non-boolean integer `id` and `rev_no` values remain valid.
- Existing revision-list parsing, parser-side revision ID/user/timestamp diagnostics, lazy `ForumPost.revisions`, duplicate cached revision reuse, `ForumPostRevisionCollection.find(...)`, `find_by_rev_no(...)`, direct and batched acquisition, cached direct acquisition, and revision HTML behavior remain green.
- Existing forum post source/edit behavior and adjacent forum category/thread workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPostRevision.id` is used for revision HTML fetches and loaded-collection lookup, while `ForumPostRevision.rev_no` is the stable edit-history ordering field. Parser paths already derive integer revision IDs from generated `showRevision(...)` handlers and assign integer revision numbers after reversing Wikidot's newest-first response. Constructor validation keeps malformed local identity state out of fixtures, generated ledgers, migration comparisons, revision HTML request planning, and downstream audit tooling while preserving parser and caller paths that construct valid revisions.

## Local Evidence

- Local rollout evidence used browser-free forum post revision reads, duplicate revision list reuse, revision HTML fetches, lazy forum post revision reads, generated forum ledgers, and tests that seed revision objects directly.
- Existing local drafts covered forum post revision fetch retry behavior, duplicate revision and revision-HTML reduction, parse reuse, response diagnostics, parser field diagnostics, cached direct acquisition, acquisition post input validation, collection initialization validation, loaded-collection mutation validation, search-key validation, optional HTML flag validation, HTML assignment validation, and direct parent-post validation, but did not cover direct `ForumPostRevision(id=..., rev_no=...)` construction.
- The focused RED failures showed invalid constructor identity fields were accepted as dataclass state. The GREEN regressions cover missing, boolean, numeric-string, and float `id` / `rev_no` values.
- This slice only validates forum post revision identity fields at construction. It does not change revision-list parsing, optional HTML parsing, parser selectors, parser-side revision ID parsing, revision timestamp parsing, revision user parsing, revision HTML content parsing, cached duplicate behavior, collection lookup semantics, source/edit behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum post text, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates type only. It does not require positive IDs, require contiguous revision numbers, verify that a revision ID belongs to the parent post, coerce numeric strings, validate creator/time fields, validate direct `_html` constructor cache values, or change live client authentication; those are separate object, parser, cache, and workflow concerns.
