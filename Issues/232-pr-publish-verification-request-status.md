# PR Draft: Expose Publish Verification Request Status

## Summary

`site.page.publish(...)` returns `PagePublishResult` so browser-free publishing callers can persist compact audit rows after saving a page, optionally verifying source, optionally updating metadata, and resolving post-save page visibility. The result already exposed `source_matches` as a tri-state value and `source_verified` as a convenience boolean, but callers still had to interpret `source_matches is not None` to distinguish "verification was skipped" from "verification was requested but did not match" in result objects and durable ledgers.

This change adds a read-only `PagePublishResult.source_verification_requested` property and includes the same boolean in `PagePublishResult.as_dict()`. The field is derived from `source_matches is not None`, so it does not change publish sequencing, source refresh behavior, metadata updates, post-save visibility polling, exception behavior, or live Wikidot requests.

## Related Issue

Builds on [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md), [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), [028-pr-publish-aggregate-status.md](028-pr-publish-aggregate-status.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [148-pr-publish-result-operation-label.md](148-pr-publish-result-operation-label.md), [204-pr-publish-source-verification-site-context.md](204-pr-publish-source-verification-site-context.md), [226-pr-publish-visibility-404-context.md](226-pr-publish-visibility-404-context.md), and [231-pr-publish-result-url.md](231-pr-publish-result-url.md). Those drafts established browser-free publishing, source verification, source normalization, source-before-metadata ordering, compact audit dictionaries, operation labels, URL export, and publish failure context as practical rollout-backed surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Add `PagePublishResult.source_verification_requested -> bool`.
- Include `"source_verification_requested"` in `PagePublishResult.as_dict()` alongside `source_matches` and `source_verified`.
- Extend publish result regressions to cover matched, skipped, and constructed-mismatch verification states.
- Preserve publish create/edit sequencing, source verification behavior, metadata side effects, post-save visibility polling, and existing result fields.

## Type Of Change

- Feature / ergonomics improvement
- Browser-free publishing ledger improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Publish results expose whether source verification was requested without requiring caller-side `source_matches is not None` branching. | `TestSitePageAccessor.test_publish_result_exposes_aggregate_operation_statuses` asserts `source_verification_requested` is true for matched and constructed-mismatch results and false for skipped verification. | Treating only successful verification as requested, or treating skipped verification as requested, rejects this local completion claim. |
| Publish audit dictionaries include the same low-cardinality verification-request field. | `TestSitePageAccessor.test_publish_result_exports_audit_record` asserts `"source_verification_requested": True` in `result.as_dict()`. | Omitting the key, returning `source_verified`, or returning a non-boolean value rejects this local completion claim. |
| The new field is side-effect-free and does not change publish behavior. | Implementation derives the value from `self.source_matches is not None`; adjacent site/page tests passed 198 tests. | Triggering lazy page/source acquisition, changing create/edit branching, changing metadata writes, changing source refresh, or changing mismatch exceptions rejects this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `7e4762c feat(site): expose publish verification request status`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` failed before the fix with `AttributeError: 'PagePublishResult' object has no attribute 'source_verification_requested'`.
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

- `PagePublishResult.source_verification_requested` returns `True` when `source_matches` is `True` or `False`.
- `PagePublishResult.source_verification_requested` returns `False` when `source_matches` is `None`.
- `PagePublishResult.as_dict()` includes `"source_verification_requested"` and does not include raw `Page` objects, source text, metadata payloads, tags, parent names, exceptions, credentials, cookies, or auth data.
- Reading `PagePublishResult.source_verification_requested` and `PagePublishResult.as_dict()` does not trigger live Wikidot requests.
- Existing `PagePublishResult.page`, `page_id`, `source_matches`, `tags_updated`, `parent_updated`, `metas_updated`, `created`, `operation`, `url`, `metadata_updated`, and `source_verified` behavior remains unchanged.
- Existing create/edit, source verification, source normalization, post-save visibility, metadata update, and publish failure behavior remains unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, non-goals, verification, and false-positive rejection checks.
- `Issues/README.md` records the local draft and implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Browser-free publishing workflows commonly persist `PagePublishResult.as_dict()` rows into JSONL or TSV-derived ledgers. `source_verified` is useful for success summaries, but it intentionally reports `False` both when verification was skipped and when a constructed result records a mismatch. A separate `source_verification_requested` boolean gives ledger writers a low-cardinality field for "requested versus skipped" without requiring every caller to encode the tri-state `source_matches` convention.

## Local Evidence, Not For Upstream Paste

- The broader local browser-free publishing draft records practical workflows that saved pages, verified source, updated tags, parent, and meta tags, and wrote audit ledgers.
- Local follow-ups already added `created`, aggregate publish status properties, `PagePublishResult.as_dict()`, `operation`, and `url` because publish callers needed structured result data.
- This slice follows the same ledger ergonomics pattern as [147-pr-source-result-error-type.md](147-pr-source-result-error-type.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), and [231-pr-publish-result-url.md](231-pr-publish-result-url.md): expose already-known low-cardinality result fields without triggering new network work.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not add JSON encoding helpers, file writing, source text serialization, metadata payload serialization, partial-failure result objects, write retries, or live Wikidot behavior. It only exposes the source-verification request status already encoded in `source_matches` and includes it in the existing compact publish audit dictionary.
