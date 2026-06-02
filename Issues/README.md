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

## Local Evidence Index

- Thread workspace ledger: `/home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/artifacts/rollout_wikidot_ledger.md`
- Focused practical evidence scan: `/home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/artifacts/rollout_lines_practical_evidence.txt`
- Local implementation branch: `codex/research-019e8a3a`
- Local implementation commits: `41c1639 fix: harden wikidot parsing and request behavior`, `e188565 perf(page): batch source page id lookups`, `2021378 perf(page): batch page id lookups for page details`, `de3c6c5 perf(page): bound listpages pagination by limit`, `3be148e test(page): cover zero listpages limit`, `4964296 fix(page): retry batched source fetches`, `6f41847 perf(page): batch meta tag updates`, `4e7f54b perf(page): skip cached source fetches`, `e7e9084 fix(page): preserve fallback edit page id`, `c505a11 perf(page): skip cached detail fetches`, `b5cd8ce fix(page): retry batched file fetches`, `3a4e96e fix(page): parse meta tags with html parser`

Do not paste private rollout paths, credentials, or local account names into upstream issues. Use the upstream-safe summaries in each draft.
