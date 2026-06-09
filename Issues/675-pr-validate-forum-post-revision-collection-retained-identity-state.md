# PR Draft: Validate Forum Post Revision Collection Retained Identity State

## Summary

`ForumPostRevisionCollection.find(id)` and `find_by_rev_no(rev_no)` validate malformed caller-provided search-key types before scanning stored revisions, but both scans still compared retained row state directly: `revision.id == id` and `revision.rev_no == rev_no`. After local fixtures, generated edit-history ledgers, cached revision collections, serialized records, or rehydrated forum-post revision collections have been mutated incorrectly, booleans and floats can satisfy Python equality against integer revision IDs or revision numbers, while `None`, strings, lists, and negative values are treated as ordinary not-found misses instead of corrupted retained revision state.

This change validates each stored revision's retained ID with `_validate_revision_id(...)` and retained revision number with `_validate_revision_number(...)` before comparing either field to the caller search key. Malformed retained revision IDs now raise `ValueError("id must be an integer")`, malformed retained revision numbers now raise `ValueError("rev_no must be an integer")`, negative retained values now raise the existing non-negative diagnostics, zero-ID and zero-revision-number lookup remain accepted, existing absent integer lookup behavior remains unchanged, and no revision-list acquisition, revision HTML acquisition, parser, cache, source/edit, or live Wikidot behavior changes.

## Outcome

Loaded forum-post revision collections can no longer return a revision by Python's loose numeric equality or hide corrupted retained revision ID / revision-number state behind an ordinary not-found result.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free forum edit-history inventories, moderation ledgers, translation review tooling, migration fixtures, cached revision indexes, local tests, or serialized and rehydrated `ForumPostRevisionCollection` objects.

## Current Evidence

Local rollout-backed drafts already established forum-post revision acquisition and lookup as practical workflow surfaces. [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), [180-pr-forum-post-revision-lazy-html-context.md](180-pr-forum-post-revision-lazy-html-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [433-pr-validate-forum-post-revision-html-assignments.md](433-pr-validate-forum-post-revision-html-assignments.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md), [637-pr-validate-non-negative-revision-numbers.md](637-pr-validate-non-negative-revision-numbers.md), [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md), [666-pr-validate-forum-post-revisions-cache-retained-id-state.md](666-pr-validate-forum-post-revisions-cache-retained-id-state.md), and [667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md](667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md) cover revision-list acquisition, retry behavior, duplicate direct revision reuse, HTML acquisition, parser diagnostics, response diagnostics, collection entry validation, caller search-key validation, collection shape, direct ID and revision-number type/range validation, cache ownership, and retained parent post/thread identity.

This slice is not a duplicate of those drafts. Issue 377 validates caller-provided `ForumPostRevisionCollection.find(id=...)` and `find_by_rev_no(rev_no=...)` search-key types before scanning stored revisions, but it does not validate retained IDs or revision numbers already stored inside the collection. Issues 463, 637, and 638 validate direct `ForumPostRevision(id=..., rev_no=...)` construction, but they cannot cover a valid revision whose fields are corrupted after construction and then reused in a collection. Issues 666 and 667 validate retained parent post/thread identity at cache and constructor ownership boundaries, not retained revision identity fields during lookup.

## Related Issue / Non-Duplicate Analysis

Builds directly on [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md), [637-pr-validate-non-negative-revision-numbers.md](637-pr-validate-non-negative-revision-numbers.md), [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md), [666-pr-validate-forum-post-revisions-cache-retained-id-state.md](666-pr-validate-forum-post-revisions-cache-retained-id-state.md), and [667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md](667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate each stored `ForumPostRevision.id` before `ForumPostRevisionCollection.find(id)` compares it to the search key.
- Validate each stored `ForumPostRevision.rev_no` before `ForumPostRevisionCollection.find_by_rev_no(rev_no)` compares it to the search key.
- Reject retained stored revision IDs such as `None`, `True`, `False`, `"9001"`, `9001.0`, and `[]` with `ValueError("id must be an integer")`.
- Reject retained stored revision numbers such as `None`, `True`, `False`, `"1"`, `1.0`, and `[]` with `ValueError("rev_no must be an integer")`.
- Reject negative retained stored revision IDs and revision numbers with the existing non-negative diagnostics.
- Preserve valid zero-ID lookup, valid zero-revision-number lookup, valid matching lookup, existing absent integer lookup behavior, malformed caller search-key type diagnostics, collection initialization, collection parent ownership, revision-list acquisition, revision HTML acquisition, parser diagnostics, cache reuse, and adjacent forum workflows.
- Do not add caller search-key range validation in this slice.

## Type Of Change

- Input validation
- Retained forum-post revision identity hardening
- Loaded collection lookup integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection.find(id)` must reject retained stored `revision.id` values such as `None`, `True`, `False`, `"9001"`, `9001.0`, and `[]` with `ValueError("id must be an integer")` before comparison. |
| R2 | `ForumPostRevisionCollection.find(id)` must reject retained stored `revision.id=-1` with `ValueError("id must be non-negative")` before comparison. |
| R3 | `ForumPostRevisionCollection.find_by_rev_no(rev_no)` must reject retained stored `revision.rev_no` values such as `None`, `True`, `False`, `"1"`, `1.0`, and `[]` with `ValueError("rev_no must be an integer")` before comparison. |
| R4 | `ForumPostRevisionCollection.find_by_rev_no(rev_no)` must reject retained stored `revision.rev_no=-1` with `ValueError("rev_no must be non-negative")` before comparison. |
| R5 | Valid lookup where the stored revision ID and search ID are both `0`, and where the stored revision number and search revision number are both `0`, must remain accepted. |
| R6 | Existing caller search-key type validation, valid matching lookup, existing absent integer lookup behavior, collection initialization, collection parent ownership, revision-list acquisition, revision HTML acquisition, parser diagnostics, cache reuse, and adjacent forum workflows must remain green. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, forum-post-revision module coverage, adjacent forum/site coverage, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained stored revision IDs fail before lookup comparison. | `test_find_rejects_revision_with_malformed_retained_ids` failed RED for six malformed values: booleans and `9001.0` could be accepted through Python equality, while `None`, `"9001"`, and `[]` returned ordinary misses. The test passed GREEN after stored revision ID validation. | Accepting booleans/floats, returning ordinary `None` misses for corrupted IDs, coercing values, or returning a revision from corrupted retained ID state rejects this local completion claim. | Stored `ForumPostRevision.id` during collection lookup | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Negative retained stored revision IDs fail before lookup comparison. | `test_find_rejects_revision_with_negative_retained_id` failed RED with an ordinary not-found result, then passed GREEN after stored revision ID range validation. | Treating negative stored IDs as ordinary misses, accepting them, matching them, or coercing them rejects this local completion claim. | Stored `ForumPostRevision.id` during collection lookup | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Malformed retained stored revision numbers fail before lookup comparison. | `test_find_by_rev_no_rejects_revision_with_malformed_retained_rev_nos` failed RED for six malformed values: booleans and `1.0` could be accepted through Python equality, while `None`, `"1"`, and `[]` returned ordinary misses. The test passed GREEN after stored revision-number validation. | Accepting booleans/floats, returning ordinary `None` misses for corrupted revision numbers, coercing values, or returning a revision from corrupted retained revision-number state rejects this local completion claim. | Stored `ForumPostRevision.rev_no` during collection lookup | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R4 | Negative retained stored revision numbers fail before lookup comparison. | `test_find_by_rev_no_rejects_revision_with_negative_retained_rev_no` failed RED with an ordinary not-found result, then passed GREEN after stored revision-number range validation. | Treating negative stored revision numbers as ordinary misses, accepting them, matching them, or coercing them rejects this local completion claim. | Stored `ForumPostRevision.rev_no` during collection lookup | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R5 | Zero remains valid for retained revision ID and revision-number lookup. | `test_find_accepts_revision_with_zero_retained_id` and `test_find_by_rev_no_accepts_revision_with_zero_retained_rev_no` passed RED and GREEN. | Rejecting `0`, treating it as missing, coercing it to false, or changing returned revision identity rejects this local completion claim. | Forum-post revision collection lookup semantics | `tests/unit/test_forum_post_revision.py` |
| R6 | Existing compatible behavior remains compatible. | Focused GREEN coverage passed 16 tests, `tests/unit/test_forum_post_revision.py` passed 187 tests, adjacent forum/site coverage passed 1047 tests, and full unit passed 3229 tests. | Regressing caller search-key type validation, valid matching lookup, existing absent integer lookup behavior, collection initialization, parent ownership, revision-list acquisition, revision HTML acquisition, parser diagnostics, cache reuse, forum category/thread/post behavior, site workflows, or any unit test rejects this local completion claim. | Forum-post revision collection and adjacent forum workflows | `tests/unit/test_forum_post_revision.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_site.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic forum-post revision objects and local unit helpers only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, forum source text, revision HTML, private forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, temporary pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `51e42cf fix(forum_post_revision): validate collection retained ids`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionFind::test_find_accepts_revision_with_zero_retained_id tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionFind::test_find_rejects_revision_with_malformed_retained_ids tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionFind::test_find_rejects_revision_with_negative_retained_id tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionFindByRevNo::test_find_by_rev_no_accepts_revision_with_zero_retained_rev_no tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionFindByRevNo::test_find_by_rev_no_rejects_revision_with_malformed_retained_rev_nos tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionFindByRevNo::test_find_by_rev_no_rejects_revision_with_negative_retained_rev_no -q` collected 16 tests: 14 retained stored revision-ID / revision-number cases failed before the fix, and 2 zero-value compatibility guards passed.
- GREEN: the same focused command passed 16 tests after stored revision IDs and revision numbers were validated before collection lookup comparison.
- `uv run ruff format src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` left both files unchanged.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 187 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_site.py -q` passed 1047 tests.
- `uv run pytest tests/unit -q` passed 3229 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPostRevisionCollection.find(9001)` raises `ValueError("id must be an integer")` when a stored revision's retained `revision.id` is `None`, `"9001"`, or `[]`.
- `ForumPostRevisionCollection.find(1)`, `find(0)`, and `find(9001)` raise `ValueError("id must be an integer")` when stored retained IDs are `True`, `False`, or `9001.0` before Python equality can match those corrupted IDs.
- `ForumPostRevisionCollection.find(9001)` raises `ValueError("id must be non-negative")` when a stored revision's retained `revision.id` is `-1`.
- `ForumPostRevisionCollection.find_by_rev_no(1)` raises `ValueError("rev_no must be an integer")` when a stored revision's retained `revision.rev_no` is `None`, `"1"`, or `[]`.
- `ForumPostRevisionCollection.find_by_rev_no(1)`, `find_by_rev_no(0)`, and `find_by_rev_no(1)` raise `ValueError("rev_no must be an integer")` when stored retained revision numbers are `True`, `False`, or `1.0` before Python equality can match those corrupted values.
- `ForumPostRevisionCollection.find_by_rev_no(1)` raises `ValueError("rev_no must be non-negative")` when a stored revision's retained `revision.rev_no` is `-1`.
- `ForumPostRevisionCollection.find(0)` still returns a revision whose retained ID is valid integer `0`.
- `ForumPostRevisionCollection.find_by_rev_no(0)` still returns a revision whose retained revision number is valid integer `0`.
- Existing malformed search-key type rejection, matching lookup, absent integer lookup behavior, collection initialization, collection parent ownership, revision-list acquisition, revision HTML acquisition, parser diagnostics, cache reuse, and adjacent forum workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private forum data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPostRevisionCollection.find(id)` and `find_by_rev_no(rev_no)` are local lookups over already loaded forum edit-history records. Caller search keys already have type validation, and stored revision rows should be held to the same retained-ID / retained-revision-number contract before comparison. Validating stored fields prevents corrupted local state from matching through Python's bool/float equality rules or disappearing as ordinary not-found results, while preserving valid zero values, existing absent integer behavior, and all parser/network behavior.

## Local Evidence

- Existing local drafts covered forum-post revision fetch retry behavior, duplicate request reduction, cache reuse, response diagnostics, parser ID/user/timestamp/content diagnostics, caller post input validation, collection entry validation, collection search-key validation, collection constructor validation, direct revision identity field validation, non-negative revision numbers, non-negative revision IDs, and retained parent post/thread identity validation.
- None of those drafts covered malformed retained stored `ForumPostRevision.id` or `ForumPostRevision.rev_no` values inside collection lookup because the scans still compared `revision.id == id` and `revision.rev_no == rev_no` directly.
- The focused RED failure showed booleans and floats could be accepted as stored revision IDs or revision numbers when they compared equal to lookup integers, while `None`, strings, lists, and negative values could be misreported as ordinary not-found results.
- This slice only validates retained stored revision identity fields at the loaded collection lookup comparison boundary. It does not change revision-list acquisition, revision HTML acquisition, parser field extraction, cached revision collections, lazy revision access, forum post source/edit behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, forum source text, revision HTML, private forum content, and private site data out of upstream discussion.

## Additional Notes

The change intentionally reuses `_validate_revision_id(...)` and `_validate_revision_number(...)` only for stored collection rows. It does not add caller search-key range validation in `ForumPostRevisionCollection.find(...)` or `find_by_rev_no(...)`, preserving the prior lookup-surface scope from Issue 377 and the explicit Issue 637/638 note that direct revision field range validation did not change loaded collection lookup semantics.
