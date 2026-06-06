# PR Draft: Validate ForumPost Parent ID Field

## Summary

`ForumPost` records optionally carry a parent post ID in `_parent_id`, exposed through the public `parent_id` property. Earlier local slices validated parser-side generated parent post IDs, direct reply-call parent IDs, direct parent-thread state, direct creator/time metadata, direct identity/text fields, direct optional edit metadata, collection entries, collection initialization, collection search IDs, acquisition inputs, source response diagnostics, and write-side edit inputs. The public dataclass constructor still accepted malformed direct `_parent_id` values such as booleans, numeric strings, floats, and dictionaries, letting callers create fixture, ledger, or rehydrated post records whose public `parent_id` was not an integer or `None`.

This change validates `_parent_id` at `ForumPost` initialization while preserving `None` for top-level posts and non-boolean integers for replies. Malformed values raise `ValueError("parent_id must be an integer or None")`. Valid post-list parsing, parser-side post ID and parent-post ID diagnostics, reply parent-ID validation, direct thread validation, direct creator/time validation, direct identity/text validation, optional edit metadata validation, collection validation, lazy source reads, lazy revision reads, edit behavior, and adjacent forum category/thread/revision workflows remain unchanged.

## Outcome

Callers cannot silently construct forum-post records whose public `parent_id` property exposes malformed parent-link state, while top-level posts, parser-created reply posts, and valid direct `ForumPost(...)` construction remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum indexing, generated discussion migration ledgers, moderation tooling, translation review tooling, forum migration checks, cached thread-post scans, duplicate thread-post reads, reply-thread reconstruction, `ForumThread.posts`, forum post source reads, forum post edit workflows, forum post revisions, local fixtures, or serialized/rehydrated post records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum-post reads and stored post records as practical workflow surfaces. Existing drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [235-pr-forum-post-id-parse-context.md](235-pr-forum-post-id-parse-context.md), [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md), [296-pr-forum-post-list-timestamp-context.md](296-pr-forum-post-list-timestamp-context.md), [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md), [298-pr-forum-post-list-edit-timestamp-context.md](298-pr-forum-post-list-edit-timestamp-context.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [369-pr-validate-forum-thread-reply-parent-id.md](369-pr-validate-forum-thread-reply-parent-id.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md), and [461-pr-validate-forum-post-edit-metadata-fields.md](461-pr-validate-forum-post-edit-metadata-fields.md) establish forum post acquisition, retry behavior, duplicate handling, parser scoping, parser diagnostics, response diagnostics, write preflight, public acquisition input validation, collection-entry validation, search-key validation, constructor field integrity, and optional edit metadata validation as active operational boundaries.

Those prior slices are not duplicates. Issue 235 validates malformed generated top-level and parent post IDs before parser-side `ForumPost` construction. Issue 369 validates `ForumThread.reply(parent_id=...)` before write-side mutation. Issue 446 validates the separate public `ForumPost.thread` parent object. Issues 459, 460, and 461 validate required creator/time fields, required identity/text fields, and optional edit metadata fields. This slice validates the separate stored parent-ID field behind the public `ForumPost.parent_id` property so malformed direct constructor values cannot become stored record state in manually constructed posts, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [235-pr-forum-post-id-parse-context.md](235-pr-forum-post-id-parse-context.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [369-pr-validate-forum-thread-reply-parent-id.md](369-pr-validate-forum-thread-reply-parent-id.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md), and [461-pr-validate-forum-post-edit-metadata-fields.md](461-pr-validate-forum-post-edit-metadata-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add optional `ForumPost._parent_id` validation at dataclass initialization.
- Preserve `_parent_id=None` for valid top-level posts.
- Preserve non-boolean integer parent IDs for valid reply posts.
- Reject booleans, strings, floats, dictionaries, and other non-integer parent IDs with `ValueError("parent_id must be an integer or None")`.
- Preserve parser-side parent post ID diagnostics, reply parent-ID validation, post-list parsing, source acquisition, revision acquisition, edit behavior, and adjacent forum behavior.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum-post parent-link state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPost(_parent_id=True)`, `"4999"`, `4999.0`, and `{"id": 4999}` must raise `ValueError("parent_id must be an integer or None")` before storing record state. |
| R2 | `_parent_id=None` must remain valid for top-level posts. |
| R3 | Valid non-boolean integer parent IDs must remain valid and preserve stored `parent_id` values. |
| R4 | Existing post-list parsing, parser-side parent-post ID diagnostics, reply parent-ID validation, direct thread validation, direct creator/time validation, direct identity/text validation, optional edit metadata validation, collection initialization, collection search validation, lazy source reads, lazy revision reads, edit behavior, and adjacent forum category/thread/revision workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-post tests, adjacent forum tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor parent IDs fail at the public dataclass boundary. | `TestForumPostBasic.test_init_rejects_malformed_parent_id` failed RED for 4 malformed values because the constructor did not raise, then passed GREEN after optional parent-ID validation was added. | Accepting booleans, numeric strings, floats, dictionaries, arbitrary objects, or exposing non-integer `parent_id` values rejects this local completion claim. | ForumPost constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Top-level post semantics stay valid. | The unchanged `mock_forum_post_no_http` fixture constructs posts with `_parent_id=None`, and existing constructor, string, source, revision, parser, and edit tests passed. | Rejecting `None`, fabricating a parent ID, or changing top-level post behavior rejects this local completion claim. | Parser-created and manually created posts | `tests/conftest.py`, `tests/unit/test_forum_post.py` |
| R3 | Valid reply parent-ID semantics stay valid. | Existing parser tests that preserve valid parent IDs still pass, and `test_parent_id_property` still observes integer parent IDs. | Rejecting valid integer parent IDs, coercing strings, or changing the `parent_id` property rejects this local completion claim. | Forum post parent-link state | `tests/unit/test_forum_post.py` |
| R4 | Existing forum-post and adjacent forum workflows remain green. | `tests/unit/test_forum_post.py` passed 133 tests, adjacent forum tests passed 410 tests, and full unit tests passed 1820 tests. | Regressing post-list parsing, parser parent-ID diagnostics, source acquisition, lazy revision acquisition, edit behavior, parent-thread validation, creator/time validation, identity/text validation, optional edit metadata validation, collection validation, forum category behavior, forum thread behavior, or forum post revision behavior rejects this local completion claim. | Forum post and adjacent forum workflows | `tests/unit/test_forum_post.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, post titles from real sites, post bodies from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-post tests passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d2f656e fix(forum_post): validate post parent id`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_parent_id -q` failed 4 tests before the fix; every malformed `_parent_id` value reported `DID NOT RAISE`.
- GREEN: the same focused command passed 4 tests after optional parent-ID validation was added.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 133 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 410 tests.
- `uv run pytest tests/unit -q` passed 1820 tests.
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

- `ForumPost(_parent_id=True)`, `"4999"`, `4999.0`, and `{"id": 4999}` raise `ValueError("parent_id must be an integer or None")`.
- `ForumPost(_parent_id=None)` remains valid for top-level posts.
- Valid non-boolean integer parent IDs remain valid and are exposed through `ForumPost.parent_id`.
- Existing post-list parsing, parser-side parent-post ID diagnostics, direct parent-thread validation, direct creator/time validation, direct identity/text validation, optional edit metadata validation, collection search validation, collection initialization, `ForumPost.source`, `ForumPost.revisions`, `ForumPost.edit(...)`, and adjacent forum category/thread/revision workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPost.parent_id` is the durable reply-link field behind browser-free forum indexing, post-list reads, generated migration ledgers, moderation summaries, cached thread-post scans, duplicate thread-post reuse, source reads, edit workflows, revision traversal, and downstream forum audit tooling. Parser paths already produce either `None` for top-level posts or integer parent IDs for replies, and they report malformed generated parent IDs with context; the record constructor should apply the same invariant so fixture-created or rehydrated posts cannot carry malformed parent-link state into logs, generated ledgers, migration comparisons, display summaries, or downstream tools.

## Local Evidence

- Local rollout evidence used browser-free forum indexing, generated moderation ledgers, translation review tooling, forum migration checks, cached thread-post scans, duplicate thread-post reads, lazy source reads, edit workflows, revision traversal, and tests that seed forum-post records directly.
- Existing local drafts covered forum post fetch retry behavior, duplicate thread-post reduction, parser scoping, parser-side generated parent ID diagnostics, reply parent-ID preflight, response diagnostics, public acquisition input validation, collection entry validation, collection search-key validation, collection constructor validation, direct parent-thread validation, direct creator/time validation, direct identity/text validation, and optional edit metadata validation, but did not cover direct `ForumPost(_parent_id=...)` construction.
- The focused RED failures showed invalid direct constructor parent IDs were accepted as dataclass state. The GREEN regressions cover boolean, numeric-string, float, and dictionary values while preserving `None`.
- This slice only validates stored optional forum-post parent IDs at construction. It does not change post-list acquisition, parser selectors, top-level post ID parsing, generated parent post ID parsing, title parsing, body parsing, created metadata parsing, edit metadata parsing, collection initialization, `find(...)`, source acquisition, revision acquisition, edit behavior, forum category behavior, forum thread behavior, forum post revision behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, post titles from real sites, post bodies from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates parent-ID type only. It does not require positive IDs, verify that the parent post exists in the same thread, coerce numeric strings, or rename the private dataclass field; those would be separate behavior changes with separate parser or workflow evidence.
