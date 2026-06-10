# PR Draft: Expose Publish Result Fullname

## Summary

`site.page.publish(...)` returns `PagePublishResult` so browser-free publishing callers can persist compact audit rows after save, optional source verification, optional metadata updates, and post-save visibility resolution. The existing publish result dictionary already exported `"fullname"`, and the result object already exposed sibling identity properties such as `site` and `url`, but callers still had to reach through `result.page.fullname` for the direct page fullname property.

This change adds a read-only `PagePublishResult.fullname` property and has `PagePublishResult.as_dict()` reuse that accessor for the existing `"fullname"` field. The value delegates to `result.page.fullname`, so it does not trigger page-ID acquisition, source reads, publish work, metadata writes, live Wikidot calls, or dictionary-shape expansion. Existing publish sequencing, source verification, metadata flags, post-save visibility behavior, exception behavior, `site`, `url`, and audit dictionary keys remain unchanged.

## Problem Statement

Publish-result audit code should be able to read page identity fields consistently from the result object itself. Before this slice, callers could use `result.site`, `result.url`, `result.page_id`, `result.operation`, and `result.as_dict()["fullname"]`, but there was no `result.fullname` property parallel to those fields. That asymmetry encourages repeated `result.page.fullname` access in ledger code and makes the public result surface less coherent than the dictionary it exports.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free publishing and publish audit rows as practical workflow surfaces. The directly related drafts are [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), [028-pr-publish-aggregate-status.md](028-pr-publish-aggregate-status.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [148-pr-publish-result-operation-label.md](148-pr-publish-result-operation-label.md), [231-pr-publish-result-url.md](231-pr-publish-result-url.md), [232-pr-publish-result-source-verification-requested.md](232-pr-publish-result-source-verification-requested.md), [257-pr-publish-result-source-verification-status.md](257-pr-publish-result-source-verification-status.md), [258-pr-publish-result-metadata-count.md](258-pr-publish-result-metadata-count.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [441-pr-validate-publish-result-page-field.md](441-pr-validate-publish-result-page-field.md), [603-pr-validate-publish-result-page-id-coherence.md](603-pr-validate-publish-result-page-id-coherence.md), [651-pr-validate-publish-result-page-id-state.md](651-pr-validate-publish-result-page-id-state.md), [660-pr-validate-publish-result-retained-page-id-state.md](660-pr-validate-publish-result-retained-page-id-state.md), and [777-pr-validate-result-page-fullnames.md](777-pr-validate-result-page-fullnames.md).

This slice is not a duplicate of [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md). Issue 070 added the compact `as_dict()` export and included a `"fullname"` key, but it did not add a direct `PagePublishResult.fullname` property.

This slice is not a duplicate of [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md) or [231-pr-publish-result-url.md](231-pr-publish-result-url.md). Those drafts added sibling `site` and `url` identity properties; this draft completes the same direct-access pattern for the already-exported page fullname.

This slice is not a duplicate of [777-pr-validate-result-page-fullnames.md](777-pr-validate-result-page-fullnames.md). Issue 777 validates retained result-page fullname state at construction time; this draft exposes the validated retained value through the publish result API.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free publishing jobs that write one durable audit row per page.
- Publish verification scripts that compare `site`, `fullname`, `url`, `page_id`, operation, and source verification fields.
- Multi-site publishing ledgers that already consume `PagePublishResult.site` and `PagePublishResult.url`.
- Report generators and retry ledgers that need direct page identity fields without reaching through the retained `Page` object.

## Proposed Fix

- Add `PagePublishResult.fullname -> str`, returning `self.page.fullname`.
- Keep the existing `"fullname"` key in `PagePublishResult.as_dict()` and source it from `self.fullname`.
- Extend the existing publish audit-record regression to assert the property.
- Preserve all existing publish result fields, dictionary keys, validation order, source verification behavior, metadata behavior, URL construction, and live Wikidot behavior.

## Implementation Notes

Implemented locally in commit `e7a2656 feat(site): expose publish result fullnames`.

The implementation mirrors the existing `PagePublishResult.site` and `PagePublishResult.url` pattern: the result object exposes a compact page identity property while the underlying `Page` remains available for callers that need the richer object. No imports, request paths, serialization helpers, caches, JSON helpers, or publish-control-flow changes were added.

The focused RED test first failed because `PagePublishResult` had no `fullname` property. The GREEN implementation added the property, updated the result docstring, and changed the existing `as_dict()` implementation from `self.page.fullname` to `self.fullname` without changing the exported dictionary shape.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| `PagePublishResult.fullname` exposes the same page fullname as the retained `Page`. | `TestSitePageAccessor.test_publish_result_exports_audit_record` asserts `result.fullname == "test-page"`. | Returning a raw `Page`, returning `None`, deriving from URL text, or returning a value that diverges from `result.page.fullname` rejects this local completion claim. |
| The existing publish audit dictionary keeps exporting `"fullname"`. | The same focused test asserts the exact `result.as_dict()` shape, including `"fullname": "test-page"`. | Omitting the key, changing its name, adding raw page objects, or expanding the dictionary with private publish payloads rejects this local completion claim. |
| The property is side-effect-free and does not change publish behavior. | Implementation reads only `self.page.fullname`; adjacent site/page tests and full unit tests passed. | Triggering page-ID lookup, source acquisition, AMC requests, publish actions, metadata writes, or visibility polling from the property rejects this local completion claim. |
| Broad quality gates remain green. | Focused, publish-result subset, adjacent site/page, full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. |

## Tests and Verification

Implemented locally in commit `e7a2656 feat(site): expose publish result fullnames`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q --tb=short` failed before the fix with `AttributeError: 'PagePublishResult' object has no attribute 'fullname'`.
- GREEN focused: the same command passed 1 test after the property and dictionary refactor were added.
- Publish-result subset: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor -k "publish_result" -q --tb=short` passed 47 tests with 55 deselected.
- Adjacent site/page coverage: `uv run pytest tests/unit/test_site.py tests/unit/test_page.py -q --tb=short` passed 837 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3870 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `PagePublishResult.fullname` returns `result.page.fullname`.
- `PagePublishResult.as_dict()` keeps the existing `"fullname"` key and value.
- Reading `PagePublishResult.fullname` does not trigger page-ID lookup, source fetching, publish actions, metadata writes, visibility polling, or live Wikidot access.
- Existing `PagePublishResult.page`, `site`, `url`, `page_id`, `source_matches`, `tags_updated`, `parent_updated`, `metas_updated`, `created`, `operation`, source verification fields, metadata fields, and audit dictionary keys remain unchanged.
- No browser, live Wikidot action, upstream Issue, upstream PR, push, raw response body, account material, credentials, cookies, auth JSON, source text, or private page content is required for this local draft.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: Adding a new public property expands the observable result API. Mitigation: the value is already exposed through `result.page.fullname` and `result.as_dict()["fullname"]`, so the new property formalizes existing deterministic state without changing behavior.
- Risk: Callers could mistake the retained fullname for proof that a live page still exists. Mitigation: the property only reports retained page identity and intentionally performs no live page visibility or existence check.
- Risk: The dictionary refactor could accidentally change exported audit rows. Mitigation: the existing exact dictionary assertion still covers all fields and values.

## Dependencies

- Existing `Page.fullname` remains the retained page identity field.
- Existing `PagePublishResult.as_dict()` remains the compact publish audit export surface.
- Existing publish result validation from prior local slices continues to reject malformed retained page objects, page IDs, status booleans, site state, and result-page fullname state.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, cache ownership boundaries, result ergonomics, or complexity candidates outside this now-covered publish-result fullname accessor path.

## Rationale for Upstream Suitability

Publish result objects already expose compact audit-friendly identity fields and already export page fullname in `as_dict()`. A direct `fullname` property makes the public result surface consistent with `site`, `url`, `page_id`, and `operation`, reduces caller-side reach-through into the retained `Page`, and avoids new network behavior, serialization behavior, or private data exposure.

## Local Evidence

- Local browser-free publishing drafts repeatedly use publish results as durable audit rows for save, source verification, metadata update, and retry/report workflows.
- Existing local drafts covered compact audit dictionaries, operation labels, source verification fields, metadata counters, site identity, URL identity, publish result page validation, page-ID coherence, retained page-ID validation, and result-page fullname validation. They did not cover a direct `PagePublishResult.fullname` property.
- The focused RED failure showed callers had no direct property even though the retained page fullname was already validated and exported through `as_dict()`.
- This slice only exposes already-retained page identity. It does not change source verification, metadata updates, post-save visibility polling, publish actions, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw page source, private page content, private site data, and private forum metadata out of upstream discussion.

## Additional Notes

This implementation intentionally does not add JSON encoding helpers, file writing, URL normalization, page existence probes, source text serialization, metadata payload serialization, partial-failure publish result objects, write retries, or live Wikidot behavior. It only exposes the retained page fullname already available from the wrapped page and keeps the existing compact publish audit dictionary stable.
