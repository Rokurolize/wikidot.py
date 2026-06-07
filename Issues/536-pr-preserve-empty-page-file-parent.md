# PR Draft: Preserve Empty Page File Collection Parent State

## Summary

`PageFileCollection(page=None, files=[])` remained constructible after the earlier explicit parent validation slice, but the constructor did not assign the public `page` attribute for that empty no-parent branch. Direct callers, fixture builders, generated attachment ledgers, migration audits, cached file-list setup, and downstream rehydration paths could create the collection and then hit `AttributeError: 'PageFileCollection' object has no attribute 'page'` when inspecting the collection parent state.

This change makes the empty no-parent state explicit by storing `self.page = None` and updates the collection parent annotation to `Page | None`. Valid explicit `Page` parents, first-file parent inference, empty file collections, ID/name lookup, direct file acquisition, lazy `Page.files`, duplicate cached file reuse, parser diagnostics, direct `PageFile` field validation, and adjacent page workflows remain unchanged.

## Outcome

Empty no-parent page-file collections now expose the readable `page is None` sentinel instead of leaking a missing-attribute error.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free attachment inventories, generated asset ledgers, migration audits, publication checks, duplicate cached file-list reuse, lazy `Page.files`, direct `PageFileCollection.acquire(page)`, or local tests that construct `PageFileCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page attachments and page-file inventories as practical workflow surfaces. Existing drafts [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [224-pr-page-file-batch-response-body-context.md](224-pr-page-file-batch-response-body-context.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [383-pr-validate-page-file-find-by-name.md](383-pr-validate-page-file-find-by-name.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md), [471-pr-validate-page-file-collection-page-field.md](471-pr-validate-page-file-collection-page-field.md), and [493-pr-validate-page-constructor-files-cache.md](493-pr-validate-page-constructor-files-cache.md) establish file fetches, parser diagnostics, response diagnostics, duplicate cache reuse, lookup validation, collection entry validation, direct parent-page validation, direct file scalar/text validation, explicit collection parent validation, and cached `Page.files` validation as active operational boundaries.

This is not a duplicate of Issue 471. Issue 471 validates non-`None` explicit collection parents and preserves `page=None` inference plus empty no-parent construction, but it did not assert that an empty no-parent collection exposes a readable `page is None` sentinel. This slice repairs that direct-state gap without changing explicit parent validation, file-entry validation, file lookup, direct acquisition, lazy cache behavior, or live Wikidot behavior.

No upstream issue was filed from this local workspace.

## Changes

- Assign `self.page = None` when `PageFileCollection` is constructed with `page=None` and no files.
- Type the collection parent as `Page | None` to match supported constructor semantics.
- Preserve valid explicit parents, first-file parent inference, empty collection chaining, ID/name lookup, direct acquisition, lazy files, duplicate cached file reuse, parser diagnostics, and adjacent page behavior.

## Type Of Change

- Contract repair
- Public collection constructor state hardening
- Page file parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageFileCollection(page=None, files=[])` must expose `page is None` and length 0 instead of raising `AttributeError` on `collection.page`. |
| R2 | `PageFileCollection(page=<valid Page>, files=[])` and `PageFileCollection(page=<valid Page>, files=[valid_file])` must remain valid. |
| R3 | `PageFileCollection(page=None, files=[valid_file])` must still infer the parent from the first file. |
| R4 | Existing malformed explicit parent validation from Issue 471 must continue to reject non-`Page` values with `ValueError("page must be a Page")`. |
| R5 | Direct file acquisition, lazy `Page.files`, duplicate cached file reuse, parser diagnostics, lookup helpers, and adjacent page workflows must remain unchanged. |
| R6 | Page-file tests, adjacent page workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Empty no-parent construction leaves a readable `page is None` state. | `test_init_empty_without_page_exposes_none_page` failed RED before the fix with `AttributeError: 'PageFileCollection' object has no attribute 'page'`, then passed GREEN after the constructor assigned `None`. | Missing `page`, raising `AttributeError`, rejecting `page=None`, or changing the empty collection length rejects this local completion claim. | PageFileCollection constructor | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | Explicit valid parent paths remain stable. | The focused constructor GREEN command covered `test_init_with_page`; the module and adjacent page suites also passed. | Losing the explicit parent, changing valid empty-list behavior, or changing valid file-list construction rejects this local completion claim. | PageFileCollection constructor | `tests/unit/test_page_file.py` |
| R3 | First-file parent inference remains available. | The focused constructor GREEN command covered `test_init_infers_page_from_files`. | Rejecting omitted parents with non-empty files or failing to preserve inferred parent state rejects this local completion claim. | PageFileCollection constructor | `tests/unit/test_page_file.py` |
| R4 | Existing malformed explicit parent preflight remains intact. | The focused constructor GREEN command covered 4 malformed explicit parent cases, all still raising `ValueError("page must be a Page")`. | Accepting booleans, strings, dictionaries, arbitrary objects, or emitting malformed explicit parent state rejects this local completion claim. | Constructor validation | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R5 | Existing page-file and adjacent page workflows remain stable. | `tests/unit/test_page_file.py` passed 83 tests and adjacent page workflow tests passed 793 tests. | Regressing direct file acquisition, lazy files, parser diagnostics, duplicate cached file reuse, file lookup, page source/revision/vote workflows, publish/create/edit, or site/page workflows rejects this local completion claim. | Page file and adjacent page workflows | `tests/unit/test_page.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py` |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, page-file module passed, adjacent page workflows passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic state and local mocks; this draft contains no credentials, cookies, auth JSON, raw response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, attachment payloads, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `a90ce9c fix(page_file): preserve empty collection parent`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollection::test_init_empty_without_page_exposes_none_page -q` failed before the fix with `AttributeError: 'PageFileCollection' object has no attribute 'page'`.
- GREEN focused constructor coverage: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollection::test_init_empty_without_page_exposes_none_page tests/unit/test_page_file.py::TestPageFileCollection::test_init_with_page tests/unit/test_page_file.py::TestPageFileCollection::test_init_infers_page_from_files tests/unit/test_page_file.py::TestPageFileCollection::test_init_rejects_malformed_pages -q` passed 7 tests.
- `uv run pytest tests/unit/test_page_file.py -q` passed 83 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 793 tests.
- `uv run pytest tests/unit -q` passed 2554 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageFileCollection(page=None, files=[])` returns an empty collection with `collection.page is None`.
- `PageFileCollection(page=<valid Page>, files=[])` keeps that explicit parent.
- `PageFileCollection(page=<valid Page>, files=[valid_file])` remains valid.
- `PageFileCollection(page=None, files=[valid_file])` still infers the parent from the first valid file.
- Malformed explicit parent values from Issue 471 still raise `ValueError("page must be a Page")`.
- Existing valid `PageFile` lists, iteration, `find(...)`, `find_by_name(...)`, direct file acquisition, lazy `Page.files`, parser-side attachment diagnostics, direct `PageFile` field validation, duplicate cached file reuse, and adjacent page workflows remain green.
- The tests use local synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be mistaken for a broader collection consistency change. Mitigation: this slice only makes the already constructible empty no-parent state readable.
- Risk: Optional parent typing could be read as permission to use a parentless collection for remote file acquisition. Mitigation: acquisition paths still construct collections with real pages, and this slice does not change request construction or parser-created collection state.
- Risk: This could be confused with Issue 471. Mitigation: Issue 471 validates malformed explicit non-`None` parent pages; this slice fixes the missing public attribute for the preserved empty no-parent branch.

## Out Of Scope

Changing file-list parsing, comparing collection parent identity with each contained file, coercing dictionaries into pages, rejecting `page=None`, changing direct acquisition, changing lazy `Page.files`, changing live Wikidot behavior, changing page revision/vote/source collection contracts, and creating upstream Issues or PRs are outside this slice.

## Why This Matters

The empty no-parent state is useful for local fixtures, attachment ledgers, migration audits, and generated workflows that may construct a file collection before a concrete `Page` owner is attached. A readable `page is None` sentinel is easier to reason about than a constructor that succeeds but leaves the public parent attribute missing.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used browser-free file acquisition, duplicate cached file reuse, lazy file state, attachment ledgers, page publish verification, and tests that seed file collections directly.
- Issue 471 preserved `page=None` inference and empty no-parent construction, but the constructor branch was not covered by an assertion and left the public attribute unset.
- The focused RED failure reproduced the missing public state without live Wikidot access. The GREEN regression now proves the empty collection exposes the documented sentinel while the broader page and repository gates prove adjacent behavior remains stable.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, page source text, attachment payloads, private content, private site data, and source text from real sites out of upstream discussion.
