# PR Draft: Validate PageSource Constructor Page

## Summary

`PageSource(...)` already validates `wiki_text`, and page/revision cache paths already validate that cached sources belong to the owning page. One direct constructor gap remained: `PageSource(page=...)` accepted arbitrary non-`Page` objects while still storing source text around malformed parent-page state.

This change validates the direct constructor page field at `PageSource.__post_init__()`. Malformed constructor pages now raise `ValueError("page must be a Page")`, while valid `Page` instances and existing wiki-text validation remain unchanged.

## Outcome

Direct `PageSource(...)` rows cannot store malformed parent-page state. Valid parser-created, fixture-created, cached, and directly constructed page source records remain accepted when they carry a real `Page` parent and string wiki text.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free source reads, source/result ledgers, page/revision comparison tools, local fixtures, serialized source records, migration checks, or rehydrated `PageSource` objects before page-source cache ownership is checked by a later `Page` or `PageRevision` access path.

## Current Evidence

Issue [430-pr-validate-page-source-wiki-text.md](430-pr-validate-page-source-wiki-text.md) established direct `PageSource.wiki_text` validation. Issues [600-pr-validate-page-source-cache-ownership.md](600-pr-validate-page-source-cache-ownership.md), [601-pr-validate-page-revision-source-cache-ownership.md](601-pr-validate-page-revision-source-cache-ownership.md), [661-pr-validate-source-result-retained-owner-page-id-state.md](661-pr-validate-source-result-retained-owner-page-id-state.md), and [663-pr-validate-page-revision-source-cache-retained-page-id-state.md](663-pr-validate-page-revision-source-cache-retained-page-id-state.md) establish that source ownership and parent-page identity are operational boundaries for source acquisition, cached source reuse, revision reads, source-result ledgers, and migration/audit workflows.

This slice is not a duplicate of those drafts. Issue 430 validates `wiki_text`, not the retained `page` object. Issues 600 and 601 validate source-cache ownership when a `PageSource` is stored on a `Page` or `PageRevision`, not the direct `PageSource(page=...)` constructor boundary. Issues 661 and 663 validate retained owner IDs and source-result/cache coherence, not direct source parent object type. No upstream issue was filed from this local workspace.

## Related Issue / Non-Duplicate Analysis

Builds directly on [430-pr-validate-page-source-wiki-text.md](430-pr-validate-page-source-wiki-text.md), [600-pr-validate-page-source-cache-ownership.md](600-pr-validate-page-source-cache-ownership.md), [601-pr-validate-page-revision-source-cache-ownership.md](601-pr-validate-page-revision-source-cache-ownership.md), [661-pr-validate-source-result-retained-owner-page-id-state.md](661-pr-validate-source-result-retained-owner-page-id-state.md), [663-pr-validate-page-revision-source-cache-retained-page-id-state.md](663-pr-validate-page-revision-source-cache-retained-page-id-state.md), and the broader parent-object constructor validation pattern in [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), and [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md).

## Changes

- Add a direct `PageSource` parent-page validator using `ValueError("page must be a Page")`.
- Validate `self.page` at the start of `PageSource.__post_init__()` before the existing `wiki_text` validation.
- Keep the runtime `Page` import local to the validator to preserve the existing `Page` / `PageSource` import cycle boundary.
- Update page source unit tests to use the real no-HTTP `Page` fixture instead of `MagicMock` placeholders.

## Type Of Change

- State validation
- Page source constructor hardening
- Parent-page integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageSource(page=...)` must reject `None`, `True`, `"test-page"`, `{"fullname": "test-page"}`, and arbitrary objects with `ValueError("page must be a Page")`. |
| R2 | Valid `Page` objects must remain accepted, and the retained page object identity must be preserved. |
| R3 | Existing `wiki_text` validation must remain unchanged for non-string source text once the page is valid. |
| R4 | Page, page revision, source cache, source-result, and site source-iterator workflows must remain compatible. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, page-source tests, adjacent page/source/revision/site coverage, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct pages fail at the constructor boundary. | `test_page_source_rejects_malformed_page` failed RED for five malformed pages with `DID NOT RAISE`, then passed GREEN after `PageSource.__post_init__()` validated `self.page`. | Accepting non-`Page` values, coercing values, or deferring failure to page cache ownership paths rejects this local completion claim. | `PageSource` constructor | `src/wikidot/module/page_source.py`, `tests/unit/test_page_source.py` |
| R2 | Valid `Page` parents remain accepted and retained. | `test_page_source_accepts_string_wiki_text` passed with the `mock_page_no_http` fixture and asserts object identity. | Replacing, copying, rejecting, or lazily resolving valid `Page` parents rejects this local completion claim. | `PageSource` constructor | `tests/unit/test_page_source.py` |
| R3 | Existing source text validation remains stable. | `test_page_source_rejects_non_string_wiki_text` passed for `None`, `True`, `1`, and `["source"]` with a valid page parent. | Changing the existing `wiki_text must be a string` diagnostic or accepting non-string source text rejects this local completion claim. | `PageSource` source text | `tests/unit/test_page_source.py` |
| R4 | Adjacent source workflows remain compatible. | Adjacent page/source/revision/site coverage passed 1118 tests, and full unit coverage passed 3534 tests. | Breaking page source reads, source cache ownership, page revision source behavior, source-result behavior, or site source iterator behavior rejects this local completion claim. | Page/source workflows | `tests/unit/test_page.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_site.py` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic pages and no-HTTP fixtures only. | Using credentials, cookies, auth JSON, private site data, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, page-source/adjacent/full-unit tests, ruff, format check, mypy, pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `f38bcb5 fix(page_source): validate constructor page`.

- RED: `uv run pytest tests/unit/test_page_source.py::test_page_source_rejects_malformed_page -q` failed 5 malformed page cases before the fix with `DID NOT RAISE`.
- GREEN: the same focused command passed 5 tests after direct constructor page validation was added.
- `uv run pytest tests/unit/test_page_source.py -q` passed 11 tests.
- `uv run pytest tests/unit/test_page_source.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_constructor.py tests/unit/test_site.py -q` passed 1118 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run pytest tests/unit -q` passed 3534 tests.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `PageSource(page=None)`, `PageSource(page=True)`, `PageSource(page="test-page")`, `PageSource(page={"fullname": "test-page"})`, and `PageSource(page=object())` raise `ValueError("page must be a Page")`.
- Valid `PageSource(page=<Page>, wiki_text=<str>)` construction preserves the exact `Page` object and source text.
- Existing non-string `wiki_text` values still raise `ValueError("wiki_text must be a string")` when the parent page is valid.
- Page source reads, page source cache ownership, page revision source cache ownership, source-result ledgers, page constructor coverage, and site source iterator behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Tests or downstream code may have used `MagicMock` or duck-typed page placeholders when creating direct `PageSource` records. Mitigation: `PageSource.page` participates in page/revision source cache ownership, source-result ledgers, and adjacent page workflows, so requiring a real `Page` keeps this constructor aligned with existing parent-object validation boundaries.
- Risk: A top-level runtime import of `Page` could create an import cycle. Mitigation: the validator imports `Page` inside the helper, preserving the existing `Page` imports `PageSource` relationship.
- Risk: Constructor validation order could hide wiki-text diagnostics when both fields are bad. Mitigation: the page parent is the structural owner boundary; existing wiki-text diagnostics remain unchanged once the parent page is valid.

## Dependencies

- Existing `Page` class identity remains the parent-page contract.
- Existing page source, page revision source, source-result, page constructor, and site source-iterator validators remain otherwise unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked action/read boundaries, response-body field-type checks, direct parser/scalar conversions, retained parent-site/client/page surfaces, mixed-site or mixed-client single-request batch checks, result ergonomics, or true complexity candidates outside this now-covered `PageSource(page=...)` constructor boundary.

## Upstream-Safe Motivation

`PageSource` is the source text record used by page-source reads, revision-source reads, source-result ledgers, cache ownership checks, migration comparisons, and browser-free source workflows. Constructor-side page validation keeps malformed local fixtures, serialized records, or rehydrated source rows from carrying arbitrary parent objects into those workflows while preserving valid page parents and existing source text validation.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work repeatedly used page source reads and source-result ledgers for browser-free source capture, translation/migration comparison, publish verification, and audit reporting.
- Existing local drafts covered `PageSource.wiki_text`, `Page.source` cache ownership, `PageRevision.source` cache ownership, source-result retained owner IDs, and page/revision source retained ID state, but did not validate the direct `PageSource.page` field.
- The focused RED failure showed malformed direct pages could be stored. The GREEN regressions cover malformed page rejection, valid page preservation, existing wiki-text validation, adjacent page/source/revision/site behavior, full unit compatibility, lint, format, type, pyright, and whitespace gates.
- This slice only validates direct `PageSource(page=...)` constructor state. It does not change source acquisition HTTP behavior, page/revision cache ownership semantics, source text parsing, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private site data, raw action responses, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The test fixture update is intentional: direct `PageSource` construction should prove valid source text behavior with a real no-HTTP `Page`, not a generic mock, because the constructor now enforces the same parent object shape that downstream cache ownership logic relies on.
