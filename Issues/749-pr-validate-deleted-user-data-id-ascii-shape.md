# PR Draft: Validate Deleted User Data ID ASCII Shape

## Summary

`wikidot.util.parser.user.user_parse(...)` is the shared parser for Wikidot `span.printuser` markup across site membership, applications, private messages, page votes, forum threads, forum posts, page metadata, revision lists, recent changes, and other browser-free read paths. Issue [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md) made present non-integer deleted-user `data-id` values observable, and Issue [730-pr-validate-deleted-user-data-id-range.md](730-pr-validate-deleted-user-data-id-range.md) kept explicit negative values inside the parser diagnostic family. One accepted-value gap remained: Python `int(...)` accepts Unicode decimal digit glyphs, so generated markup such as `data-id="\uff11\uff12\uff13"` normalized into ordinary deleted-user ID `123`.

This change requires deleted-user `data-id` values to match ASCII digits before integer conversion. Missing `data-id` still uses the existing compatibility fallback ID `0`, valid ASCII generated IDs still parse, and malformed explicit values now consistently raise `ValueError("deleted user id is malformed: <value>")` from the shared parser boundary.

## Outcome

Browser-free deleted-user parsing no longer fabricates deleted-user identities by normalizing non-ASCII digit glyphs from generated `data-id` metadata. The diagnostic remains local to the malformed scalar and does not require raw generated page, forum, message, member, application, revision, or vote HTML.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free attribution, membership, moderation, audit, migration, translation review, cached forum scans, private-message processing, page metadata reads, page vote ledgers, application reviews, or generated fixtures where deleted-user identity must come from structurally valid Wikidot `printuser` metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify the shared user parser as a high-traffic boundary. Existing drafts cover display-name spacing, missing regular-user hrefs, malformed regular-user `onclick` diagnostics, deleted-user `data-id` diagnostics, deleted-user `data-id` range validation, direct user ID invariants, regular-user href route shape, profile ID href shape and route validation, QuickModule user IDs, module-specific malformed-user context, and adjacent generated scalar ASCII-shape boundaries.

This slice is not a duplicate of [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md), which covers present non-integer deleted-user `data-id` values such as `latest`. It is also not a duplicate of [730-pr-validate-deleted-user-data-id-range.md](730-pr-validate-deleted-user-data-id-range.md), which covers explicit negative integer values, or [748-pr-validate-regular-user-onclick-id-ascii-shape.md](748-pr-validate-regular-user-onclick-id-ascii-shape.md), which covers regular-user `onclick` ID glyph normalization. This slice covers Unicode digit normalization in an otherwise parseable deleted-user `data-id` scalar.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md), [316-pr-regular-user-onclick-id-context.md](316-pr-regular-user-onclick-id-context.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [730-pr-validate-deleted-user-data-id-range.md](730-pr-validate-deleted-user-data-id-range.md), [743-pr-validate-forum-thread-script-id-ascii-shape.md](743-pr-validate-forum-thread-script-id-ascii-shape.md), [744-pr-validate-page-file-row-id-ascii-shape.md](744-pr-validate-page-file-row-id-ascii-shape.md), [745-pr-validate-private-message-data-href-id-ascii-shape.md](745-pr-validate-private-message-data-href-id-ascii-shape.md), [746-pr-validate-forum-category-href-id-ascii-shape.md](746-pr-validate-forum-category-href-id-ascii-shape.md), [747-pr-validate-forum-thread-href-id-ascii-shape.md](747-pr-validate-forum-thread-href-id-ascii-shape.md), and [748-pr-validate-regular-user-onclick-id-ascii-shape.md](748-pr-validate-regular-user-onclick-id-ascii-shape.md).

## Changes

- Require deleted-user `data-id` values to match `[0-9]+` before `int(...)`.
- Preserve valid deleted-user parsing, missing-`data-id` compatibility as ID `0`, malformed non-numeric diagnostics, negative-value diagnostics, regular-user parsing, anonymous-user parsing, guest-user parsing, and Wikidot system-user parsing.
- Add focused regression coverage for fullwidth deleted-user ID text `\uff11\uff12\uff13`.

## Type Of Change

- Bug fix
- Shared user parser scalar-shape validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A deleted-user `printuser` element whose `data-id` contains non-ASCII decimal digit glyphs must fail before `DeletedUser` construction. |
| R2 | The malformed-ID error must preserve the observed scalar value through the existing `deleted user id is malformed: <value>` diagnostic. |
| R3 | Valid ASCII generated deleted-user IDs must continue to parse the same `DeletedUser.id`. |
| R4 | Missing deleted-user `data-id` must still parse as compatibility ID `0`. |
| R5 | Existing non-integer and negative deleted-user `data-id` diagnostics must remain compatible. |
| R6 | Existing regular-user, anonymous-user, guest-user, Wikidot system-user, and shared user-parser caller workflows must remain compatible. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, raw generated HTML from real sites, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, parser tests, shared-user caller tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `data-id="\uff11\uff12\uff13"` raises before a `DeletedUser` is returned. | `test_parse_deleted_user_rejects_non_ascii_digit_data_id` failed RED with `DID NOT RAISE`, then passed after ASCII-only ID validation. | Returning a `DeletedUser`, storing ID `123`, or silently dropping the element rejects this local completion claim. | Shared deleted-user parser branch | `src/wikidot/util/parser/user.py`, `tests/unit/parsers/test_user_parser.py` |
| R2 | The parser reports the malformed scalar through the existing deleted-user malformed-ID message family. | The focused regression asserts `deleted user id is malformed: \uff11\uff12\uff13`. | Reporting only `id must be non-negative or None`, leaking a raw conversion error, omitting the scalar, or using an unrelated parser message rejects this local completion claim. | Parser diagnostics | focused test |
| R3 | Valid ASCII generated deleted-user IDs still work. | Focused GREEN included `test_parse_deleted_user_with_id`. | Rejecting `data-id="99999"` or changing the parsed ID rejects this local completion claim. | Valid deleted-user compatibility | parser tests |
| R4 | Missing `data-id` still maps to the existing unknown-ID fallback. | Focused GREEN included `test_parse_deleted_user_without_data_id`. | Raising for missing `data-id` or changing the fallback ID rejects this local completion claim. | Unknown deleted-user compatibility | parser tests |
| R5 | Existing malformed and negative branches stay green. | Focused GREEN included `test_parse_deleted_user_with_malformed_data_id_raises` and `test_parse_deleted_user_with_negative_data_id_raises`; parser-file coverage passed. | Reclassifying `latest` or `-1` into another diagnostic path rejects this local completion claim. | Prior deleted-user parser branches | parser tests |
| R6 | Shared callers remain green. | `tests/unit/parsers/test_user_parser.py` passed 24 tests, shared user caller coverage passed 1866 tests, and full unit passed 3750 tests. | Regressing regular-user href/onclick parsing, display-name spacing, deleted/anonymous/guest/Wikidot user parsing, site/member/application/private-message/forum/page/revision workflows, or any unit test rejects this local completion claim. | Shared user workflows | `tests/unit` |
| R7 | No live site state or private material is needed. | The regression uses synthetic unit-level `printuser` HTML and a no-HTTP mock client. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, real user names, private page source, private message data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, parser tests, shared-caller tests, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `54f4278 fix(user): validate deleted user data id shape`.

- RED: `uv run --extra test pytest tests/unit/parsers/test_user_parser.py::TestUserParserDeletedUser::test_parse_deleted_user_rejects_non_ascii_digit_data_id -q` failed before the fix with `DID NOT RAISE` because `data-id="\uff11\uff12\uff13"` was accepted and normalized as deleted-user ID `123`.
- GREEN focused: `uv run --extra test pytest tests/unit/parsers/test_user_parser.py::TestUserParserDeletedUser::test_parse_deleted_user_with_id tests/unit/parsers/test_user_parser.py::TestUserParserDeletedUser::test_parse_deleted_user_without_data_id tests/unit/parsers/test_user_parser.py::TestUserParserDeletedUser::test_parse_deleted_user_with_malformed_data_id_raises tests/unit/parsers/test_user_parser.py::TestUserParserDeletedUser::test_parse_deleted_user_rejects_non_ascii_digit_data_id tests/unit/parsers/test_user_parser.py::TestUserParserDeletedUser::test_parse_deleted_user_with_negative_data_id_raises -q` passed 5 tests.
- `uv run --extra test pytest tests/unit/parsers/test_user_parser.py -q` passed 24 tests.
- `uv run --extra test pytest tests/unit/parsers/test_user_parser.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_private_message.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py tests/unit/test_site_application.py -q` passed 1866 tests.
- `uv run --extra test pytest tests/unit -q` passed 3750 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no parser-boundary, compatibility, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad safe/risky cleanup behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker: `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, launcher SHA256 `0518e09af8c6a44990de082462039c9593a8f969a8e0eb10426aa6b3dcf630be`.

## Acceptance Criteria

- `user_parse(...)` raises `ValueError("deleted user id is malformed: \uff11\uff12\uff13")` for a deleted-user `printuser` element whose `data-id` contains fullwidth decimal digits.
- The parser does not construct `DeletedUser(id=123)` from non-ASCII digit `data-id` metadata.
- Valid deleted-user markup with ASCII `data-id="99999"` still returns `DeletedUser(id=99999)`.
- Missing deleted-user `data-id` still returns `DeletedUser(id=0)`.
- Present non-numeric deleted-user `data-id` values such as `latest` still raise `ValueError("deleted user id is malformed: latest")`.
- Negative deleted-user `data-id` values such as `-1` still raise `ValueError("deleted user id is malformed: -1")`.
- Existing regular-user parsing, anonymous-user parsing, guest-user parsing, Wikidot system-user parsing, and shared user-parser caller wrappers remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real sites, raw rollout path, real user name, private page source, private message data, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 301. Mitigation: Issue 301 covers present non-integer malformed IDs such as `latest`; this slice covers Unicode digit normalization that still passes the old numeric branch.
- Risk: This could be confused with Issue 730. Mitigation: Issue 730 covers explicit negative generated IDs; this slice covers non-ASCII digit glyphs that Python treats as decimal digits.
- Risk: Tightening deleted-user parsing could break compatibility for unknown deleted users. Mitigation: missing `data-id` still maps to ID `0`; only explicit non-ASCII digit values are rejected.
- Risk: Changing the shared user parser could affect many modules. Mitigation: the change is limited to the deleted-user accepted ID character class, and broad shared-caller plus full-unit tests passed.
- Risk: Diagnostics could expose private user context. Mitigation: the parser-level diagnostic includes only the malformed scalar already inside the parser input and omits raw generated HTML, site names, page source, private message bodies, credentials, cookies, local paths, and rollout context.

## Dependencies

- BeautifulSoup continues to expose deleted-user `data-id` values as attributes.
- Normal Wikidot deleted-user metadata continues to identify explicit deleted-user IDs through ASCII decimal `data-id` values.
- `DeletedUser(id=0)` remains the existing representation for unknown deleted-user IDs when generated markup omits `data-id`.
- Module parsers continue to catch shared parser `ValueError` and add their own site, page, thread, post, message, revision, application, member, or vote context where applicable.

## Open Questions

None for this local slice. Future shared user parser changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Deleted-user markup supplies identity through a generated `data-id` scalar. Unicode digit normalization can silently turn malformed generated metadata into a valid-looking deleted-user ID. Requiring ASCII digits keeps generated identity parsing strict and consistent with adjacent generated scalar-shape fixes while preserving valid deleted-user markup, the existing unknown-ID fallback, and caller-specific parser context.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: fullwidth digit `data-id` payloads were accepted and normalized to deleted-user ID `123`.
- Existing local drafts covered non-integer deleted-user `data-id` values, explicit negative deleted-user `data-id` values, direct `DeletedUser` ID invariants, regular-user `onclick` Unicode digit normalization, and adjacent generated scalar ASCII-shape fixes; they did not validate Unicode digit normalization in shared deleted-user `data-id` values.
- This slice does not change request payloads, live Wikidot behavior, regular-user parsing, anonymous-user parsing, guest-user parsing, Wikidot system-user parsing, caller-specific wrappers, direct `DeletedUser` constructor invariants, missing deleted-user ID compatibility, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated HTML from real sites, real user names, private page source, private message data, and private site data out of upstream discussion.
