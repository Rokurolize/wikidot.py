# PR Draft: Validate Regular User Href Shape

## Summary

`wikidot.util.parser.user.user_parse(...)` is the shared `span.printuser` parser used by site members, site applications, private messages, forum metadata, page metadata, page votes, revision lists, recent changes, and downstream browser-free ledgers. Issue 302 made missing or empty regular-user `href` values fail before constructing `User(unix_name="")`, but one adjacent parser-boundary gap remained: any non-empty `href` that did not contain an exact Wikidot `/user:info/<unix>` route was accepted as the unix name, and hrefs with embedded `/user:info/...` substrings were partially extracted.

This change requires regular-user anchors to use the expected user-info route shape before constructing a `User`. Valid relative `/user:info/<unix>` links and valid absolute `http://www.wikidot.com/user:info/<unix>` or `https://www.wikidot.com/user:info/<unix>` links remain compatible. Malformed hrefs such as `/user:info/test-user/extra`, `http://example.com/user:info/test-user`, and `javascript:;` now raise `ValueError("user href is malformed: <href>")` with the observed value.

## Outcome

Regular `printuser` parsing no longer fabricates or partially extracts `User.unix_name` from arbitrary, foreign-host, or extra-path href values.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who rely on generated user metadata for browser-free audits, member/application reads, message exports, forum/page inventories, migration checks, moderation summaries, or cached identity ledgers.

## Current Evidence

Local rollout-backed drafts repeatedly identify shared user parsing as a high-traffic parser boundary. [118-pr-preserve-printuser-name-spacing.md](118-pr-preserve-printuser-name-spacing.md) preserved display-name text, [302-pr-regular-user-href-validation.md](302-pr-regular-user-href-validation.md) rejected missing regular-user hrefs, [316-pr-regular-user-onclick-id-context.md](316-pr-regular-user-onclick-id-context.md) made malformed regular-user `onclick` IDs observable, [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md) hardened direct `User` IDs, and [730-pr-validate-deleted-user-data-id-range.md](730-pr-validate-deleted-user-data-id-range.md) validated deleted-user generated ID ranges inside this shared parser.

This slice is not a duplicate of those drafts. Issue 302 only rejects missing or empty regular-user hrefs and explicitly left non-`/user:info/...` href shape validation open. Issue 316 validates `userInfo(...)` ID extraction, not href-derived unix-name extraction. Issue 118 preserves display-name spacing. Issue 730 covers deleted-user `data-id`, and Issue 647 covers direct constructed user IDs after caller or parser input has already become a numeric ID.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [302-pr-regular-user-href-validation.md](302-pr-regular-user-href-validation.md), [316-pr-regular-user-onclick-id-context.md](316-pr-regular-user-onclick-id-context.md), [118-pr-preserve-printuser-name-spacing.md](118-pr-preserve-printuser-name-spacing.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), and [730-pr-validate-deleted-user-data-id-range.md](730-pr-validate-deleted-user-data-id-range.md).

## Changes

- Replace substring search for `/user:info/...` with exact route-shape validation in the regular-user branch.
- Accept relative `/user:info/<unix>` links and absolute `http://www.wikidot.com/user:info/<unix>` or `https://www.wikidot.com/user:info/<unix>` links.
- Reject extra path segments, foreign hosts, and arbitrary non-user-info hrefs with `ValueError("user href is malformed: <href>")`.
- Preserve missing or empty regular-user `href` behavior from Issue 302 as `ValueError("user href is not found")`.
- Preserve valid display-name extraction, `onclick` user ID extraction, avatar URL generation, deleted-user parsing, anonymous-user parsing, guest-user parsing, and Wikidot system-user parsing.
- Update one site-application length-mismatch fixture to use valid `/user:info/...` links so it continues testing its original count-mismatch behavior under stricter shared parser validation.

## Type Of Change

- Bug fix
- Shared user parser shape validation
- Regression test
- Fixture correction

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A regular `printuser` href with an extra path segment after the unix name must fail before constructing `User`. |
| R2 | A regular `printuser` href on a non-Wikidot host must fail before constructing `User`. |
| R3 | An arbitrary non-user-info href must fail before constructing `User`. |
| R4 | The malformed-href error must include the observed raw href value. |
| R5 | Valid relative, HTTP, and HTTPS Wikidot user-info links must keep existing parsing behavior. |
| R6 | Missing or empty `href` behavior, malformed `onclick` behavior, display-name spacing, avatar URL construction, and non-regular printuser variants must remain unchanged. |
| R7 | Shared parser callers must remain green, including site applications whose tests use regular-user fixtures. |
| R8 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, parser tests, adjacent shared-caller tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `/user:info/test-user/extra` raises `ValueError("user href is malformed: /user:info/test-user/extra")`. | Focused RED failed because the parser returned `User`; focused GREEN passed after exact route validation. | Returning a `User`, extracting `test-user/extra`, or silently truncating the path rejects this local completion claim. | Shared user parser | `src/wikidot/util/parser/user.py`, `tests/unit/parsers/test_user_parser.py` |
| R2 | `http://example.com/user:info/test-user` raises `ValueError("user href is malformed: http://example.com/user:info/test-user")`. | Focused RED failed because the parser extracted the embedded substring; focused GREEN passed after host-aware route validation. | Accepting a foreign-host href because it contains `/user:info/` rejects this local completion claim. | Shared user parser | parser tests |
| R3 | `javascript:;` raises `ValueError("user href is malformed: javascript:;")`. | Focused RED failed because the parser treated the href as the unix name; focused GREEN passed after exact route validation. | Treating arbitrary href text as `User.unix_name` rejects this local completion claim. | Shared user parser | parser tests |
| R4 | Each malformed-href error includes the exact observed href. | The parametrized regression asserts exact exception strings for all three malformed href values. | Omitting the raw value, masking the value, or raising an unrelated parser message rejects this local completion claim. | Parser diagnostics | parser tests |
| R5 | Valid absolute HTTP and HTTPS user-info links still parse, and a relative user-info link remains valid through a site-application caller fixture. | Parser suite passed 22 tests and adjacent shared-caller suite passed 2194 tests after the fixture correction. | Regressing valid ID, display name, unix name, or caller parsing rejects this local completion claim. | Valid regular-user parsing | parser and caller tests |
| R6 | Existing regular-user and variant behavior remains stable. | Existing parser tests for missing href, malformed onclick ID, display-name spacing, HTTP, HTTPS, deleted, anonymous, guest, Wikidot, no-link, special-name, and image-first cases remained green. | Reclassifying missing href, changing variant dispatch, or altering successful `User` fields rejects this local completion claim. | Shared parser compatibility | parser tests |
| R7 | Shared caller workflows remain compatible. | Adjacent suite covering parser, user, site, member, application, forum, private-message, page, revision, and vote consumers passed 2194 tests; full unit passed 3705 tests. | Regressing member/application/forum/page/private-message/read workflows or leaving stale malformed fixtures rejects this local completion claim. | User parser consumers | affected unit suites |
| R8 | No live site state or private material is needed. | All regressions use synthetic HTML and mocked clients. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, parser tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `c71aea5 fix(user): validate regular user href shape`.

- RED: `uv run --extra test pytest tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_regular_user_with_malformed_href_raises -q` failed before the fix because `/user:info/test-user/extra`, `http://example.com/user:info/test-user`, and `javascript:;` all returned `User` instead of raising.
- GREEN focused: `uv run --extra test pytest tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_regular_user_with_malformed_href_raises -q` passed 3 tests.
- `uv run --extra test pytest tests/unit/parsers/test_user_parser.py -q` passed 22 tests.
- `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_length_mismatch -q` passed 1 test after updating the fixture hrefs to valid `/user:info/user1` and `/user:info/user2` links.
- `uv run --extra test pytest tests/unit/parsers/test_user_parser.py tests/unit/test_user.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_private_message.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py -q` passed 2194 tests.
- `uv run --extra test pytest tests/unit -q` passed 3705 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted after applying the formatter to the new parser test.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `user_parse(...)` raises `ValueError("user href is malformed: /user:info/test-user/extra")` for a regular user href with an extra path segment.
- `user_parse(...)` raises `ValueError("user href is malformed: http://example.com/user:info/test-user")` for a foreign-host href that only embeds a Wikidot route substring.
- `user_parse(...)` raises `ValueError("user href is malformed: javascript:;")` for arbitrary non-user-info href text.
- Missing or empty regular-user hrefs still raise `ValueError("user href is not found")`.
- Valid HTTP and HTTPS Wikidot `/user:info/<unix>` links still extract the same ID, display name, unix name, and avatar URL.
- Valid relative `/user:info/<unix>` links remain usable by shared-parser callers.
- Deleted-user, anonymous-user, guest-user, Wikidot system-user, display-name spacing, malformed `onclick` ID diagnostics, and avatar URL generation remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated user markup from real sites, local rollout path, or private account detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Changing the shared user parser could affect many modules. Mitigation: the change is limited to regular-user href shape after a non-empty href exists, and the adjacent shared-caller suite plus full unit suite passed.
- Risk: This could be confused with Issue 302. Mitigation: Issue 302 rejects missing or empty href values; this slice rejects present hrefs that are not exact Wikidot user-info routes.
- Risk: Some stale tests may have used placeholder hrefs while testing unrelated behavior. Mitigation: one site-application length-mismatch fixture was corrected to valid user-info links so the test still exercises its original mismatch branch.
- Risk: Overly loose matching could continue accepting malformed hrefs. Mitigation: the parser now uses full route matching instead of searching for a substring.

## Dependencies

- BeautifulSoup continues to expose anchor `href` values as strings.
- Normal Wikidot regular-user metadata continues to identify users through `/user:info/<unix>` links plus `userInfo(...)` IDs.
- Module parsers continue to treat shared user parser failures as `ValueError` and may add caller-specific site/page/thread/message context around them.

## Open Questions

None for this local slice. Future user-parser work should be selected only with a fresh non-duplicate boundary and a public RED test.

## Upstream-Safe Motivation

Regular user markup supplies a numeric ID and a user-info route-derived unix name. Accepting arbitrary href text or partial foreign-host route substrings creates misleading identity records and can push malformed generated markup into downstream ledgers. Exact route-shape validation keeps malformed user metadata visible while preserving normal Wikidot links.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated three prior behaviors: extra path text was accepted, a foreign host was accepted because it embedded `/user:info/`, and arbitrary href text became `User.unix_name`.
- Existing local drafts covered missing regular-user hrefs, malformed regular-user onclick IDs, display-name spacing, direct user ID invariants, and deleted-user generated ID parsing; they did not validate the route shape of present regular-user hrefs.
- The adjacent suite initially exposed one stale synthetic fixture that used `href="#"` while testing site-application row/text count mismatch. The fixture was corrected to valid user-info hrefs, and the intended mismatch test passed.
- This slice does not change request behavior, module parser scoping, valid user parsing, deleted-user fallback behavior, cache behavior, live Wikidot behavior, or any upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated user markup from real sites, real user names, and private site history out of upstream discussion.
