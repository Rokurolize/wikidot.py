# PR Draft: Validate Non-Negative Revision Numbers

## Summary

`PageRevision.rev_no` and `ForumPostRevision.rev_no` identify revision order in page and forum-post history workflows. Existing local drafts validated revision identity fields as integers but explicitly left numeric range semantics unchanged, so direct constructors still accepted impossible negative revision numbers. Page revision-list parsing also accepted parseable negative cells such as `-1.` and stored them as page revision state if the rest of the row was valid.

This change validates revision numbers as non-negative integers at the direct constructor boundary for both page revisions and forum-post revisions. It also rejects parseable negative page history cells with the same site/page/revision/id/field/value context style used by adjacent parser diagnostics. `rev_no=0` remains valid because forum post revisions use `0` for the initial version and direct page revision objects should not infer a stricter positive-only invariant without rollout evidence.

## Outcome

Direct and parser-created revision records can no longer contain negative revision numbers, while malformed-type diagnostics, initial forum-post revision `0`, direct page revision `0`, normal page revision-list parsing, page source/html workflows, and forum post revision workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use page history ledgers, forum post revision ledgers, source/html acquisition, generated migration or moderation audits, serialized revision records, or publish-adjacent checks that rely on revision order metadata.

## Current Evidence

Local rollout-backed drafts repeatedly use page and forum revision objects as practical workflow surfaces for source retrieval, HTML retrieval, history ledgers, and publish-adjacent verification. [237-pr-page-revision-number-parse-context.md](237-pr-page-revision-number-parse-context.md) adds context for malformed page revision-number text. [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md) and [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md) validate revision identity field types but explicitly avoid positive-ID or contiguous-number requirements.

This slice is not a duplicate of Issues 463 or 465. Those drafts reject booleans, strings, floats, and arbitrary objects for direct `id` and `rev_no`, but they still accept negative integers. This slice is also not a duplicate of Issue 237, which handles non-integer page revision-number cells such as `not-a-number.`; this follow-up covers parseable but impossible negative numbers such as `-1.`.

## Related Issue / Non-Duplicate Analysis

Builds directly on [237-pr-page-revision-number-parse-context.md](237-pr-page-revision-number-parse-context.md), [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md), and [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject direct `PageRevision(rev_no=-1)` with `ValueError("rev_no must be non-negative")`.
- Reject direct `ForumPostRevision(rev_no=-1)` with `ValueError("rev_no must be non-negative")`.
- Preserve existing integer-type diagnostics for malformed direct revision numbers.
- Preserve direct `rev_no=0` for both page revisions and forum post revisions.
- Reject generated page history revision-number cells such as `-1.` with contextual `NoElementException`.
- Preserve malformed generated page revision-number diagnostics for non-integer text.
- Preserve forum post revision-list parsing behavior, which assigns non-negative revision numbers from parsed row order.

## Type Of Change

- Input validation
- Parser diagnostics
- Public dataclass constructor behavior hardening
- Revision metadata state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `PageRevision(rev_no=-1)` must raise `ValueError("rev_no must be non-negative")`. |
| R2 | Direct `ForumPostRevision(rev_no=-1)` must raise `ValueError("rev_no must be non-negative")`. |
| R3 | Direct `PageRevision(rev_no=0)` and `ForumPostRevision(rev_no=0)` must remain valid. |
| R4 | Existing malformed direct revision-number type diagnostics must remain `ValueError("rev_no must be an integer")`. |
| R5 | Generated page revision-list cells such as `<td>-1.</td>` must raise contextual `NoElementException` with site, page, revision row ID, page ID, field, and raw value. |
| R6 | Existing malformed generated page revision-number text such as `not-a-number.` must keep the existing contextual malformed-number diagnostic. |
| R7 | Page source/html revision workflows, forum post revision list/search/html workflows, and adjacent page workflows must remain green. |
| R8 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, touched revision/page tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Page revision objects cannot store negative revision numbers. | `TestPageRevision.test_init_rejects_negative_revision_numbers` failed RED with `DID NOT RAISE`, then passed GREEN after `_validate_revision_number(...)` rejected values below zero. | Accepting `-1`, coercing it to `0`, or changing malformed-type behavior rejects this local completion claim. | PageRevision constructor | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Forum post revision objects cannot store negative revision numbers. | `TestForumPostRevisionBasic.test_init_rejects_negative_revision_numbers` failed RED with `DID NOT RAISE`, then passed GREEN after `_validate_revision_number(...)` rejected values below zero. | Accepting `-1`, coercing it to `0`, or rejecting initial version `0` rejects this local completion claim. | ForumPostRevision constructor | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Zero remains valid for direct revision objects. | `TestPageRevision.test_init_accepts_zero_revision_number` and `TestForumPostRevisionBasic.test_init_accepts_zero_revision_number` passed in focused RED and GREEN runs. | Requiring positive-only page or forum revision numbers without separate evidence rejects this local completion claim. | Constructor compatibility | `tests/unit/test_page_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R4 | Existing malformed direct type diagnostics remain stable. | Existing malformed revision-number tests passed in focused RED and GREEN commands for page and forum post revisions. | Changing `rev_no must be an integer`, accepting booleans, or coercing strings/floats rejects this local completion claim. | Constructor type validation | `tests/unit/test_page_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R5 | Parseable negative page revision cells fail before revision state is cached. | `TestPageCollectionAcquire.test_acquire_revisions_negative_revision_number_includes_site_page_and_value_context` failed RED with `DID NOT RAISE`, then passed GREEN with contextual `NoElementException`. | Returning a `PageRevision` with negative `rev_no`, raising a raw constructor `ValueError`, omitting site/page/revision/id/field/value context, or leaving `page._revisions` populated rejects this local completion claim. | Page revision-list parser | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R6 | Existing malformed page revision-number text diagnostics remain stable. | `TestPageCollectionAcquire.test_acquire_revisions_malformed_revision_number_includes_site_page_and_value_context` passed in focused RED and GREEN commands. | Treating malformed text as a range error or dropping raw value context rejects this local completion claim. | Page revision-list parser compatibility | `tests/unit/test_page.py` |
| R7 | Existing revision and adjacent workflows remain green. | The touched page/page-revision/forum-post-revision suites passed 557 tests, and the full unit suite passed 2879 tests. | Regressing page revision source/html retrieval, forum post revision list/search/html behavior, page parsing, or adjacent page workflows rejects this local completion claim. | Revision and page workflows | `tests/unit/test_page_revision.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit/test_page.py`, `tests/unit` |
| R8 | No live site state or private material is needed to prove the behavior. | All regression coverage uses unit-level synthetic constructors or synthetic AMC response bodies only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, upstream Issues, upstream PRs, live Wikidot actions, raw page history HTML from real sites, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, touched suites, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `ef0e5d9 fix(revision): validate non-negative revision numbers`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_malformed_revision_numbers tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_negative_revision_numbers tests/unit/test_page_revision.py::TestPageRevision::test_init_accepts_zero_revision_number tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_rejects_malformed_revision_numbers tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_rejects_negative_revision_numbers tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_accepts_zero_revision_number tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_revision_number_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_negative_revision_number_includes_site_page_and_value_context -q` failed 3 new negative-revision-number cases before the fix with `DID NOT RAISE`; 11 malformed-type, malformed-parser-text, and zero-value guard cases stayed green.
- GREEN: the same focused command passed 14 tests after constructor and parser range validation was added.
- `uv run ruff format src/wikidot/module/page.py src/wikidot/module/page_revision.py src/wikidot/module/forum_post_revision.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_forum_post_revision.py` left 6 files unchanged.
- `uv run pytest tests/unit/test_page_revision.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py -q` passed 557 tests.
- `uv run pytest tests/unit -q` passed 2879 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageRevision(rev_no=-1)` raises `ValueError("rev_no must be non-negative")`.
- `ForumPostRevision(rev_no=-1)` raises `ValueError("rev_no must be non-negative")`.
- `PageRevision(rev_no=0)` and `ForumPostRevision(rev_no=0)` remain accepted and store `0`.
- Existing malformed direct revision-number values still raise `ValueError("rev_no must be an integer")`.
- Generated page history revision-number text `-1.` raises `NoElementException("Revision number must be non-negative for site: test-site, page: test-page, revision: 123 (id=12345, field=revision_number, value=-1.)")`.
- Existing generated page history text `not-a-number.` keeps the existing malformed revision-number diagnostic.
- Page revision source/html workflows, forum post revision list/search/html workflows, and adjacent page workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Revision numbers are ordering metadata. Negative revision numbers are not useful sentinel values in the current API surface; they look like legitimate integer state and can move through ledgers, caches, serialized records, or downstream verification without triggering malformed-type checks. Non-negative validation keeps constructors and the page history parser aligned while deliberately preserving `0` for the existing forum initial-version convention.

## Local Evidence

- Local rollout evidence uses page revisions and forum post revisions for source retrieval, HTML retrieval, history ledgers, generated audits, cached records, and publish-adjacent checks.
- Existing local drafts covered malformed page revision-number text and direct revision identity field types, but did not cover parseable negative revision numbers.
- The focused RED failures showed direct negative revision numbers and generated negative page history cells were accepted as stored state. The GREEN regressions cover invalid values, zero compatibility, existing malformed type validation, existing malformed parser text validation, and contextual parser diagnostics.
- This slice only validates non-negative revision-number semantics. It does not change revision IDs, positive-only requirements, contiguous-number assumptions, page revision collection search, forum post revision search, source/html acquisition, retry policy, row ordering, cached state, live Wikidot behavior, or upstream actions.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, raw page history HTML from real sites, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

This change intentionally validates non-negative revision numbers only. It does not require positive page revision numbers or contiguous revision sequences because prior local identity-field drafts explicitly avoided those stronger semantics, and forum post revisions use `0` for the initial version.
