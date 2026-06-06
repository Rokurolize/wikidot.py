# PR Draft: Validate Forum Post Revision Creator And Time Fields

## Summary

`ForumPostRevision` records carry the user and timestamp metadata used by browser-free edit-history reads, generated migration ledgers, revision audit summaries, and local fixtures. Earlier local slices validated revision acquisition inputs, collection entries, collection initialization, loaded-collection search keys, optional HTML controls, direct `html` assignments, the parent `post` field, direct `id` / `rev_no` fields, and parser-side revision ID/user/timestamp diagnostics. The public `ForumPostRevision(...)` constructor still accepted malformed direct `created_by` and `created_at` values such as `None`, booleans, integers, strings, dictionaries, epoch integers, date strings, and lists, letting manually constructed or rehydrated revision records carry invalid creator/time state.

This change validates `ForumPostRevision.created_by` and `ForumPostRevision.created_at` at initialization. `created_by` now accepts only `AbstractUser` instances, preserving regular, deleted, anonymous, guest, and Wikidot system users returned by the shared user parser. `created_at` now accepts only `datetime` instances. Malformed values raise stable diagnostics: `ValueError("created_by must be an AbstractUser")` and `ValueError("created_at must be a datetime")`. Existing revision-list parsing, parser-side revision ID/user/timestamp diagnostics, lazy `ForumPost.revisions`, duplicate cached revision reuse, direct and batched revision acquisition, revision HTML behavior, collection lookup, and adjacent forum workflows remain unchanged.

## Outcome

Callers cannot silently construct forum-post revision records with malformed creator or timestamp metadata, while parser-created, fixture-created, and manually created valid revisions continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum edit-history reads, generated discussion migration ledgers, revision HTML capture, duplicate revision cache reuse, direct `ForumPostRevisionCollection.acquire_all(post)`, lazy `ForumPost.revisions`, multi-post `ForumPostRevisionCollection.acquire_all_for_posts(...)`, collection lookup, moderation summaries, timestamp-sensitive migration checks, or local tests that construct `ForumPostRevision` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post revision creator/time metadata as a practical workflow surface. Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [433-pr-validate-forum-post-revision-html-assignments.md](433-pr-validate-forum-post-revision-html-assignments.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), and [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md) establish revision-list acquisition, retry behavior, duplicate request reduction, cache reuse, response diagnostics, parser diagnostics, acquisition-input validation, collection-entry validation, lookup-key validation, optional HTML controls, collection constructor integrity, HTML assignment integrity, parent-post constructor integrity, and direct revision identity integrity as active operational boundaries.

Those prior slices are not duplicates. Issue 284 validates malformed generated timestamp metadata at the parser boundary and Issue 285 validates malformed generated user metadata at the parser boundary. Issue 445 validates the parent `post` field. Issue 463 validates direct `id` and `rev_no` fields. This slice validates direct `ForumPostRevision(created_by=..., created_at=...)` construction so malformed creator/time values cannot become stored record state in manually constructed revisions, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [433-pr-validate-forum-post-revision-html-assignments.md](433-pr-validate-forum-post-revision-html-assignments.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md), and the adjacent constructor creator/time validation pattern from [458-pr-validate-forum-thread-creator-time-fields.md](458-pr-validate-forum-thread-creator-time-fields.md) and [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumPostRevision.created_by` validation at dataclass initialization.
- Add `ForumPostRevision.created_at` validation at dataclass initialization.
- Reject non-`AbstractUser` creator values with `ValueError("created_by must be an AbstractUser")`.
- Reject non-`datetime` timestamp values with `ValueError("created_at must be a datetime")`.
- Preserve valid parser-created and directly constructed revisions with real `AbstractUser` creators and `datetime` timestamps.
- Preserve existing revision-list parsing, lazy `ForumPost.revisions`, direct and batched acquisition, revision HTML behavior, collection lookup, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum post revision metadata state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevision(created_by=None)`, `True`, `9001`, `"test-user"`, and `{"id": 12345}` must raise `ValueError("created_by must be an AbstractUser")` when every other revision field is valid. |
| R2 | `ForumPostRevision(created_at=None)`, `True`, `1700000000`, `"2023-11-14"`, and `[]` must raise `ValueError("created_at must be a datetime")` when every other revision field is valid. |
| R3 | Valid `AbstractUser` creator values and valid `datetime` timestamp values must remain valid and preserve existing revision fields. |
| R4 | Existing revision-list parsing, parser-side revision ID/user/timestamp diagnostics, lazy `ForumPost.revisions`, duplicate cached revision reuse, direct and batched acquisition, revision HTML behavior, collection lookup, and adjacent forum workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-post-revision tests, adjacent forum tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor creators fail at the public dataclass boundary. | `TestForumPostRevisionBasic.test_init_rejects_malformed_creators` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after creator validation was added. | Accepting missing values, booleans, integers, strings, dictionaries, arbitrary objects, or emitting revision rows with non-`AbstractUser` creator state rejects this local completion claim. | ForumPostRevision constructor | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Malformed constructor timestamps fail at the public dataclass boundary. | `TestForumPostRevisionBasic.test_init_rejects_malformed_created_at` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after timestamp validation was added. | Accepting missing values, booleans, epoch integers, date strings, lists, arbitrary objects, or emitting revision rows with non-`datetime` timestamp state rejects this local completion claim. | ForumPostRevision constructor | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Valid revision creator/time semantics stay green. | Existing string, cache, parser, collection lookup, identity-field, and HTML tests passed after constructor validation was added. | Rejecting valid `AbstractUser` implementations, valid `datetime` values, parser-created revisions, or manually created valid revisions rejects this local completion claim. | Parser-created and manually created revisions | `tests/unit/test_forum_post_revision.py` |
| R4 | Existing adjacent forum workflows remain green. | `tests/unit/test_forum_post_revision.py` passed 108 tests, adjacent forum tests passed 428 tests, and full unit tests passed 1838 tests. | Regressing direct revision acquisition, lazy `ForumPost.revisions`, multi-post acquisition, cached direct acquisition, duplicate post-revision reuse, parser diagnostics, response diagnostics, search lookup, HTML acquisition, forum post source/edit workflows, forum category workflows, or forum thread workflows rejects this local completion claim. | Forum revision and adjacent forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum post text, revision HTML, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d07904b fix(forum_post_revision): validate revision creator metadata`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_rejects_malformed_creators tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_rejects_malformed_created_at -q` failed 10 tests before the fix; every malformed `created_by` or `created_at` value reported `DID NOT RAISE`.
- GREEN: the same focused command passed 10 tests after `ForumPostRevision` creator/time validation was added.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 108 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 428 tests.
- `uv run pytest tests/unit -q` passed 1838 tests.
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

- `ForumPostRevision(created_by=None)`, `True`, `9001`, `"test-user"`, and `{"id": 12345}` raise `ValueError("created_by must be an AbstractUser")`.
- `ForumPostRevision(created_at=None)`, `True`, `1700000000`, `"2023-11-14"`, and `[]` raise `ValueError("created_at must be a datetime")`.
- Valid `AbstractUser` creators and valid `datetime` timestamps remain valid.
- Existing revision-list parsing, parser-side revision ID/user/timestamp diagnostics, lazy `ForumPost.revisions`, duplicate cached revision reuse, `ForumPostRevisionCollection.find(...)`, `find_by_rev_no(...)`, direct and batched acquisition, cached direct acquisition, and revision HTML behavior remain green.
- Existing forum post source/edit behavior and adjacent forum category/thread workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPostRevision.created_by` and `ForumPostRevision.created_at` are core audit fields for reconstructing forum edit history, comparing revision timelines, and building generated migration ledgers. Parser paths already produce `AbstractUser` instances and `datetime` timestamps or contextual parser failures. Constructor validation keeps malformed local metadata out of fixtures, generated ledgers, migration comparisons, revision summaries, and downstream audit tooling while preserving parser and caller paths that construct valid revisions.

## Local Evidence

- Local rollout evidence used browser-free forum post revision reads, duplicate revision list reuse, revision HTML fetches, lazy forum post revision reads, generated forum ledgers, and tests that seed revision objects directly.
- Existing local drafts covered forum post revision fetch retry behavior, duplicate revision and revision-HTML reduction, parse reuse, response diagnostics, parser ID/user/timestamp diagnostics, cached direct acquisition, acquisition post input validation, collection initialization validation, loaded-collection mutation validation, search-key validation, optional HTML flag validation, HTML assignment validation, direct parent-post validation, and direct identity-field validation, but did not cover direct `ForumPostRevision(created_by=..., created_at=...)` construction.
- The focused RED failures showed invalid constructor creator/time fields were accepted as dataclass state. The GREEN regressions cover missing, boolean, integer, string, dictionary, epoch-integer, date-string, and list values.
- This slice only validates forum post revision creator/time fields at construction. It does not change revision-list parsing, optional HTML parsing, parser selectors, parser-side revision ID parsing, revision timestamp parsing, revision user parsing, revision HTML content parsing, cached duplicate behavior, collection lookup semantics, source/edit behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum post text, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates type only. It does not verify user membership, compare creator/time fields against parent post metadata, require timezone-aware datetimes, coerce epoch integers or date strings, validate direct `_html` constructor cache values, or change live client authentication; those are separate parser, cache, and workflow concerns.
