# PR Draft: Validate Forum Post Pager Page ASCII Shape

## Summary

`ForumPostCollection.acquire_all_in_threads(...)` parses the first forum post-list response pager to decide whether additional `forum/ForumViewThreadPostsModule` pages should be fetched. The current response-wide pager scan uses `page_text.isdigit()` before `int(page_text)`, so generated labels containing Unicode digit glyphs such as `"\uff12"` are accepted and normalized into ordinary page number `2`. That can turn malformed generated pager metadata into a real follow-up forum post-list request.

This change accepts forum post-list pager page labels only when they match ASCII digits. Ordinary non-numeric pager labels such as `next` continue to be ignored, valid ASCII pagination still fetches subsequent pages, authored-content pager markup remains scoped away from the response-wide pager, and digit-like non-ASCII labels now fail with `NoElementException("Forum post list pager page is malformed ...")` including site, thread, page, field, and observed value context.

## Outcome

Forum post-list acquisition no longer fabricates pagination traversal from malformed generated pager labels. A thread post-list response with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like pager text now fails at the pager boundary instead of issuing unintended extra page requests.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum thread post reads, moderation ledgers, migration checks, discussion audits, local fixtures, or generated workflows where page traversal must come only from structurally valid Wikidot pager metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post lists and forum post source reads as practical workflow surfaces. Existing drafts cover retry-aware post-list fetching, duplicate thread post reduction, cached-thread reuse, authored-content parser scoping, response-body diagnostics, parser diagnostics, post ID and route validation, direct source acquisition, edit workflows, and collection ownership validation.

This slice is not a duplicate of [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), which protects authored forum post content from being mistaken for the response-wide pager. It is not a duplicate of [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), or [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), which cover post-list parser, fetch, and response diagnostics around pager parsing. It is not a duplicate of the forum category/thread href and route validation drafts, which validate IDs after list pagination has already been chosen. This slice covers the accepted-value shape of response-wide forum post-list pager page numbers after the pager has already been selected.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md), [461-pr-validate-forum-post-edit-metadata-fields.md](461-pr-validate-forum-post-edit-metadata-fields.md), [462-pr-validate-forum-post-parent-id-field.md](462-pr-validate-forum-post-parent-id-field.md), and the adjacent response-wide pager-page drafts [750-pr-validate-site-member-pager-page-ascii-shape.md](750-pr-validate-site-member-pager-page-ascii-shape.md) and [751-pr-validate-private-message-pager-page-ascii-shape.md](751-pr-validate-private-message-pager-page-ascii-shape.md).

## Changes

- Add a local pager-page parser for `ForumPostCollection.acquire_all_in_threads(...)` that accepts only `[0-9]+` before integer conversion.
- Raise `NoElementException` with site, thread, first-page, field, and observed value context when a pager label is digit-like but not ASCII digits.
- Preserve ordinary non-numeric pager labels, missing pager behavior, valid ASCII pagination, paginated retry exhaustion handling, list response-body diagnostics, post-row parsing, authored-content pager filtering, cached-thread behavior, duplicate thread-ID handling, source acquisition, edit workflows, and reply workflows.
- Add focused regression coverage for a response-wide forum post-list pager containing fullwidth page label `"\uff12"`.

## Type Of Change

- Bug fix
- Forum post-list pager scalar-shape validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A response-wide forum post-list pager label containing non-ASCII digit glyphs must fail before any extra page request is issued. |
| R2 | The malformed pager diagnostic must include site, thread, page, field, and observed value context. |
| R3 | Valid ASCII pager labels must continue to fetch subsequent forum post-list pages. |
| R4 | Ordinary non-numeric pager labels such as `next` must continue to be ignored. |
| R5 | Authored-content-local pager markup must continue to be ignored as post content, not response pagination. |
| R6 | Existing list response-body, retry-exhaustion, parser-context, duplicate-thread, cached-thread, source acquisition, edit, reply, and adjacent forum workflows must remain compatible. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, real forum content, raw generated HTML from real accounts, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, forum-post tests, adjacent forum tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `"\uff12"` in the response-wide pager raises before a page-2 request can be made. | `test_acquire_all_rejects_non_ascii_digit_pager_target` failed RED with `DID NOT RAISE`, then passed after ASCII-only pager parsing. | Returning posts, normalizing `"\uff12"` into page `2`, issuing a second request, or silently dropping the malformed digit rejects this local completion claim. | Forum post-list pager parser | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | The exception reports `Forum post list pager page is malformed for site: test-site, thread: 3001, page: 1 (field=page, value=\uff12)`. | The focused regression asserts the exact diagnostic family and contextual fields. | A raw `ValueError`, omitted site/thread/page context, omitted scalar value, or unrelated post-row diagnostic rejects this local completion claim. | Pager diagnostics | focused test |
| R3 | Valid ASCII pager label `2` still fetches page 2 and appends paginated posts. | Focused GREEN included `test_acquire_all_pagination`. | Failing to fetch page 2, changing request payloads, or returning only first-page posts rejects this local completion claim. | Valid pagination | forum-post pagination test |
| R4 | `next` remains ignored when no numeric page label exists. | Focused GREEN included `test_acquire_all_ignores_non_numeric_pager_targets`. | Raising for `next` or making a synthetic extra request rejects this local completion claim. | Non-numeric pager compatibility | forum-post pager tests |
| R5 | Pager-like markup inside authored post content remains scoped away from response pagination. | Focused GREEN included `test_acquire_all_ignores_content_pager_markup`. | Treating authored post content as response pagination or issuing a page-2 request rejects this local completion claim. | Content scoping | forum-post content-pager test |
| R6 | Adjacent forum workflows remain green. | `tests/unit/test_forum_post.py` passed 293 tests, adjacent forum suite passed 903 tests, and full unit passed 3753 tests. | Regressing first-page retry exhaustion, paginated retry exhaustion, response-body diagnostics, post-row parser context, duplicate-thread handling, cached-thread behavior, source acquisition, edit workflows, reply workflows, category/thread/post revision behavior, or any unit test rejects this local completion claim. | Forum workflows | `tests/unit` |
| R7 | No live site state or private material is needed. | The regression uses synthetic unit-level forum post-list HTML and mock AMC responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, real account names, real forum content, or raw generated HTML from real accounts rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, forum-post tests, adjacent forum tests, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `efee046 fix(forum_post): validate pager page shape`.

- RED: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_pager_target -q` failed before the fix with `DID NOT RAISE` because pager label `"\uff12"` was accepted and normalized as page `2`.
- GREEN focused pager slice: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_pager_target tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_pagination tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_ignores_non_numeric_pager_targets tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_ignores_content_pager_markup tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_raises_when_paginated_retry_is_exhausted tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_missing_paginated_response_body_includes_thread_and_page_context -q` passed 6 tests.
- `uv run --extra test pytest tests/unit/test_forum_post.py -q` passed 293 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 903 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 3753 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no forum-post pager-boundary, compatibility, architecture, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker: `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, launcher SHA256 `0518e09af8c6a44990de082462039c9593a8f969a8e0eb10426aa6b3dcf630be`.

## Acceptance Criteria

- `ForumPostCollection.acquire_all_in_thread(thread)` raises `NoElementException("Forum post list pager page is malformed ...")` for a response-wide pager label whose text is `"\uff12"`.
- The malformed pager diagnostic includes `site: test-site`, `thread: 3001`, `page: 1`, `field=page`, and `value=\uff12` context.
- The parser does not issue a page-2 forum post-list request from non-ASCII digit pager text.
- Valid ASCII response-wide pager labels such as `2` still fetch and parse paginated forum post lists.
- Ordinary non-numeric pager labels such as `next` still leave the post list as a single-page result when no numeric page label exists.
- Authored-content-local pager-like markup is still ignored as post content and does not drive response-wide pagination.
- Existing forum post-list response-body diagnostics, retry-exhaustion behavior, parser-context diagnostics, duplicate-thread handling, cached-thread behavior, source acquisition, edit workflows, replies, adjacent forum suites, and full unit behavior remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real accounts, raw rollout path, real account name, real forum content, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with authored-content pager scoping. Mitigation: content pager markup remains covered by Issue 097; this slice validates response-wide pager page-label shape after pager selection.
- Risk: This could be confused with forum category/thread href ID validation. Mitigation: href route and ID shape remain covered by their own drafts; this slice runs before post rows and related IDs are parsed.
- Risk: This could break ordinary pager labels such as `next`. Mitigation: non-numeric labels are still ignored; only digit-like non-ASCII labels that the old code treated as numeric now fail.
- Risk: This could break valid pagination. Mitigation: ASCII `[0-9]+` labels still convert to integers, and the existing paginated acquisition test remains green.
- Risk: Diagnostics could expose forum content. Mitigation: the new diagnostic includes only site/thread/page context and the malformed pager scalar; tests use synthetic HTML and do not include real forum content.
- Risk: Another digit-like Unicode category could behave differently than fullwidth digits. Mitigation: the code rejects any `str.isdigit()` value that does not match ASCII digits, covering fullwidth, superscript, Arabic-Indic, and similar digit glyphs.

## Dependencies

- BeautifulSoup continues to expose generated pager target text through `get_text(strip=True)`.
- Normal Wikidot forum post-list pager page labels are expected to be ASCII decimal digits.
- `ForumPostCollection._pager_from_html(...)` continues to scope the response-wide pager before page-number parsing.
- `ForumPostCollection._post_list_response_body(...)` continues to validate first and paginated response bodies before pager and row parsing.

## Open Questions

None for this local slice. Future forum post-list pagination changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Forum post-list pagination is a browser-free acquisition boundary. Unicode digit normalization can silently turn malformed generated pager text into a valid-looking page request, which is surprising and hard to diagnose in moderation, migration, or discussion ledgers. Requiring ASCII digits keeps generated pagination strict while preserving valid Wikidot pager behavior and existing parser diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: fullwidth digit pager text was accepted and normalized into page `2`.
- Existing local drafts covered forum post-list retries, duplicate source reduction, duplicate thread post reduction, cached-thread reuse, authored-content parser scoping, response-body diagnostics, parser diagnostics, post ID and route validation, direct source acquisition, edit workflows, and collection ownership validation; they did not validate Unicode digit normalization in response-wide forum post-list pager labels.
- This slice does not change request module names, retry policy, valid ASCII pagination, first-page parsing, paginated response-body diagnostics, post-row parsing, content-pager scoping, source acquisition, edit workflows, reply behavior, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated HTML from real accounts, real account names, real forum content, private site data, and private page source out of upstream discussion.
