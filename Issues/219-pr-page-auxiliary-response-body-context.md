# PR Draft: Validate Page Discussion And Metas Response Bodies

## Summary

`Page.discussion` retrieves generated `forum/ForumCommentsListModule` markup to find the backing discussion thread ID, while `Page.metas` retrieves generated `edit/EditMetaModule` markup to parse page meta tags. Earlier local slices made both auxiliary page reads retry-aware and site/page-context-rich for exhausted fetches, and later slices hardened related parser and response-boundary paths. The remaining malformed response-body paths still read `response.json()["body"]`, so an AMC response without a `body` field leaked a raw `KeyError` before the page auxiliary boundary could report which site and page produced the malformed response.

This follow-up keeps request payloads, retry-exhausted `None` handling, discussion-thread lookup, no-discussion caching, meta tag decoding, flexible meta attribute parsing, meta mutation batching, and cached property behavior unchanged. It only treats discussion and meta responses without JSON `body` fields as malformed generated-module responses and raises `NoElementException` with site and page context before regex or HTML parsing.

## Related Issue

Builds on [045-pr-retry-page-discussion-fetch.md](045-pr-retry-page-discussion-fetch.md), [046-pr-retry-page-meta-fetch.md](046-pr-retry-page-meta-fetch.md), [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), and [192-pr-page-auxiliary-fetch-site-context.md](192-pr-page-auxiliary-fetch-site-context.md). Those drafts established page auxiliary reads as practical retry-aware workflows with page context, action/read boundary protection, and metadata mutation safety.

No upstream issue was filed from this local workspace.

## Changes

- Read page discussion response bodies with `response.json().get("body")`.
- Read page metas response bodies with `response.json().get("body")`.
- Convert missing `forum/ForumCommentsListModule` response `body` fields into `NoElementException` with site and page context.
- Convert missing `edit/EditMetaModule` response `body` fields into `NoElementException` with site and page context.
- Preserve retry-exhausted `None` handling as `UnexpectedException`.
- Preserve discussion thread-ID extraction, no-discussion checked-state behavior, successful meta decoding, flexible meta tag parsing, meta mutation batching, and cached property reads.
- Add focused regressions for missing page discussion and metas response bodies through public `Page` properties.

## Type Of Change

- Bug fix / diagnostics improvement
- Page auxiliary response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A page discussion response without JSON `body` fails before thread-ID regex parsing. | `TestPageProperties.test_discussion_missing_response_body_includes_page_context` returns `{}` from the AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, marks discussion checked, fabricates no discussion, or calls `ForumThread.get_from_id` rejects this local completion claim. |
| A page metas response without JSON `body` fails before entity restoration or BeautifulSoup parsing. | `TestPageWriteMethods.test_metas_getter_missing_response_body_includes_page_context` returns `{}` from the AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, stores an empty meta dict, or enters meta parsing rejects this local completion claim. |
| Malformed auxiliary response errors identify site and page. | The focused regressions assert `Page discussion response body is not found for site: test-site, page: test-page` and `Page metas response body is not found for site: test-site, page: test-page`. | An exception without site/page context rejects this local completion claim. |
| Retry-exhausted `None` responses remain distinct from malformed response bodies. | Existing discussion and metas retry-exhausted tests remain green and preserve `UnexpectedException`. | A change that turns retry exhaustion into body-validation failure rejects this local completion claim. |
| Existing page auxiliary behavior remains green. | `uv run pytest tests/unit/test_page.py -q` passed 118 tests. | Regressions in discussion lookup, no-discussion checked state, metas parsing, meta decoding, metadata writes, or page workflows reject this local completion claim. |
| Adjacent page/site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 265 tests. | Regressions in page source/revision/vote/file/site flows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `28b2745 fix(page): validate auxiliary response bodies`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_discussion_missing_response_body_includes_page_context -q` failed before the discussion fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_discussion_missing_response_body_includes_page_context -q` passed after the discussion fix.
- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_missing_response_body_includes_page_context -q` failed before the metas fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_missing_response_body_includes_page_context -q` passed after the metas fix.
- `uv run pytest tests/unit/test_page.py::TestPageProperties::test_discussion_missing_response_body_includes_page_context tests/unit/test_page.py::TestPageProperties::test_discussion_retries_transient_fetch_failures tests/unit/test_page.py::TestPageProperties::test_discussion_raises_when_retry_is_exhausted tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_missing_response_body_includes_page_context tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_parses_decoded_flexible_markup tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_retries_transient_fetch_failures tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_raises_when_retry_is_exhausted -q` passed 7 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 118 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 265 tests.
- `uv run pytest tests/unit -q` passed 761 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Page.discussion` still uses retry-aware AMC and the same `forum/ForumCommentsListModule` request payload.
- `Page.metas` still uses retry-aware AMC and the same `edit/EditMetaModule` request payload.
- A missing page discussion response JSON `body` raises `NoElementException` naming the site and page.
- A missing page metas response JSON `body` raises `NoElementException` naming the site and page.
- Missing response-body handling does not convert retry-exhausted `None` responses into malformed-body failures.
- Discussion thread-ID extraction, no-discussion checked-state behavior, meta tag decoding, flexible meta tag parsing, meta mutation batching, and cached property reads remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, non-goals, verification, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Page discussion and meta reads are small but important page auxiliary lookups. If Wikidot returns malformed generated-module responses, wikidot.py should report a structured failure with the site and page name, not a raw dictionary `KeyError`, so caller logs can route the failure without preserving raw response JSON, generated HTML, credentials, local rollout paths, forum thread details, or private metadata.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established page discussion and meta reads as retry-aware and page-context-rich auxiliary fetches.
- Recent response-body validation slices across private-message, forum-post, forum-category, forum-thread, site-application, site-member, page-file, page-revision, forum-post-revision, and recent-changes modules showed the same raw `KeyError` failure mode at AMC response-body boundaries.
- The refreshed complexity memo continues to list raw response-body boundaries in `page` collection helpers as follow-up leads after this slice removes the direct page discussion/metas raw body reads.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated discussion/meta HTML, and private metadata out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, retry-exhausted `None` handling, discussion thread-ID parsing, no-discussion checked-state behavior, meta entity restoration, meta tag parsing, metadata mutation behavior, cached property reads, or live Wikidot behavior. It only converts missing page discussion and metas response `body` fields into site/page-context `NoElementException` failures before parser work.
