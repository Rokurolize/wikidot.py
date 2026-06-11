# PR: Validate regular user onclick action shapes

## Summary

The shared `wikidot.util.parser.user.user_parse(...)` regular-user branch should validate the complete generated `userInfo(...)` onclick statement before accepting a user ID.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 316, which reports present non-numeric `userInfo(latest)` values, and local Issue 748, which rejects non-ASCII digit `userInfo(...)` IDs. It is also distinct from caller-specific malformed-user context drafts that wrap shared parser failures with site, page, thread, post, message, revision, application, or member context. This slice covers a valid numeric `userInfo(12345)` call embedded inside a larger malformed `onclick` value.

## Problem Statement

`user_parse(...)` previously used a substring search for `userInfo(<ascii-digits>)` inside regular-user anchor `onclick` attributes. That meant a value such as:

```text
WIKIDOT.page.listeners.userInfo(12345); return false; extraAction()
```

was accepted as user ID `12345`, even though the full `onclick` attribute contained unexpected trailing action text after the known generated statement.

The shared parser is used by recent changes, member lists, private messages, forum threads, forum posts, page metadata, applications, revision lists, votes, ListPages fields, and other generated read paths. Silently accepting embedded numeric user metadata can convert malformed module markup, fixture mistakes, response-adapter bugs, or changed Wikidot action text into a valid-looking `User`.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify the shared `printuser` parser as a high-traffic browser-free identity boundary for attribution, membership, moderation, audits, migration checks, translation review tooling, cached forum scans, private-message processing, page metadata reads, and generated fixtures.

Existing local drafts already covered display-name spacing, missing regular-user hrefs, malformed regular-user `onclick` ID diagnostics, regular-user href route shape, non-ASCII `onclick` ID digits, deleted-user `data-id` validation, direct user ID invariants, QuickModule user IDs, profile ID href validation, and many caller-specific malformed-user context wrappers. The remaining source-level gap before this slice was that the accepted branch only searched for a valid numeric `userInfo(...)` substring rather than validating the complete known onclick statement shape.

The local fix is committed as `50a5c88`.

## Affected Workflows

- Shared `span.printuser` regular-user parsing through `user_parse(...)`.
- Recent changes, site members, site applications, private messages, forum threads, forum posts, forum post revisions, page revisions, page metadata, WhoRated votes, and ListPages fields that consume shared user metadata.
- Browser-free attribution, membership, moderation, audit, migration, translation-review, cached forum, and generated-fixture workflows that trust parsed Wikidot user identities.

## Proposed Fix

Require regular-user `onclick` values to fully match one of the supported generated statement shapes:

```text
userInfo(<ascii-digits>)
WIKIDOT.page.listeners.userInfo(<ascii-digits>)
userInfo(<ascii-digits>); return false;
WIKIDOT.page.listeners.userInfo(<ascii-digits>); return false;
```

If an `onclick` value contains `userInfo(...)` but does not match a supported full statement, raise `ValueError("user onclick is malformed: <onclick>")`. Keep the existing `ValueError("user id is malformed: <value>")` behavior for complete `userInfo(...)` statements whose argument is present but malformed, and keep `ValueError("user id is not found")` for absent ID metadata.

## Implementation Notes

The patch changes the regular-user `onclick` ID extraction in `user_parse(...)` from `re.search(...)` to `re.fullmatch(...)` against the known Wikidot listener statement shapes.

The regression test constructs a regular `printuser` anchor with a valid `href`, visible username, and malformed trailing onclick text:

```text
WIKIDOT.page.listeners.userInfo(12345); return false; extraAction()
```

It asserts that the parser raises:

```text
user onclick is malformed: WIKIDOT.page.listeners.userInfo(12345); return false; extraAction()
```

Existing parser tests still prove valid regular users, malformed `userInfo(latest)`, non-ASCII digit IDs, display-name spacing, HTTP/HTTPS hrefs, missing hrefs, malformed hrefs, deleted users, anonymous users, guest users, and the Wikidot system user remain compatible.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_regular_user_rejects_trailing_onclick_action_text -q
uv run pytest tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_regular_user_rejects_trailing_onclick_action_text tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_regular_user_with_malformed_onclick_id_raises tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_regular_user_rejects_non_ascii_digit_onclick_id tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_user_extracts_onclick_id tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_regular_user -q
uv run pytest tests/unit/parsers/test_user_parser.py -q
uv run pytest tests/unit/parsers/test_user_parser.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_private_message.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py tests/unit/test_site_application.py -q
uv run pytest tests/unit -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pyright
git diff --check
```

Observed results:

```text
RED: failed with "Failed: DID NOT RAISE <class 'ValueError'>" before the fix
focused GREEN: 5 passed
shared parser file: 25 passed
shared caller suite: 2017 passed
full unit suite: 3944 passed
ruff: passed
format check: passed after formatting the edited test file
mypy: passed with existing notes only
pyright: passed
diff whitespace: passed
```

The complexity scan reported only pre-existing hotspots outside the touched shared parser path.

## Compatibility And Risk Notes

The change only rejects `onclick` attributes where `userInfo(...)` is present but the complete value is not one of the known generated statement shapes. Valid bare calls, valid fully-qualified Wikidot listener calls, and the common `; return false;` suffix remain accepted.

The diagnostic includes the malformed synthetic `onclick` string needed to debug the parser boundary. It does not include raw generated HTML from real sites, page source, forum content, private message bodies, account material, cookies, tokens, passwords, secrets, auth JSON, browser profile data, or raw rollout paths.

## Rationale For Upstream Suitability

The patch replaces permissive substring matching with exact validation at a shared identity parser boundary. It follows the same hardening pattern as the forum post revision action-shape fix, preserves valid Wikidot generated user metadata, and is covered by a regression through the public shared parser API plus broad shared-caller coverage.

## Acceptance Criteria

- Regular-user parser accepts valid bare and known fully-qualified `userInfo(<ascii-digits>)` statements.
- Regular-user parser accepts the existing valid `; return false;` statement suffix.
- Regular-user parser rejects trailing unexpected action text after the known statement.
- Present malformed `userInfo(...)` ID arguments keep the existing malformed-ID diagnostic.
- Missing regular-user ID metadata keeps the existing missing-ID diagnostic.
- Existing deleted-user, anonymous-user, guest-user, Wikidot-user, href, display-name spacing, shared-caller, and full-unit behavior remains covered.

## Local Evidence, Not For Upstream Paste

- Local code commit: `50a5c88`
- Thread workspace report records the RED/GREEN and full gate evidence for this slice.
- Clawpatch provenance was checked against local fork `d89ca91`, provider `codex`, state `missing`, `codex-cli 0.139.0`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.
- No raw generated HTML from real sites, page source, forum content, private message bodies, account material, cookies, tokens, passwords, secrets, auth JSON, browser profile data, or raw rollout paths were captured in this draft.
