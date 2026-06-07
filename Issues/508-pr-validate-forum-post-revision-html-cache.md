# PR Draft: Validate ForumPostRevision HTML Cache

## Summary

`ForumPostRevision._html` is the optional cached HTML string behind the public `ForumPostRevision.html` property. It is populated by lazy revision HTML acquisition, batched `with_html` acquisition, duplicate cached HTML reuse, generated forum edit-history ledgers, local fixtures, generated adapters, and rehydrated forum revision records. Earlier local slices validated revision-list acquisition inputs, revision-list response diagnostics, revision HTML response content, duplicate revision HTML reuse, direct revision-field construction, revision collection inputs, collection parent posts, direct public `revision.html = ...` assignments, and cached `ForumPost._revisions` construction, but direct `ForumPostRevision(..., _html=...)` construction still accepted malformed cached values such as booleans, integers, lists, dictionaries, and arbitrary objects.

This change validates the direct constructor's optional HTML cache during `ForumPostRevision.__post_init__`. `_html=None` remains valid for revisions that have not acquired HTML yet, real strings remain valid, and malformed non-null values now raise the same stable `ValueError("revision.html must be a string")` diagnostic used by the public `html` setter before malformed local cache state can be returned by `revision.html`.

## Outcome

Directly constructed `ForumPostRevision` objects now fail early when optional cached HTML state is malformed, while preserving lazy HTML acquisition for `_html=None` and preserving valid preloaded HTML strings.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free forum edit-history inventories, revision comparison ledgers, moderation tooling, translation review tooling, cached forum records, local fixtures, generated adapters, or serialized and rehydrated `ForumPostRevision` objects.

## Current Evidence

Forum-post revision HTML drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), and [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md) establish revision HTML acquisition, cached direct revision reuse, duplicate HTML reuse, response diagnostics, and revision cache population as active operational surfaces.

Constructor and state-integrity drafts [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [433-pr-validate-forum-post-revision-html-assignments.md](433-pr-validate-forum-post-revision-html-assignments.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md), [464-pr-validate-forum-post-revision-creator-time-fields.md](464-pr-validate-forum-post-revision-creator-time-fields.md), [473-pr-validate-forum-post-revision-collection-post-field.md](473-pr-validate-forum-post-revision-collection-post-field.md), [506-pr-validate-forum-post-source-cache.md](506-pr-validate-forum-post-source-cache.md), and [507-pr-validate-forum-post-revisions-cache.md](507-pr-validate-forum-post-revisions-cache.md) establish the local pattern for validating direct record and cache state instead of relying only on parser-created objects or public property setters.

Adjacent PageRevision source/HTML assignment drafts [431-pr-validate-page-revision-source-assignments.md](431-pr-validate-page-revision-source-assignments.md) and [432-pr-validate-page-revision-html-assignments.md](432-pr-validate-page-revision-html-assignments.md) reinforce the distinction between validating public cache mutation and validating constructor-seeded cache state.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 433. Issue 433 validates direct public `revision.html = ...` assignments and preserves the previous cached value on invalid setter input; this slice validates constructor-seeded `_html` before any public setter is invoked.

This is not a duplicate of Issues 463 or 464. Those slices validate direct `ForumPostRevision` identity, creator, and timestamp fields; this slice validates the optional cached HTML field that can be returned by `revision.html`.

This is not a duplicate of Issue 178. Issue 178 requires response JSON content during acquired revision HTML fetches; this slice rejects malformed constructor cache values without making a request.

This is not a duplicate of Issue 421 or 473. Those slices validate revision collections and collection parent posts, not the optional HTML cache stored on a single `ForumPostRevision`.

This is not a duplicate of Issue 507. Issue 507 validates the `ForumPost._revisions` collection cache; this slice validates the `ForumPostRevision._html` string cache.

No upstream issue was filed from this local workspace.

## Changes

- Add optional cached HTML validation for direct `ForumPostRevision(...)` construction.
- Preserve `_html=None` for revisions that should lazily acquire HTML.
- Preserve valid cached HTML strings without coercion.
- Reject booleans, integers, lists, dictionaries, and arbitrary non-string objects using `ValueError("revision.html must be a string")`.
- Add constructor tests for malformed direct `_html` values and valid cached HTML strings.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached forum-post revision HTML state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevision(_html=...)` must accept `None` and real strings. |
| R2 | `ForumPostRevision(_html=...)` must reject non-`None` non-string values with `ValueError("revision.html must be a string")`. |
| R3 | Valid cached HTML strings must be returned by `revision.html` without triggering revision HTML acquisition. |
| R4 | Valid revision construction, lazy revision HTML acquisition, batched `with_html` acquisition, duplicate cached HTML reuse, revision-list acquisition, direct revision acquisition cache population, public `revision.html = ...` assignment validation, revision collections, post revisions-cache behavior, and adjacent forum category/thread/post/revision workflows must remain unchanged. |
| R5 | This slice must not change revision-list acquisition, revision HTML acquisition, response-body diagnostics, parser selectors, post-source acquisition, edit-form parsing, post-list parsing, request construction, live request behavior, or unrelated constructor fields. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, revision basic/HTML tests, revision-file tests, adjacent forum tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None` and valid cached HTML strings remain accepted. | `TestForumPostRevisionBasic.test_init_accepts_valid_html_cache` passed before and after validation was added, preserving a valid cached string and returning it through `revision.html`. Existing constructors continue to use `_html=None`. | Rejecting missing cached HTML, triggering HTML lookup during construction, or coercing valid strings rejects this local completion claim. | `ForumPostRevision` constructor cached HTML state | `tests/unit/test_forum_post_revision.py` |
| R2 | Malformed optional cached HTML values fail at the constructor boundary. | `TestForumPostRevisionBasic.test_init_rejects_malformed_html_cache` failed RED for 5 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, integers, lists, dictionaries, arbitrary objects, or silently coercing malformed values rejects this local completion claim. | `ForumPostRevision` constructor cached HTML state | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Valid cached HTML access remains a cache hit. | The valid-cache test asserts `revision.html == "<p>Cached HTML</p>"` and `revision.is_html_acquired() is True` from the constructor-seeded cache. | Calling AMC, clearing `_html`, replacing the cached string, or treating a valid string as missing rejects this local completion claim. | `ForumPostRevision.html` cache access | `tests/unit/test_forum_post_revision.py` |
| R4 | Existing revision HTML and adjacent forum workflows remain green. | `tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml` passed 40 tests, `tests/unit/test_forum_post_revision.py` passed 118 tests, adjacent forum tests passed 490 tests, and the full unit suite passed 2265 tests. | Regressing lazy HTML acquisition, batched HTML acquisition, duplicate cached HTML reuse, direct revision acquisition, revision-list acquisition, revision collection behavior, post revision-cache behavior, thread post reads, category/thread/post behavior, or setter assignment validation rejects this local completion claim. | Forum post revision and adjacent forum workflows | `tests/unit` |
| R5 | Broader revision semantics remain outside scope. | Existing acquisition, parser, response-body, setter, collection, and adjacent tests remain green; this slice only validates direct constructor cache type integrity. | Changing request construction, parser conversion, response diagnostics, revision ordering, HTML response content handling, edit payloads, source semantics, post-list behavior, thread/category behavior, or live request behavior rejects this local completion claim. | ForumPostRevision constructor scope | `src/wikidot/module/forum_post_revision.py`, adjacent tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, revision HTML, source text, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4bf0c59 fix(forum_post_revision): validate html cache`.

- RED cache tests: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_rejects_malformed_html_cache tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_accepts_valid_html_cache -q` failed 5 malformed `_html` cases before the fix with `DID NOT RAISE`, while the valid cached HTML case passed.
- GREEN cache tests: the same focused command passed 6 tests after optional HTML-cache validation was added.
- Constructor/HTML block: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml -q` passed 40 tests.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 118 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 490 tests.
- `uv run ruff format --check src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed with 2 files already formatted.
- `uv run ruff check src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed.
- `uv run mypy src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2265 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPostRevision(_html=None)` remains valid and lazy HTML acquisition remains available.
- `ForumPostRevision(_html="<p>Cached HTML</p>")` remains valid and `revision.html` returns the cached string without a lookup.
- `ForumPostRevision(_html=True)`, `ForumPostRevision(_html=9001)`, `ForumPostRevision(_html=["<p>Cached HTML</p>"])`, `ForumPostRevision(_html={"html": "<p>Cached HTML</p>"})`, and `ForumPostRevision(_html=object())` raise `ValueError("revision.html must be a string")` when every other constructor field is valid.
- Existing parser-created revisions, direct revision fixtures, lazy `ForumPostRevision.html`, direct and batched `ForumPostRevisionCollection.get_htmls(...)`, cached direct revision acquisition, duplicate cached revision and HTML reuse, public `revision.html = ...` assignment validation, `ForumPost.revisions`, forum post source behavior, forum post edit behavior, and adjacent forum workflows remain green.
- The new tests use unit-level code only and do not validate revision HTML contents, source contents, parser selectors, live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Constructor validation could be confused with revision HTML response validation. Mitigation: the validator checks cache object type only; response content parsing and fetch diagnostics remain outside scope and existing tests stay green.
- Risk: Valid cached HTML strings could accidentally trigger acquisition. Mitigation: the valid-cache test returns the constructor-seeded string and confirms `is_html_acquired()` is true.
- Risk: Public setter behavior could diverge from constructor behavior. Mitigation: the constructor reuses the same string validator as the `html` setter for non-`None` values.
