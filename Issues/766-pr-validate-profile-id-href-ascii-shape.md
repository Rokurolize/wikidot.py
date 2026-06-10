# PR Draft: Validate User Profile ID Href ASCII Shape

## Summary

`UserCollection.from_names(...)`, exposed through `User.from_name(...)` and client user accessors, fetches Wikidot profile pages and extracts a concrete user ID from generated profile controls such as `userkarma.php/<id>` and `account/messages#/new/<id>`. Issue 312 made present non-numeric profile ID hrefs value-aware, and Issue 737 tightened profile-control route matching, but one accepted-value gap remained: both accepted route regexes still used Python `\d+`, so Unicode decimal digit strings such as `\uff11\uff12\uff13` were accepted and normalized into ordinary `User.id=123`.

This change requires profile ID href route ID segments to match ASCII `[0-9]+` before integer conversion. Valid generated profile controls such as `http://www.wikidot.com/userkarma.php/123`, `https://www.wikidot.com/userkarma.php/123?tab=karma`, `http://www.wikidot.com/account/messages#/new/123`, and relative accepted routes continue to parse normally. Unicode digit-like ID segments now reuse the existing contextual malformed-ID `NoElementException` path.

## Outcome

Profile lookup no longer fabricates `User.id` values by normalizing malformed generated profile-control route IDs. A fetched profile page with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like ID text in an otherwise accepted profile-control route now fails at the profile parser boundary with requested-user, index, field, and observed href context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free user profile lookup for membership checks, attribution, moderation tooling, migration ledgers, audit scripts, generated fixtures, cached identity resolution, or profile-backed user records where generated identity metadata must be strict.

## Current Evidence

Local rollout-backed drafts repeatedly identify user profile lookup as a practical read boundary. Existing drafts cover profile-title text spacing, requested-user/index diagnostics, malformed present profile ID href diagnostics, profile-control route validation, lookup username validation, blank lookup names, empty bulk lookups, user record invariants, and adjacent shared-user parser ASCII-shape fixes.

This slice is not a duplicate of [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md). Issue 312 covers non-numeric ID segments such as `http://www.wikidot.com/userkarma.php/not-a-number`, which Python `int(...)` rejects. This slice covers Unicode decimal digit text that Python accepts.

This slice is not a duplicate of [737-pr-validate-profile-id-href-routes.md](737-pr-validate-profile-id-href-routes.md). Issue 737 requires exact accepted profile-control routes and rejects foreign hosts, unrelated paths, and extra path segments. This slice preserves those accepted route shapes but rejects non-ASCII digit IDs inside them.

This slice follows the same generated-identity scalar-shape pattern as [748-pr-validate-regular-user-onclick-id-ascii-shape.md](748-pr-validate-regular-user-onclick-id-ascii-shape.md), while applying it to fetched profile-page controls rather than shared `span.printuser` markup.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md), [166-pr-user-profile-parse-context.md](166-pr-user-profile-parse-context.md), [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md), [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md), [623-pr-validate-blank-user-profile-lookup-names.md](623-pr-validate-blank-user-profile-lookup-names.md), [706-pr-skip-empty-user-profile-lookups.md](706-pr-skip-empty-user-profile-lookups.md), [737-pr-validate-profile-id-href-routes.md](737-pr-validate-profile-id-href-routes.md), and adjacent user identity scalar-shape drafts [748-pr-validate-regular-user-onclick-id-ascii-shape.md](748-pr-validate-regular-user-onclick-id-ascii-shape.md), [749-pr-validate-deleted-user-data-id-ascii-shape.md](749-pr-validate-deleted-user-data-id-ascii-shape.md), and [764-pr-validate-quickmodule-user-id-ascii-shape.md](764-pr-validate-quickmodule-user-id-ascii-shape.md).

## Changes

- Require ASCII `[0-9]+` in accepted profile-control href ID segments before integer conversion.
- Preserve valid karma-link and private-message profile-control ID parsing for ASCII IDs.
- Preserve query/fragment suffix handling for accepted valid routes.
- Preserve existing contextual malformed-ID diagnostics for non-numeric, malformed-route, and now non-ASCII digit ID hrefs.
- Add regression coverage for `http://www.wikidot.com/userkarma.php/\uff11\uff12\uff13` and `http://www.wikidot.com/account/messages#/new/\uff11\uff12\uff13`.

## Type Of Change

- Bug fix
- User profile parser validation
- Generated identity scalar hardening
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Accepted profile-control href routes with non-ASCII digit ID segments must fail before constructing a `User`. |
| R2 | The malformed-ID diagnostic must retain requested user, request index, `field=user_id`, and the observed href value. |
| R3 | Valid ASCII karma-link and private-message profile-control IDs must still parse to the same `User.id` values. |
| R4 | Existing non-numeric href diagnostics, malformed route diagnostics, missing-ID behavior, profile-title parsing, avatar URL construction, not-found skip/raise behavior, request batching, collection ordering, `User.from_name(...)`, and client accessor behavior must remain compatible. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, real profile HTML, private user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, user tests, adjacent user-consuming tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `http://www.wikidot.com/userkarma.php/\uff11\uff12\uff13` and `http://www.wikidot.com/account/messages#/new/\uff11\uff12\uff13` raise before a `User` is returned. | `test_from_names_rejects_non_ascii_digit_id_href` failed RED with `DID NOT RAISE`, then passed after ASCII-only profile-control ID parsing. | Returning a `User`, storing ID `123`, or silently dropping the profile response rejects this local completion claim. | Profile lookup parser | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R2 | Each exception reports `User ID is malformed for requested user: bad (index=1, field=user_id, value=<href>)`. | The focused regression asserts the exact established malformed-ID diagnostic for both accepted route families. | Leaking a raw `ValueError`, reporting only missing ID, omitting the observed href, or losing requested-user/index context rejects this local completion claim. | Profile lookup diagnostics | focused test |
| R3 | Valid ASCII profile-control routes still parse as before. | Focused GREEN included multiple-user karma links, message-link skip-not-found behavior, query-suffix karma links, and title-spacing coverage; `tests/unit/test_user.py` passed 122 tests. | Rejecting `111`, `222`, `333`, `444`, or `555` valid profile IDs, changing avatar URL construction, or changing collection order rejects this local completion claim. | Valid profile lookup workflow | user tests |
| R4 | Existing malformed and missing paths stay stable. | Focused GREEN included existing non-numeric malformed href and route-shape regressions. Adjacent user-consuming coverage passed 2161 tests and full unit passed 3770 tests. | Regressing Issue 312 or Issue 737 behavior, not-found handling, request batching, title parsing, user parser callers, QuickModule callers, site/member/application/private-message/page/forum adjacent workflows, or any unit test rejects this local completion claim. | User lookup and adjacent workflows | `tests/unit` |
| R5 | No live site state or private material is needed. | The regression uses synthetic profile HTML and mocked HTTP responses only. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, real profile HTML, private account data, private user names, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, user suite, adjacent suite, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4135cb7 fix(user): validate profile id href ascii shape`.

- RED: `uv run pytest tests/unit/test_user.py::TestUserCollection::test_from_names_rejects_non_ascii_digit_id_href -q` failed before the fix with two `DID NOT RAISE` failures because both supported profile-control route families accepted `\uff11\uff12\uff13` and normalized it to `123`.
- GREEN focused profile ID href slice: `uv run pytest tests/unit/test_user.py::TestUserCollection::test_from_names_rejects_non_ascii_digit_id_href tests/unit/test_user.py::TestUserCollection::test_from_names_malformed_id_href_raises tests/unit/test_user.py::TestUserCollection::test_from_names_rejects_malformed_id_href_routes tests/unit/test_user.py::TestUserCollection::test_from_names_multiple tests/unit/test_user.py::TestUserCollection::test_from_names_skip_not_found tests/unit/test_user.py::TestUserCollection::test_from_names_extracts_id_from_href_with_query tests/unit/test_user.py::TestUserCollection::test_from_names_preserves_profile_title_text_spacing -q` passed 11 tests.
- `uv run pytest tests/unit/test_user.py -q` passed 122 tests.
- `uv run pytest tests/unit/parsers/test_user_parser.py tests/unit/test_user.py tests/unit/test_requestutil.py tests/unit/test_client.py tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_private_message.py tests/unit/test_page_votes.py tests/unit/test_page_revision.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 2161 tests.
- `uv run pytest tests/unit -q` passed 3770 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no change-propagation, cognitive-load, duplication, accidental-complexity, dependency, domain-model, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker. Code pre-commit evidence reported `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.139.0"`, local clawpatch commit `d89ca91`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `UserCollection.from_names(...)` raises `NoElementException("User ID is malformed ...")` for `http://www.wikidot.com/userkarma.php/\uff11\uff12\uff13`.
- `UserCollection.from_names(...)` raises the same diagnostic family for `http://www.wikidot.com/account/messages#/new/\uff11\uff12\uff13`.
- The parser does not construct `User(id=123, ...)` from non-ASCII digit profile-control href metadata.
- Valid ASCII karma and private-message profile-control links still extract the same IDs.
- Existing query-suffix karma links still parse.
- Existing non-numeric present href diagnostics from Issue 312 remain unchanged.
- Existing malformed route diagnostics from Issue 737 remain unchanged.
- Missing/blank ID hrefs, missing profile ID controls, missing/blank profile titles, not-found skip/raise behavior, avatar URL construction, request batching, collection ordering, `User.from_name(...)`, and client accessors remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw real profile HTML, local rollout path, private account detail, private user name, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 312. Mitigation: Issue 312 covers href ID segments that cannot be parsed as integers at all; this slice covers Unicode decimal digit glyphs that Python parses successfully.
- Risk: This could be confused with Issue 737. Mitigation: Issue 737 covers malformed profile-control route shape; this slice keeps the accepted routes but tightens the ID segment grammar.
- Risk: Tightening profile ID href parsing could reject unusual but valid generated Wikidot profile-control links. Mitigation: normal Wikidot IDs in fixtures and accepted route examples are ASCII decimal digits, and valid karma, private-message, and query-suffix controls remained green.
- Risk: Diagnostics could expose raw profile HTML or private data. Mitigation: the diagnostic includes only requested lookup key, index, field name, and scalar href value; tests use synthetic profile HTML and mocked HTTP responses.

## Dependencies

- Wikidot profile pages continue to expose a generated ID-bearing control through either a karma link or a private-message link.
- Normal generated profile-control IDs are expected to use ASCII decimal digits.
- `UserCollection.from_names(...)` remains the source of truth for profile-page user lookup.
- Existing request mocking and BeautifulSoup parsing continue to expose profile-control `href` values as strings.

## Open Questions

None for this local slice. Future profile parser changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Profile lookup turns fetched Wikidot profile controls into concrete `User` records. Unicode digit normalization can silently turn malformed generated identity metadata into a valid-looking user ID. Requiring ASCII digits keeps profile ID extraction strict and consistent with adjacent generated scalar-shape fixes while preserving valid profile controls and established diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: both supported profile-control href route families accepted fullwidth ID text and returned a `User` instead of raising.
- Existing local drafts covered profile title spacing, requested-user/index context, non-numeric profile ID href diagnostics, profile ID href route validation, lookup input validation, blank lookup names, empty bulk lookups, shared user `onclick` ID ASCII-shape validation, deleted-user data-id ASCII-shape validation, and QuickModule returned user ID ASCII-shape validation; they did not validate Unicode digit normalization in fetched profile-control href IDs.
- This slice does not change request URLs, profile-page existence checks, skipped/raised not-found behavior, route-shape validation, title text normalization, avatar URL construction, returned `User` fields for valid ASCII IDs, `User.from_name(...)`, request helper behavior, shared `span.printuser` parsing, QuickModule parsing, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, real profile HTML, real user names, private user data, usernames, passwords, and session-cookie values out of upstream discussion.

## Additional Notes

This is a generated profile-control scalar parser fix. It preserves exact-route validation and valid ASCII ID parsing while preventing Python's Unicode digit support from manufacturing ordinary user IDs out of malformed fetched profile metadata.
