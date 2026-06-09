# PR Draft: Validate Forum Category Href Routes

## Summary

`ForumCategoryCollection.acquire_all(...)`, exposed through `site.forum.categories`, parses generated `forum/ForumStartModule` category title links into `ForumCategory.id` values. Issue [726-pr-validate-forum-category-href-id-shape.md](726-pr-validate-forum-category-href-id-shape.md) made malformed `c-<id>` path segments such as `/forum/c-1001-latest/test-category` fail instead of becoming category ID `1001`, but the parser still searched the raw href text for a valid-looking `c-<digits>` segment. As a result, `http://example.com/forum/c-1001/test-category`, `https://other-site.wikidot.com/forum/c-1001/test-category`, `http:forum/c-1001/test-category`, `javascript:/forum/c-1001/test-category`, and `mailto:forum/c-1001/test-category` could become current-site `ForumCategory.id=1001`.

This change validates generated forum category href route shape before extracting the category ID. Relative category links and same-site absolute HTTP(S) category links remain compatible, while foreign, hostless-HTTP, and non-HTTP(S) present hrefs raise contextual `NoElementException`.

## Outcome

Browser-free forum category discovery no longer fabricates current-site category identities from foreign absolute URLs, other-site Wikidot URLs, hostless HTTP strings, JavaScript URLs, or mailto URLs. Valid relative category links such as `/forum/c-1001/test-category` and same-site absolute links such as `http://test-site.wikidot.com/forum/c-1001/test-category?from=start#top` continue to parse the same category IDs.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using forum category discovery for browser-free forum inventories, category-owned thread traversal, migration ledgers, moderation tooling, translation review tooling, cached forum scans, generated fixtures, or `site.forum.categories`.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum category discovery as a practical read-heavy workflow and as the entry point for category-owned thread, post, and revision traversal. Existing drafts cover retry-aware category-list fetching, nested-table scoping, title/description text fidelity, row-level parser context, response-body diagnostics, count parsing, collection initialization, direct category ID validation, retained category ID validation, category-thread acquisition ID validation, and generated category href ID-segment validation.

This slice is not a duplicate of [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [644-pr-validate-non-negative-forum-category-ids.md](644-pr-validate-non-negative-forum-category-ids.md), [670-pr-validate-forum-category-collection-retained-id-state.md](670-pr-validate-forum-category-collection-retained-id-state.md), [681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md](681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md), or [726-pr-validate-forum-category-href-id-shape.md](726-pr-validate-forum-category-href-id-shape.md). Issue 726 covers the shape of the `c-<id>` path segment once the generated href is otherwise treated as a category link. This slice covers route and scheme validation before any `c-<id>` segment is accepted as current-site category identity.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [726-pr-validate-forum-category-href-id-shape.md](726-pr-validate-forum-category-href-id-shape.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), and the category/thread traversal drafts listed in Current Evidence.

## Changes

- Parse generated category hrefs with `urlsplit(...)`.
- Reject category hrefs with non-HTTP(S) schemes such as `javascript:` and `mailto:`.
- Reject `http` or `https` hrefs that do not include a host, such as `http:forum/c-1001/test-category`.
- Reject absolute hrefs whose host does not match the current site's domain.
- Extract category IDs from the parsed URL path after route validation.
- Preserve valid relative category hrefs and same-site absolute HTTP(S) category hrefs.
- Preserve existing missing-ID diagnostics, malformed `c-<id>` segment diagnostics, nested-table scoping, title/description text extraction, count parsing, retry behavior, response-body validation, collection behavior, category thread reads, and create-thread behavior.

## Type Of Change

- Bug fix
- Forum category parser route-shape validation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated category href with a non-HTTP(S) scheme such as `javascript:` or `mailto:` must fail before constructing `ForumCategory`. |
| R2 | An `http` or `https` href without a host must fail before constructing `ForumCategory`. |
| R3 | An absolute category href whose host does not match the current site domain must fail before constructing `ForumCategory`. |
| R4 | Malformed href diagnostics must include site unix name, structural row number, `field=id`, and the observed href value. |
| R5 | Valid relative category hrefs must continue to parse the same category IDs. |
| R6 | Valid same-site absolute HTTP(S) category hrefs must continue to parse the same category IDs. |
| R7 | Existing malformed `c-<id>` segment errors, missing-ID errors, nested-row scoping, title/description text, count parsing, category collection behavior, category thread reads, and adjacent forum workflows must remain compatible. |
| R8 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw generated forum HTML, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, full forum-category tests, adjacent forum tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `javascript:/forum/c-1001/test-category` and `mailto:forum/c-1001/test-category` raise `NoElementException` before `ForumCategory` construction. | The focused RED failed with `DID NOT RAISE`; focused GREEN passed after href route validation. | Storing a category ID from a non-HTTP(S) scheme rejects this local completion claim. | Forum category parser | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | `http:forum/c-1001/test-category` raises the contextual malformed-ID error. | The parametrized malformed-route regression covers hostless HTTP. | Treating hostless HTTP text as a relative category route rejects this local completion claim. | Forum category parser | forum-category tests |
| R3 | `http://example.com/forum/c-1001/test-category` and `https://other-site.wikidot.com/forum/c-1001/test-category` raise the contextual malformed-ID error. | The parametrized malformed-route regression covers foreign absolute and other-site Wikidot hosts. | Extracting current-site category IDs from a foreign host rejects this local completion claim. | Forum category parser | forum-category tests |
| R4 | The malformed-href diagnostic includes site, row, field, and raw href value. | The regression matches `Category ID is malformed for site: test-site (row=1, field=id, value=<href>)`. | Omitting structural location or observed href rejects this local completion claim. | Parser diagnostics | forum-category tests |
| R5 | `/forum/c-1001/test-category` still parses category ID `1001`. | Existing `test_acquire_all_success` passed in focused and full forum-category coverage. | Rejecting valid relative category links or changing parsed category IDs rejects this local completion claim. | Relative category href compatibility | forum-category tests |
| R6 | `http://test-site.wikidot.com/forum/c-1001/test-category?from=start#top` still parses category ID `1001`. | `test_acquire_all_preserves_same_site_absolute_category_href` passed. | Rejecting same-site absolute HTTP(S) category routes rejects this local completion claim. | Same-site absolute category href compatibility | forum-category tests |
| R7 | Existing forum category and adjacent forum workflows remain green. | Focused nearby tests, full `test_forum_category.py`, adjacent forum category/thread/post/revision tests, and full unit tests passed. | Regressing malformed segment diagnostics, missing-ID diagnostics, nested-table filtering, title/description text, count parsing, category/thread traversal, or adjacent forum workflows rejects this local completion claim. | Forum workflow | `tests/unit` |
| R8 | No live site state or private material is needed. | All regressions use synthetic generated forum-start HTML and mocked AMC responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private forum names, private thread titles, page source, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, forum-category tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `b26e1c9 fix(forum_category): validate category href routes`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_rejects_malformed_category_href_routes -q` failed before the fix with 5 `DID NOT RAISE` malformed-route cases.
- GREEN focused: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_rejects_malformed_category_href_routes tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_preserves_same_site_absolute_category_href tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_malformed_category_id_includes_site_context tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_success tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_preserves_title_text_spacing tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_ignores_nested_category_tables -q` passed 10 tests.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 147 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 893 tests.
- `uv run pytest tests/unit -q` passed 3728 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumCategoryCollection.acquire_all(...)` raises contextual `NoElementException` for `http://example.com/forum/c-1001/test-category`.
- `ForumCategoryCollection.acquire_all(...)` raises the same diagnostic family for `https://other-site.wikidot.com/forum/c-1001/test-category`.
- `ForumCategoryCollection.acquire_all(...)` raises the same diagnostic family for `http:forum/c-1001/test-category`.
- `ForumCategoryCollection.acquire_all(...)` raises the same diagnostic family for `javascript:/forum/c-1001/test-category`.
- `ForumCategoryCollection.acquire_all(...)` raises the same diagnostic family for `mailto:forum/c-1001/test-category`.
- The malformed-href error includes site unix name, structural row number, `field=id`, and the raw href value.
- Valid relative category links such as `/forum/c-1001/test-category` still parse the same category ID.
- Valid same-site absolute category links such as `http://test-site.wikidot.com/forum/c-1001/test-category?from=start#top` still parse the same category ID.
- Existing malformed ID-segment behavior remains on the `Category ID is malformed ...` path.
- Existing no-ID behavior remains on the `Category ID is not found ...` path.
- Existing nested-table filtering, title/description spacing, count parsing, category collection behavior, lazy category-thread reads, direct thread reads, post/revision traversal, and forum action behavior remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw real forum-start HTML, local rollout path, private forum name, private thread title, page source, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Tightening forum category href route parsing could reject an unusual but valid generated category link. Mitigation: relative category links remain supported, same-site absolute HTTP(S) links remain supported, and the validation only rejects foreign hosts, hostless HTTP(S), and non-HTTP(S) schemes when an ID-looking category segment is present.
- Risk: This could be confused with Issue 726. Mitigation: Issue 726 validates the `c-<id>` path segment shape; this slice validates route scheme and host before accepting an otherwise valid `c-<id>` segment.
- Risk: This could blur previous missing-ID diagnostics. Mitigation: hrefs without any category ID candidate still use `Category ID is not found ...`; present hrefs with ID-looking malformed routes use `Category ID is malformed ...`.
- Risk: Diagnostics could expose raw generated forum HTML. Mitigation: the new diagnostic reports only the scalar href value plus site/row/field context, not full response bodies, credentials, cookies, local paths, page source, private forum content, or private site data.

## Dependencies

- `forum/ForumStartModule` continues to represent category links as relative or same-site HTTP(S) hrefs.
- `ForumCategory.id` remains a parsed integer category identity; direct constructor validation is unchanged.
- `ForumCategoryCollection.acquire_all(...)` remains the public category-list parser for `site.forum.categories`.

## Open Questions

None for this local slice. Future forum category parser changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

`ForumCategory.id` is durable identity metadata for browser-free forum inventories, moderation summaries, migration checks, cached category ledgers, category-owned thread traversal, and downstream forum revision traversal. A category href from another host, a non-HTTP scheme, or a hostless HTTP string is not a current-site generated forum category route. Validating route shape keeps malformed module output visible while preserving normal relative and same-site absolute category links.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: five malformed present href routes did not raise and were accepted as current-site category IDs.
- Existing local drafts covered category-list retrying, parser scoping, missing category IDs, malformed `c-<id>` path segments, title/description/count diagnostics, response-body typing, direct record fields, collection construction, retained state, and adjacent forum traversal; they did not validate present generated category href route/scheme/host shape before `ForumCategory.id` is stored.
- This slice does not change request payloads, retry policy, category row selectors, title text extraction, description text extraction, count parsing, direct `ForumCategory` constructor rules, direct `ForumCategoryCollection` constructor rules, lazy category-thread cache behavior, live Wikidot behavior, upstream filing state, or valid relative/same-site HTTP(S) category output.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated forum-start HTML from real sites, private forum names, private thread titles, page source, private forum content, and private site data out of upstream discussion.
