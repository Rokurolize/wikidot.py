# PR Draft: Reject Blank User Profile Titles

## Summary

`UserCollection.from_names(...)` already rejects blank caller-provided lookup names and raises contextual `NoElementException` when the fetched profile page is missing the `h1.profile-title` element. One adjacent parser boundary still accepted a present `h1.profile-title` whose normalized visible text was empty. In that case, wikidot.py returned a `User` with an empty `name` and derived empty `unix_name` instead of reporting malformed profile content.

This change keeps the existing title selector and visible-text spacing normalization, then rejects an empty normalized profile title with `NoElementException("User name is not found for requested user: ...")`. Valid profile titles, missing-title-element diagnostics, user ID parsing, not-found handling, avatar URL construction, collection ordering, `User.from_name(...)`, and adjacent user/profile consumers remain unchanged.

## Outcome

Fetched user profile pages can no longer produce blank local user identities when the title element exists but contains no visible name. Malformed profile HTML now fails at the user-profile parser boundary with requested-user and index context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `client.user.get(...)`, `client.user.get_bulk(...)`, `User.from_name(...)`, or `UserCollection.from_names(...)` for browser-free identity lookup, membership checks, migration tooling, moderation workflows, generated ledgers, or local fixtures that rely on `User.name` and `User.unix_name` being meaningful profile identity fields.

## Current Evidence

Local rollout-backed drafts repeatedly identify user/profile lookup, printuser parsing, profile-title text fidelity, parser diagnostics, and generated user collections as practical read surfaces. Existing drafts [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md), [166-pr-user-profile-parse-context.md](166-pr-user-profile-parse-context.md), [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md), [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md), [623-pr-validate-blank-user-profile-lookup-names.md](623-pr-validate-blank-user-profile-lookup-names.md), [426-pr-validate-user-collection-initialization.md](426-pr-validate-user-collection-initialization.md), and [495-pr-validate-user-scalar-fields.md](495-pr-validate-user-scalar-fields.md) establish profile lookup, profile-title normalization, malformed profile diagnostics, caller lookup-name validation, blank caller-name validation, collection initialization, and direct user scalar type validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issue 120 preserves visible word boundaries in non-empty profile titles, not blank-title rejection. Issue 166 adds requested-user/index context to missing profile parser failures and states that fabricated or empty display names should reject completion, but it only implemented missing-element coverage. Issue 312 reports malformed profile ID href values, not title text emptiness. Issues 358 and 623 validate caller-provided lookup names before request construction, not fetched profile HTML. Issue 426 validates `UserCollection(users=...)` container shape, and Issue 495 validates direct user scalar types but intentionally allows optional text strings; neither covers a fetched blank profile title returning a blank `User.name`.

No upstream issue was filed from this local workspace.

## Changes

- After extracting `h1.profile-title` with `get_text(" ", strip=True)`, reject an empty normalized profile title with `NoElementException("User name is not found ...")`.
- Add a public `UserCollection.from_names(...)` regression covering empty, whitespace-only, and nested-whitespace profile-title markup.
- Preserve missing-title-element diagnostics: `User name element not found for requested user: ...`.
- Preserve profile-title spacing for valid names, user ID extraction from PM/karma links, avatar URL construction, skipped/raised not-found handling, collection ordering, `User.from_name(...)`, client user accessors, request helper behavior, QuickModule behavior, and adjacent page/site/forum workflows.

## Type Of Change

- Parser validation
- User profile identity hardening
- Diagnostics improvement
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A fetched profile page with a present but empty normalized `h1.profile-title` must raise `NoElementException("User name is not found ...")` instead of returning a `User` with blank `name` or `unix_name`. |
| R2 | Empty text, whitespace-only text, and nested markup whose visible text is whitespace-only must be rejected. |
| R3 | Missing `h1.profile-title` elements must keep the existing `User name element not found ...` diagnostic. |
| R4 | Valid profile-title spacing, user ID extraction, avatar URL construction, not-found skip/raise behavior, collection ordering, `User.from_name(...)`, and client accessor delegation must remain unchanged. |
| R5 | Existing user parser, request helper, QuickModule, private-message, site, member/application, forum, and page workflows must remain compatible. |
| R6 | Focused RED/GREEN, user tests, adjacent read-path tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private profile HTML, private user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Blank normalized profile titles fail at the profile parser boundary. | `test_from_names_blank_name_element_raises` failed RED with `DID NOT RAISE`, then passed GREEN after the post-extraction blank-title guard was added. | Returning a `User`, deriving empty `unix_name`, fabricating a profile title, or deferring the failure rejects this local completion claim. | `UserCollection.from_names(...)` profile-title parser | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R2 | Empty, whitespace-only, and nested-whitespace title markup all fail. | The focused regression parameterizes `""`, `"   "`, and `"<span> </span>"`, and all three cases passed GREEN. | Rejecting only one blank shape while accepting another rejects this local completion claim. | Profile-title visible text normalization | `tests/unit/test_user.py` |
| R3 | Missing title elements keep their distinct diagnostic. | Focused GREEN included `test_from_names_missing_name_element`. | Collapsing missing elements and blank present elements into one message, or rewording existing missing-title diagnostics, rejects this local completion claim. | User profile missing-field handling | `tests/unit/test_user.py` |
| R4 | Valid profile lookup behavior remains unchanged. | Focused GREEN included non-empty title spacing, multi-user lookup, malformed ID href diagnostics, and missing ID diagnostics; `tests/unit/test_user.py` passed 116 tests. | Regressing profile URLs, title spacing, ID extraction, avatar URLs, not-found behavior, collection ordering, or `User.from_name(...)` rejects this local completion claim. | User profile lookup workflow | `tests/unit/test_user.py` |
| R5 | Adjacent read workflows remain green. | Adjacent user/parser/client/request/QuickModule/private-message/site/member/application/forum/page coverage passed 2207 tests, and full unit coverage passed 3559 tests. | Regressing shared user parser variants, request helpers, QuickModule lookups, private-message metadata, site/member/application reads, forum reads, page metadata, or client accessors rejects this local completion claim. | User consumers and adjacent modules | `tests/unit` |
| R6 | Repository quality gates pass in the local dependency environment. | Full ruff check passed, full ruff format check passed, full mypy passed with no issues in 87 source files, pyright passed with 0 errors, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic profile HTML and unit-level request mocks only, and this draft avoids raw rollout paths and private payloads. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private profile HTML, private user data, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `c236186 fix(user): reject blank profile titles`.

- RED: `uv run pytest tests/unit/test_user.py::TestUserCollection::test_from_names_blank_name_element_raises -q` failed 3 parameterized cases before the fix because blank profile titles did not raise.
- GREEN focused: `uv run pytest tests/unit/test_user.py::TestUserCollection::test_from_names_blank_name_element_raises tests/unit/test_user.py::TestUserCollection::test_from_names_missing_name_element tests/unit/test_user.py::TestUserCollection::test_from_names_preserves_profile_title_text_spacing tests/unit/test_user.py::TestUserCollection::test_from_names_multiple tests/unit/test_user.py::TestUserCollection::test_from_names_malformed_id_href_raises tests/unit/test_user.py::TestUserCollection::test_from_names_missing_id_element -q` passed 8 tests.
- `uv run pytest tests/unit/test_user.py -q` passed 116 tests.
- `uv run ruff format src/wikidot/module/user.py tests/unit/test_user.py --check` passed with 2 files already formatted.
- `uv run ruff check src/wikidot/module/user.py tests/unit/test_user.py` passed.
- `uv run mypy src/wikidot/module/user.py tests/unit/test_user.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/user.py tests/unit/test_user.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit/test_user.py tests/unit/parsers/test_user_parser.py tests/unit/test_client.py tests/unit/test_requestutil.py tests/unit/test_quick_module.py tests/unit/test_private_message.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py -q` passed 2207 tests.
- `uv run pytest tests/unit -q` passed 3559 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `UserCollection.from_names(client, ["bad"])` raises `NoElementException("User name is not found for requested user: bad (index=1)")` when the fetched profile title is `<h1 class="profile-title"></h1>`.
- The same diagnostic is raised when the fetched profile title is whitespace-only or nested markup with whitespace-only visible text.
- A missing profile-title element still raises `User name element not found for requested user: bad (index=1)`.
- Valid profile-title spacing still preserves visible word boundaries and derives `unix_name` from the non-empty title.
- Valid profile lookup, multi-user lookup, not-found skip/raise behavior, profile ID extraction from PM/karma links, avatar URL construction, collection ordering, `User.from_name(...)`, request helper behavior, user parser variants, QuickModule behavior, and adjacent page/site/forum workflows remain green.
- The new tests use unit-level synthetic profile HTML only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Some unusual real profile could expose an intentionally blank title. Mitigation: a profile title is the source for `User.name` and `User.unix_name`; returning blank identity breaks downstream ledgers more severely than a contextual parser failure.
- Risk: Blank-title handling could blur missing-element diagnostics. Mitigation: the guard runs only after the existing `h1.profile-title` selector succeeds, and missing-element coverage remains green.
- Risk: Tightening parser behavior could affect synthetic fixtures. Mitigation: valid title spacing, multi-user lookup, user suite, adjacent read-path coverage, and full unit/static gates all passed.

## Out Of Scope

Changing profile URL construction, user ID extraction patterns, not-found behavior, `StringUtil.to_unix(...)`, direct `User(...)` optional text semantics, QuickModule parsing, client authentication, live Wikidot behavior, pushing changes, opening upstream Issues, and opening upstream PRs are outside this slice.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used user/profile lookup, user parser output, generated membership/user ledgers, moderation checks, and browser-free identity resolution.
- Existing local drafts covered profile-title spacing, profile parser missing-field context, malformed ID href values, caller username type validation, caller blank-name validation, user collection initialization, and direct user scalar field types, but did not reject a fetched blank profile title.
- The focused RED failure showed a present blank profile-title element returned normally instead of producing a deterministic malformed-profile diagnostic.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private profile HTML, private user data, private site data, and source text from real sites out of upstream discussion.
