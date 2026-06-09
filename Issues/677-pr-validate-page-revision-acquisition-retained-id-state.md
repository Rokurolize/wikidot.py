# PR Draft: Validate PageRevision Acquisition Retained Revision IDs

## Summary

`PageRevisionCollection.get_sources()` and `get_htmls()` already reject non-`PageRevision` collection entries before fetching, and direct `PageRevision(id=...)` construction validates revision identity fields. The acquisition path still grouped, cached, and requested by retained `revision.id` values directly. If a valid `PageRevision` is later mutated, rehydrated, or fixture-loaded with corrupted retained ID state, `None`, strings, floats, booleans, negative integers, or unhashable values can reach duplicate-cache grouping or AMC request payload construction instead of producing the same deterministic revision-ID diagnostics used elsewhere.

This change validates each retained `PageRevision.id` with the existing revision-ID validator at the start of shared source/HTML acquisition. Malformed retained IDs now raise `ValueError("id must be an integer")`, negative retained IDs now raise `ValueError("id must be non-negative")`, valid zero revision IDs remain accepted, duplicate cached revision reuse is preserved, and acquisition requests are still batched by valid revision ID.

## Outcome

Page revision source and HTML acquisition no longer sends, groups, hashes, or reuses corrupted retained revision IDs. Valid parser-created revisions, directly constructed valid revisions, source fetches, HTML fetches, duplicate cached revision reuse, lazy `Page.revisions`, lazy `Page.latest_revision`, and adjacent page workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page history reads, revision source/HTML comparison, translation review ledgers, publication verification, cached duplicate revision reuse, generated reports, migration checks, or local fixtures that construct, persist, mutate, or rehydrate `PageRevision` objects before source/HTML acquisition.

## Current Evidence

Local rollout-backed drafts repeatedly identify page revision acquisition as a practical workflow surface. Existing drafts [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [153-pr-latest-revision-failure-context.md](153-pr-latest-revision-failure-context.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), [222-pr-page-revision-batch-response-body-context.md](222-pr-page-revision-batch-response-body-context.md), [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md), [237-pr-page-revision-number-parse-context.md](237-pr-page-revision-number-parse-context.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [332-pr-page-revision-list-response-body-type-context.md](332-pr-page-revision-list-response-body-type-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), [472-pr-validate-page-revision-collection-page-field.md](472-pr-validate-page-revision-collection-page-field.md), and [676-pr-validate-page-revision-collection-retained-id-state.md](676-pr-validate-page-revision-collection-retained-id-state.md) establish revision acquisition, parsing, cached reuse, lookup validation, collection validation, direct revision field validation, collection parent validation, and lookup-only retained-ID validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issue 365 validates collection entries before `get_sources()` and `get_htmls()` fetch anything, but it only proves entries are `PageRevision` instances. Issue 465 validates direct `PageRevision(id=..., rev_no=...)` construction, but it cannot cover a valid revision whose `id` is corrupted after construction and then acquired. Issue 676 validates retained `PageRevision.id` during `PageRevisionCollection.find(id)`, but it does not cover source/HTML acquisition grouping, duplicate cached reuse, or AMC payload construction.

## Related Issue / Non-Duplicate Analysis

Builds directly on [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), [472-pr-validate-page-revision-collection-page-field.md](472-pr-validate-page-revision-collection-page-field.md), and [676-pr-validate-page-revision-collection-retained-id-state.md](676-pr-validate-page-revision-collection-retained-id-state.md). It also follows the adjacent retained state hardening pattern from [663-pr-validate-page-revision-source-cache-retained-page-id-state.md](663-pr-validate-page-revision-source-cache-retained-page-id-state.md), [666-pr-validate-forum-post-revisions-cache-retained-id-state.md](666-pr-validate-forum-post-revisions-cache-retained-id-state.md), [675-pr-validate-forum-post-revision-collection-retained-identity-state.md](675-pr-validate-forum-post-revision-collection-retained-identity-state.md), and [676-pr-validate-page-revision-collection-retained-id-state.md](676-pr-validate-page-revision-collection-retained-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate every retained `revision.id` before page revision source/HTML acquisition uses it for duplicate-cache lookup, target grouping, or AMC request payload construction.
- Reject malformed retained IDs such as `None`, `True`, `False`, `"100"`, `100.0`, and `[]` with `ValueError("id must be an integer")`.
- Reject negative retained IDs with `ValueError("id must be non-negative")`.
- Preserve valid zero retained revision IDs for both source and HTML acquisition.
- Preserve duplicate cached revision reuse by grouping and cache-copying through validated integer revision IDs.
- Preserve existing source extraction, HTML extraction, response diagnostics, parser behavior, lazy page revision reads, and adjacent page workflows.

## Type Of Change

- State validation
- Source/HTML acquisition hardening
- Page revision retained identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevisionCollection.get_sources()` must reject retained `revision.id` values such as `None`, `True`, `False`, `"100"`, `100.0`, and `[]` with `ValueError("id must be an integer")` before request construction. |
| R2 | `PageRevisionCollection.get_htmls()` must reject retained `revision.id` values such as `None`, `True`, `False`, `"100"`, `100.0`, and `[]` with `ValueError("id must be an integer")` before request construction. |
| R3 | `get_sources()` and `get_htmls()` must reject retained `revision.id=-1` with `ValueError("id must be non-negative")` before request construction. |
| R4 | Valid retained revision ID `0` must remain accepted for source and HTML acquisition. |
| R5 | Duplicate cached revision reuse, valid source/HTML acquisition, parser diagnostics, lazy `Page.revisions`, lazy `Page.latest_revision`, and adjacent page workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, raw revision source text, rendered revision HTML, or private revision comments. |
| R7 | Focused RED/GREEN, page-revision tests, adjacent page workflow tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained source-acquisition revision IDs fail before grouping, hashing, or request construction. | `test_get_sources_rejects_malformed_retained_revision_ids_before_fetch` failed RED for six retained values, then passed GREEN after acquisition retained-ID validation was added. | Sending malformed IDs, accepting booleans/floats, raising unrelated `zip()` or unhashable errors, coercing values, or calling AMC rejects this local completion claim. | Page revision source acquisition | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Malformed retained HTML-acquisition revision IDs fail before grouping, hashing, or request construction. | `test_get_htmls_rejects_malformed_retained_revision_ids_before_fetch` failed RED for six retained values, then passed GREEN after acquisition retained-ID validation was added. | Sending malformed IDs, accepting booleans/floats, raising unrelated `zip()` or unhashable errors, coercing values, or calling AMC rejects this local completion claim. | Page revision HTML acquisition | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R3 | Negative retained IDs fail with the existing non-negative diagnostic before acquisition uses them. | `test_get_sources_rejects_negative_retained_revision_id_before_fetch` and `test_get_htmls_rejects_negative_retained_revision_id_before_fetch` failed RED as wrong acquisition failures, then passed GREEN. | Treating negative retained IDs as request IDs, ordinary misses, cache keys, or coercible values rejects this local completion claim. | Page revision acquisition | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R4 | Valid zero retained IDs remain accepted for both acquisition modes. | `test_get_sources_accepts_zero_retained_revision_id` and `test_get_htmls_accepts_zero_retained_revision_id` passed after fixture correction and continued to pass GREEN. | Rejecting zero IDs or changing valid zero-ID request payloads rejects this local completion claim. | Page revision source/HTML acquisition | `tests/unit/test_page_revision.py` |
| R5 | Existing page revision behavior and adjacent page workflows remain green. | `tests/unit/test_page_revision.py` passed 164 tests, adjacent page/source/file/vote/site coverage passed 1230 tests, and full unit coverage passed 3253 tests. | Regressing source extraction, HTML extraction, duplicate cached revision reuse, parser diagnostics, lazy revision reads, page source/file/vote workflows, create/edit/publish behavior, or site/page behavior rejects this local completion claim. | Page revision workflows | `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft excludes private content. | Using credentials, cookies, auth JSON, raw rollout paths, private revision source, rendered HTML, private comments, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, full page-revision and adjacent tests passed, full unit passed, ruff passed, format check passed, mypy passed, temporary pyright passed, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `362702e fix(page_revision): validate acquisition retained ids`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_accepts_zero_retained_revision_id tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_rejects_malformed_retained_revision_ids_before_fetch tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_rejects_negative_retained_revision_id_before_fetch tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_accepts_zero_retained_revision_id tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_rejects_malformed_retained_revision_ids_before_fetch tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_rejects_negative_retained_revision_id_before_fetch -q` first exposed an invalid HTML zero-ID fixture, then failed 14 retained malformed/negative stored ID cases while 2 zero-ID compatibility guards passed.
- GREEN: the same focused command passed 16 tests after acquisition retained-ID validation was added.
- `uv run ruff format src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_page_revision.py -q` passed 164 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1230 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run pytest tests/unit -q` passed 3253 tests.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `PageRevisionCollection.get_sources()` raises `ValueError("id must be an integer")` when a stored revision's retained `revision.id` is `None`, `True`, `False`, `"100"`, `100.0`, or `[]`.
- `PageRevisionCollection.get_htmls()` raises `ValueError("id must be an integer")` when a stored revision's retained `revision.id` is `None`, `True`, `False`, `"100"`, `100.0`, or `[]`.
- `get_sources()` and `get_htmls()` raise `ValueError("id must be non-negative")` when a stored revision's retained `revision.id` is `-1`.
- Valid retained revision ID `0` still produces source and HTML acquisition request payloads with `"revision_id": 0`.
- Existing valid source fetch, valid HTML fetch, duplicate cached revision reuse, response-body diagnostics, parser diagnostics, lazy `Page.revisions`, lazy `Page.latest_revision`, page source/file/vote behavior, create/edit/publish behavior, and adjacent site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, raw revision source text, rendered revision HTML, or private revision comments.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rehydrated records with malformed retained IDs now fail before source/HTML acquisition. Mitigation: corrupted retained identity state should be corrected before request construction; deterministic diagnostics are preferable to invalid cache keys, unhashable failures, bool/float equality surprises, or malformed AMC payloads.
- Risk: Duplicate cached revision reuse could accidentally diverge if validation changes grouping order. Mitigation: the implementation validates IDs once, preserves original revision order, and continues grouping/copying by integer revision ID.
- Risk: Diagnostics could expose private revision context. Mitigation: the new diagnostics include only the field name and expected/range constraint, not page names, source text, rendered HTML, revision comments, site names, or account details.

## Dependencies

- Existing `_validate_revision_id(...)` remains the canonical page revision ID validator.
- Existing `PageRevision(id=...)` constructor validation remains unchanged.
- Existing `PageRevisionCollection.find(id)` retained-ID lookup validation from Issue 676 remains unchanged.
- Existing source/HTML response parsing and duplicate cached revision reuse behavior remains unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, or complexity candidates outside this now-covered page revision source/HTML acquisition boundary.

## Upstream-Safe Motivation

Page revision source and HTML acquisition uses retained revision IDs for cache reuse, request grouping, and AMC payload construction. Those retained IDs should satisfy the same integer/non-negative contract as directly constructed revisions before they leave local state. Validating stored fields prevents corrupted local state from becoming invalid request IDs or incidental cache keys, while preserving valid zero IDs, duplicate cached revision reuse, source extraction, HTML extraction, and all parser/network behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established page revision source/HTML acquisition as a practical workflow through page-history reads, duplicate fetch reduction, parser reuse, response diagnostics, cached duplicate revision reuse, lazy page revision access, and generated page-history ledgers.
- Existing local drafts covered page revision acquisition reliability, parsing, response diagnostics, cached/direct acquisition, parsed revision fields, collection entries, caller search-key validation, direct constructor identity validation, and lookup-only retained-ID validation; they did not validate retained stored `PageRevision.id` before source/HTML acquisition grouping or request construction.
- The focused RED failure showed malformed retained IDs could reach acquisition internals as wrong `zip()` failures, unhashable key errors, or malformed payload candidates instead of deterministic revision-ID diagnostics. The GREEN regressions cover malformed rejection, negative rejection, zero-ID compatibility, source acquisition, HTML acquisition, duplicate cached revision reuse, adjacent page workflows, and full unit compatibility.
- This slice only validates retained stored revision IDs at the loaded source/HTML acquisition boundary. It does not change revision-list acquisition, parser field extraction, cached revision collections, lazy revision access, page source/file/vote behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw revision source text, rendered revision HTML, revision comments from private pages, source text from real sites, private page content, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates retained IDs once in the shared `_generic_acquire(...)` path and then reuses those validated integer IDs for acquired-cache indexing, target grouping, request payloads, and response application. This keeps the change local to the source/HTML acquisition boundary while preserving the existing public API surface.
