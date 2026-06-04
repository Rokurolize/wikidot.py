# PR Draft: Expose Publish Result URL

## Summary

`site.page.publish(...)` returns `PagePublishResult` so browser-free publishing callers can persist audit rows after saving, optional source verification, optional metadata updates, and post-save visibility resolution. The existing result object and `as_dict()` export already included `fullname`, `page_id`, create/edit status, source verification fields, and metadata flags, but omitted the page URL that the returned `Page` can already derive locally.

This change adds a read-only `PagePublishResult.url` property and includes the same value in `PagePublishResult.as_dict()`. The URL is derived from `result.page.get_url()`, so it does not trigger page-ID acquisition, source reads, live Wikidot calls, or publish sequencing changes. Existing publish result fields, source verification, metadata updates, post-save visibility retry behavior, exception behavior, and create/edit branching remain unchanged.

## Related Issue

Builds on [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), [028-pr-publish-aggregate-status.md](028-pr-publish-aggregate-status.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [148-pr-publish-result-operation-label.md](148-pr-publish-result-operation-label.md), [204-pr-publish-source-verification-site-context.md](204-pr-publish-source-verification-site-context.md), and [226-pr-publish-visibility-404-context.md](226-pr-publish-visibility-404-context.md). Those drafts established browser-free publishing, source verification, visibility retry, create/edit operation labels, compact audit dictionaries, and publish failure context as practical rollout-backed surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Add `PagePublishResult.url -> str`.
- Include `"url"` in `PagePublishResult.as_dict()` alongside `fullname`, `page_id`, `created`, `operation`, source verification fields, and metadata flags.
- Extend the publish audit-record regression to assert both the property and exported dictionary field.
- Preserve publish create/edit sequencing, source verification, metadata side effects, post-save visibility polling, and existing result fields.

## Type Of Change

- Feature / ergonomics improvement
- Browser-free publishing ledger improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Publish results expose the page URL without requiring caller-side `result.page.get_url()` boilerplate. | `TestSitePageAccessor.test_publish_result_exports_audit_record` asserts `result.url == "https://test-site.wikidot.com/test-page"`. | The RED test failed before the fix because `PagePublishResult` had no `url` attribute. |
| Publish audit dictionaries include the same URL field. | The same focused test asserts `"url": "https://test-site.wikidot.com/test-page"` in `result.as_dict()`. | Omitting the key, returning a raw `Page` object, returning a method object, or using a value that does not match `page.get_url()` rejects this local completion claim. |
| URL export is side-effect-free and does not change publish behavior. | Implementation delegates to `self.page.get_url()` and does not touch publish flow; adjacent site/page tests passed 198 tests. | Triggering lazy page-ID/source acquisition, changing create/edit branching, changing metadata writes, or changing source verification rejects this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `4fd8986 feat(site): expose publish result URL`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` failed before the fix with `AttributeError: 'PagePublishResult' object has no attribute 'url'`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q`.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_reports_create_or_edit_outcome tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exposes_aggregate_operation_statuses tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` passed 3 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 198 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run pytest tests/unit -q` passed 775 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PagePublishResult.url` returns the same URL as `Page.get_url()` for the returned page.
- `PagePublishResult.as_dict()` includes `"url"` and does not include raw `Page` objects, source text, metadata payloads, tags, parent names, exceptions, credentials, cookies, or auth data.
- Reading `PagePublishResult.url` and `PagePublishResult.as_dict()` does not trigger live Wikidot requests.
- Existing `PagePublishResult.page`, `page_id`, `source_matches`, `tags_updated`, `parent_updated`, `metas_updated`, `created`, `operation`, `metadata_updated`, and `source_verified` behavior remains unchanged.
- Existing create/edit, source verification, source normalization, post-save visibility, metadata update, and publish failure behavior remains unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, non-goals, verification, and false-positive rejection checks.
- `Issues/README.md` records the local draft and implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Browser-free publishing workflows commonly persist `PagePublishResult.as_dict()` rows into JSONL or TSV-derived ledgers. A canonical URL lets callers open, retry, reconcile, or report the saved page without repeating `result.page.get_url()` in every ledger writer. Because the URL is already derivable from the returned page object, exposing it keeps the audit record compact while avoiding source text, metadata payloads, credentials, or raw response data.

## Local Evidence, Not For Upstream Paste

- The broader local browser-free publishing draft records practical workflows that saved pages, verified source, updated tags, parent, and meta tags, and wrote audit ledgers.
- Local follow-ups already added `created`, aggregate publish status properties, `PagePublishResult.as_dict()`, and `operation` because publish callers needed structured result data.
- This slice follows the same ledger ergonomics pattern as [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md): expose already-known identity fields in result records without triggering new network work.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not add JSON encoding helpers, file writing, source text serialization, metadata payload serialization, partial-failure result objects, write retries, or live Wikidot behavior. It only exposes the page URL already available from the returned page object and includes it in the existing compact publish audit dictionary.
