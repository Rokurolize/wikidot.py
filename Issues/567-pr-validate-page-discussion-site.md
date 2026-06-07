# PR Draft: Validate Page Discussion Site

## Summary

`Page.discussion` lazily retrieves `forum/ForumCommentsListModule`, parses the generated `WIKIDOT.forumThreadId`, and then delegates to `ForumThread.get_from_id(...)`. Existing discussion work already covers retry-aware fetching, exhausted retry diagnostics, missing and malformed response bodies, malformed generated thread IDs, constructor discussion-cache validation, and adjacent page action-time site guards. One adjacent read-time state boundary still trusted `page.site` after construction: if a caller, fixture, or rehydrated page object replaced `page.site` with a mock, dictionary-like object, or other non-`Site` value, `Page.discussion` could reach the mutated object's AMC request path and parser diagnostics before reporting the parent-site problem.

This change revalidates `self.site` at the start of the uncached `Page.discussion` read before AMC request work, generated discussion parsing, delegated forum-thread lookup, or `_discussion_checked` mutation. Malformed read-time page sites now raise `ValueError("site must be a Site")` and leave discussion cache state untouched. Valid cached discussion reads, valid no-discussion checked-state reads, retry behavior, response diagnostics, generated thread-ID parsing, and delegated forum-thread lookup remain unchanged.

## Outcome

The page discussion read path now has an explicit read-time parent-site preflight consistent with the page constructor and adjacent page action/read guards.

## Current Evidence

Existing drafts [045-pr-retry-page-discussion-fetch.md](045-pr-retry-page-discussion-fetch.md), [192-pr-page-auxiliary-fetch-site-context.md](192-pr-page-auxiliary-fetch-site-context.md), [219-pr-page-auxiliary-response-body-context.md](219-pr-page-auxiliary-response-body-context.md), [309-pr-page-discussion-thread-id-context.md](309-pr-page-discussion-thread-id-context.md), [335-pr-page-auxiliary-response-body-type-context.md](335-pr-page-auxiliary-response-body-type-context.md), [512-pr-validate-page-constructor-discussion-cache.md](512-pr-validate-page-constructor-discussion-cache.md), [543-pr-validate-forum-thread-direct-site.md](543-pr-validate-forum-thread-direct-site.md), and [566-pr-validate-page-refresh-source-site.md](566-pr-validate-page-refresh-source-site.md) establish discussion retry behavior, auxiliary site/page diagnostics, response-body validation, generated discussion thread-ID diagnostics, constructor discussion-cache validation, delegated direct forum-thread site validation, and adjacent page read-time site validation. This slice covers mutated `Page.site` at uncached `Page.discussion` read time, not response parsing, thread-ID parsing, constructor cache validation, or direct forum-thread acquisition.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.site` at the start of the uncached `Page.discussion` path.
- Use the validated site for the discussion AMC request, diagnostics, and delegated `ForumThread.get_from_id(...)` call.
- Add a regression for a mutated non-`Site` `page.site` that asserts no AMC request work, no cached discussion mutation, and no `_discussion_checked` update.
- Preserve valid discussion retries, exhausted retry diagnostics, missing/malformed body diagnostics, malformed thread-ID diagnostics, and delegated forum-thread lookup.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Uncached `Page.discussion` must reject a mutated non-`Site` `page.site` with `ValueError("site must be a Site")` before AMC request work, response parsing, delegated thread lookup, or checked-state mutation. |
| R2 | A malformed read-time site must leave `_discussion` as `None` and `_discussion_checked` as `False`. |
| R3 | Valid discussion retry behavior, exhausted retry diagnostics, response-body diagnostics, generated thread-ID diagnostics, and delegated thread lookup must remain stable. |
| R4 | Focused discussion tests, full page module tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A mutated non-`Site` parent fails before discussion request surfaces. | `TestPageProperties.test_discussion_rejects_malformed_site_before_request` failed RED by reaching the mocked `amc_request_with_retry(...)` path and surfacing a mock-derived malformed-body diagnostic, then passed GREEN with `ValueError("site must be a Site")`. | Calling `amc_request(...)`, calling `amc_request_with_retry(...)`, accepting dictionaries/mocks as sites, parsing generated discussion markup, or delegating to `ForumThread.get_from_id(...)` rejects this local completion claim. | `Page.discussion` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | A malformed parent site preserves unchecked discussion state. | The new regression mutates `page.site`, calls `page.discussion`, and asserts `_discussion is None` and `_discussion_checked is False`. | Setting `_discussion_checked = True`, replacing `_discussion`, or caching a false no-discussion result before parent-site validation rejects this local completion claim. | Page discussion cache state | `tests/unit/test_page.py` |
| R3 | Existing discussion behavior remains stable. | Focused GREEN included transient retry, exhausted retry, missing body, malformed body type, malformed thread ID, and malformed-site tests; the full page module run and full unit suite stayed green. | Changing request payloads, retry behavior, exhausted retry exception shape, response diagnostics, no-discussion checked-state behavior, generated thread-ID parsing, or delegated thread lookup rejects this local completion claim. | Page discussion behavior | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Existing repository quality gates remain green. | Focused discussion tests passed 6 tests, full page module tests passed 291 tests, full unit passed 2662 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live auth material or private state is needed to prove the behavior. | The regression uses a synthetic mutated site and mocked unit-level page state; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, private forum data, or live account details. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `971d888 fix(page): validate discussion site`.

- RED read-time site validation: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_discussion_rejects_malformed_site_before_request -q` failed before the fix because mutated `page.site` reached the mocked `amc_request_with_retry(...)` path and surfaced `Page discussion response body is malformed for site: <MagicMock ...>, page: test-page (id=12345, field=body, expected=str, actual=MagicMock)` instead of `ValueError("site must be a Site")`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_discussion_rejects_malformed_site_before_request tests/unit/test_page.py::TestPageProperties::test_discussion_retries_transient_fetch_failures tests/unit/test_page.py::TestPageProperties::test_discussion_raises_when_retry_is_exhausted tests/unit/test_page.py::TestPageProperties::test_discussion_missing_response_body_includes_page_context tests/unit/test_page.py::TestPageProperties::test_discussion_malformed_response_body_type_includes_page_context tests/unit/test_page.py::TestPageProperties::test_discussion_malformed_thread_id_includes_page_context -q` passed 6 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 291 tests.
- `uv run pytest tests/unit -q` passed 2662 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Uncached `Page.discussion` rejects a mutated malformed `page.site` with `ValueError("site must be a Site")` before AMC request work, response parsing, delegated thread lookup, or checked-state mutation.
- `_discussion` and `_discussion_checked` remain unchanged after malformed parent-site validation.
- Valid discussion retry behavior, exhausted retry diagnostics, response-body diagnostics, generated thread-ID diagnostics, and delegated forum-thread lookup remain intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed invalid mutated parent state reaching mocked discussion request work and producing a mock-derived generated-body diagnostic instead of an explicit parent-site diagnostic.
- This slice only validates mutated `Page.site` before the uncached `Page.discussion` read. It does not change page construction, discussion response parsing, generated thread-ID parsing, direct forum-thread acquisition, source/meta/file/revision/vote behavior, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private-message content, private forum content, and live Wikidot account details out of upstream discussion.
