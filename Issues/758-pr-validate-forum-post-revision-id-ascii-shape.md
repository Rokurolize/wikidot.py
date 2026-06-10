# PR Draft: Validate Forum Post Revision ID ASCII Shape

## Summary

`ForumPostRevisionCollection.acquire_all(...)` parses generated forum post revision rows whose direct action links call `showRevision(event, <id>)`. The contextual revision-ID parser added by Issue 283 still used a Unicode-aware `\d+` regex before `int(...)`, so generated IDs containing Unicode digit glyphs such as `showRevision(event, \uff19\uff10\uff10\uff13)` were accepted and normalized into ordinary revision ID `9003`.

This change accepts generated forum post revision IDs only when the `showRevision(...)` argument matches ASCII digits. Valid generated IDs such as `showRevision(event, 9003)` continue to parse normally, malformed non-numeric IDs keep the same contextual `NoElementException`, and digit-like non-ASCII IDs now fail with `NoElementException("Forum post revision ID is malformed ...")` including site, post, row, field, and observed `onclick` value context.

## Outcome

Forum post revision-list parsing no longer fabricates revision identities by normalizing malformed generated action metadata. A `ForumPostRevisionsModule` response with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like `showRevision(...)` argument text now fails at the revision-ID parser boundary before any `ForumPostRevision` record is created from that row.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum post revision history reads, rollback/audit workflows, moderation ledgers, migration checks, historical source/HTML retrieval, local fixtures, or generated workflows where revision identity must come only from structurally valid Wikidot revision action metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post revision history as a practical workflow for retry-aware acquisition, deduplicated revision-list and revision-HTML requests, direct-cell parser scoping, response-body validation, historical content retrieval, and cache reuse.

This slice is not a duplicate of [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md). Issue 283 converted present non-numeric `showRevision(...)` values such as `showRevision(event, latest)` from a silent skipped-row path into contextual `NoElementException`, but its parser still accepted Unicode digit glyphs because Python regex `\d` is Unicode-aware. This slice covers the accepted-value shape of the generated revision ID argument.

It is also not a duplicate of [637-pr-validate-non-negative-revision-numbers.md](637-pr-validate-non-negative-revision-numbers.md), [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md), [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md), [675-pr-validate-forum-post-revision-collection-retained-identity-state.md](675-pr-validate-forum-post-revision-collection-retained-identity-state.md), or revision HTML acquisition retained-ID drafts, which cover direct object state, range validation, loaded-collection lookup, or retained cached IDs rather than generated revision-list action metadata Unicode normalization.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md), [637-pr-validate-non-negative-revision-numbers.md](637-pr-validate-non-negative-revision-numbers.md), [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md), [675-pr-validate-forum-post-revision-collection-retained-identity-state.md](675-pr-validate-forum-post-revision-collection-retained-identity-state.md), and adjacent generated-scalar ASCII-shape drafts [743-pr-validate-forum-thread-script-id-ascii-shape.md](743-pr-validate-forum-thread-script-id-ascii-shape.md), [756-pr-validate-page-revision-row-id-ascii-shape.md](756-pr-validate-page-revision-row-id-ascii-shape.md), and [757-pr-validate-forum-post-id-ascii-shape.md](757-pr-validate-forum-post-id-ascii-shape.md).

## Changes

- Require ASCII `[0-9]+` before integer conversion when parsing generated forum post revision `showRevision(...)` ID arguments.
- Preserve the existing contextual `NoElementException` message family for present non-numeric revision ID values and now non-ASCII digit values.
- Preserve missing/non-revision row skipping, successful revision-list parsing, oldest-first `rev_no` assignment, direct-cell scoping, user parsing, timestamp parsing, cached revision reuse, duplicate post-ID handling, duplicate revision ID HTML fetch deduplication, source/HTML acquisition, and adjacent forum workflows.
- Add focused regression coverage for a generated revision action containing fullwidth revision ID text `showRevision(event, \uff19\uff10\uff10\uff13)`.

## Type Of Change

- Bug fix
- Forum post revision-list generated identity validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated forum post revision ID containing non-ASCII digit glyphs must fail before any `ForumPostRevision` is created from that row. |
| R2 | The malformed revision-ID diagnostic must include site, post, row, field, and observed `onclick` value context. |
| R3 | Valid ASCII `showRevision(event, <digits>)` IDs must continue to parse and populate revision collections. |
| R4 | Existing malformed non-numeric revision IDs such as `showRevision(event, latest)` must keep the contextual `NoElementException` path. |
| R5 | Existing revision-list response-body, row skipping, direct-cell scoping, user, timestamp, duplicate, cache, source/HTML, forum-post, forum-thread, and adjacent forum workflows must remain compatible. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, real forum content, raw generated HTML from real accounts, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, forum-post-revision acquisition tests, full forum-post-revision tests, adjacent forum tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `showRevision(event, \uff19\uff10\uff10\uff13)` raises before a revision collection is returned. | `test_acquire_all_rejects_non_ascii_digit_revision_id` failed RED with `DID NOT RAISE`, then passed after ASCII-only revision-ID parsing. | Returning a `ForumPostRevision`, normalizing `"\uff19\uff10\uff10\uff13"` into revision ID `9003`, assigning `post._revisions`, or silently skipping the row rejects this local completion claim. | Forum post revision-list ID parser | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | The exception reports `Forum post revision ID is malformed for site: test-site, post: 5001 (row=1, field=revision_id, value=WIKIDOT.modules.ForumViewThreadModule.listeners.showRevision(event, \uff19\uff10\uff10\uff13))`. | The focused regression asserts the diagnostic family and contextual fields. | A raw `ValueError`, omitted site/post/row context, omitted field/value, or unrelated row diagnostic rejects this local completion claim. | Revision-ID diagnostics | focused test |
| R3 | Valid ASCII revision IDs still parse successfully. | Focused GREEN included `TestForumPostRevisionCollectionParse.test_parse_success`, and `test_forum_post_revision.py` passed 230 tests. | Rejecting `showRevision(event, 9003)`, changing revision IDs, changing oldest-first order, or changing `rev_no` assignment rejects this local completion claim. | Valid revision-list parsing | `tests/unit/test_forum_post_revision.py` |
| R4 | Non-numeric revision IDs retain contextual failure. | Focused GREEN included `test_acquire_all_malformed_revision_id_includes_post_row_and_value_context`. | Reintroducing silent skipped rows, changing the message family, or dropping the observed `onclick` value rejects this local completion claim. | Existing revision-ID diagnostic | `tests/unit/test_forum_post_revision.py` |
| R5 | Adjacent forum workflows remain green. | `tests/unit/test_forum_post_revision.py` passed 230 tests, adjacent forum suite passed 906 tests, and full unit passed 3759 tests. | Regressing response-body diagnostics, row skipping, direct-cell scoping, revision order, users, timestamps, duplicate reuse, source/HTML acquisition, post workflows, thread workflows, category workflows, or any unit test rejects this local completion claim. | Forum workflows | `tests/unit` |
| R6 | No live site state or private material is needed. | The regression uses a synthetic fixture-derived forum post revision-list body and mock AMC responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, real account names, real forum content, or raw generated HTML from real accounts rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, revision acquisition tests, full forum-post-revision tests, adjacent forum tests, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `55aaab1 fix(forum_post_revision): validate revision id ascii shape`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_revision_id -q` failed before the fix with `DID NOT RAISE` because `showRevision(event, \uff19\uff10\uff10\uff13)` was accepted and normalized as revision ID `9003`.
- GREEN focused revision-ID slice: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_revision_id tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_revision_id_includes_post_row_and_value_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionParse::test_parse_success -q` passed 3 tests.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 230 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 906 tests.
- `uv run pytest tests/unit -q` passed 3759 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no revision-ID boundary, compatibility, architecture, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker: `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, local clawpatch commit `59e2dea`, launcher SHA256 `d6726fac4db7531d06c27d38e71e881f5e6360b1536df9a51f72bd8c4913ece1`.

## Acceptance Criteria

- `ForumPostRevisionCollection.acquire_all(post)` raises `NoElementException("Forum post revision ID is malformed ...")` for a generated revision row whose `onclick` contains `showRevision(event, \uff19\uff10\uff10\uff13)`.
- The malformed revision-ID diagnostic includes `site: test-site`, `post: 5001`, `row=1`, `field=revision_id`, and the observed `onclick` value.
- The parser does not create, cache, or return a `ForumPostRevision(id=9003, ...)` from non-ASCII digit revision metadata.
- Valid ASCII structural revision IDs such as `showRevision(event, 9003)` still parse successfully.
- Existing malformed non-numeric structural revision IDs such as `showRevision(event, latest)` still raise contextual `NoElementException`.
- Existing missing/non-revision row skipping, response-body diagnostics, direct-cell scoping, oldest-first ordering, `rev_no` assignment, user/timestamp parsing, cached revision reuse, duplicate revision HTML batching, source/HTML acquisition, adjacent forum suites, and full unit behavior remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real accounts, raw rollout path, real account name, real forum content, post source text, post title from real sites, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 283. Mitigation: Issue 283 covers non-numeric revision-ID diagnostics and skipped-row prevention; this slice covers Unicode digit normalization that still passed the old regex branch.
- Risk: This could be confused with direct revision identity validation. Mitigation: direct `ForumPostRevision.id` and retained lookup/cache state remain separate surfaces; this slice runs at the generated revision-list parser boundary before object construction.
- Risk: This could break valid revision history parsing. Mitigation: ASCII `[0-9]+` generated revision IDs still convert to integers, and successful parsing plus adjacent forum tests remain green.
- Risk: Diagnostics could expose forum content. Mitigation: the diagnostic includes only site/post/row, field name, and the generated action scalar; tests use synthetic fixture HTML and do not include real forum content.
- Risk: Another digit-like Unicode category could behave differently than fullwidth digits. Mitigation: the regex now accepts only ASCII `[0-9]+`, covering fullwidth, superscript, Arabic-Indic, and similar digit glyphs.

## Dependencies

- BeautifulSoup continues to expose generated forum post revision action links through direct revision cells.
- Normal Wikidot forum post revision `showRevision(...)` arguments are expected to use ASCII decimal digits.
- `ForumPostRevisionCollection._parse(...)` continues to skip genuinely incomplete/non-revision rows before revision ID parsing.
- Existing `ForumPostRevision` constructor identity validation continues to validate direct record state after parser-side conversion.

## Open Questions

None for this local slice. Future generated identity-shape changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Forum post revision IDs are durable generated identity metadata for historical source/html reads, rollback decisions, moderation summaries, migration ledgers, discussion audits, and local fixtures. Unicode digit normalization can silently turn malformed generated revision action metadata into a valid-looking revision ID. Requiring ASCII digits keeps generated identity parsing strict while preserving valid Wikidot revision rows and existing contextual parser diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: a fullwidth generated revision ID argument was accepted and normalized into revision ID `9003`.
- Existing local drafts covered forum post revision-list retry behavior, duplicate request reduction, direct-cell scoping, response-body diagnostics, non-numeric revision-ID context, user/timestamp context, direct revision identity validation, and adjacent generated scalar ASCII-shape fixes; they did not validate Unicode digit normalization in generated forum post revision IDs.
- This slice does not change request module names, retry policy, response-body validation, valid ASCII revision rows, missing-row skipping, revision ordering, `rev_no` assignment, user parsing, timestamp parsing, cached revision reuse, source/HTML acquisition, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated HTML from real accounts, real account names, real forum content, post source text, post titles from real sites, private site data, and private page source out of upstream discussion.
