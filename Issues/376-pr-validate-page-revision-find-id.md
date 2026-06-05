# PR Draft: Validate PageRevisionCollection.find ID Input

## Summary

`PageRevisionCollection.find(id)` documents `id` as `int`, but malformed caller-provided search keys were not rejected at the public search boundary. Values such as `None`, `"100"`, and `100.0` were treated as ordinary not-found misses or equality matches, while `True` could match revision ID `1` because `bool` is an `int` subclass.

This change validates the search key before scanning the revision collection. Non-integer and boolean values now raise `ValueError("id must be an integer")`. Existing valid lookup behavior and valid not-found behavior remain unchanged for non-boolean integer IDs.

## Outcome

Page revision collection callers now get deterministic Python-side preflight validation for malformed revision search IDs instead of misleading not-found misses, float/string equality surprises, or accidental boolean ID matches.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using page revision histories, source/HTML revision reads, archival ledgers, publication verification, moderation audits, or browser-free page review workflows that need stable revision lookup behavior.

## Current Evidence

Local rollout-backed drafts repeatedly identify page revision history and revision source/HTML reads as practical read surfaces. Existing drafts [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [150-pr-page-revision-failure-context.md](150-pr-page-revision-failure-context.md), [153-pr-latest-revision-failure-context.md](153-pr-latest-revision-failure-context.md), [164-pr-page-revision-source-parse-context.md](164-pr-page-revision-source-parse-context.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [200-pr-page-revision-source-parse-site-context.md](200-pr-page-revision-source-parse-site-context.md), [201-pr-page-revision-lazy-site-context.md](201-pr-page-revision-lazy-site-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), [222-pr-page-revision-batch-response-body-context.md](222-pr-page-revision-batch-response-body-context.md), [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md), [237-pr-page-revision-number-parse-context.md](237-pr-page-revision-number-parse-context.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [332-pr-page-revision-list-response-body-type-context.md](332-pr-page-revision-list-response-body-type-context.md), and [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md) cover page revision acquisition, source/HTML acquisition, retry behavior, duplicate response reuse, row parsing, parser diagnostics, response diagnostics, and stored collection-entry validation. Adjacent search preflight drafts [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md) and [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md) cover page vote and page file collection lookup inputs.

Those prior slices are not duplicates. They fetch, parse, cache, diagnose, or validate stored revision records and adjacent search surfaces, but they do not validate the caller-provided `id` argument to `PageRevisionCollection.find(...)` before scanning stored revisions.

## Related Issue

Builds directly on the page revision acquisition and parser hardening line from [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [332-pr-page-revision-list-response-body-type-context.md](332-pr-page-revision-list-response-body-type-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), and the adjacent `find(...)` preflight pattern from [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `PageRevisionCollection.find(id=...)` accepts only non-boolean integer IDs before scanning stored revisions.
- Preserve valid `collection.find(100)` behavior when a matching revision exists.
- Preserve valid unknown integer behavior: a well-formed integer ID that is absent from the collection still returns `None`.
- Preserve revision list acquisition, source/HTML acquisition, parser diagnostics, cached revision collections, and lazy `Page.revisions` / `Page.latest_revision` semantics.

## Type Of Change

- Input validation
- Public API behavior hardening
- Page revision lookup preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevisionCollection.find(id=...)` must reject `None`, booleans, strings, floats, and other non-integer values with `ValueError("id must be an integer")` before scanning revisions. |
| R2 | Valid lookup must remain unchanged for well-formed non-boolean integer IDs that match stored revision IDs. |
| R3 | Valid not-found behavior must remain unchanged for well-formed non-boolean integer IDs that are absent from the collection. |
| R4 | Existing revision list acquisition, revision source/HTML acquisition, parser diagnostics, cached collection reuse, and lazy `Page.revisions` / `Page.latest_revision` behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private revision data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, page-revision collection tests, adjacent page/page-file/page-vote/site tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed search IDs fail before collection iteration can compare them with stored revision IDs. | `TestPageRevisionCollection.test_find_rejects_non_integer_ids` failed RED before the fix for `None`, `True`, `"100"`, and `100.0`, then passed GREEN after validation was added. | Treating malformed IDs as ordinary misses, coercing values, scanning revisions, or matching `True` to revision ID `1` rejects this local completion claim. | Page revision search preflight | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Matching non-boolean integer IDs still return the stored `PageRevision`. | Existing page-revision collection tests passed after validation was added. | Changing returned revision identity, rejecting valid integer IDs, or comparing revision numbers instead of revision IDs rejects this local completion claim. | Page revision collection lookup | `tests/unit/test_page_revision.py` |
| R3 | Missing non-boolean integer IDs still return `None`. | Existing page-revision collection tests passed after validation was added. | Raising for a valid but absent integer ID or changing not-found behavior rejects this local completion claim. | Page revision collection lookup | `tests/unit/test_page_revision.py` |
| R4 | Adjacent page revision behavior remains green. | `tests/unit/test_page_revision.py` passed 49 tests, and adjacent page/page-file/page-vote/site tests passed 304 tests. | Regressing revision source/HTML acquisition, revision list parsing, cached revisions, lazy `Page.revisions`, `Page.latest_revision`, page-file reads, page-vote reads, or site/page workflows rejects this local completion claim. | Page revision workflow | affected page-revision, page, page-file, page-vote, and site tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw revision source/HTML, private page content, private revision comments, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, page-revision tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `61a5e79 fix(page_revision): validate revision search ids`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_page_revision.py::TestPageRevisionCollection::test_find_rejects_non_integer_ids` failed 4 parameterized cases before the fix: malformed IDs did not raise, and comparison was reached for every malformed value.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_page_revision.py::TestPageRevisionCollection::test_find_rejects_non_integer_ids` passed 4 tests after adding search-ID preflight.
- `.venv/bin/python -m pytest -q tests/unit/test_page_revision.py` passed 49 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_page_revision.py tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_page.py::TestPageProperties tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py` passed 304 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1074 tests.
- `.venv/bin/ruff check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed.
- `.venv/bin/ruff format src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` left 2 files unchanged.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `collection.find(None)`, `collection.find(True)`, `collection.find("100")`, and `collection.find(100.0)` raise `ValueError("id must be an integer")`.
- A well-formed integer ID matching an existing revision still returns that revision.
- A well-formed integer ID that is absent from the collection still returns `None`.
- Existing revision list acquisition, source/HTML acquisition, parser diagnostics, cached revision collections, lazy `Page.revisions`, lazy `Page.latest_revision`, page-file reads, and page-vote reads remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private revision data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `True` tightens behavior for a value that could previously match revision ID `1`. Mitigation: `bool` is not a meaningful revision ID even though it is an `int` subclass, and accepting it can hide caller payload bugs.
- Risk: Rejecting float or string IDs can expose upstream caller bugs. Mitigation: the documented API type is `int`; callers loading IDs from JSON, CLI flags, spreadsheets, or generated ledgers should normalize to non-boolean integers before calling `find(...)`.
- Risk: Diagnostics could expose private revision context. Mitigation: the new error message contains only the input-field name and expected type, not page names, revision comments, source text, rendered HTML, site names, or account details.

## Dependencies

- Existing `PageRevisionCollection` storage and iteration semantics remain authoritative for valid integer IDs.
- Existing revision list acquisition and revision source/HTML acquisition code remains unchanged.
- Existing page-revision parser diagnostics remain unchanged.
- The validation is local to `src/wikidot/module/page_revision.py` and does not affect page lookup, page files, page votes, forum revisions, site search, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered page revision find-ID validation path.

## Upstream-Safe Motivation

Revision lookup is often fed by generated history inventories, audit scripts, migration ledgers, publication checks, or archival indexes. Since `find(...)` compares the supplied ID against stored revision IDs, malformed search keys should fail deterministically before collection scanning rather than producing misleading misses or accidentally matching a boolean ID to integer ID `1`.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established page revision data as a practical workflow through revision-list acquisition, source/HTML acquisition, retry behavior, duplicate fetch reduction, parser diagnostics, response-body diagnostics, parsed-field diagnostics, cache reuse, and lazy page revision reads.
- Existing page-revision drafts covered fetching, parsing, response diagnostics, cached/direct acquisition, parsed revision fields, and stored collection-entry validation; they did not validate the caller-provided `PageRevisionCollection.find(id=...)` search key.
- This slice only validates `PageRevisionCollection.find(...)` inputs. It does not change revision list acquisition, source/HTML acquisition, page-revision parser field extraction, cached revision collections, lazy `Page.revisions`, lazy `Page.latest_revision`, page source/file/vote caches, forum revision behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw revision source, raw rendered revision HTML, revision comments from private pages, source text from real sites, private page content, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed search IDs instead of coercing them. Callers that load revision search targets from JSON, YAML, CLI flags, spreadsheets, generated structures, or audit ledgers should resolve them into non-boolean integers before calling `PageRevisionCollection.find(...)`.
