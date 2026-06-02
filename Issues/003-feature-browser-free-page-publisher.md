# Feature Draft: High-Level Browser-Free Page Publishing Workflow

## Background / Problem

Automation that publishes or updates Wikidot pages currently has to combine several low-level pieces manually:

- acquire a page edit lock
- call `savePage`
- discover or verify the public page ID
- fetch `ViewSourceModule` output for roundtrip verification
- save tags
- set parent page
- set meta tags
- retry direct page visibility after save

The library exposes many of these primitives, but practical users still end up writing raw AMC dictionaries for the full workflow. That makes scripts harder to review and increases the chance of inconsistent handling around locks, stale ListPages results, and post-save verification.

## Proposed Solution

Add a high-level page publishing helper that wraps the common browser-free workflow while reusing existing `Page` APIs internally.

Possible shape:

```python
result = site.page.publish(
    fullname="target-page",
    title="Target Page",
    source="[[module ListPages]]",
    comment="Automated update",
    tags=["tag-one", "tag-two"],
    parent_fullname="parent-page",
    metas={"codex-source": "example"},
    force_edit=True,
    verify_source=True,
)

assert result.page.id
assert result.source_matches
```

The exact API name can change; the important contract is that callers can publish and verify a page without hand-writing AMC payloads.

## Alternatives Considered

- Keep using `Page.create_or_edit()`, `Page.set_metadata()`, and optional direct source verification separately. This now reduces post-save metadata duplication, but it still does not centralize lock/save/visibility/source-verification sequencing or return structured publish status.
- Document raw `site.amc_request(...)` payloads. This preserves flexibility but gives callers no safer default workflow.

## Use Case

Bulk translation or test-site publishing needs to write many pages from local source files, then verify that Wikidot accepted the saved source and metadata. The desired path is a browser-free script using wikidot.py rather than Playwright or manual browser automation.

## Acceptance Criteria

- The helper can create a new page and edit an existing page.
- The helper can optionally set tags, parent, and meta tags after saving, reusing `Page.set_metadata()` where possible.
- The helper can optionally verify saved source by fetching `ViewSourceModule`.
- It returns structured result data: page object, page id, source verification status, and metadata operation statuses.
- It raises existing wikidot.py exceptions where possible, with clear failure details for lock, save, source verification, tags, parent, and meta operations.
- Unit tests cover new page, existing page, stale direct visibility, tag/parent/meta updates, and failed source verification.

## Upstream-Safe Motivation

wikidot.py is useful as a browser-free client for Wikidot page operations. A high-level publish helper would let users rely on library-tested sequencing instead of duplicating raw AMC payloads in every automation script.

## Local Evidence, Not For Upstream Paste

- Local rollout `019e6067-989d-73f1-86a4-a2f0abc22af7` recorded that browser-free AMC usage was preferred over browser automation for lock acquisition, `savePage`, public URL retrieval, and tag saving.
- Local rollout `019e7a39-505b-76b3-bfb4-b68be3c71fb9` included a publishing script that imported `wikidot`, used `AjaxModuleConnectorConfig`, then manually implemented `save_page`, `view_source`, `set_metadata`, tags, parent, and meta operations.
- The local hardening commit `41c1639` fixed several edge cases this helper would rely on, and local commit `d2a6fe6` added a smaller `Page.set_metadata()` slice for the post-save metadata phase.

## Additional Information

This should be filed as a feature issue before implementation. It is larger than the small batching PRs in [002-pr-batch-source-page-id-lookups.md](002-pr-batch-source-page-id-lookups.md), [007-pr-batch-meta-tag-updates.md](007-pr-batch-meta-tag-updates.md), [011-pr-robust-meta-tag-parsing.md](011-pr-robust-meta-tag-parsing.md), and [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md).
