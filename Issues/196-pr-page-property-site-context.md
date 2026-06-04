# PR Draft: Include Site Context In Page Property Failures

## Summary

`Page.revisions`, `Page.latest_revision`, `Page.votes`, and `Page.files` are direct page-level properties that lazy-load Wikidot page details and raise `NotFoundException` when the detail cannot be resolved after the existing fetch path. Earlier local slices made the underlying retry/fetch and parser surfaces more explicit, but these final property fallback messages still named only the page fullname, such as `Cannot find page revisions: scp-001`. That is ambiguous in multi-site ledgers where several Wikidot sites can contain the same page fullname.

This follow-up keeps lazy loading, request payloads, retry behavior, collection types, revision matching, exception type, and successful behavior unchanged. It only adds the site unix name to the page-property fallback errors: `Cannot find page revisions for site: <site>, page: <fullname>`, `Cannot find latest revision for site: <site>, page: <fullname> (rev_no=<n>)`, `Cannot find page votes for site: <site>, page: <fullname>`, and `Cannot find page files for site: <site>, page: <fullname>`.

## Related Issue

Builds on [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [192-pr-page-auxiliary-fetch-site-context.md](192-pr-page-auxiliary-fetch-site-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [194-pr-page-source-site-context.md](194-pr-page-source-site-context.md), and [195-pr-source-iterator-site-context.md](195-pr-source-iterator-site-context.md). Those drafts established practical local demand for direct page property fetches, deduplicated/batched page detail acquisition, and site-aware diagnostics in source, file, and auxiliary page workflows.

No upstream issue was filed from this local workspace.

## Changes

- Include `self.site.unix_name` and `self.fullname` in the `Page.revisions` fallback `NotFoundException`.
- Include `self.site.unix_name`, `self.fullname`, and the expected `revisions_count` in the `Page.latest_revision` fallback `NotFoundException`.
- Include `self.site.unix_name` and `self.fullname` in the `Page.votes` fallback `NotFoundException`.
- Include `self.site.unix_name` and `self.fullname` in the `Page.files` fallback `NotFoundException`.
- Preserve request construction, retry exhaustion behavior, collection setters, revision ordering, `rev_no` matching, and exception type.

## Type Of Change

- Bug fix / diagnostics improvement
- Multi-site page-detail ledger context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| `Page.revisions` still lazy-loads through `PageCollection(...).get_page_revisions()` and raises `NotFoundException` only when `_revisions` remains unset. | `TestPageProperties.test_revisions_property_includes_page_context_when_retry_is_exhausted` asserts the existing request payload and a site/page message after exhausted retry. | Changing request payloads, bypassing lazy loading, fabricating an empty collection, or leaving a page-only message rejects this local completion claim. |
| `Page.latest_revision` still returns the revision whose `rev_no` equals `revisions_count`, and its miss message preserves the expected revision number. | `TestPageProperties.test_latest_revision_includes_page_context_when_not_found` asserts `Cannot find latest revision for site: test-site, page: test-page (rev_no=5)`. | Dropping `rev_no`, changing revision matching, or changing successful latest revision behavior rejects this local completion claim. |
| `Page.votes` still lazy-loads through `PageCollection(...).get_page_votes()` and raises `NotFoundException` only when `_votes` remains unset. | `TestPageProperties.test_votes_property_includes_page_context_when_retry_is_exhausted` asserts the existing request payload and a site/page message after exhausted retry. | Changing request payloads, treating a missing vote collection as success, or leaving a page-only message rejects this local completion claim. |
| `Page.files` still lazy-loads through `PageCollection(...).get_page_files()` and raises `NotFoundException` only when `_files` remains unset. | `TestPageProperties.test_files_property_includes_page_context_when_retry_is_exhausted` asserts the existing request payload and a site/page message after exhausted retry. | Changing request payloads, treating a missing file collection as success, or leaving a page-only message rejects this local completion claim. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 182 tests. | Regressions in source loading, page ID lookup, ListPages parsing, source iterators, discussion/meta fetches, or page-file acquisition reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `bac092a fix(page): include site in page property failures`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_revisions_property_includes_page_context_when_retry_is_exhausted -q` failed before the fix because the message was `Cannot find page revisions: test-page`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_revisions_property_includes_page_context_when_retry_is_exhausted -q`.
- RED: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_votes_property_includes_page_context_when_retry_is_exhausted -q` failed before the fix because the message was `Cannot find page votes: test-page`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_votes_property_includes_page_context_when_retry_is_exhausted -q`.
- RED: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_latest_revision_includes_page_context_when_not_found -q` failed before the fix because the message was `Cannot find latest revision: test-page (rev_no=5)`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_latest_revision_includes_page_context_when_not_found -q`.
- RED: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_files_property_includes_page_context_when_retry_is_exhausted -q` failed before the fix because the message was `Cannot find page files: test-page`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_files_property_includes_page_context_when_retry_is_exhausted -q`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_revisions_property_includes_page_context_when_retry_is_exhausted tests/unit/test_page.py::TestPageProperties::test_votes_property_includes_page_context_when_retry_is_exhausted tests/unit/test_page.py::TestPageProperties::test_latest_revision_includes_page_context_when_not_found tests/unit/test_page.py::TestPageProperties::test_files_property_includes_page_context_when_retry_is_exhausted -q` passed 4 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 182 tests.
- `uv run pytest tests/unit -q` passed 733 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Page.revisions`, `Page.latest_revision`, `Page.votes`, and `Page.files` continue to use the existing lazy-load paths and successful return types.
- Exhausted or unresolved page property detail lookups keep raising `NotFoundException`.
- Every changed fallback message now includes the site unix name and page fullname.
- The `latest_revision` fallback message still includes the expected revision number.
- Request payloads, retry behavior, parser behavior, collection setters, source behavior, discussion/meta behavior, and direct page-file acquisition remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Large local Codex workflows use page detail properties while traversing multiple Wikidot sites and often write plain-text error ledgers. A page-only fallback message forces downstream code to recover context from surrounding objects or log rows, and makes failures involving common fullnames such as `start`, `system:join`, or `scp-001` harder to audit. Adding the site unix name keeps the public behavior strict while making the existing errors self-contained.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified page revision, vote, file, source, and auxiliary page details as practical workflow surfaces for corpus collection and audit ledgers.
- Recent site-context slices showed the same low-risk pattern: add compact site/object identifiers to existing plain-text exceptions without changing successful behavior.
- This slice only claims direct page property fallback diagnostics. It does not claim any live Wikidot behavior change.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not add a shared exception helper. The four changed properties are close together, and the surgical f-string updates avoid creating a broader abstraction before there is a stronger reason to do so.
