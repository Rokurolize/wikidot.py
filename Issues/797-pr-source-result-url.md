# PR Draft: Expose Source Result URL

## Summary

`Site.pages.iter_sources(...)` returns one `PageSourceResult` per page so large source-collection callers can persist source successes, per-page failures, and retry targets. The existing source result ledger shape already included `site`, `fullname`, `page_id`, `ok`, `wiki_text`, `error_type`, and `error_message`, but it omitted the canonical page URL that the wrapped `Page` can already derive locally.

This change adds a read-only `PageSourceResult.url` property and includes `"url"` in `PageSourceResult.as_dict()`. The URL delegates to `result.page.get_url()`, so reading it does not trigger page-ID lookup, source fetching, live Wikidot calls, retry work, fallback behavior, or parser changes.

## Problem Statement

Source-collection ledgers are easier to inspect, retry, and reconcile when each row contains both machine-friendly identity and a directly openable page URL. Without a canonical `PageSourceResult.url`, callers that already use `PageSourceResult.as_dict()` still have to repeat `result.page.get_url()` beside the ledger helper, which reintroduces boilerplate into the same persistence path that `as_dict()` was created to simplify.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify page source collection, resumable source ledgers, partial-failure handling, and compact result exports as practical workflow surfaces. The directly related drafts are [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [429-pr-validate-source-result-outcomes.md](429-pr-validate-source-result-outcomes.md), [440-pr-validate-source-result-page-field.md](440-pr-validate-source-result-page-field.md), [776-pr-validate-result-page-sites.md](776-pr-validate-result-page-sites.md), [777-pr-validate-result-page-fullnames.md](777-pr-validate-result-page-fullnames.md), and [778-pr-validate-source-result-source-fullnames.md](778-pr-validate-source-result-source-fullnames.md).

This slice is not a duplicate of [231-pr-publish-result-url.md](231-pr-publish-result-url.md). Issue 231 covers `PagePublishResult.url` for browser-free publish audit records; this draft applies the same result-ergonomics pattern to source iterator ledgers.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Large source-corpus collection jobs that write one durable row per page.
- Retry ledgers that need a human-openable page URL next to `site`, `fullname`, and `page_id`.
- Audit, reconciliation, and reporting scripts that already consume `PageSourceResult.as_dict()`.
- Failure ledgers where a missing source still needs a stable page URL for later inspection.

## Proposed Fix

- Add `PageSourceResult.url -> str`, returning `self.page.get_url()`.
- Include `"url": self.url` in `PageSourceResult.as_dict()` between `fullname` and `page_id`.
- Preserve existing `PageSourceResult.page`, `source`, `error`, `ok`, `site`, `fullname`, `page_id`, `wiki_text`, `error_type`, and `error_message` behavior.
- Add focused regressions proving the property is side-effect-free and exported in both successful and failed source result dictionaries.

## Implementation Notes

Implemented locally in commit `4e682e2 feat(site): expose source result urls`.

The implementation mirrors the existing `PagePublishResult.url` pattern: the result object delegates to `Page.get_url()` and keeps URL construction inside the `Page` abstraction. It does not add new imports, new request paths, new serialization helpers, new caches, or new fallback behavior.

The focused RED tests first failed because `PageSourceResult` had no `url` property and because `PageSourceResult.as_dict()` omitted the `"url"` key. The GREEN implementation added the property, updated the result docstring, and extended the existing ledger-export regression.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| `PageSourceResult.url` exposes the same canonical page URL as the wrapped `Page`. | `TestSitePagesAccessor.test_source_result_exposes_url_without_lookup` asserts `result.url == "https://test-site.wikidot.com/page-one"`. | Returning a raw `Page`, a method object, a malformed URL, or a value that diverges from `Page.get_url()` rejects this local completion claim. |
| Reading the URL is side-effect-free. | The focused property test constructs a page with `_id = None`, patches `PageCollection.get_page_ids`, and asserts no ID lookup or AMC request occurs. | Calling `Page.id`, performing live lookup work, source fetching, retrying, or mutating retained page state rejects this local completion claim. |
| Source-result ledger dictionaries include the URL for both success and failure rows. | `TestSitePagesAccessor.test_iter_sources_result_exports_ledger_record` asserts exact dictionaries with `"url"` for a successful source row and a failed source row. | Omitting `"url"`, including raw objects, including source metadata payloads, or changing existing keys rejects this local completion claim. |
| Existing source iterator behavior remains unchanged. | Focused source-result subset, adjacent site/page/source tests, full unit tests, lint, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Regressions in batching, fallback retry, parse failure isolation, result ordering, source text, error typing, retained page IDs, or static gates reject this local completion claim. |

## Tests and Verification

Implemented locally in commit `4e682e2 feat(site): expose source result urls`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_exposes_url_without_lookup tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exports_ledger_record -q --tb=short` failed before the fix with `AttributeError: 'PageSourceResult' object has no attribute 'url'` and with the expected `"url"` key missing from `as_dict()`.
- GREEN focused: the same command passed 2 tests after the property and dictionary export were added.
- Source-result subset: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor -k "source_result or iter_sources" -q --tb=short` passed 54 tests with 10 deselected.
- Adjacent source/page coverage: `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_page_source.py tests/unit/test_search_pages_query.py -q --tb=short` passed 898 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3870 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `PageSourceResult.url` returns the same URL as `Page.get_url()` for the wrapped page.
- Reading `PageSourceResult.url` does not trigger page-ID lookup, live Wikidot work, source fetching, fallback retry, parser work, or mutation of retained page state.
- `PageSourceResult.as_dict()` includes `"url"` for successful and failed source iterator results.
- Existing `site`, `fullname`, `page_id`, `ok`, `wiki_text`, `error_type`, and `error_message` dictionary fields remain unchanged.
- Existing source iterator batching, fallback retry, parse failure isolation, result ordering, error handling, source cache behavior, and page-ID retained-state behavior remain unchanged.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Compatibility and Risk Notes

- Risk: Adding a new key to `PageSourceResult.as_dict()` may affect callers that compare the exact dictionary shape. Mitigation: `as_dict()` is a convenience ledger helper in a local pre-upstream draft sequence, and the added field is deterministic, string-valued, and consistent with the existing publish-result URL precedent.
- Risk: Callers could mistake the URL for proof that a page currently exists on Wikidot. Mitigation: the property only reports the URL derivable from `site.url` and `page.fullname`; it intentionally does not validate live page visibility.
- Risk: URL export could accidentally trigger lookup work if implemented through `Page.id` or source access. Mitigation: implementation delegates only to `Page.get_url()`, and the focused regression asserts no page-ID lookup or AMC request occurs when `_id` is unset.

## Dependencies

- Existing `Page.get_url()` remains the canonical page URL builder.
- Existing `PageSourceResult.as_dict()` remains the compact source-result ledger export surface.
- Existing source iterator, source fetching, fallback, cache, and parser behavior remain unchanged for valid and failed source results.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, cache ownership boundaries, result ergonomics, or complexity candidates outside this now-covered source-result URL export path.

## Rationale for Upstream Suitability

Source-collection workflows commonly write durable ledgers that are inspected by both scripts and humans. Adding the canonical page URL to `PageSourceResult` follows the existing `PagePublishResult.url` precedent, keeps URL construction in one place, avoids new network behavior, and makes source-result dictionaries immediately more useful for retry and audit without exposing source text beyond the already-present `wiki_text` field.

## Local Evidence

- Local rollout-backed work established source iterator fallback, partial-success preservation, source result context fields, source result page IDs, result page/site validation, and source ownership validation as practical large-corpus source-collection needs.
- Existing local drafts covered source text, failure context, error type, site, fullname, page ID, and ledger dictionary export; they did not cover a directly openable page URL on source result records.
- The focused RED failure showed callers had no `PageSourceResult.url` property and that `as_dict()` omitted `"url"` even though the wrapped page could derive it without lookup work.
- This slice only exposes the already-derivable page URL. It does not change source fetches, fallback retry, parse failure handling, page-ID lookup behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw page source, private page content, private site data, and private forum metadata out of upstream discussion.

## Additional Notes

This implementation intentionally does not add JSON encoding helpers, file writing, link checking, page existence probes, URL normalization beyond `Page.get_url()`, or live Wikidot behavior. It only exposes the page URL already available from the wrapped result page and includes it in the existing compact source-result dictionary.
