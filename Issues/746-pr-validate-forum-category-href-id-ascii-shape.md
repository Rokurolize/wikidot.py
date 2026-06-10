# PR Draft: Validate Forum Category Href ID ASCII Shape

## Summary

`ForumCategoryCollection.acquire_all(...)`, exposed through `site.forum.categories`, parses generated `forum/ForumStartModule` category title links into `ForumCategory.id` values. Issues [726-pr-validate-forum-category-href-id-shape.md](726-pr-validate-forum-category-href-id-shape.md) and [740-pr-validate-forum-category-href-routes.md](740-pr-validate-forum-category-href-routes.md) made embedded malformed `c-<id>` segments and invalid route/scheme/host shapes fail, but the accepted terminal ID segment still used Python regex `\d+`. That allowed Unicode decimal digit glyphs such as `/forum/c-\uff11\uff10\uff10\uff11/test-category` to normalize into ordinary category ID `1001`.

This change requires the generated forum category href ID segment to match ASCII digits before integer conversion. Valid generated routes such as `/forum/c-1001/test-category` and same-site absolute routes such as `http://test-site.wikidot.com/forum/c-1001/test-category?from=start#top` remain compatible, while present non-ASCII digit payloads now raise the existing contextual malformed-category-ID `NoElementException`.

## Outcome

Browser-free forum category discovery no longer fabricates category identities by normalizing non-ASCII digit glyphs from generated category href metadata. The malformed-value diagnostic remains actionable and does not include raw forum-start HTML or private forum content.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum inventories, category-owned thread traversal, moderation summaries, migration ledgers, translation review tooling, cached forum scans, generated fixtures, or `site.forum.categories` where category identity must come from structurally valid generated category links.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum category discovery as a practical read-heavy workflow and as the entry point for category-owned thread, post, and revision traversal. Existing drafts cover retry-aware category-list fetching, nested-table scoping, title/description text fidelity, row-level parser context, response-body diagnostics, count parsing, collection initialization, direct category ID validation, retained category ID validation, category-thread acquisition ID validation, generated category href ID-segment validation, and generated category href route validation.

This slice is not a duplicate of [726-pr-validate-forum-category-href-id-shape.md](726-pr-validate-forum-category-href-id-shape.md) or [740-pr-validate-forum-category-href-routes.md](740-pr-validate-forum-category-href-routes.md). Issue 726 covers embedded non-ID segment text such as `c-1001-latest`; Issue 740 covers route, scheme, and host shape before accepting a numeric segment. This slice covers Unicode digit normalization in an otherwise valid generated category href ID segment.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [726-pr-validate-forum-category-href-id-shape.md](726-pr-validate-forum-category-href-id-shape.md), [740-pr-validate-forum-category-href-routes.md](740-pr-validate-forum-category-href-routes.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [670-pr-validate-forum-category-collection-retained-id-state.md](670-pr-validate-forum-category-collection-retained-id-state.md), [681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md](681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md), [743-pr-validate-forum-thread-script-id-ascii-shape.md](743-pr-validate-forum-thread-script-id-ascii-shape.md), [744-pr-validate-page-file-row-id-ascii-shape.md](744-pr-validate-page-file-row-id-ascii-shape.md), and [745-pr-validate-private-message-data-href-id-ascii-shape.md](745-pr-validate-private-message-data-href-id-ascii-shape.md).

## Changes

- Require generated forum category `c-<id>` path IDs to match `[0-9]+` before `int(...)`.
- Preserve valid relative category routes and same-site absolute HTTP(S) category routes.
- Preserve existing no-ID diagnostics, embedded malformed-ID diagnostics, route/scheme/host malformed diagnostics, nested-table scoping, title/description extraction, count parsing, retry behavior, response-body validation, collection behavior, category thread reads, and create-thread behavior.
- Add focused regression coverage for escaped fullwidth category ID text `\uff11\uff10\uff10\uff11`.

## Type Of Change

- Bug fix
- Forum category parser scalar-shape validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated forum category href with a non-ASCII digit ID segment must fail before `ForumCategory` construction. |
| R2 | The malformed category-ID error must preserve existing site, row, field, and observed href context. |
| R3 | Valid relative and same-site absolute ASCII category routes must continue to parse the same category IDs. |
| R4 | Existing no-ID, embedded malformed-ID, and route/scheme/host diagnostics must remain compatible. |
| R5 | Existing forum category list workflows and adjacent forum traversal workflows must remain compatible. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw generated forum HTML, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, forum-category tests, adjacent forum tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `/forum/c-\uff11\uff10\uff10\uff11/test-category` raises before a category is returned. | `test_acquire_all_rejects_non_ascii_digit_category_href_id` failed RED with `DID NOT RAISE`, then passed after ASCII-only ID validation. | Returning a `ForumCategory`, storing ID `1001`, or silently dropping the row rejects this local completion claim. | Forum category list parser | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | The malformed diagnostic includes site, row, `field=id`, and raw href value. | The focused regression matches the existing malformed-ID message family. | Omitting structural context or the observed href rejects this local completion claim. | Parser diagnostics | focused test |
| R3 | Valid generated ASCII routes continue to work. | Focused GREEN included `test_acquire_all_success` and same-site absolute href compatibility. | Rejecting valid relative or same-site absolute category links rejects this local completion claim. | Valid href compatibility | forum-category tests |
| R4 | Existing malformed branches stay green. | Focused GREEN included embedded malformed-ID and malformed-route regressions. | Reclassifying no-ID links, embedded malformed-ID links, or invalid routes into a different diagnostic family rejects this local completion claim. | Prior parser branches | forum-category tests |
| R5 | Adjacent workflows remain green. | `tests/unit/test_forum_category.py` passed 148 tests, adjacent forum category/thread/post/revision coverage passed 901 tests, and full unit passed 3747 tests. | Regressing category list parsing, nested-table filtering, title/description spacing, count parsing, collection validation, category-thread traversal, post/revision traversal, create-thread behavior, or any unit test rejects this local completion claim. | Forum workflows | `tests/unit` |
| R6 | No live site state or private material is needed. | The regression uses synthetic unit-level forum-start HTML and mocked responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private forum names, private thread titles, page source, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, forum-category tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `bc84782 fix(forum_category): validate href id ascii shape`.

- RED: `uv run --extra test pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_category_href_id -q` failed before the fix with `DID NOT RAISE` because `/forum/c-\uff11\uff10\uff10\uff11/test-category` was accepted and normalized as category ID `1001`.
- GREEN focused: `uv run --extra test pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_category_href_id tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_malformed_category_id_includes_site_context tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_rejects_malformed_category_href_routes tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_preserves_same_site_absolute_category_href tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_success tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_preserves_title_text_spacing tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_ignores_nested_category_tables -q` passed 11 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py -q` passed 148 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 901 tests.
- `uv run --extra test pytest tests/unit -q` passed 3747 tests.
- `uv run --extra lint ruff check src tests` passed.
- `uv run --extra format ruff format --check src tests` passed with 87 files already formatted.
- `uv run --extra lint mypy src tests --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumCategoryCollection.acquire_all(...)` raises contextual `NoElementException` for a present generated href built from escaped fullwidth digit text `/forum/c-\uff11\uff10\uff10\uff11/test-category`.
- The exception includes site unix name, structural category row number, `field=id`, and raw href value.
- Valid relative category links such as `/forum/c-1001/test-category` still parse category ID `1001`.
- Valid same-site absolute category links such as `http://test-site.wikidot.com/forum/c-1001/test-category?from=start#top` still parse category ID `1001`.
- Existing no-ID behavior, embedded malformed-ID behavior, and malformed route/scheme/host behavior remain on their existing diagnostic paths.
- Existing category-list parsing, retry handling, empty-result behavior, response-body validation, nested-table filtering, title/description spacing, count parsing, collection initialization, `find(...)`, lazy `site.forum.categories`, `ForumCategory.threads`, `reload_threads(...)`, create-thread behavior, and adjacent forum traversal remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw real forum-start HTML, raw rollout path, private forum name, private thread title, page source, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issues 726 or 740. Mitigation: those issues cover embedded malformed-ID segment text and route/scheme/host shape; this slice covers Unicode digit normalization that still passes those branches.
- Risk: Tightening category ID parsing could reject unusual but valid generated forum output. Mitigation: Wikidot category IDs in fixtures are ordinary ASCII decimal digits, and valid relative plus same-site absolute category routes remain tested.
- Risk: Diagnostics could expose private forum content. Mitigation: the diagnostic reports only the scalar href value plus site/row/field context, not response bodies, credentials, cookies, forum names, thread titles, page source, local paths, or private site data.

## Dependencies

- `forum/ForumStartModule` continues to represent category links as relative category routes or same-site HTTP(S) category routes.
- `ForumCategoryCollection.acquire_all(...)` remains the public category-list parser for `site.forum.categories`.
- Direct `ForumCategory.id` constructor and retained category-state validation remain unchanged.

## Open Questions

None for this local slice. Future forum category parser changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

`ForumCategory.id` is durable identity metadata for browser-free forum inventories, moderation summaries, migration checks, cached category ledgers, category-owned thread traversal, and downstream forum revision traversal. Unicode digit normalization can silently turn malformed generated category route metadata into a valid-looking category ID. Requiring ASCII digits keeps generated identity parsing strict and consistent with adjacent forum-thread, page-file, and private-message scalar-shape fixes while preserving valid category links.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: escaped fullwidth digit route IDs were accepted and normalized to category ID `1001`.
- Existing local drafts covered category-list retrying, parser scoping, missing category IDs, embedded malformed `c-<id>` segments, route/scheme/host diagnostics, title/description/count diagnostics, response-body typing, direct record fields, collection construction, retained state, and adjacent forum traversal; they did not validate Unicode digit normalization in generated category href ID scalars.
- This slice does not change request payloads, retry policy, category row selectors, title text extraction, description text extraction, count parsing, direct `ForumCategory` constructor rules, direct `ForumCategoryCollection` constructor rules, lazy category-thread cache behavior, live Wikidot behavior, upstream filing state, or valid relative/same-site HTTP(S) category output.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated forum-start HTML from real sites, private forum names, private thread titles, page source, private forum content, and private site data out of upstream discussion.
