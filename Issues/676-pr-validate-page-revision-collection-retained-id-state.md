# PR Draft: Validate PageRevisionCollection Retained Revision IDs

## Summary

`PageRevisionCollection.find(id)` already validates malformed caller-provided search-key types before scanning stored revisions, but the scan still compared retained row state directly: `revision.id == id`. After local fixtures, generated revision ledgers, cached revision collections, serialized records, or rehydrated page revision collections have been mutated incorrectly, booleans and floats can satisfy Python equality against integer revision IDs, while `None`, strings, lists, and negative values are treated as ordinary not-found misses instead of corrupted retained revision state.

This change validates each stored `PageRevision.id` with the existing revision-ID validator before comparison. Malformed retained stored IDs now raise `ValueError("id must be an integer")`, negative retained stored IDs now raise `ValueError("id must be non-negative")`, valid zero-ID lookup remains accepted, and existing absent integer lookup behavior remains unchanged.

## Outcome

Loaded page revision collections can no longer accept, match, or hide corrupted retained revision IDs during local lookup. Valid parser-created collections, directly constructed valid collections, source/HTML acquisition, duplicate cached revision reuse, `Page.revisions`, `Page.latest_revision`, and adjacent page workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page history reads, revision source/HTML comparison, publication verification, translation review ledgers, migration checks, duplicate cached revision reuse, generated reports, or local fixtures that construct, persist, mutate, or rehydrate `PageRevisionCollection` records.

## Current Evidence

Local rollout-backed drafts repeatedly identify page revisions as a practical workflow surface. Existing drafts [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [153-pr-latest-revision-failure-context.md](153-pr-latest-revision-failure-context.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), [222-pr-page-revision-batch-response-body-context.md](222-pr-page-revision-batch-response-body-context.md), [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md), [237-pr-page-revision-number-parse-context.md](237-pr-page-revision-number-parse-context.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [332-pr-page-revision-list-response-body-type-context.md](332-pr-page-revision-list-response-body-type-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), and [472-pr-validate-page-revision-collection-page-field.md](472-pr-validate-page-revision-collection-page-field.md) establish revision acquisition, parsing, cached reuse, lookup validation, collection validation, direct revision field validation, and collection parent validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issue 376 validates caller-provided `PageRevisionCollection.find(id=...)` search-key types before scanning stored revisions, but it does not validate retained IDs already stored inside the collection. Issue 465 validates direct `PageRevision(id=..., rev_no=...)` construction, but it cannot cover a valid revision whose `id` is corrupted after construction and then reused in a collection. Issues 365, 419, and 472 validate collection entry shape, collection initialization, and collection parent state, not retained revision row identity during lookup.

## Related Issue / Non-Duplicate Analysis

Builds directly on [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), [472-pr-validate-page-revision-collection-page-field.md](472-pr-validate-page-revision-collection-page-field.md), and the adjacent retained collection lookup hardening pattern from [670-pr-validate-forum-category-collection-retained-id-state.md](670-pr-validate-forum-category-collection-retained-id-state.md), [671-pr-validate-page-file-collection-retained-id-state.md](671-pr-validate-page-file-collection-retained-id-state.md), [672-pr-validate-forum-post-collection-retained-id-state.md](672-pr-validate-forum-post-collection-retained-id-state.md), [673-pr-validate-forum-thread-collection-retained-id-state.md](673-pr-validate-forum-thread-collection-retained-id-state.md), [674-pr-validate-private-message-collection-retained-id-state.md](674-pr-validate-private-message-collection-retained-id-state.md), and [675-pr-validate-forum-post-revision-collection-retained-identity-state.md](675-pr-validate-forum-post-revision-collection-retained-identity-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate each stored `PageRevision.id` before `PageRevisionCollection.find(id)` compares it to the search key.
- Reject malformed retained stored IDs such as `None`, `True`, `False`, `"100"`, `100.0`, and `[]` with `ValueError("id must be an integer")`.
- Reject negative retained stored IDs with `ValueError("id must be non-negative")`.
- Preserve valid zero retained revision ID lookup.
- Preserve valid existing match and absent integer lookup behavior.
- Preserve revision list acquisition, source/HTML acquisition, parser diagnostics, cached revision collections, lazy `Page.revisions`, lazy `Page.latest_revision`, and adjacent page workflows.

## Type Of Change

- State validation
- Public collection lookup hardening
- Page revision retained identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevisionCollection.find(id)` must reject retained stored `revision.id` values such as `None`, `True`, `False`, `"100"`, `100.0`, and `[]` with `ValueError("id must be an integer")` before comparison. |
| R2 | `PageRevisionCollection.find(id)` must reject retained stored `revision.id=-1` with `ValueError("id must be non-negative")` before comparison. |
| R3 | `PageRevisionCollection.find(0)` must still return a revision whose retained ID is valid integer `0`. |
| R4 | Existing matching lookup, absent integer lookup, search-key type diagnostics, revision source/HTML acquisition, cached duplicate revision reuse, lazy `Page.revisions`, lazy `Page.latest_revision`, and adjacent page workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, raw revision source text, rendered revision HTML, or private revision comments. |
| R6 | Focused RED/GREEN, page-revision tests, adjacent page workflow tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained stored revision IDs fail before Python equality can match booleans/floats or report corrupted values as ordinary misses. | `test_find_rejects_revision_with_malformed_retained_ids` failed RED for six retained values, then passed GREEN after stored `revision.id` validation was added. | Accepting booleans/floats, returning `None` for corrupted retained IDs, coercing values, or scanning without validation rejects this local completion claim. | Page revision collection lookup | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Negative retained stored revision IDs fail with the existing non-negative diagnostic before comparison. | `test_find_rejects_revision_with_negative_retained_id` failed RED as an ordinary miss, then passed GREEN after stored `revision.id` validation was added. | Treating negative retained IDs as ordinary not-found state, accepting them, or coercing them rejects this local completion claim. | Page revision collection lookup | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R3 | Valid zero retained revision IDs remain accepted. | `test_find_accepts_revision_with_zero_retained_id` passed in RED and GREEN. | Rejecting zero IDs or changing valid lookup semantics rejects this local completion claim. | Page revision collection lookup | `tests/unit/test_page_revision.py` |
| R4 | Existing adjacent page workflows remain green. | `tests/unit/test_page_revision.py` passed 148 tests, adjacent page/source/file/vote/site coverage passed 1214 tests, and full unit coverage passed 3237 tests. | Regressing source/HTML acquisition, duplicate cached revisions, parser diagnostics, lazy revision reads, page source/file/vote workflows, create/edit/publish, or site/page behavior rejects this local completion claim. | Page revision workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft excludes private content. | Using credentials, cookies, auth JSON, raw rollout paths, private revision source, rendered HTML, private comments, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, full page-revision and adjacent tests passed, full unit passed, ruff passed, format check passed, mypy passed, temporary pyright passed, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `90fda3c fix(page_revision): validate collection retained ids`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_find_accepts_revision_with_zero_retained_id tests/unit/test_page_revision.py::TestPageRevisionCollection::test_find_rejects_revision_with_malformed_retained_ids tests/unit/test_page_revision.py::TestPageRevisionCollection::test_find_rejects_revision_with_negative_retained_id -q` failed 7 retained malformed/negative stored ID cases before the fix, while the zero-ID compatibility guard passed.
- GREEN: the same focused command passed 8 tests after stored `revision.id` validation was added.
- `uv run ruff format src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_page_revision.py -q` passed 148 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1214 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run pytest tests/unit -q` passed 3237 tests.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `PageRevisionCollection.find(100)` raises `ValueError("id must be an integer")` when a stored revision's retained `revision.id` is `None`, `"100"`, or `[]`.
- `PageRevisionCollection.find(1)`, `find(0)`, and `find(100)` raise `ValueError("id must be an integer")` when stored retained revision IDs are `True`, `False`, or `100.0` before Python equality can match those corrupted values.
- `PageRevisionCollection.find(100)` raises `ValueError("id must be non-negative")` when a stored revision's retained `revision.id` is `-1`.
- `PageRevisionCollection.find(0)` still returns a revision whose retained ID is valid integer `0`.
- Existing valid matching lookup, valid absent integer lookup, search-key type diagnostics, revision list acquisition, source/HTML acquisition, parser diagnostics, cached revision collections, lazy `Page.revisions`, lazy `Page.latest_revision`, page source/file/vote behavior, create/edit/publish behavior, and adjacent site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, raw revision source text, rendered revision HTML, or private revision comments.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Valid-but-absent negative caller search keys remain allowed because this slice only validates retained stored row state. Mitigation: this preserves the search-key scope from Issue 376 and limits behavior change to corrupted stored revision IDs.
- Risk: Rehydrated records with malformed retained IDs now fail earlier. Mitigation: corrupted retained identity state should be corrected before collection lookup; deterministic diagnostics are preferable to bool/float equality matches or misleading not-found results.
- Risk: Diagnostics could expose private revision context. Mitigation: the new diagnostics include only the field name and expected/range constraint, not page names, source text, rendered HTML, revision comments, site names, or account details.

## Dependencies

- Existing `_validate_revision_id(...)` remains the canonical page revision ID validator.
- Existing `PageRevisionCollection.find(id)` caller search-key validation remains unchanged.
- Existing `PageRevision(id=...)` constructor validation remains unchanged.
- Existing source/HTML acquisition and parser behavior remains unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, or complexity candidates outside this now-covered page revision collection retained-ID lookup path.

## Upstream-Safe Motivation

`PageRevisionCollection.find(id)` is a local lookup over already loaded page history records. Caller search keys already have type validation, and stored revision rows should be held to the same retained-ID contract before comparison. Validating stored fields prevents corrupted local state from matching through Python's bool/float equality rules or disappearing as ordinary not-found results, while preserving valid zero IDs, existing absent integer behavior, and all parser/network behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established page revision data as a practical workflow through revision-list acquisition, source/HTML acquisition, retry behavior, duplicate fetch reduction, parser diagnostics, response diagnostics, parsed-field diagnostics, cache reuse, lazy page revision reads, and generated page-history ledgers.
- Existing local drafts covered fetching, parsing, response diagnostics, cached/direct acquisition, parsed revision fields, caller search-key validation, direct constructor identity validation, and stored collection-entry validation; they did not validate retained stored `PageRevision.id` at collection lookup comparison time.
- The focused RED failure showed booleans and floats could be accepted as retained stored revision IDs when they compared equal to explicit integers, while `None`, strings, lists, and negative IDs could be misreported as ordinary not-found lookup results. The GREEN regressions cover malformed rejection, negative rejection, zero-ID compatibility, valid matching lookup, valid absent integer lookup, adjacent page workflows, and full unit compatibility.
- This slice only validates retained stored revision IDs at the loaded collection lookup comparison boundary. It does not change revision-list acquisition, source/HTML acquisition, parser field extraction, cached revision collections, lazy revision access, page source/file/vote behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw revision source text, rendered revision HTML, revision comments from private pages, source text from real sites, private page content, and private site data out of upstream discussion.

## Additional Notes

The change intentionally reuses `_validate_revision_id(...)` only for stored collection rows. It does not add caller search-key range validation in `PageRevisionCollection.find(...)`, preserving the prior lookup-surface scope from Issue 376 and the direct identity-field scope from Issue 465.
