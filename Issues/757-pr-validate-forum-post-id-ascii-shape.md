# PR Draft: Validate Forum Post ID ASCII Shape

## Summary

`ForumPostCollection.acquire_all_in_thread(...)` parses generated `forum/ForumViewThreadPostsModule` post elements whose structural IDs use the `post-<id>` form. The contextual ID parser added by Issue 235 still used `raw_id.isdigit()` before `int(raw_id)`, so generated IDs containing Unicode digit glyphs such as `"post-\uff15\uff10\uff10\uff11"` were accepted and normalized into ordinary post ID `5001`.

This change accepts generated forum post IDs only when the suffix matches ASCII digits. Valid generated IDs such as `post-5001` continue to parse normally, malformed non-numeric IDs keep the same contextual `NoElementException`, and digit-like non-ASCII IDs now fail with `NoElementException("Post ID is malformed ...")` including site, thread, page, structural post position, field, and observed value context.

## Outcome

Forum post-list parsing no longer fabricates post identities by normalizing malformed generated post metadata. A `ForumViewThreadPostsModule` response with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like structural post ID text now fails at the post-ID parser boundary before any `ForumPost` record is created from that element.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum thread post reads, moderation ledgers, migration checks, discussion audits, source/revision traversal, local fixtures, or generated workflows where forum post identity must come only from structurally valid Wikidot post metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post-list acquisition as a practical read-heavy workflow. Existing drafts cover retry-aware post-list fetching, duplicate thread post reduction, cached-thread reuse, authored-content parser scoping, response-body diagnostics, parser diagnostics, post ID and route validation, direct source acquisition, edit workflows, reply workflows, and collection ownership validation.

This slice is not a duplicate of [235-pr-forum-post-id-parse-context.md](235-pr-forum-post-id-parse-context.md). Issue 235 converted malformed non-numeric `post-*` values such as `post-not-a-number` and malformed parent IDs such as `bad-parent` from raw `ValueError` into contextual `NoElementException`, but its shared parser still accepted Unicode digit glyphs because Python `str.isdigit()` is broader than ASCII decimal syntax. This slice covers the accepted-value shape of the generated structural post ID suffix.

It is also not a duplicate of [641-pr-validate-non-negative-forum-post-ids.md](641-pr-validate-non-negative-forum-post-ids.md), [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), or the forum route/href ID drafts, which cover direct constructor state, loaded-collection lookup inputs, or generated routes rather than generated post-list structural ID Unicode normalization.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [235-pr-forum-post-id-parse-context.md](235-pr-forum-post-id-parse-context.md), [296-pr-forum-post-list-timestamp-context.md](296-pr-forum-post-list-timestamp-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md), [461-pr-validate-forum-post-edit-metadata-fields.md](461-pr-validate-forum-post-edit-metadata-fields.md), [462-pr-validate-forum-post-parent-id-field.md](462-pr-validate-forum-post-parent-id-field.md), [641-pr-validate-non-negative-forum-post-ids.md](641-pr-validate-non-negative-forum-post-ids.md), and adjacent generated-scalar ASCII-shape drafts [743-pr-validate-forum-thread-script-id-ascii-shape.md](743-pr-validate-forum-thread-script-id-ascii-shape.md), [747-pr-validate-forum-thread-href-id-ascii-shape.md](747-pr-validate-forum-thread-href-id-ascii-shape.md), [752-pr-validate-forum-post-pager-page-ascii-shape.md](752-pr-validate-forum-post-pager-page-ascii-shape.md), and [756-pr-validate-page-revision-row-id-ascii-shape.md](756-pr-validate-page-revision-row-id-ascii-shape.md).

## Changes

- Require ASCII `[0-9]+` before integer conversion when parsing generated forum post ID suffixes.
- Preserve the existing contextual `NoElementException` message family for missing prefixes, non-numeric suffixes, malformed parent IDs, and now non-ASCII digit suffixes.
- Preserve successful post-list parsing, parent-post ID parsing, title/body extraction, user parsing, timestamp parsing, edit metadata parsing, pagination, retry behavior, cached-thread reuse, duplicate-thread handling, source acquisition, edit workflows, reply workflows, and collection validation.
- Add focused regression coverage for a generated post ID containing fullwidth post ID text `"post-\uff15\uff10\uff10\uff11"`.

## Type Of Change

- Bug fix
- Forum post-list generated identity validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated forum post ID containing non-ASCII digit glyphs must fail before any `ForumPost` is created from that element. |
| R2 | The malformed post-ID diagnostic must include site, thread, page, structural post position, field, and observed value context. |
| R3 | Valid ASCII `post-<digits>` IDs must continue to parse and populate forum post collections. |
| R4 | Existing malformed non-numeric top-level and parent post IDs must keep the contextual `NoElementException` path. |
| R5 | Existing post-list response-body, pager, retry, parent-ID, title/body, user, timestamp, edit-metadata, duplicate-thread, cached-thread, source, edit, reply, and adjacent forum workflows must remain compatible. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, real forum content, raw generated HTML from real accounts, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, forum-post acquisition tests, full forum-post tests, adjacent forum tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `"post-\uff15\uff10\uff10\uff11"` raises before a post collection is returned. | `test_acquire_all_rejects_non_ascii_digit_post_id` failed RED with `DID NOT RAISE`, then passed after ASCII-only post-ID parsing. | Returning a `ForumPost`, normalizing `"\uff15\uff10\uff10\uff11"` into post ID `5001`, assigning `thread._posts`, or silently skipping the element rejects this local completion claim. | Forum post-list ID parser | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | The exception reports `Post ID is malformed for site: test-site (thread=3001, page=1, post=1, field=post_id, value=post-\uff15\uff10\uff10\uff11)`. | The focused regression asserts the diagnostic family and contextual fields. | A raw `ValueError`, omitted site/thread/page/post context, omitted field/value, or unrelated post-row diagnostic rejects this local completion claim. | Post-ID diagnostics | focused test |
| R3 | Valid ASCII post IDs still parse successfully. | `TestForumPostCollectionAcquireAll` passed 58 tests, including successful post-list acquisition from fixture IDs. | Rejecting `post-5001`, changing post IDs, changing post count, or breaking normal thread post parsing rejects this local completion claim. | Valid post-list parsing | `tests/unit/test_forum_post.py` |
| R4 | Non-numeric top-level and parent IDs retain contextual failure. | Focused GREEN included `test_acquire_all_malformed_post_id_includes_thread_page_and_value_context` and `test_acquire_all_malformed_parent_post_id_includes_child_post_context`. | Reintroducing raw `ValueError`, changing the message family, losing child post context for parent IDs, or skipping malformed rows rejects this local completion claim. | Existing post-ID diagnostics | `tests/unit/test_forum_post.py` |
| R5 | Adjacent forum workflows remain green. | `tests/unit/test_forum_post.py` passed 294 tests, adjacent forum suite passed 905 tests, and full unit passed 3758 tests. | Regressing response-body diagnostics, pager behavior, retry exhaustion, parent IDs, title/body text, user/timestamp parsing, edit metadata, cached-thread behavior, duplicate-thread behavior, source acquisition, edit workflows, reply workflows, category/thread/post-revision behavior, or any unit test rejects this local completion claim. | Forum workflows | `tests/unit` |
| R6 | No live site state or private material is needed. | The regression uses a synthetic fixture-derived forum post-list body and mock AMC responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, real account names, real forum content, or raw generated HTML from real accounts rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, acquisition tests, full forum-post tests, adjacent forum tests, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `01da4b6 fix(forum_post): validate post id ascii shape`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_post_id -q` failed before the fix with `DID NOT RAISE` because `post-\uff15\uff10\uff10\uff11` was accepted and normalized as post ID `5001`.
- GREEN focused post-ID slice: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_post_id tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_malformed_post_id_includes_thread_page_and_value_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_malformed_parent_post_id_includes_child_post_context -q` passed 3 tests.
- `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll -q` passed 58 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 294 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 905 tests.
- `uv run pytest tests/unit -q` passed 3758 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no post-ID boundary, compatibility, architecture, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker: `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, local clawpatch commit `59e2dea`, launcher SHA256 `d6726fac4db7531d06c27d38e71e881f5e6360b1536df9a51f72bd8c4913ece1`.

## Acceptance Criteria

- `ForumPostCollection.acquire_all_in_thread(thread)` raises `NoElementException("Post ID is malformed ...")` for a generated post element whose ID is `post-\uff15\uff10\uff10\uff11`.
- The malformed post-ID diagnostic includes `site: test-site`, `thread=3001`, `page=1`, `post=1`, `field=post_id`, and `value=post-\uff15\uff10\uff10\uff11` context.
- The parser does not create, cache, or return a `ForumPost(id=5001, ...)` from non-ASCII digit post metadata.
- Valid ASCII structural post IDs such as `post-5001` still parse successfully.
- Existing malformed non-numeric structural post IDs such as `post-not-a-number` still raise contextual `NoElementException`.
- Existing malformed parent post IDs still raise contextual `NoElementException` with child post context.
- Existing response-body diagnostics, pager behavior, retry exhaustion, parent-ID parsing, title/body extraction, user/timestamp parsing, edit-metadata parsing, cached-thread behavior, duplicate-thread behavior, source acquisition, edit workflows, replies, adjacent forum suites, and full unit behavior remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real accounts, raw rollout path, real account name, real forum content, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 235. Mitigation: Issue 235 covers non-numeric top-level and parent-ID diagnostics; this slice covers Unicode digit normalization that still passed the old numeric branch.
- Risk: This could be confused with direct `ForumPost` constructor validation. Mitigation: direct retained post IDs remain separate public inputs; this slice runs at the generated post-list parser boundary before object construction.
- Risk: This could break valid forum post-list parsing. Mitigation: ASCII `[0-9]+` generated post IDs still convert to integers, and successful acquisition plus adjacent forum tests remain green.
- Risk: Parent post IDs share the same parser. Mitigation: the existing malformed-parent test remains in the focused GREEN gate and proves the parent-ID diagnostic path still preserves child post context after the parser guard change.
- Risk: Diagnostics could expose forum content. Mitigation: the diagnostic includes only site/thread/page/post position, field name, and the malformed scalar; tests use synthetic fixture HTML and do not include real forum content.
- Risk: Another digit-like Unicode category could behave differently than fullwidth digits. Mitigation: the code rejects any suffix that does not match ASCII `[0-9]+`, covering fullwidth, superscript, Arabic-Indic, and similar digit glyphs.

## Dependencies

- BeautifulSoup continues to expose generated forum post element IDs through `post_elem.get("id")`.
- Normal Wikidot forum post element IDs are expected to use ASCII decimal digits after `post-`.
- `ForumPostCollection._parse(...)` continues to select generated post elements before field parsing.
- Existing `ForumPost` constructor identity validation continues to validate direct record state after parser-side conversion.

## Open Questions

None for this local slice. Future generated identity-shape changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Forum post IDs are durable generated identity metadata for source reads, revision reads, moderation summaries, reply reconstruction, migration ledgers, discussion audits, and local fixtures. Unicode digit normalization can silently turn malformed generated post metadata into a valid-looking post ID. Requiring ASCII digits keeps generated identity parsing strict while preserving valid Wikidot post-list rows and existing contextual parser diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: a fullwidth generated post ID suffix was accepted and normalized into post ID `5001`.
- Existing local drafts covered forum post-list retry behavior, duplicate request reduction, cached-thread reuse, authored-content parser scoping, response-body diagnostics, non-numeric post-ID context, parent-ID context, timestamp context, direct post identity validation, and adjacent generated scalar ASCII-shape fixes; they did not validate Unicode digit normalization in generated forum post IDs.
- This slice does not change request module names, retry policy, response-body validation, valid ASCII post rows, parent-ID behavior, title/body extraction, user parsing, timestamp parsing, edit metadata parsing, cached-thread reuse, source acquisition, edit workflows, reply workflows, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated HTML from real accounts, real account names, real forum content, private site data, and private page source out of upstream discussion.
