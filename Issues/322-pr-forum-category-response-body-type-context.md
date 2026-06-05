# PR Draft: Report Malformed Forum Category Response Body Types

## Summary

`ForumCategoryCollection.acquire_all(site)`, also exposed through `site.forum.categories`, parses the `forum/ForumStartModule` AMC response `body` as generated forum index HTML. Earlier local slices made forum category reads retry-aware, rejected nested category-like tables, preserved title/description spacing, added site/row parser context, converted malformed count fields into contextual parser errors, and converted missing response `body` fields into site-specific `NoElementException` failures. One adjacent response-boundary gap remained: if the decoded AMC response was a dictionary with a present but non-string `body` value, the code passed that value into BeautifulSoup and leaked a low-level parser `AttributeError`.

This local slice validates present forum category list response `body` values before HTML parsing. Non-string bodies now raise site-specific `NoElementException` with `field=body`, expected type, and observed type. The diagnostic reports only compact structural context and type names; it does not include raw forum index HTML, response JSON, local rollout paths, credentials, or account material.

## Outcome

Malformed forum category list response body types now fail at the module response boundary with actionable site/type context instead of BeautifulSoup internals.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use forum category discovery in browser-free forum, thread, post, or moderation tooling.

## Related Issue

Builds on [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), and [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md). Those drafts established forum category acquisition as a practical retry-aware, parser-scoped, and diagnosable read path while leaving present non-string response bodies as a separate parser-entry boundary.

No upstream issue was filed from this local workspace.

## Changes

- Validate forum category list response `body` values are strings before BeautifulSoup parsing.
- Convert present non-string category-list body values into site-specific `NoElementException`.
- Preserve missing-body diagnostics, retry-exhausted behavior, empty forum indexes, nested category-table filtering, title/description spacing, count diagnostics, site/row parser context, category thread access, reload behavior, and thread creation behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum category response-body type validation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A forum category list response with a present non-string `body` field must fail before BeautifulSoup parsing. |
| R2 | Malformed-body-type errors must identify the affected site, `field=body`, expected type, and observed type while omitting raw generated forum content. |
| R3 | Existing missing-body diagnostics, retry handling, forum category parsing, adjacent forum workflows, and repository quality gates must remain compatible. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `ForumCategoryCollection.acquire_all(site)` raises contextual `NoElementException` when `forum/ForumStartModule` returns a list-valued `body`. | `TestForumCategoryCollectionAcquireAll.test_acquire_all_malformed_response_body_type_includes_site_context` expects `Forum category list response body is malformed for site: test-site (field=body, expected=str, actual=list)`. | Leaking BeautifulSoup `AttributeError`, silently returning an empty collection, or entering category row parsing rejects this local completion claim. | Forum category list reads | `tests/unit/test_forum_category.py` |
| R2 | The malformed-body-type diagnostic includes only the site, field name, expected type, and observed type. | The focused regression matches the full message shape and uses a synthetic list-valued body. | Including raw response JSON, generated forum HTML, category descriptions, credentials, local rollout paths, or account names rejects this local completion claim. | Forum category diagnostics | `src/wikidot/module/forum_category.py` |
| R3 | Existing forum category and adjacent forum behavior remains green. | The forum category suite passed 25 tests, the adjacent forum category/thread/post/revision run passed 193 tests, and the full unit suite passed 889 tests. | Regressing missing-body diagnostics, retry exhaustion, empty forums, nested category filtering, title/description spacing, count parsing, row parser context, category thread access, reload behavior, thread creation, or adjacent forum workflows rejects this local completion claim. | Forum workflows | `tests/unit/test_forum_category.py`; `tests/unit/test_forum_thread.py`; `tests/unit/test_forum_post.py`; `tests/unit/test_forum_post_revision.py` |

## Testing

Implemented locally in commit `eeb7816 fix(forum_category): report malformed body types`.

- RED: `uv run --extra test pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_malformed_response_body_type_includes_site_context -q` failed before the fix with BeautifulSoup `AttributeError` for the list-valued category list body.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_malformed_response_body_type_includes_site_context tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_missing_response_body_includes_site_context tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_success tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_empty tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_raises_when_retry_is_exhausted -q` passed 5 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py -q` passed 25 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 193 tests.
- `uv run --extra test pytest tests/unit -q` passed 889 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- Forum category list reads still request `forum/ForumStartModule` with the existing payload.
- Missing `body` fields still raise the existing not-found diagnostic from Issue 211.
- Present non-string `body` values raise contextual `NoElementException` before BeautifulSoup parsing.
- The malformed-body-type message includes site, `field=body`, expected type, and observed type.
- The malformed-body-type message does not include raw response JSON, generated forum HTML, category descriptions, credentials, local rollout paths, or private account material.
- Existing retry-exhausted behavior, empty forum indexes, nested category-table filtering, title/description spacing, malformed count diagnostics, site/row parser context, category thread access, reload behavior, and thread creation remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real forum-start response body, local rollout path, account material, or generated forum HTML is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Type validation could treat a future bytes-like body as malformed. Mitigation: AMC JSON bodies are expected to decode generated HTML as strings; preserving only string input keeps the parser boundary explicit.
- Risk: Type validation could mask missing-body diagnostics. Mitigation: `None` remains on the existing missing-body path; only present non-string values use the malformed-type diagnostic.
- Risk: Diagnostics could expose generated forum content. Mitigation: messages include site and type names only.

## Dependencies

- The AMC connector already validates decoded response roots as dictionaries before normal module parsing; this slice targets the `body` field value within that dictionary.
- Forum category HTML parser behavior remains unchanged after a valid string body is supplied.

## Open Questions

None for this local slice. Remaining useful work should continue the broader response-body field-type audit across other modules rather than expanding this forum-category change beyond its list boundary.

## Upstream-Safe Motivation

Forum category discovery is a read-heavy prerequisite for thread, post, and revision workflows. If the generated forum index response contains a present non-string `body`, wikidot.py should report the affected site and type mismatch before BeautifulSoup internals obscure the failure.

## Local Evidence, Not For Upstream Paste

- The RED failure showed a list-valued category-list `body` leaking BeautifulSoup `AttributeError`.
- Existing Issue 211 covered missing `body` fields but intentionally left present malformed values as a separate boundary.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, and generated forum HTML out of upstream discussion.

## Additional Notes

This is a response-body field type diagnostics fix. It preserves valid forum category behavior while making malformed present response bodies actionable without retaining generated forum content.
