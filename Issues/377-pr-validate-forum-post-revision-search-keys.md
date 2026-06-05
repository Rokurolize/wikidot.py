# PR Draft: Validate ForumPostRevisionCollection Search Keys

## Summary

`ForumPostRevisionCollection.find(id)` and `ForumPostRevisionCollection.find_by_rev_no(rev_no)` both document integer search keys, but malformed caller-provided values were not rejected at the public search boundary. Values such as `None`, strings, and floats could be treated as ordinary misses or equality matches, while booleans could match integer revision IDs or revision numbers because `bool` is an `int` subclass.

This change validates both search keys before scanning the revision collection. Malformed `id` values now raise `ValueError("id must be an integer")`, and malformed `rev_no` values now raise `ValueError("rev_no must be an integer")`. Existing valid lookup behavior and valid not-found behavior remain unchanged for non-boolean integer search keys.

## Outcome

Forum post revision collection callers now get deterministic Python-side preflight validation for malformed revision search keys instead of misleading not-found misses, float/string equality surprises, or accidental boolean matches.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum post revision history for moderation ledgers, translation review tooling, edit-history audits, forum migration checks, archival jobs, local indexing, or generated workflows that need stable revision lookup behavior.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post revision-list and revision-HTML reads as practical read surfaces. Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), [180-pr-forum-post-revision-lazy-html-context.md](180-pr-forum-post-revision-lazy-html-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), and [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md) cover revision-list acquisition, revision-HTML acquisition, retry behavior, duplicate response reuse, cached direct helpers, parser diagnostics, response diagnostics, caller-provided post inputs, and stored collection-entry validation. Adjacent search preflight drafts [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md) and [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md) cover page file and page revision collection lookup IDs.

Those prior slices are not duplicates. They fetch, parse, cache, diagnose, or validate stored forum post revision records and acquisition inputs, but they do not validate the caller-provided search keys to `ForumPostRevisionCollection.find(...)` or `find_by_rev_no(...)` before scanning stored revisions.

## Related Issue

Builds directly on the forum post revision acquisition and parser hardening line from [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), and the adjacent `find(...)` preflight pattern from [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `ForumPostRevisionCollection.find(id=...)` accepts only non-boolean integer IDs before scanning stored revisions.
- Validate `ForumPostRevisionCollection.find_by_rev_no(rev_no=...)` accepts only non-boolean integer revision numbers before scanning stored revisions.
- Preserve valid `collection.find(9001)` and `collection.find_by_rev_no(1)` behavior when a matching revision exists.
- Preserve valid unknown integer behavior: a well-formed absent ID or revision number still returns `None`.
- Preserve revision-list acquisition, revision-HTML acquisition, parser diagnostics, cached revision collections, optional `with_html=True`, and lazy `ForumPostRevision.html` semantics.

## Type Of Change

- Input validation
- Public API behavior hardening
- Forum post revision lookup preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection.find(id=...)` must reject `None`, booleans, strings, floats, and other non-integer values with `ValueError("id must be an integer")` before scanning revisions. |
| R2 | `ForumPostRevisionCollection.find_by_rev_no(rev_no=...)` must reject `None`, booleans, strings, floats, and other non-integer values with `ValueError("rev_no must be an integer")` before scanning revisions. |
| R3 | Valid lookup must remain unchanged for well-formed non-boolean integer IDs and revision numbers that match stored revisions. |
| R4 | Valid not-found behavior must remain unchanged for well-formed non-boolean integer IDs and revision numbers that are absent from the collection. |
| R5 | Existing revision-list acquisition, revision-HTML acquisition, parser diagnostics, cached collection reuse, optional `with_html=True`, and lazy `ForumPostRevision.html` behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private revision data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, forum-post-revision tests, adjacent forum tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed revision IDs fail before collection iteration can compare them with stored revision IDs. | `TestForumPostRevisionCollectionFind.test_find_rejects_non_integer_ids` failed RED before the fix for `None`, `True`, `"9001"`, and `9001.0`, then passed GREEN after validation was added. | Treating malformed IDs as ordinary misses, coercing values, scanning revisions, or matching booleans/floats as integer IDs rejects this local completion claim. | Forum post revision ID search preflight | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Malformed revision numbers fail before collection iteration can compare them with stored `rev_no` values. | `TestForumPostRevisionCollectionFindByRevNo.test_find_by_rev_no_rejects_non_integer_revision_numbers` failed RED before the fix for `None`, `True`, `"1"`, and `1.0`, then passed GREEN after validation was added. | Treating malformed revision numbers as ordinary misses, coercing values, scanning revisions, or matching `True` / `1.0` to revision number `1` rejects this local completion claim. | Forum post revision number search preflight | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Matching non-boolean integer search keys still return the stored `ForumPostRevision`. | Existing `test_find_existing` and `test_find_by_rev_no_existing` passed after validation was added. | Changing returned revision identity, rejecting valid integer IDs, rejecting valid revision numbers, or comparing IDs and revision numbers interchangeably rejects this local completion claim. | Forum post revision collection lookup | `tests/unit/test_forum_post_revision.py` |
| R4 | Missing non-boolean integer search keys still return `None`. | Existing `test_find_nonexistent` and `test_find_by_rev_no_nonexistent` passed after validation was added. | Raising for a valid but absent integer ID/revision number or changing not-found behavior rejects this local completion claim. | Forum post revision collection lookup | `tests/unit/test_forum_post_revision.py` |
| R5 | Adjacent forum post revision behavior remains green. | `tests/unit/test_forum_post_revision.py` passed 68 tests, and adjacent forum tests passed 248 tests. | Regressing revision-list acquisition, revision HTML acquisition, cached revisions, optional `with_html=True`, parser diagnostics, lazy `ForumPostRevision.html`, forum post source reads, thread reads, or category reads rejects this local completion claim. | Forum post revision workflow | affected forum-post-revision, forum-post, forum-thread, and forum-category tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw revision source/HTML, private forum content, private revision comments, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-post-revision tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `2bd89f2 fix(forum_post_revision): validate revision search keys`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionFind::test_find_rejects_non_integer_ids` failed 4 parameterized cases before the `find(id=...)` fix: malformed IDs did not raise, and comparison was reached for every malformed value.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionFind::test_find_rejects_non_integer_ids` passed 4 tests after adding ID search preflight.
- RED: `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionFindByRevNo::test_find_by_rev_no_rejects_non_integer_revision_numbers` failed 4 parameterized cases before the `find_by_rev_no(rev_no=...)` fix: malformed revision numbers did not raise, and comparison was reached for every malformed value.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionFind::test_find_rejects_non_integer_ids tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionFindByRevNo::test_find_by_rev_no_rejects_non_integer_revision_numbers` passed 8 tests after adding both search-key preflights.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py` passed 68 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py` passed 248 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1082 tests.
- `.venv/bin/ruff check src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed.
- `.venv/bin/ruff format src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` left 2 files unchanged.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `collection.find(None)`, `collection.find(True)`, `collection.find("9001")`, and `collection.find(9001.0)` raise `ValueError("id must be an integer")`.
- `collection.find_by_rev_no(None)`, `collection.find_by_rev_no(True)`, `collection.find_by_rev_no("1")`, and `collection.find_by_rev_no(1.0)` raise `ValueError("rev_no must be an integer")`.
- A well-formed integer ID matching an existing revision still returns that revision.
- A well-formed integer revision number matching an existing revision still returns that revision.
- Well-formed integer IDs and revision numbers that are absent from the collection still return `None`.
- Existing revision-list acquisition, revision-HTML acquisition, parser diagnostics, cached revision collections, optional `with_html=True`, lazy `ForumPostRevision.html`, forum post reads, thread reads, and category reads remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private revision data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `True` tightens behavior for values that could previously compare equal to integer search keys. Mitigation: `bool` is not a meaningful forum post revision ID or revision number, and accepting it can hide caller payload bugs.
- Risk: Rejecting float or string search keys can expose upstream caller bugs. Mitigation: the documented API types are integers; callers loading IDs or revision numbers from JSON, CLI flags, spreadsheets, or generated ledgers should normalize to non-boolean integers before calling `find(...)` or `find_by_rev_no(...)`.
- Risk: Diagnostics could expose private revision context. Mitigation: the new error messages contain only the input-field names and expected types, not post IDs, revision comments, source text, rendered HTML, site names, or account details.

## Dependencies

- Existing `ForumPostRevisionCollection` storage and iteration semantics remain authoritative for valid integer search keys.
- Existing revision-list acquisition and revision-HTML acquisition code remains unchanged.
- Existing forum post revision parser diagnostics remain unchanged.
- The validation is local to `src/wikidot/module/forum_post_revision.py` and does not affect forum post acquisition, forum thread acquisition, forum category acquisition, page revision behavior, site search, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered forum post revision search-key validation path.

## Upstream-Safe Motivation

Forum post revision lookup is often fed by generated edit-history inventories, moderation ledgers, translation tooling, migration scripts, or archival indexes. Since `find(...)` and `find_by_rev_no(...)` compare supplied values against stored revision IDs and revision numbers, malformed search keys should fail deterministically before collection scanning rather than producing misleading misses or accidentally matching boolean or float values to integer revision fields.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established forum post revision data as a practical workflow through revision-list acquisition, revision-HTML acquisition, retry behavior, duplicate fetch reduction, parser diagnostics, response-body diagnostics, parsed-field diagnostics, cache reuse, and lazy revision HTML reads.
- Existing forum-post-revision drafts covered fetching, parsing, response diagnostics, cached/direct acquisition, caller-provided post inputs, stored collection-entry validation, and parsed revision fields; they did not validate caller-provided search keys to `ForumPostRevisionCollection.find(id=...)` or `find_by_rev_no(rev_no=...)`.
- This slice only validates `ForumPostRevisionCollection` search-key inputs. It does not change revision-list acquisition, revision-HTML acquisition, forum post revision parser field extraction, cached revision collections, optional `with_html=True`, lazy `ForumPostRevision.html`, forum post source reads, thread reads, category reads, page revision behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw revision source, raw rendered revision HTML, revision comments from private forums, source text from real sites, private forum content, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed search keys instead of coercing them. Callers that load forum post revision search targets from JSON, YAML, CLI flags, spreadsheets, generated structures, or audit ledgers should resolve them into non-boolean integers before calling `ForumPostRevisionCollection.find(...)` or `find_by_rev_no(...)`.
