# PR Draft: Validate Forum Thread Script ID ASCII Shape

## Summary

`Page.discussion` and `ForumThreadCollection.acquire_from_thread_ids(...)` both parse generated `WIKIDOT.forumThreadId = <id>;` script metadata before using the value as a forum-thread identity. Issues [309-pr-page-discussion-thread-id-context.md](309-pr-page-discussion-thread-id-context.md) and [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md) made present malformed values such as `latest` fail with page-local or thread-local context, but both parser paths still accepted Unicode decimal digit glyphs because Python `str.isdigit()` and regex `\d+` are Unicode-aware. As a result, a generated value such as `\uff13\uff10\uff10\uff11` was normalized into ordinary thread ID `3001` before discussion or direct thread-detail workflows continued.

This change requires generated `forumThreadId` script values to match ASCII digits before integer conversion. Valid generated values such as `3001` remain compatible, missing script metadata keeps the existing missing-field behavior for each surface, and present non-ASCII digit payloads now raise the existing contextual malformed-thread-ID `NoElementException`.

## Outcome

Browser-free page discussion lookup and direct forum-thread detail acquisition no longer fabricate thread identities by normalizing non-ASCII digit glyphs from generated script metadata. The malformed-value diagnostics remain actionable and do not include raw generated page or forum HTML.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page discussion navigation, direct forum-thread reads, category/forum inventories, moderation workflows, migration ledgers, translation review tooling, generated fixtures, or local read-model tests where generated `forumThreadId` script metadata is treated as durable forum identity.

## Current Evidence

Local rollout-backed drafts repeatedly identify page discussion reads and direct forum-thread reads as practical navigation and inventory surfaces. Existing drafts cover retry-aware discussion fetching, page auxiliary response-body diagnostics, page discussion retained site validation, direct thread-detail retry behavior, direct thread-detail parser context, direct response-body typing, direct thread ID input validation, non-negative direct thread IDs, generated detail post-count shape validation, forum thread collection state, category-owned thread-list parsing, forum thread href ID shape, and forum thread href route validation.

This slice is not a duplicate of [309-pr-page-discussion-thread-id-context.md](309-pr-page-discussion-thread-id-context.md) or [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md). Those issues made present non-numeric generated script assignments contextual instead of missing, but they still allowed Python Unicode digit normalization. This slice also follows the newer generated-script scalar-shape boundary from [734-pr-validate-page-id-script-shape.md](734-pr-validate-page-id-script-shape.md) and [735-pr-validate-site-id-script-shape.md](735-pr-validate-site-id-script-shape.md), which require ASCII digits before `int(...)` on generated identity metadata.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [309-pr-page-discussion-thread-id-context.md](309-pr-page-discussion-thread-id-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [335-pr-page-auxiliary-response-body-type-context.md](335-pr-page-auxiliary-response-body-type-context.md), [567-pr-validate-page-discussion-site.md](567-pr-validate-page-discussion-site.md), [642-pr-validate-non-negative-forum-thread-ids.md](642-pr-validate-non-negative-forum-thread-ids.md), [734-pr-validate-page-id-script-shape.md](734-pr-validate-page-id-script-shape.md), and [735-pr-validate-site-id-script-shape.md](735-pr-validate-site-id-script-shape.md).

## Changes

- Require `Page.discussion` generated `WIKIDOT.forumThreadId` values to match `[0-9]+` before `int(...)`.
- Require direct forum-thread detail generated `WIKIDOT.forumThreadId` values to match `[0-9]+` before `int(...)`.
- Preserve page discussion malformed-value diagnostics with site, page, page ID, `field=thread_id`, and observed value.
- Preserve direct thread-detail malformed-value diagnostics with site, requested thread ID, optional category context, `field=thread_id`, and observed value.
- Preserve valid ASCII numeric discussion and direct thread-detail lookup.
- Preserve absent discussion marker behavior, missing direct script diagnostics, response-body diagnostics, retry behavior, category association, parser field diagnostics, direct thread lookup input validation, and adjacent page/forum workflows.
- Add focused regression coverage for escaped fullwidth thread ID text `\uff13\uff10\uff10\uff11` in both generated script surfaces.

## Type Of Change

- Bug fix
- Generated script scalar-shape validation
- Page discussion and forum-thread detail parser hardening
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.discussion` must reject a present generated `forumThreadId` value made of non-ASCII digit glyphs before calling `ForumThread.get_from_id(...)`. |
| R2 | `ForumThreadCollection.acquire_from_thread_ids(...)` must reject a present direct thread-detail `forumThreadId` value made of non-ASCII digit glyphs before returning a `ForumThread`. |
| R3 | Both malformed-value errors must preserve their existing site/page/thread field context and include the observed value. |
| R4 | Valid ASCII generated thread IDs must continue to parse and delegate/fetch normally. |
| R5 | Existing present non-numeric diagnostics such as `latest` must remain compatible. |
| R6 | Existing absent marker behavior must remain compatible: no discussion marker still means no page discussion, while a missing direct thread-detail script still raises the existing missing-script error. |
| R7 | Existing response-body diagnostics, retry behavior, direct thread ID input validation, non-negative thread ID validation, page discussion site validation, and adjacent page/forum workflows must remain compatible. |
| R8 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw generated page/forum HTML from real sites, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, touched page/forum-thread tests, adjacent page/forum workflow tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `Page.discussion` raises `NoElementException` for escaped fullwidth generated thread ID text before delegation. | `test_discussion_rejects_non_ascii_digit_thread_id` failed RED with `DID NOT RAISE`, then passed after ASCII-only validation. | Calling `ForumThread.get_from_id(...)`, setting `_discussion_checked = True`, caching a thread, or normalizing the value to `3001` rejects this local completion claim. | Page discussion parser | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Direct thread-detail acquisition raises `NoElementException` for escaped fullwidth generated thread ID text. | `test_acquire_from_ids_rejects_non_ascii_digit_script_thread_id` failed RED with `DID NOT RAISE`, then passed after ASCII-only validation. | Returning a `ForumThread`, accepting the generated value as `3001`, or treating the value as absent script metadata rejects this local completion claim. | Forum thread detail parser | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R3 | The page diagnostic includes site, page, page ID, `field=thread_id`, and observed value; the direct-thread diagnostic includes site, requested thread ID, `field=thread_id`, and observed value. | The focused regressions match both existing malformed-value message shapes. | Dropping location context, replacing the malformed-value branch with a generic `ValueError`, or omitting the observed scalar rejects this local completion claim. | Parser diagnostics | focused tests |
| R4 | Valid ASCII generated IDs continue to work. | Focused GREEN included `test_discussion_retries_transient_fetch_failures` and `test_acquire_from_ids_success`. | Rejecting `3001`, changing delegation arguments, or changing direct thread-detail result fields rejects this local completion claim. | Valid generated ID compatibility | page and forum-thread tests |
| R5 | Existing `latest` malformed-value diagnostics stay green. | Focused GREEN included `test_discussion_malformed_thread_id_includes_page_context` and `test_acquire_from_ids_malformed_script_thread_id_includes_thread_and_value_context`. | Losing the Issue 309 or Issue 311 malformed-value behavior rejects this local completion claim. | Prior malformed-value branches | page and forum-thread tests |
| R6 | Absent marker branches remain out of scope and unchanged. | Touched-file and adjacent page/forum suites passed after the parser change. | Treating no-discussion pages as malformed, changing missing direct script behavior, or caching false states on malformed values rejects this local completion claim. | Missing marker behavior | touched and adjacent tests |
| R7 | Adjacent workflows remain green. | Touched `test_page.py` plus `test_forum_thread.py` passed 625 tests, adjacent page/forum workflows passed 2015 tests, and full unit passed 3744 tests. | Regressing response-body typing, retry behavior, direct thread lookup, category/thread/post/revision traversal, page source/revision/file/vote/site workflows, or parser diagnostics rejects this local completion claim. | Page and forum workflows | `tests/unit` |
| R8 | No live site state or private material is needed. | All regressions use synthetic unit-level generated script text and mocked responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw generated HTML from real sites, forum content, page content, private site data, or real account names rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, touched tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `7e5ba29 fix(forum_thread): validate script id ascii shape`.

- RED page discussion: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_discussion_rejects_non_ascii_digit_thread_id -q` failed before the fix with `DID NOT RAISE` after the escaped fullwidth value was accepted and delegated as thread ID `3001`.
- GREEN first surface: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_discussion_rejects_non_ascii_digit_thread_id tests/unit/test_page.py::TestPageProperties::test_discussion_malformed_thread_id_includes_page_context tests/unit/test_page.py::TestPageProperties::test_discussion_retries_transient_fetch_failures -q` passed 3 tests after the page parser required ASCII digits.
- RED direct thread detail: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_rejects_non_ascii_digit_script_thread_id -q` failed before the direct thread-detail fix with `DID NOT RAISE`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_discussion_rejects_non_ascii_digit_thread_id tests/unit/test_page.py::TestPageProperties::test_discussion_malformed_thread_id_includes_page_context tests/unit/test_page.py::TestPageProperties::test_discussion_retries_transient_fetch_failures tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_rejects_non_ascii_digit_script_thread_id tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_malformed_script_thread_id_includes_thread_and_value_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_success -q` passed 6 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_forum_thread.py -q` passed 625 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 2015 tests.
- `uv run pytest tests/unit -q` passed 3744 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.discussion` raises contextual `NoElementException` for a present generated `WIKIDOT.forumThreadId` value built from escaped fullwidth digit text `\uff13\uff10\uff10\uff11`.
- `Page.discussion` does not call `ForumThread.get_from_id(...)`, does not set `_discussion_checked`, and does not cache `_discussion` for that malformed value.
- `ForumThreadCollection.acquire_from_thread_ids(...)` raises contextual `NoElementException` for a direct thread-detail generated `WIKIDOT.forumThreadId` value built from escaped fullwidth digit text `\uff13\uff10\uff10\uff11`.
- Valid ASCII `WIKIDOT.forumThreadId = 3001;` discussion and direct thread-detail paths remain compatible.
- Existing `latest` malformed-value diagnostics remain compatible.
- Existing missing marker behavior remains compatible for no-discussion pages and missing direct thread-detail script metadata.
- Existing response-body validation, retry behavior, direct thread ID lookup validation, non-negative direct thread IDs, discussion retained-site validation, category/thread/post/revision traversal, page source/revision/file/vote/site workflows, and parser diagnostics remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real sites, raw rollout path, forum content, page content, real account name, or private site data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issues 309 and 311. Mitigation: those issues cover present non-numeric generated values and missing-vs-malformed branch separation; this slice covers Unicode digit normalization that still passes those branches.
- Risk: Tightening generated script parsing could reject unusual but valid generated output. Mitigation: Wikidot generated identity scalars are ordinary ASCII decimal digits in the existing fixtures and adjacent generated-script shape fixes, and valid `3001` behavior remains tested.
- Risk: The change could blur absent marker semantics. Mitigation: the parser only raises after a `forumThreadId` assignment is captured; absent markers keep their existing branch behavior.
- Risk: Diagnostics could expose generated page or forum content. Mitigation: the diagnostic includes only site/page/thread identifiers, field name, and the scalar generated value, not raw response bodies, page source, forum content, credentials, cookies, local paths, or private account data.

## Dependencies

- Page discussion modules and direct forum-thread detail modules continue to expose thread identity through generated `WIKIDOT.forumThreadId = <id>;` assignments when a backing thread exists.
- `ForumThread.get_from_id(...)` remains the direct loader after `Page.discussion` parses a valid generated thread ID.
- `ForumThreadCollection.acquire_from_thread_ids(...)` remains the direct thread-detail loader for valid caller-provided thread IDs.

## Open Questions

None for this local slice. Future generated scalar parser work should be selected only with a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Generated `forumThreadId` values are identity metadata for browser-free page discussion navigation and direct forum-thread acquisition. Unicode digit normalization can silently turn malformed generated script text into a valid-looking thread ID. Requiring ASCII digits keeps generated identity parsing strict and consistent with page/site script ID parsers while preserving existing valid numeric behavior and contextual malformed-value diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED tests demonstrated prior behavior on both surfaces: escaped fullwidth digit script values were accepted and normalized to thread ID `3001`.
- Existing local drafts covered page discussion retry behavior, page auxiliary response body diagnostics, present non-numeric discussion IDs, direct thread-detail retry behavior, present non-numeric direct thread IDs, direct thread ID type/range validation, and generated href shape/route validation; they did not validate Unicode digit normalization in generated `forumThreadId` script scalars.
- This slice does not change request payloads, retry policy, response-body checks, no-discussion behavior, missing direct-script diagnostics, category association, direct lookup ID validation, forum thread records, page records, live Wikidot behavior, upstream filing state, or valid ASCII generated output.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated page/forum HTML from real sites, forum contents, page source text, real usernames, and private site data out of upstream discussion.
