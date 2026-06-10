# PR Draft: Validate Regular User Onclick ID ASCII Shape

## Summary

`wikidot.util.parser.user.user_parse(...)` is the shared parser for Wikidot `span.printuser` markup across recent changes, member lists, private messages, forum threads, forum posts, page metadata, applications, revision lists, votes, and other generated read paths. Issue [316-pr-regular-user-onclick-id-context.md](316-pr-regular-user-onclick-id-context.md) made present non-numeric regular-user `userInfo(...)` values observable, but the accepted ID regex still used Python `\d+`. That allowed Unicode decimal digit glyphs such as `userInfo(\uff11\uff12\uff13\uff14\uff15)` to normalize into ordinary user ID `12345`.

This change requires regular-user `onclick` IDs to match ASCII digits before integer conversion. Valid generated `userInfo(12345)` markup remains compatible, while present non-ASCII digit payloads now raise the existing parser-level malformed-ID `ValueError`.

## Outcome

Browser-free user metadata parsing no longer fabricates registered-user identities by normalizing non-ASCII digit glyphs from generated `onclick` metadata. The diagnostic remains local to the malformed scalar and does not require raw generated page, forum, message, member, application, revision, or vote HTML.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free attribution, membership, moderation, audit, migration, translation review, cached forum scans, private-message processing, page metadata reads, or generated fixtures where registered-user identity must come from structurally valid Wikidot `printuser` metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify the shared user parser as a high-traffic boundary. Existing drafts cover display-name spacing, missing regular-user hrefs, malformed regular-user `onclick` diagnostics, regular-user href route shape, deleted-user `data-id` validation and range validation, direct user ID invariants, profile ID href shape and route validation, QuickModule user IDs, module-specific malformed-user context, and adjacent generated scalar ASCII-shape boundaries.

This slice is not a duplicate of [316-pr-regular-user-onclick-id-context.md](316-pr-regular-user-onclick-id-context.md), [736-pr-validate-regular-user-href-shape.md](736-pr-validate-regular-user-href-shape.md), or [737-pr-validate-profile-id-href-routes.md](737-pr-validate-profile-id-href-routes.md). Issue 316 covers present non-numeric `userInfo(latest)` values; Issue 736 covers href-derived unix-name route shape; Issue 737 covers fetched profile ID href routes. This slice covers Unicode digit normalization in an otherwise parseable regular-user `onclick` ID scalar.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [316-pr-regular-user-onclick-id-context.md](316-pr-regular-user-onclick-id-context.md), [302-pr-regular-user-href-validation.md](302-pr-regular-user-href-validation.md), [736-pr-validate-regular-user-href-shape.md](736-pr-validate-regular-user-href-shape.md), [737-pr-validate-profile-id-href-routes.md](737-pr-validate-profile-id-href-routes.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [730-pr-validate-deleted-user-data-id-range.md](730-pr-validate-deleted-user-data-id-range.md), [743-pr-validate-forum-thread-script-id-ascii-shape.md](743-pr-validate-forum-thread-script-id-ascii-shape.md), [745-pr-validate-private-message-data-href-id-ascii-shape.md](745-pr-validate-private-message-data-href-id-ascii-shape.md), [746-pr-validate-forum-category-href-id-ascii-shape.md](746-pr-validate-forum-category-href-id-ascii-shape.md), and [747-pr-validate-forum-thread-href-id-ascii-shape.md](747-pr-validate-forum-thread-href-id-ascii-shape.md).

## Changes

- Require regular-user `userInfo(...)` IDs to match `[0-9]+` before `int(...)`.
- Preserve valid regular-user parsing, display-name spacing, href/unix-name extraction, avatar URL construction, missing-href validation, malformed-href validation, present non-numeric `onclick` diagnostics, missing-ID diagnostics, deleted-user parsing, anonymous-user parsing, guest-user parsing, and Wikidot system-user parsing.
- Add focused regression coverage for fullwidth regular-user ID text `\uff11\uff12\uff13\uff14\uff15`.

## Type Of Change

- Bug fix
- Shared user parser scalar-shape validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A regular `printuser` anchor whose `onclick` has a non-ASCII digit `userInfo(...)` ID must fail before `User` construction. |
| R2 | The malformed-ID error must preserve the observed scalar value through the existing `user id is malformed: <value>` diagnostic. |
| R3 | Valid ASCII `userInfo(...)` IDs must continue to parse the same `User.id` and generated avatar URL. |
| R4 | Existing missing-ID and present non-numeric malformed-ID diagnostics must remain compatible. |
| R5 | Existing regular-user href parsing, non-regular user parsing, and shared-parser caller workflows must remain compatible. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, raw generated HTML from real sites, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, parser tests, shared-user caller tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `userInfo(\uff11\uff12\uff13\uff14\uff15)` raises before a `User` is returned. | `test_parse_regular_user_rejects_non_ascii_digit_onclick_id` failed RED with `DID NOT RAISE`, then passed after ASCII-only ID validation. | Returning a `User`, storing ID `12345`, or silently dropping the anchor rejects this local completion claim. | Shared user parser | `src/wikidot/util/parser/user.py`, `tests/unit/parsers/test_user_parser.py` |
| R2 | The parser reports the malformed scalar through the existing malformed-ID message family. | The focused regression asserts `user id is malformed: \uff11\uff12\uff13\uff14\uff15`. | Reporting only `user id is not found`, leaking a raw conversion error, or hiding the scalar rejects this local completion claim. | Parser diagnostics | focused test |
| R3 | Valid ASCII generated IDs continue to work. | Focused GREEN included `test_parse_user_extracts_onclick_id`. | Rejecting `userInfo(99999)`, changing the extracted ID, or changing generated avatar URL behavior rejects this local completion claim. | Valid regular-user compatibility | parser tests |
| R4 | Existing malformed and missing-ID branches stay green. | Focused GREEN included `test_parse_regular_user_with_malformed_onclick_id_raises`, and parser-file coverage passed. | Reclassifying `userInfo(latest)` or absent metadata into the wrong diagnostic path rejects this local completion claim. | Prior parser branches | parser tests |
| R5 | Shared callers remain green. | `tests/unit/parsers/test_user_parser.py` passed 23 tests, shared user caller coverage passed 1865 tests, and full unit passed 3749 tests. | Regressing regular-user href parsing, display-name spacing, deleted/anonymous/guest/Wikidot user parsing, site/member/application/private-message/forum/page/revision workflows, or any unit test rejects this local completion claim. | Shared user workflows | `tests/unit` |
| R6 | No live site state or private material is needed. | The regression uses synthetic unit-level `printuser` HTML and a no-HTTP mock client. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, real user names, private page source, private message data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, parser tests, shared-caller tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `ec14aea fix(user): validate onclick id ascii shape`.

- RED: `uv run --extra test pytest tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_regular_user_rejects_non_ascii_digit_onclick_id -q` failed before the fix with `DID NOT RAISE` because `userInfo(\uff11\uff12\uff13\uff14\uff15)` was accepted and normalized as user ID `12345`.
- GREEN focused: `uv run --extra test pytest tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_regular_user_rejects_non_ascii_digit_onclick_id tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_regular_user_with_malformed_onclick_id_raises tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_user_extracts_onclick_id -q` passed 3 tests.
- `uv run --extra test pytest tests/unit/parsers/test_user_parser.py -q` passed 23 tests.
- `uv run --extra test pytest tests/unit/parsers/test_user_parser.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_private_message.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py tests/unit/test_site_application.py -q` passed 1865 tests.
- `uv run --extra test pytest tests/unit -q` passed 3749 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `user_parse(...)` raises `ValueError("user id is malformed: \uff11\uff12\uff13\uff14\uff15")` for a regular user anchor whose `onclick` contains fullwidth decimal digits in `userInfo(...)`.
- The parser does not construct `User(id=12345)` from non-ASCII digit `onclick` metadata.
- Valid regular user markup with ASCII `userInfo(99999)` still extracts the same ID, display name, unix name, and generated avatar URL.
- Present non-numeric regular-user `onclick` values such as `userInfo(latest)` still raise `ValueError("user id is malformed: latest")`.
- Missing regular-user ID metadata still raises `ValueError("user id is not found")`.
- Existing regular-user href parsing, display-name spacing, deleted-user parsing, anonymous-user parsing, guest-user parsing, Wikidot system-user parsing, and shared user-parser caller wrappers remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real sites, raw rollout path, real user name, private page source, private message data, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 316. Mitigation: Issue 316 covers present non-numeric malformed IDs such as `latest`; this slice covers Unicode digit normalization that still passes the old numeric branch.
- Risk: Tightening `onclick` parsing could reject unusual but valid generated output. Mitigation: Wikidot generated user IDs in fixtures are ordinary ASCII decimal digits, and valid ASCII parsing remains tested.
- Risk: Changing the shared user parser could affect many modules. Mitigation: the change is limited to the regular-user accepted ID character class, and broad shared-caller plus full-unit tests passed.
- Risk: Diagnostics could expose private user context. Mitigation: the parser-level diagnostic includes only the malformed scalar already inside the parser input and omits raw generated HTML, site names, page source, private message bodies, credentials, cookies, local paths, and rollout context.

## Dependencies

- BeautifulSoup continues to expose anchor `onclick` values as attributes.
- Normal Wikidot user metadata continues to identify registered users through `/user:info/...` links plus ASCII numeric `userInfo(...)` IDs.
- Module parsers continue to catch shared parser `ValueError` and add their own site, page, thread, post, message, revision, application, or member context where applicable.

## Open Questions

None for this local slice. Future shared user parser changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Regular user markup supplies both an integer user ID and a user-info link-derived unix name. Unicode digit normalization can silently turn malformed generated `onclick` metadata into a valid-looking registered user ID. Requiring ASCII digits keeps generated identity parsing strict and consistent with adjacent generated scalar-shape fixes while preserving valid regular-user markup and existing caller-specific parser context.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: fullwidth digit `userInfo(...)` payloads were accepted and normalized to user ID `12345`.
- Existing local drafts covered display-name spacing, missing/malformed hrefs, present non-numeric `onclick` diagnostics, deleted-user `data-id` validation, direct user ID invariants, profile ID href validation, module-specific malformed user context, and adjacent generated scalar ASCII-shape fixes; they did not validate Unicode digit normalization in shared regular-user `onclick` IDs.
- This slice does not change request payloads, live Wikidot behavior, user-info href route validation, profile fetching, direct user constructors, deleted-user parsing, anonymous-user parsing, guest-user parsing, Wikidot system-user parsing, shared caller wrappers, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated HTML from real sites, real user names, private page source, private message data, and private site data out of upstream discussion.
