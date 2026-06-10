# PR Draft: Validate Forum Thread Pager Page ASCII Shape

## Summary

`ForumThreadCollection.acquire_all_in_category(...)` parses the first category thread-list response pager to decide whether additional `forum/ForumViewCategoryModule` pages should be fetched. The response-wide pager scan used `page_text.isdigit()` before `int(page_text)`, so generated labels containing Unicode digit glyphs such as `"\uff12"` were accepted and normalized into ordinary page number `2`. That could turn malformed generated pager metadata into a real follow-up category thread-list request.

This change accepts category thread-list pager page labels only when they match ASCII digits. Ordinary non-numeric pager labels such as `next` continue to be ignored, valid ASCII pagination still fetches subsequent pages, thread-description pager markup remains scoped away from the response-wide pager, and digit-like non-ASCII labels now fail with `NoElementException("Forum thread list pager page is malformed ...")` including site, category, page, field, and observed value context.

## Outcome

Category thread-list acquisition no longer fabricates pagination traversal from malformed generated pager labels. A `ForumViewCategoryModule` response with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like pager text now fails at the pager boundary instead of issuing unintended extra page requests.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free category thread-list reads, forum inventories, moderation summaries, migration checks, cached category ledgers, local fixtures, or generated workflows where page traversal must come only from structurally valid Wikidot pager metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify category thread-list acquisition as a practical read-heavy forum workflow. Existing drafts cover retry-aware category thread-list fetching, duplicate/cached category behavior, thread-description pager scoping, nested table filtering, title/description spacing, response-body diagnostics, parser diagnostics, thread href route/ID shape validation, direct thread detail acquisition, post traversal, and reply behavior.

This slice is not a duplicate of [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), which protects thread-description content from being mistaken for the response-wide pager. It is not a duplicate of [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), or adjacent parser diagnostics, which cover thread-list row and response behavior around pager parsing. It is not a duplicate of [727-pr-validate-forum-thread-href-id-shape.md](727-pr-validate-forum-thread-href-id-shape.md), [741-pr-validate-forum-thread-href-routes.md](741-pr-validate-forum-thread-href-routes.md), or [747-pr-validate-forum-thread-href-id-ascii-shape.md](747-pr-validate-forum-thread-href-id-ascii-shape.md), which validate thread identity after list pagination has already been chosen.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [486-pr-validate-forum-thread-direct-fields.md](486-pr-validate-forum-thread-direct-fields.md), [504-pr-validate-forum-thread-posts-cache.md](504-pr-validate-forum-thread-posts-cache.md), [681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md](681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md), [727-pr-validate-forum-thread-href-id-shape.md](727-pr-validate-forum-thread-href-id-shape.md), [741-pr-validate-forum-thread-href-routes.md](741-pr-validate-forum-thread-href-routes.md), [743-pr-validate-forum-thread-script-id-ascii-shape.md](743-pr-validate-forum-thread-script-id-ascii-shape.md), [747-pr-validate-forum-thread-href-id-ascii-shape.md](747-pr-validate-forum-thread-href-id-ascii-shape.md), and the adjacent response-wide pager-page drafts [750-pr-validate-site-member-pager-page-ascii-shape.md](750-pr-validate-site-member-pager-page-ascii-shape.md), [751-pr-validate-private-message-pager-page-ascii-shape.md](751-pr-validate-private-message-pager-page-ascii-shape.md), and [752-pr-validate-forum-post-pager-page-ascii-shape.md](752-pr-validate-forum-post-pager-page-ascii-shape.md).

## Changes

- Add a local pager-page parser for `ForumThreadCollection.acquire_all_in_category(...)` that accepts only `[0-9]+` before integer conversion.
- Raise `NoElementException` with site, category, first-page, field, and observed value context when a pager label is digit-like but not ASCII digits.
- Preserve ordinary non-numeric pager labels, missing pager behavior, valid ASCII pagination, paginated retry exhaustion handling, list response-body diagnostics, thread-row parsing, thread-description pager filtering, cached-category behavior, direct thread detail acquisition, post traversal, and reply workflows.
- Add focused regression coverage for a response-wide category thread-list pager containing fullwidth page label `"\uff12"`.

## Type Of Change

- Bug fix
- Forum category thread-list pager scalar-shape validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A response-wide category thread-list pager label containing non-ASCII digit glyphs must fail before any extra page request is issued. |
| R2 | The malformed pager diagnostic must include site, category, page, field, and observed value context. |
| R3 | Valid ASCII pager labels must continue to fetch subsequent category thread-list pages. |
| R4 | Ordinary non-numeric pager labels such as `next` must continue to be ignored. |
| R5 | Thread-description-local pager markup must continue to be ignored as row content, not response pagination. |
| R6 | Existing response-body, retry-exhaustion, parser-context, cached-category, direct thread detail, post traversal, reply, and adjacent forum workflows must remain compatible. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, real forum content, raw generated HTML from real accounts, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, forum-thread tests, adjacent forum tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `"\uff12"` in the response-wide pager raises before a page-2 request can be made. | `test_acquire_all_rejects_non_ascii_digit_pager_link` failed RED with `DID NOT RAISE`, then passed after ASCII-only pager parsing. | Returning threads, normalizing `"\uff12"` into page `2`, issuing a second request, or silently dropping the malformed digit rejects this local completion claim. | Forum category thread-list pager parser | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | The exception reports `Forum thread list pager page is malformed for site: test-site, category: 1001, page: 1 (field=page, value=\uff12)`. | The focused regression asserts the exact diagnostic family and contextual fields. | A raw `ValueError`, omitted site/category/page context, omitted scalar value, or unrelated thread-row diagnostic rejects this local completion claim. | Pager diagnostics | focused test |
| R3 | Valid ASCII pager label `2` still fetches page 2 and appends paginated threads. | Focused GREEN included `test_acquire_all_pagination`. | Failing to fetch page 2, changing request payloads, or returning only first-page threads rejects this local completion claim. | Valid pagination | forum-thread pagination test |
| R4 | `next` remains ignored when no numeric page label exists. | Focused GREEN included `test_acquire_all_ignores_non_numeric_pager_links`. | Raising for `next` or making a synthetic extra request rejects this local completion claim. | Non-numeric pager compatibility | forum-thread pager test |
| R5 | Pager-like markup inside a thread description remains scoped away from response pagination. | Focused GREEN included `test_acquire_all_ignores_description_pager_markup`. | Treating thread-description content as response pagination or issuing a page-2 request rejects this local completion claim. | Description scoping | forum-thread description-pager test |
| R6 | Adjacent forum workflows remain green. | `tests/unit/test_forum_thread.py` passed 234 tests, adjacent forum suite passed 904 tests, and full unit passed 3754 tests. | Regressing first-page retry exhaustion, paginated retry exhaustion, response-body diagnostics, thread-row parser context, cached-category behavior, direct thread detail reads, post traversal, replies, category/post/revision behavior, or any unit test rejects this local completion claim. | Forum workflows | `tests/unit` |
| R7 | No live site state or private material is needed. | The regression uses synthetic unit-level category thread-list HTML and mock AMC responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, real account names, real forum content, or raw generated HTML from real accounts rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, forum-thread tests, adjacent forum tests, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `5d5d87e fix(forum_thread): validate pager page shape`.

- RED: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_pager_link -q` failed before the fix with `DID NOT RAISE` because pager label `"\uff12"` was accepted and normalized as page `2`.
- GREEN focused pager slice: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_pager_link tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_pagination tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_ignores_non_numeric_pager_links tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_ignores_description_pager_markup tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_raises_when_paginated_retry_is_exhausted tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_missing_paginated_response_body_includes_context -q` passed 6 tests.
- `uv run --extra test pytest tests/unit/test_forum_thread.py -q` passed 234 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 904 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 3754 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted after formatting `tests/unit/test_forum_thread.py`.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no forum-thread pager-boundary, compatibility, architecture, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker: `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, launcher SHA256 `0518e09af8c6a44990de082462039c9593a8f969a8e0eb10426aa6b3dcf630be`.

## Acceptance Criteria

- `ForumThreadCollection.acquire_all_in_category(category)` raises `NoElementException("Forum thread list pager page is malformed ...")` for a response-wide pager label whose text is `"\uff12"`.
- The malformed pager diagnostic includes `site: test-site`, `category: 1001`, `page: 1`, `field=page`, and `value=\uff12` context.
- The parser does not issue a page-2 category thread-list request from non-ASCII digit pager text.
- Valid ASCII response-wide pager labels such as `2` still fetch and parse paginated category thread lists.
- Ordinary non-numeric pager labels such as `next` still leave the category thread list as a single-page result when no numeric page label exists.
- Thread-description-local pager-like markup is still ignored as row content and does not drive response-wide pagination.
- Existing response-body diagnostics, retry-exhaustion behavior, parser-context diagnostics, cached-category behavior, direct thread detail reads, post traversal, replies, adjacent forum suites, and full unit behavior remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real accounts, raw rollout path, real account name, real forum content, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with thread-description pager scoping. Mitigation: description pager markup remains covered by Issue 098; this slice validates response-wide pager page-label shape after pager selection.
- Risk: This could be confused with forum thread href ID validation. Mitigation: href route and ID shape remain covered by Issues 727, 741, and 747; this slice runs before thread rows and href IDs drive accepted output.
- Risk: This could break ordinary pager labels such as `next`. Mitigation: non-numeric labels are still ignored; only digit-like non-ASCII labels that the old code treated as numeric now fail.
- Risk: This could break valid pagination. Mitigation: ASCII `[0-9]+` labels still convert to integers, and the existing paginated acquisition test remains green.
- Risk: Diagnostics could expose forum content. Mitigation: the new diagnostic includes only site/category/page context and the malformed pager scalar; tests use synthetic HTML and do not include real forum content.
- Risk: Another digit-like Unicode category could behave differently than fullwidth digits. Mitigation: the code rejects any `str.isdigit()` value that does not match ASCII digits, covering fullwidth, superscript, Arabic-Indic, and similar digit glyphs.

## Dependencies

- BeautifulSoup continues to expose generated pager link text through `get_text(strip=True)`.
- Normal Wikidot category thread-list pager page labels are expected to be ASCII decimal digits.
- `ForumThreadCollection._pager_from_html(...)` continues to scope the response-wide pager before page-number parsing.
- `ForumThreadCollection._thread_list_response_body(...)` continues to validate first and paginated response bodies before pager and row parsing.

## Open Questions

None for this local slice. Future forum thread-list pagination changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Category thread-list pagination is a browser-free acquisition boundary. Unicode digit normalization can silently turn malformed generated pager text into a valid-looking page request, which is surprising and hard to diagnose in forum inventories, moderation summaries, migration checks, or cached category ledgers. Requiring ASCII digits keeps generated pagination strict while preserving valid Wikidot pager behavior and existing parser diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: fullwidth digit pager text was accepted and normalized into page `2`.
- Existing local drafts covered category thread-list retries, cached category reuse, description pager scoping, nested table filtering, title/description fidelity, response-body diagnostics, parser diagnostics, thread href route/ID validation, direct thread detail reads, post traversal, and replies; they did not validate Unicode digit normalization in response-wide category thread-list pager labels.
- This slice does not change request module names, retry policy, valid ASCII pagination, first-page parsing, paginated response-body diagnostics, thread-row parsing, description-pager scoping, direct thread detail reads, post traversal, reply behavior, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated HTML from real accounts, real account names, real forum content, private site data, and private page source out of upstream discussion.
