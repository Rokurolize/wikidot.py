# Local Issue And PR Drafts

These are local-only drafts prepared from Codex rollout evidence. They are not filed upstream.

## Drafts

- [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md): upstream PR draft for robust page lookup, direct page probing, and create/edit post-save behavior.
- [002-pr-batch-source-page-id-lookups.md](002-pr-batch-source-page-id-lookups.md): upstream PR draft for committed page-detail batching optimizations.
- [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md): feature issue draft for a high-level browser-free page publishing workflow.
- [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md): feature issue draft for large ListPages/source collection ergonomics.
- [005-pr-bound-listpages-pagination-by-limit.md](005-pr-bound-listpages-pagination-by-limit.md): upstream PR draft for the committed bounded ListPages pagination optimization.
- [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md): upstream PR draft for the committed batched source-fetch retry improvement.
- [007-pr-batch-meta-tag-updates.md](007-pr-batch-meta-tag-updates.md): upstream PR draft for the committed meta-tag batching optimization.
- [008-pr-skip-cached-source-fetches.md](008-pr-skip-cached-source-fetches.md): upstream PR draft for the committed cache-aware source-fetch optimization.
- [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md): upstream PR draft for the committed cache-aware revision, vote, and file detail optimization.
- [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md): upstream PR draft for the committed batched file-fetch retry improvement.
- [011-pr-robust-meta-tag-parsing.md](011-pr-robust-meta-tag-parsing.md): upstream PR draft for the committed robust meta-tag parsing improvement.
- [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md): upstream PR draft for the committed batched page metadata update helper.
- [013-pr-refresh-cached-page-source.md](013-pr-refresh-cached-page-source.md): upstream PR draft for the committed explicit page source refresh helper.
- [014-pr-preserve-viewsource-text.md](014-pr-preserve-viewsource-text.md): upstream PR draft for the committed multiline ViewSource text preservation fix.
- [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md): upstream PR draft for the committed retry-aware revision source and HTML fetch improvement.
- [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md): upstream PR draft for the committed retry-aware ListPages pagination improvement.
- [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md): upstream PR draft for the committed browser-free page publish helper.
- [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md): upstream PR draft for the committed bounded page search iterator.
- [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md): upstream PR draft for the committed page source iterator with fallback.
- [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md): upstream PR draft for the committed publish source verification normalizer hook.
- [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md): upstream PR draft for the committed publish post-save visibility retry hook.
- [022-pr-source-iterator-large-fallback-batch.md](022-pr-source-iterator-large-fallback-batch.md): upstream PR draft for the committed source iterator fallback batch-size fix.
- [023-pr-search-pagination-validation.md](023-pr-search-pagination-validation.md): upstream PR draft for the committed search pagination validation fix.
- [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md): upstream PR draft for the committed publish create/edit outcome field.
- [025-pr-source-result-error-page-context.md](025-pr-source-result-error-page-context.md): upstream PR draft for the committed source iterator failure context fix.
- [026-pr-source-iterator-parse-failure-isolation.md](026-pr-source-iterator-parse-failure-isolation.md): upstream PR draft for the committed source iterator parse failure isolation fix.

## Local Evidence Index

- Thread workspace ledger: `/home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/artifacts/rollout_wikidot_ledger.md`
- Focused practical evidence scan: `/home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/artifacts/rollout_lines_practical_evidence.txt`
- Local implementation branch: `codex/research-019e8a3a`
- Local implementation commits: `41c1639 fix: harden wikidot parsing and request behavior`, `e188565 perf(page): batch source page id lookups`, `2021378 perf(page): batch page id lookups for page details`, `de3c6c5 perf(page): bound listpages pagination by limit`, `3be148e test(page): cover zero listpages limit`, `4964296 fix(page): retry batched source fetches`, `6f41847 perf(page): batch meta tag updates`, `4e7f54b perf(page): skip cached source fetches`, `e7e9084 fix(page): preserve fallback edit page id`, `c505a11 perf(page): skip cached detail fetches`, `b5cd8ce fix(page): retry batched file fetches`, `3a4e96e fix(page): parse meta tags with html parser`, `d2a6fe6 feat(page): batch page metadata updates`, `ada455f feat(page): refresh cached source`, `f89b170 fix(page): preserve viewsource text`, `2d79241 fix(page_revision): retry revision fetches`, `8f09f91 fix(page): retry listpages pagination`, `087312d feat(site): add browser-free page publish helper`, `9f7b2da feat(site): iterate page searches in bounded chunks`, `9d82979 feat(site): iterate page sources with fallback`, `ebb3434 feat(site): normalize publish source verification`, `bfe364c feat(site): retry publish page visibility`, `52cf6ce fix(site): retry missing source fallback batches`, `5982ad7 fix(page): validate search pagination parameters`, `763c270 feat(site): report publish create outcome`, `988bbea fix(site): include page name in source failures`, `3a4d63c fix(site): isolate source parse failures`

Do not paste private rollout paths, credentials, or local account names into upstream issues. Use the upstream-safe summaries in each draft.
