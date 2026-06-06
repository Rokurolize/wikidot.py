# PR Draft: Validate PageSource Wiki Text

## Summary

`PageSource` is the source-text wrapper used by lazy page source reads, revision source reads, duplicate source cache reuse, source iterators, publish verification, and source-result ledgers. Its `wiki_text` attribute is documented as `str`, but direct `PageSource(...)` construction accepted malformed non-string values. A caller could construct `PageSource(page=page, wiki_text=True)` or `PageSource(page=page, wiki_text=["source"])`, then store the malformed object in `Page.source`, `PageRevision.source`, or `PageSourceResult`, deferring failures to later code that expects string source text.

This change validates `PageSource.wiki_text` at initialization. Non-string source text now raises `ValueError("wiki_text must be a string")`, while valid strings, including empty source strings, remain accepted. Existing page source acquisition, revision source acquisition, source text extraction, source iterator results, page source assignment validation, source-result outcome validation, and publish behavior remain unchanged.

## Outcome

Caller-created and fixture-created `PageSource` objects can no longer carry malformed source text into page, revision, publish-verification, or ledger workflows.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who construct `PageSource` objects directly for browser-free source reads, revision source snapshots, generated source ledgers, migration tools, translation audits, publish verification, tests, or local cache rehydration.

## Current Evidence

Local rollout-backed drafts repeatedly identify page source state and source ledgers as practical workflow surfaces. Existing drafts [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [013-pr-refresh-cached-page-source.md](013-pr-refresh-cached-page-source.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md), [051-pr-preserve-source-batch-successes.md](051-pr-preserve-source-batch-successes.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [149-pr-page-source-failure-context.md](149-pr-page-source-failure-context.md), [194-pr-page-source-site-context.md](194-pr-page-source-site-context.md), [195-pr-source-iterator-site-context.md](195-pr-source-iterator-site-context.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), [414-pr-validate-page-source-assignments.md](414-pr-validate-page-source-assignments.md), and [429-pr-validate-source-result-outcomes.md](429-pr-validate-source-result-outcomes.md) establish source text as active operational state.

Those prior slices are not duplicates. Issue349 validates page-write API `source` inputs before remote write work, Issue414 validates direct `Page.source = ...` object shape before cache mutation, and Issue429 validates `PageSourceResult(...)` source/error outcome state. None of them validates direct `PageSource(..., wiki_text=...)` construction before malformed source text becomes stored object state.

## Related Issue

Builds directly on [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md), [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), [414-pr-validate-page-source-assignments.md](414-pr-validate-page-source-assignments.md), and [429-pr-validate-source-result-outcomes.md](429-pr-validate-source-result-outcomes.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PageSource.__post_init__()` validation.
- Reject non-string `wiki_text` values with `ValueError("wiki_text must be a string")`.
- Preserve valid string source text, including empty strings.
- Preserve existing `PageSource.page` storage behavior.
- Preserve existing page source acquisition, revision source acquisition, duplicate source cache reuse, source iterator ledgers, page source assignment validation, source-result outcome validation, publish verification, and parsing behavior.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Source text state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageSource(wiki_text=...)` must reject non-string values with `ValueError("wiki_text must be a string")` before construction completes. |
| R2 | Valid source strings, including `""`, must remain accepted and stored unchanged. |
| R3 | Existing page source, page revision source, source iterator, publish verification, source-result, and page/site workflows must remain unchanged. |
| R4 | This slice must not add `PageSource.page` owner/type validation, because existing revision-source fixtures and caller-created cache wrappers rely on page-like objects and separate ownership behavior. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent source tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed source text fails at the public `PageSource` constructor boundary. | `test_page_source_rejects_non_string_wiki_text` failed RED for `None`, `True`, `1`, and `["source"]` with `DID NOT RAISE`, then passed GREEN after `PageSource.__post_init__()` validation was added. | Accepting missing values, booleans, integers, lists, dictionaries, or other non-string source text rejects this local completion claim. | PageSource constructor | `src/wikidot/module/page_source.py`, `tests/unit/test_page_source.py` |
| R2 | Valid source text remains unchanged. | `test_page_source_accepts_string_wiki_text` passed for `""` and `"source text"` after the fix. | Coercing source values, rejecting empty source text, or mutating stored `wiki_text` rejects this local completion claim. | PageSource constructor | `tests/unit/test_page_source.py` |
| R3 | Existing adjacent source workflows remain green. | `tests/unit/test_page_source.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py` passed 509 tests, and full unit tests passed 1620 tests. | Regressing lazy page source reads, revision source reads, source extraction, duplicate cache reuse, source iterators, publish verification, source-result ledgers, or page/site workflows rejects this local completion claim. | Source, page, revision, and site workflows | `tests/unit` |
| R4 | Page object ownership behavior is intentionally unchanged. | The implementation validates only `wiki_text`; existing `PageSource(page=MagicMock(), wiki_text="...")` revision fixtures remain valid. | Rejecting MagicMock page fixtures, requiring exact `Page` ownership, or changing duplicate cached source wrapper ownership rejects this local completion claim. | PageSource page reference | `src/wikidot/module/page_source.py`, `tests/unit/test_page_revision.py` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent source tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `afacb97 fix(page_source): validate wiki text`.

- RED: `uv run pytest tests/unit/test_page_source.py -q` failed 4 tests before the fix; every malformed `wiki_text` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_page_source.py -q` passed 4 tests after adding constructor validation.
- Preservation check: `uv run pytest tests/unit/test_page_source.py -q` passed 6 tests after adding valid string coverage.
- `uv run ruff format src/wikidot/module/page_source.py tests/unit/test_page_source.py` left 2 files unchanged.
- `uv run mypy src/wikidot/module/page_source.py tests/unit/test_page_source.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_page_source.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 509 tests.
- `uv run pytest tests/unit -q` passed 1620 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `PageSource(page=page, wiki_text=None)`, `wiki_text=True`, `wiki_text=1`, and `wiki_text=["source"]` raise `ValueError("wiki_text must be a string")`.
- `PageSource(page=page, wiki_text="")` and `wiki_text="source text"` remain valid and store the exact string.
- Existing lazy page source reads, explicit source refresh, revision source reads, source extraction, duplicate cached source reuse, source iterator rows, source-result ledgers, page source assignment validation, and publish verification remain green.
- `PageSource.page` ownership/type validation is not introduced in this slice.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageSource` is the foundational wrapper for source text across page reads, revision snapshots, iterator results, duplicate cached source reuse, publish verification, and source ledgers. Constructor validation keeps malformed local source text from poisoning those workflows while preserving all valid string source behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used page source collection, revision source snapshots, publish verification, source iterator ledgers, source-result audit dictionaries, and tests that construct `PageSource` directly.
- Existing local drafts covered write API source validation, direct `Page.source` assignment validation, and source-result outcome validation, but did not cover direct `PageSource(..., wiki_text=...)` construction.
- The focused RED failures showed malformed `wiki_text` values were accepted by the dataclass constructor. The GREEN regressions cover malformed text rejection, valid empty and non-empty strings, adjacent page/revision/site workflows, and full unit behavior.
- This slice only validates `PageSource.wiki_text`. It does not change `PageSource.page` ownership, lazy source acquisition, source text extraction, revision source parsing, source iterator behavior, page source setter validation, source-result outcome validation, create/edit, publish, live site behavior, or parser behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed source text instead of coercing it. Callers that load source from generated structures, JSON, YAML, CLI flags, spreadsheets, databases, or ledgers should normalize the final page body to `str` before constructing `PageSource`.
