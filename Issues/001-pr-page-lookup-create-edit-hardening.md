# PR Draft: Harden Page Lookup, Direct Probes, And Create/Edit Save Results

## Summary

Improve page lookup and page create/edit behavior when Wikidot's ListPagesModule response is stale, incomplete, or temporarily inconsistent with direct page visibility.

This PR should be kept narrower than the local preservation commit `41c1639`. The upstreamable slice is:

- treat ListPages misses as inconclusive when a direct page URL exposes `WIKIREQUEST.info.pageId`
- return a usable `Page` after successful create/edit even when ListPages has not caught up
- tolerate empty or placeholder ListPages fields where Wikidot emits template markers or missing values
- preserve existing exception behavior for genuinely missing pages and failed saves
- cover the behavior with unit fixtures and focused integration notes

## Related Issue

Drafted from local rollout evidence; no upstream issue filed yet.

## Changes

- Add direct page-id probing for `Site.page.get(fullname, raise_when_not_found=False)` after a ListPages miss.
- Add a fallback synthesized `Page` after `Page.create_or_edit(...)` succeeds but immediate ListPages lookup returns no page.
- Preserve a known edit `page_id` on the fallback synthesized `Page`.
- Normalize placeholder `rating_percent` and missing metadata into values compatible with the `Page` dataclass contract.
- Keep failed direct probes as `None` for missing pages rather than surfacing parser-only failures to callers.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Test addition/modification
- [ ] CI/CD or build related

## Testing

Local preservation commit: `41c1639 fix: harden wikidot parsing and request behavior`

Follow-up implementation commit: `e7e9084 fix(page): preserve fallback edit page id`

Validation already run locally before drafting:

- [x] `uv run pytest tests/unit -q` passed with 514 tests in the shared checkout before the later source-batching test was added.
- [x] `uv run ruff check src tests` passed.
- [x] `uv run ruff format --check src tests` passed.
- [x] `uv run mypy src tests --install-types --non-interactive` passed after dataclass fallback typing fixes.
- [x] `git diff --check` passed.
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_edit_existing_page_stale_search_preserves_page_id -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCreateOrEdit -q` passed with 7 tests.
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 66 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 525 tests.
- [x] `uv run --extra lint ruff check src tests`
- [x] `uv run --extra format ruff format --check src tests`
- [x] `uv run --extra lint mypy src tests --install-types --non-interactive`
- [x] `git diff --check`

## Acceptance Criteria

- `site.page.get("existing-page", raise_when_not_found=False)` can return a `Page` when ListPages misses but the direct page HTML exposes a page id.
- `site.page.get("missing-page", raise_when_not_found=False)` still returns `None`.
- `site.page.create(..., force_edit=True)` and `Page.edit(...)` return a usable `Page` immediately after a successful `savePage` response, even if ListPages is stale.
- A fallback `Page` synthesized after editing an existing page preserves the caller-provided page ID.
- Placeholder or missing ListPages fields do not produce invalid `Page` dataclass values.
- Existing public APIs remain source-compatible.

## Upstream-Safe Motivation

Wikidot page metadata endpoints can lag behind direct page visibility after create/edit, and ListPages-generated fields can contain placeholders. Callers that successfully save a page should not be forced to reimplement direct URL probing or synthesize page objects outside the library.

## Local Evidence, Not For Upstream Paste

- Local rollout `019e6067-989d-73f1-86a4-a2f0abc22af7` recorded that existing probes used wikidot.py's AMC API for lock acquisition, `savePage`, public URL retrieval, and tag saving because it was lighter than browser automation.
- Local rollout `019e7a39-505b-76b3-bfb4-b68be3c71fb9` contained a publishing script that manually reimplemented page-id probing, `savePage`, `ViewSourceModule`, `saveTags`, parent setting, and meta tag setting.
- Thread workspace evidence files are listed in [README.md](README.md).

## Additional Notes

For upstream review quality, consider splitting parser/AMC retry hardening from the page create/edit fallback if the local `41c1639` diff is too broad.

Follow-up [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md) removes duplicate save-response decoding on the failed `savePage` path while preserving the create/edit save-result behavior described here.
