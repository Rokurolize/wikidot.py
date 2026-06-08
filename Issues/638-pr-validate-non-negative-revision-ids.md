# PR Draft: Validate Non-Negative Revision IDs

## Summary

`PageRevision.id` and `ForumPostRevision.id` identify the concrete revision rows used by page revision source/html fetches, forum post revision HTML fetches, cached revision ledgers, and generated audit records. Issues 463 and 465 validated these direct constructor fields as non-boolean integers, and generated parser paths already reject malformed or non-digit revision IDs before constructing revision records. Direct constructors still accepted negative integer IDs such as `-1`, letting fixtures, generated ledgers, or rehydrated records carry impossible revision identity state.

This change validates direct page and forum post revision IDs as non-negative integers. It deliberately preserves `id=0` because prior identity-field drafts avoided a stronger positive-ID requirement, and generated parser IDs already remain non-negative through existing parser rules. Loaded collection lookup behavior is unchanged.

## Outcome

Direct `PageRevision` and `ForumPostRevision` records can no longer store negative revision IDs, while zero-ID compatibility, malformed-type diagnostics, parser-created revision IDs, loaded `find(...)` behavior, source/html acquisition, and adjacent revision workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use page revision histories, forum post revision histories, source/html acquisition, duplicate revision caches, generated migration or moderation ledgers, serialized revision records, or publish-adjacent checks that rely on revision identity metadata.

## Current Evidence

Local rollout-backed drafts repeatedly use revision IDs in page source/html fetch requests, forum post revision HTML fetch requests, duplicate request reduction, cache reuse, revision ledgers, and publish-adjacent verification. [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md) and [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md) cover malformed generated revision IDs. [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md) and [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md) cover direct revision identity field types. [637-pr-validate-non-negative-revision-numbers.md](637-pr-validate-non-negative-revision-numbers.md) covers revision-number range semantics, not revision IDs.

This slice is not a duplicate of Issues 463 or 465. Those drafts reject booleans, strings, floats, and arbitrary objects for direct `id`, but still accept negative integers. This slice is also not a duplicate of Issues 236 or 283 because generated parser paths already reject non-digit IDs; this follow-up closes the direct constructor state boundary only.

## Related Issue / Non-Duplicate Analysis

Builds directly on [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md), [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), and [637-pr-validate-non-negative-revision-numbers.md](637-pr-validate-non-negative-revision-numbers.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject direct `PageRevision(id=-1)` with `ValueError("id must be non-negative")`.
- Reject direct `ForumPostRevision(id=-1)` with `ValueError("id must be non-negative")`.
- Preserve existing integer-type diagnostics for malformed direct revision IDs.
- Preserve direct `id=0` as a non-negative value.
- Preserve generated parser-side revision ID diagnostics and loaded collection lookup behavior.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Revision identity state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `PageRevision(id=-1)` must raise `ValueError("id must be non-negative")`. |
| R2 | Direct `ForumPostRevision(id=-1)` must raise `ValueError("id must be non-negative")`. |
| R3 | Direct `PageRevision(id=0)` and `ForumPostRevision(id=0)` must remain valid. |
| R4 | Existing malformed direct ID type diagnostics must remain `ValueError("id must be an integer")`. |
| R5 | Existing non-negative revision-number validation from Issue 637 must remain green. |
| R6 | Parser-created page/forum revision IDs, generated revision-ID diagnostics, source/html acquisition, cached revision workflows, and loaded lookup behavior must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, revision module tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Page revision objects cannot store negative revision IDs. | `TestPageRevision.test_init_rejects_negative_ids` failed RED with `DID NOT RAISE`, then passed GREEN after `_validate_revision_id(...)` rejected values below zero. | Accepting `-1`, coercing it to `0`, or changing malformed-type behavior rejects this local completion claim. | PageRevision constructor | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Forum post revision objects cannot store negative revision IDs. | `TestForumPostRevisionBasic.test_init_rejects_negative_ids` failed RED with `DID NOT RAISE`, then passed GREEN after `_validate_revision_id(...)` rejected values below zero. | Accepting `-1`, coercing it to `0`, or changing parser-created forum post revision behavior rejects this local completion claim. | ForumPostRevision constructor | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Zero remains valid for direct revision IDs. | `TestPageRevision.test_init_accepts_zero_id` and `TestForumPostRevisionBasic.test_init_accepts_zero_id` passed in focused RED and GREEN runs. | Requiring positive-only revision IDs without separate evidence rejects this local completion claim. | Constructor compatibility | `tests/unit/test_page_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R4 | Existing malformed direct type diagnostics remain stable. | Existing malformed ID tests passed in focused RED and GREEN commands for page and forum post revisions. | Changing `id must be an integer`, accepting booleans, or coercing strings/floats rejects this local completion claim. | Constructor type validation | `tests/unit/test_page_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R5 | Existing non-negative revision-number validation stays intact. | Issue 637 negative revision-number tests passed in the focused command. | Regressing `rev_no` range validation, zero revision-number compatibility, or malformed revision-number type behavior rejects this local completion claim. | Revision-number compatibility | `tests/unit/test_page_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R6 | Existing revision workflows remain green. | The touched page-revision/forum-post-revision suites passed 254 tests, and the full unit suite passed 2883 tests. | Regressing generated revision ID parsing, source/html acquisition, duplicate cache behavior, loaded lookup behavior, page revision parsing, or forum post revision parsing rejects this local completion claim. | Revision workflows | `tests/unit/test_page_revision.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regression coverage uses unit-level synthetic constructors only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, upstream Issues, upstream PRs, live Wikidot actions, raw revision HTML from real sites, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, revision suites, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `db53b40 fix(revision): validate non-negative revision ids`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_malformed_ids tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_negative_ids tests/unit/test_page_revision.py::TestPageRevision::test_init_accepts_zero_id tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_malformed_revision_numbers tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_negative_revision_numbers tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_rejects_malformed_ids tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_rejects_negative_ids tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_accepts_zero_id tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_rejects_malformed_revision_numbers tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_rejects_negative_revision_numbers -q` failed 2 new negative-ID cases before the fix with `DID NOT RAISE`; 20 malformed-ID, malformed-revision-number, negative-revision-number, and zero-value guards stayed green.
- GREEN: the same focused command passed 22 tests after constructor ID range validation was added.
- `uv run ruff format src/wikidot/module/page_revision.py src/wikidot/module/forum_post_revision.py tests/unit/test_page_revision.py tests/unit/test_forum_post_revision.py` left 4 files unchanged.
- `uv run pytest tests/unit/test_page_revision.py tests/unit/test_forum_post_revision.py -q` passed 254 tests.
- `uv run pytest tests/unit -q` passed 2883 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageRevision(id=-1)` raises `ValueError("id must be non-negative")`.
- `ForumPostRevision(id=-1)` raises `ValueError("id must be non-negative")`.
- `PageRevision(id=0)` and `ForumPostRevision(id=0)` remain accepted and store `0`.
- Existing malformed direct ID values still raise `ValueError("id must be an integer")`.
- Existing non-negative `rev_no` validation remains green.
- Parser-created revision IDs, source/html acquisition, duplicate cache behavior, loaded collection lookup behavior, and adjacent revision workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Revision IDs are concrete identity metadata. Negative IDs are not useful sentinel values in the current direct constructor surface; they can move through generated ledgers, fixtures, and rehydrated records as apparently valid integers and only fail later when used in source/html requests. Non-negative validation rejects impossible revision identity state early while deliberately avoiding a stronger positive-ID requirement.

## Local Evidence

- Local rollout evidence uses page and forum post revision IDs for source/html fetches, duplicate request reduction, cache reuse, generated audit ledgers, serialized records, and publish-adjacent checks.
- Existing local drafts covered generated malformed revision IDs, direct revision identity field types, and revision-number ranges, but did not cover negative direct revision IDs.
- The focused RED failures showed negative direct revision IDs were accepted as stored state. The GREEN regressions cover invalid values, zero compatibility, existing malformed type validation, and existing non-negative revision-number validation.
- This slice only validates direct revision ID range semantics. It does not change parser selectors, generated revision ID parsing, loaded collection lookup, revision numbers, positive-only requirements, source/html acquisition, retry policy, cached state, live Wikidot behavior, or upstream actions.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, raw revision HTML from real sites, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

This change intentionally validates non-negative direct revision IDs only. It does not require positive IDs or change loaded `find(...)` lookup semantics because prior local search-key drafts preserved absent integer lookup behavior and generated parser IDs already reject non-digit values.
