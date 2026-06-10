# PR Draft: Validate Forum Category Count ASCII Shape

## Summary

`ForumCategoryCollection.acquire_all(...)` parses generated forum-start category rows into `ForumCategory` records. Issue 233 converted malformed count cells such as `not-a-number` into contextual `NoElementException`, and Issue 634 rejects parseable negative counts such as `-1`. One accepted-value gap remained: `_parse_category_count(...)` still passed the generated `threads` or `posts` cell text directly to Python `int(...)`, so non-ASCII digit glyphs such as `\uff11\uff10` and `\uff15\uff10` were accepted and normalized into ordinary `threads_count=10` and `posts_count=50`.

This change accepts generated forum category counts only when the cell text matches ASCII digits, with the existing optional leading minus retained so negative ASCII values continue through the established non-negative diagnostic. Valid generated count cells such as `10` and `50` continue to parse normally, malformed text keeps the contextual `Thread count is malformed ...` or `Post count is malformed ...` path, negative ASCII cells keep the contextual non-negative path, and non-ASCII digit-like cells now fail before any `ForumCategory` record is returned.

## Outcome

Forum-start parsing no longer fabricates category thread/post counts by normalizing malformed generated count metadata. A `forum/ForumStartModule` response with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like count text now fails at the category count parser boundary with site, row, field, and observed value context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum category discovery, forum inventory ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, reply-side category cache synchronization, local fixtures, or generated review records where `ForumCategory.threads_count` and `ForumCategory.posts_count` must reflect structurally valid Wikidot forum-start metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum category discovery as a practical entry point for thread, post, and revision traversal. Existing drafts cover retry-aware category fetches, nested-table scoping, title/description text fidelity, response-body diagnostics, malformed category count diagnostics, non-negative direct and generated category count validation, direct category field validation, collection validation, cached category thread reuse, category href route validation, category href ID ASCII-shape validation, and adjacent generated scalar ASCII-shape fixes.

This slice is not a duplicate of [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md). Issue 233 covers malformed count text that `int(...)` rejects, such as `not-a-number` and `bad-count`; it did not cover Unicode digit glyphs that `int(...)` accepts.

This slice is not a duplicate of [634-pr-validate-non-negative-forum-category-counts.md](634-pr-validate-non-negative-forum-category-counts.md). Issue 634 covers negative direct constructor counts and generated negative count cells such as `-1`. The new ASCII-shape check deliberately preserves the existing negative-value path for ASCII `-1`.

This slice is also not a duplicate of [746-pr-validate-forum-category-href-id-ascii-shape.md](746-pr-validate-forum-category-href-id-ascii-shape.md), which covers generated category href ID segments, not generated category count cells.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [453-pr-validate-forum-category-count-fields.md](453-pr-validate-forum-category-count-fields.md), [454-pr-validate-forum-category-text-fields.md](454-pr-validate-forum-category-text-fields.md), [502-pr-validate-forum-category-site-field.md](502-pr-validate-forum-category-site-field.md), [668-pr-validate-forum-category-threads-cache-retained-category-id-state.md](668-pr-validate-forum-category-threads-cache-retained-category-id-state.md), [670-pr-validate-forum-category-collection-retained-id-state.md](670-pr-validate-forum-category-collection-retained-id-state.md), [681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md](681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md), [719-pr-validate-forum-category-create-thread-status-type.md](719-pr-validate-forum-category-create-thread-status-type.md), [726-pr-validate-forum-category-href-id-shape.md](726-pr-validate-forum-category-href-id-shape.md), [740-pr-validate-forum-category-href-routes.md](740-pr-validate-forum-category-href-routes.md), [746-pr-validate-forum-category-href-id-ascii-shape.md](746-pr-validate-forum-category-href-id-ascii-shape.md), and adjacent generated-scalar ASCII-shape drafts [757-pr-validate-forum-post-id-ascii-shape.md](757-pr-validate-forum-post-id-ascii-shape.md), [758-pr-validate-forum-post-revision-id-ascii-shape.md](758-pr-validate-forum-post-revision-id-ascii-shape.md), [759-pr-validate-recent-change-revision-cell-ascii-shape.md](759-pr-validate-recent-change-revision-cell-ascii-shape.md), [760-pr-validate-forum-thread-detail-post-count-ascii-shape.md](760-pr-validate-forum-thread-detail-post-count-ascii-shape.md), and [761-pr-validate-page-revision-number-ascii-shape.md](761-pr-validate-page-revision-number-ascii-shape.md).

## Changes

- Require ASCII `-?[0-9]+` before integer conversion when parsing generated forum-start category `threads` and `posts` count cells.
- Preserve successful parsing for valid generated count cells such as `10` and `50`.
- Preserve the existing contextual malformed-count diagnostics for non-integer text.
- Preserve the existing contextual non-negative diagnostics for negative ASCII cells such as `-1`.
- Add parameterized regression coverage for generated `threads` count text `\uff11\uff10` and generated `posts` count text `\uff15\uff10`.

## Type Of Change

- Bug fix
- Forum-start generated scalar validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Generated forum category `threads` and `posts` count cells containing non-ASCII digit glyphs must fail before a `ForumCategoryCollection` is returned. |
| R2 | The malformed count diagnostics must identify the site, row, affected field, and observed raw value. |
| R3 | Valid generated ASCII count cells such as `10` and `50` must continue to parse into the same counts. |
| R4 | Existing malformed text and negative ASCII count paths must keep their established diagnostics. |
| R5 | Existing forum category response validation, nested-table scoping, title/description parsing, category href parsing, collection/search behavior, cached category thread behavior, create-thread behavior, and adjacent forum workflows must remain compatible. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, real forum-start HTML, raw forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, forum category tests, adjacent forum tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `\uff11\uff10` and `\uff15\uff10` count cells raise before a category collection is returned. | `test_acquire_all_rejects_non_ascii_digit_counts` failed RED with `DID NOT RAISE` for both generated count cells, then passed after ASCII-only count parsing. | Returning a `ForumCategory`, normalizing `"\uff11\uff10"` into `threads_count=10`, normalizing `"\uff15\uff10"` into `posts_count=50`, or silently skipping the row rejects this local completion claim. | Forum category count parser | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | The exceptions report `Thread count is malformed for site: test-site (row=1, field=threads, value=\uff11\uff10)` and `Post count is malformed for site: test-site (row=1, field=posts, value=\uff15\uff10)`. | The parameterized regression asserts both diagnostic families, structural row, field, and observed value. | A raw `ValueError`, omitted site/row/field/value context, or unrelated parser diagnostic rejects this local completion claim. | Count diagnostics | focused test |
| R3 | Valid ASCII count cells still parse successfully. | Focused GREEN included `test_acquire_all_parse_fields`; `tests/unit/test_forum_category.py` passed 150 tests. | Rejecting `10` or `50`, changing parsed counts, changing category order, or changing parsed category fields rejects this local completion claim. | Valid forum-start parsing | `tests/unit/test_forum_category.py` |
| R4 | Existing malformed and negative paths stay stable. | Focused GREEN included `test_acquire_all_malformed_count_includes_site_context` and `test_acquire_all_negative_count_includes_site_context`. | Accepting malformed text, reclassifying `-1` as malformed text, dropping context, or changing the non-negative diagnostic rejects this local completion claim. | Parser compatibility | `tests/unit/test_forum_category.py` |
| R5 | Adjacent forum workflows remain green. | Adjacent forum category/thread/post/revision coverage passed 909 tests, and full unit passed 3764 tests. | Regressing response-body diagnostics, nested-table filtering, title/description parsing, href parsing, collection/search behavior, cached category thread behavior, create-thread behavior, forum thread/post/revision behavior, or any unit test rejects this local completion claim. | Forum and adjacent workflows | `tests/unit` |
| R6 | No live site state or private material is needed. | The regression mutates the synthetic `forum_start` fixture and uses mocked AMC responses only. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum-start HTML from real sites, private forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, forum category module, adjacent suite, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `0ae2953 fix(forum_category): validate count ascii shape`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_counts -q` failed before the fix with `DID NOT RAISE` for both `\uff11\uff10` and `\uff15\uff10`, because Python normalized the generated count cells into `10` and `50`.
- GREEN focused forum category count slice: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_counts tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_malformed_count_includes_site_context tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_negative_count_includes_site_context tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_parse_fields -q` passed 7 tests.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 150 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 909 tests.
- `uv run pytest tests/unit -q` passed 3764 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no parser boundary, compatibility, architecture, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker: `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, local clawpatch commit `59e2dea`, launcher SHA256 `d6726fac4db7531d06c27d38e71e881f5e6360b1536df9a51f72bd8c4913ece1`.

## Acceptance Criteria

- `ForumCategoryCollection.acquire_all(...)` raises `NoElementException("Thread count is malformed ...")` for a generated `threads` cell whose text is `\uff11\uff10`.
- `ForumCategoryCollection.acquire_all(...)` raises `NoElementException("Post count is malformed ...")` for a generated `posts` cell whose text is `\uff15\uff10`.
- The malformed diagnostics include `site: test-site`, `row=1`, the affected `field`, and the observed generated cell value.
- The parser does not create or return `ForumCategory(threads_count=10, ...)` or `ForumCategory(posts_count=50, ...)` from non-ASCII digit count metadata.
- Valid ASCII generated count cells such as `10` and `50` still parse successfully.
- Existing malformed text such as `not-a-number` and `bad-count` still raises the contextual malformed count diagnostics.
- Existing negative ASCII text such as `-1` still raises the contextual non-negative count diagnostics.
- Existing response-body diagnostics, nested-table scoping, title/description parsing, category href parsing, collection/search behavior, cached category thread behavior, create-thread behavior, adjacent forum workflows, and full unit behavior remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real accounts, raw rollout path, private forum content, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 233. Mitigation: Issue 233 covers malformed text that `int(...)` rejects; this slice covers Unicode digit glyphs that `int(...)` accepts.
- Risk: This could be confused with Issue 634. Mitigation: Issue 634 covers negative category counts; this slice keeps ASCII negative text valid for parser classification so the existing non-negative diagnostic remains intact.
- Risk: This could be confused with Issue 746. Mitigation: Issue 746 covers generated category href IDs; this slice covers generated count cells after the category identity has already parsed.
- Risk: This could alter valid forum-start parsing. Mitigation: ASCII `[0-9]+` generated count cells still convert to integers, and successful acquisition plus adjacent forum tests remain green.
- Risk: Diagnostics could expose forum content. Mitigation: the diagnostic includes only site, row, field, and the compact count scalar; tests use synthetic fixture HTML and do not include real forum content.

## Dependencies

- BeautifulSoup continues to expose generated forum-start category count cells as direct structural `td` text.
- Normal Wikidot forum-start category count cells are expected to use ASCII decimal digits.
- Existing forum category parser context continues to identify site, structural row, field, and raw scalar value.
- Existing `ForumCategory` constructor validation continues to validate direct record state after parser-side conversion.

## Open Questions

None for this local slice. Future generated scalar-shape changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Forum category counts are durable generated metadata for forum inventories, moderation exports, migration ledgers, cached scans, category-owned thread reads, and downstream traversal decisions. Unicode digit normalization can silently turn malformed generated count text into valid-looking category totals. Requiring ASCII digits keeps generated count parsing strict while preserving valid Wikidot forum-start rows and existing contextual parser diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: fullwidth generated category count values were accepted and normalized into `threads_count=10` and `posts_count=50`.
- Existing local drafts covered forum category fetch retries, nested-table scoping, title/description text fidelity, response diagnostics, parser-side malformed count diagnostics, negative count validation, direct constructor state, category href route validation, category href ID ASCII-shape validation, and adjacent generated scalar ASCII-shape fixes; they did not validate Unicode digit normalization in generated forum category count cells.
- This slice does not change request payloads, retry policy, response-body validation, title/description extraction, category href parsing, collection/search behavior, cached category thread behavior, create-thread behavior, live Wikidot behavior, direct `ForumCategory` constructors, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated forum-start HTML from real accounts, private forum content, and private site data out of upstream discussion.
