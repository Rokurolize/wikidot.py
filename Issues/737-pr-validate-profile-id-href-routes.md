# PR Draft: Validate User Profile ID Href Routes

## Summary

`UserCollection.from_names(...)`, exposed through `User.from_name(...)` and client user accessors, fetches Wikidot profile pages and extracts a concrete user ID from generated profile controls such as `userkarma.php/<id>` and `account/messages#/new/<id>`. Issue 312 made present non-numeric profile ID hrefs fail with requested-user, index, field, and observed-value context, but one adjacent parser-boundary gap remained: the ID extractor still used an unanchored regex, so it accepted foreign hosts, unrelated paths that merely embedded `userkarma.php/<id>`, and extra path segments after the ID.

This change requires profile ID hrefs to match an expected Wikidot profile-control route before extracting a user ID. Valid `http://www.wikidot.com/userkarma.php/<id>`, `https://www.wikidot.com/userkarma.php/<id>`, relative `/userkarma.php/<id>`, `http(s)://www.wikidot.com/account/messages#/new/<id>`, and relative `/account/messages#/new/<id>` forms remain compatible, including query or fragment suffixes after the ID. Malformed present href routes now reuse the existing value-aware `NoElementException("User ID is malformed ... field=user_id, value=<href>")` path.

## Outcome

Profile lookup no longer fabricates `User.id` from numeric substrings embedded in foreign-host, unrelated-path, or extra-segment profile-control hrefs.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free user lookup for membership checks, attribution, moderation tooling, migration ledgers, audit scripts, generated fixtures, or cached identity resolution.

## Current Evidence

Local rollout-backed drafts repeatedly identify user profile lookup as a practical read boundary. [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md) preserved rendered profile title text, [166-pr-user-profile-parse-context.md](166-pr-user-profile-parse-context.md) added requested-user/index diagnostics, [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md) made malformed present profile ID hrefs value-aware, [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md) and [623-pr-validate-blank-user-profile-lookup-names.md](623-pr-validate-blank-user-profile-lookup-names.md) hardened lookup inputs, and [706-pr-skip-empty-user-profile-lookups.md](706-pr-skip-empty-user-profile-lookups.md) optimized empty bulk lookups.

This slice is not a duplicate of Issue 312. Issue 312 rejects present hrefs that cannot yield a numeric ID, such as `http://www.wikidot.com/userkarma.php/not-a-number`, and preserves observed-value diagnostics. It did not require the numeric ID to come from an exact profile-control route. This slice is also not a duplicate of Issue 736, which validates shared `span.printuser` `/user:info/<unix>` hrefs rather than fetched profile-page ID controls.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md), [166-pr-user-profile-parse-context.md](166-pr-user-profile-parse-context.md), [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md), [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md), [623-pr-validate-blank-user-profile-lookup-names.md](623-pr-validate-blank-user-profile-lookup-names.md), [706-pr-skip-empty-user-profile-lookups.md](706-pr-skip-empty-user-profile-lookups.md), and [736-pr-validate-regular-user-href-shape.md](736-pr-validate-regular-user-href-shape.md).

## Changes

- Replace unanchored profile ID href substring search with exact accepted route matching.
- Accept expected karma and private-message profile-control routes on `www.wikidot.com` or as relative paths.
- Preserve existing valid query/fragment suffix behavior after the numeric ID.
- Reject foreign hosts, unrelated paths that embed `userkarma.php/<id>`, extra path segments after the ID, and foreign `account/messages#/new/<id>` hrefs with the existing contextual malformed-ID error.
- Preserve missing/blank ID href behavior as `User ID is not found ...`.
- Preserve non-numeric present ID href behavior from Issue 312 as `User ID is malformed ... value=<href>`.
- Preserve profile title parsing, avatar URL construction, skipped/raised not-found behavior, request batching, collection ordering, `User.from_name(...)`, and client accessor behavior.

## Type Of Change

- Bug fix
- User profile parser route-shape validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A profile ID control on a foreign host must fail before constructing a `User`. |
| R2 | A profile ID control on an unrelated Wikidot path that embeds `userkarma.php/<id>` must fail before constructing a `User`. |
| R3 | A profile ID control with an extra path segment after the numeric ID must fail before constructing a `User`. |
| R4 | A foreign `account/messages#/new/<id>` route must fail before constructing a `User`. |
| R5 | Malformed route errors must keep the existing requested user, index, `field=user_id`, and observed href diagnostics. |
| R6 | Valid karma links, message links, query suffixes, profile title parsing, avatar URLs, not-found behavior, request batching, and collection ordering must remain compatible. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, full user tests, adjacent user/request/client/QuickModule/user-consuming tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `http://example.com/userkarma.php/777` raises `NoElementException("User ID is malformed ... value=http://example.com/userkarma.php/777")`. | Focused RED failed because the parser returned a `User`; focused GREEN passed after exact route matching. | Extracting ID `777` from a foreign host rejects this local completion claim. | Profile lookup parser | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R2 | `http://www.wikidot.com/profile/userkarma.php/777` raises the same contextual malformed-ID branch. | The parametrized route regression covers the unrelated-path case. | Accepting an unrelated path because it contains `userkarma.php/777` rejects this local completion claim. | Profile lookup parser | user tests |
| R3 | `http://www.wikidot.com/userkarma.php/777/extra` raises the contextual malformed-ID branch. | The parametrized route regression covers the extra-segment case. | Treating `/extra` as a harmless suffix or truncating the path rejects this local completion claim. | Profile lookup parser | user tests |
| R4 | `http://example.com/account/messages#/new/777` raises the contextual malformed-ID branch. | The parametrized route regression covers the foreign message-link case. | Extracting `/new/777` from a foreign-host fragment rejects this local completion claim. | Profile lookup parser | user tests |
| R5 | Each malformed route error includes requested user `bad`, index `1`, field `user_id`, and the observed href value. | The regression asserts the exact exception string for every malformed route. | Omitting the observed href, losing requested-user/index context, or changing the existing diagnostic family rejects this local completion claim. | User profile diagnostics | user tests |
| R6 | Valid profile lookup behavior remains compatible. | Focused GREEN included multiple-user karma links, message-link not-found skip behavior, query-suffix karma links, title spacing, and existing non-numeric malformed href diagnostics; the full user suite passed 120 tests. | Regressing valid IDs, skipped not-found users, query suffixes, title parsing, avatar URL construction, or collection order rejects this local completion claim. | Profile lookup workflow | user tests |
| R7 | No live site state or private material is needed. | All regressions use synthetic HTML and mocked HTTP responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, user tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `aec2e8d fix(user): validate profile id href routes`.

- RED: `uv run pytest tests/unit/test_user.py::TestUserCollection::test_from_names_rejects_malformed_id_href_routes -q` failed before the fix because all four malformed route cases returned `User` instead of raising `NoElementException`.
- GREEN focused: `uv run pytest tests/unit/test_user.py::TestUserCollection::test_from_names_rejects_malformed_id_href_routes tests/unit/test_user.py::TestUserCollection::test_from_names_malformed_id_href_raises tests/unit/test_user.py::TestUserCollection::test_from_names_multiple tests/unit/test_user.py::TestUserCollection::test_from_names_skip_not_found tests/unit/test_user.py::TestUserCollection::test_from_names_extracts_id_from_href_with_query tests/unit/test_user.py::TestUserCollection::test_from_names_preserves_profile_title_text_spacing -q` passed 9 tests.
- `uv run pytest tests/unit/test_user.py -q` passed 120 tests.
- `uv run pytest tests/unit/parsers/test_user_parser.py tests/unit/test_user.py tests/unit/test_requestutil.py tests/unit/test_client.py tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_private_message.py tests/unit/test_page_votes.py tests/unit/test_page_revision.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 2120 tests.
- `uv run pytest tests/unit -q` passed 3709 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted after formatting the new user test.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `UserCollection.from_names(...)` raises a value-aware `NoElementException` for `http://example.com/userkarma.php/777`.
- `UserCollection.from_names(...)` raises the same diagnostic family for `http://www.wikidot.com/profile/userkarma.php/777`.
- `UserCollection.from_names(...)` raises the same diagnostic family for `http://www.wikidot.com/userkarma.php/777/extra`.
- `UserCollection.from_names(...)` raises the same diagnostic family for `http://example.com/account/messages#/new/777`.
- Valid karma and message profile-control links still extract the same IDs.
- Existing query-suffix karma link parsing still works.
- Existing non-numeric present href diagnostics from Issue 312 remain unchanged.
- Missing/blank ID hrefs, missing profile ID controls, missing/blank profile titles, not-found skip/raise behavior, avatar URL construction, request batching, collection ordering, `User.from_name(...)`, and client accessors remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw real profile HTML, local rollout path, or private account detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Tightening profile ID href parsing could reject a valid generated Wikidot profile-control link. Mitigation: accepted patterns cover the existing karma and message-link controls, support HTTP/HTTPS `www.wikidot.com`, relative paths, and query/fragment suffixes; focused and full user tests remained green.
- Risk: This could blur the Issue 312 malformed-value behavior. Mitigation: non-numeric present href diagnostics remain on the same `User ID is malformed ... value=<href>` branch, and the existing Issue 312 regression stayed green.
- Risk: Overly loose matching could continue accepting embedded IDs. Mitigation: route extraction now uses `fullmatch(...)` against expected profile-control patterns instead of searching for a substring.
- Risk: Diagnostics could expose raw profile HTML. Mitigation: the error reports only requested user, index, field name, and scalar href value, not the full fetched profile page, credentials, cookies, or local paths.

## Dependencies

- Wikidot profile pages continue to expose a generated ID-bearing control through either a karma link or a private-message link.
- `UserCollection.from_names(...)` remains the source of truth for profile-page user lookup.
- Existing request mocking and BeautifulSoup parsing continue to expose profile-control `href` values as strings.

## Open Questions

None for this local slice. Future profile parser changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Profile lookup turns fetched Wikidot profile controls into concrete `User` records. Numeric substrings embedded in foreign or unrelated links should not become authoritative user IDs. Exact route matching keeps malformed generated profile markup visible while preserving normal karma and private-message profile controls.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated four prior behaviors: a foreign karma host was accepted, an unrelated Wikidot path was accepted, an extra path segment was accepted, and a foreign message-link fragment was accepted.
- Existing local drafts covered profile title spacing, requested-user/index context, non-numeric profile ID href diagnostics, lookup input validation, blank lookup names, and empty bulk lookups; they did not validate exact profile-control route shape.
- This slice does not change shared `printuser` parsing, QuickModule parsing, request retry behavior, client authentication, live Wikidot behavior, upstream filing state, or valid profile lookup output.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, real profile HTML, real user names, and private user data out of upstream discussion.

