# PR Draft: Validate Odate Time Class Shape

## Summary

`wikidot.util.parser.odate.odate_parse(...)` reads generated Wikidot timestamp metadata from `span.odate` class tokens such as `time_1702814400`. Issue 317 stabilized the direct parser diagnostic for a present malformed class such as `time_latest`, but one shape bug remained: the parser used `odate_class.replace("time_", "")` before integer conversion. That removes every `time_` substring, so a malformed token such as `time_time_1702814400` was accepted as Unix timestamp `1702814400`.

This change accepts only exact `time_<digits>` class tokens. Tokens that contain `time_` but have an embedded prefix, repeated prefix, suffix marker, or non-digit payload now raise the existing parser-level malformed-time error: `ValueError("odate unix time is malformed: <class>")`. Valid timestamps, epoch timestamps, old timestamps, recent timestamps, multiple ordinary classes, missing-time-class behavior, and module-specific timestamp wrappers remain unchanged.

## Outcome

The shared odate parser no longer fabricates timestamps from malformed generated class tokens merely because removing all `time_` substrings leaves digits.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who parse generated Wikidot timestamp metadata in browser-free audit, archival, moderation, import, source collection, forum, page, member, or messaging workflows.

## Current Evidence

Local rollout-backed drafts repeatedly identify `odate_parse(...)` as shared infrastructure underneath recent changes, member lists, private messages, forum threads, forum posts, page history, ListPages rows, and forum post revisions. [317-pr-odate-time-class-context.md](317-pr-odate-time-class-context.md) made present malformed `time_...` conversion failures stable instead of exposing raw Python `int(...)` text. It did not change the token-shape parser logic that accepted repeated `time_` prefixes after global string replacement.

That prior slice is not a duplicate. Issue 317 covered malformed payload diagnostics for values like `time_latest`; this slice covers malformed class shapes such as `time_time_1702814400` that were accepted as valid timestamps.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [317-pr-odate-time-class-context.md](317-pr-odate-time-class-context.md) and the timestamp caller-context drafts it references, including recent-change, member, private-message, forum, page-history, and ListPages timestamp diagnostics.

## Changes

- Replace global `time_` substring removal with an exact `time_` prefix check.
- Require the class payload after `time_` to be decimal digits before calling `int(...)`.
- Raise `ValueError("odate unix time is malformed: <class>")` for malformed class tokens that contain `time_` but do not match `time_<digits>`.
- Preserve the existing missing-valid-time error for `span.odate` values without any `time_` token.
- Preserve valid timestamp parsing for epoch, old, recent, and multiple-class inputs.
- Add parser coverage for repeated-prefix and suffix-marker malformed time class shapes.

## Type Of Change

- Bug fix
- Shared timestamp parser hardening
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `odate_parse(...)` must reject `time_time_1702814400` with `ValueError("odate unix time is malformed: time_time_1702814400")`. |
| R2 | `odate_parse(...)` must reject malformed class tokens that contain repeated or trailing `time_` markers instead of normalizing them into digits. |
| R3 | Valid exact `time_<digits>` classes must continue to parse to the same `datetime.fromtimestamp(...)` values. |
| R4 | Existing malformed payload diagnostics, including `time_latest`, must remain unchanged. |
| R5 | Missing `time_...` metadata must keep the existing `ValueError("odate element does not contain a valid unix time")` behavior. |
| R6 | Module caller wrappers for recent changes, members, messages, forum, page history, and ListPages timestamps must remain compatible. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, full odate parser tests, timestamp caller tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `time_time_1702814400` fails as malformed. | Focused RED failed with `DID NOT RAISE`; focused GREEN passed after exact token validation. | Returning `datetime.fromtimestamp(1702814400)` rejects this local completion claim. | Shared timestamp parser | `src/wikidot/util/parser/odate.py`, `tests/unit/parsers/test_odate_parser.py` |
| R2 | Repeated/trailing `time_` markers are not normalized. | The parser-shape regression covers `time_time_1702814400` and `time_1702814400_time_`. | Any implementation that strips all `time_` substrings before parsing rejects this local completion claim. | Shared timestamp parser | parser tests |
| R3 | Valid timestamp classes remain stable. | `tests/unit/parsers/test_odate_parser.py` passed epoch, multiple-class, recent, old, and ordinary valid timestamp tests. | Regressing valid timestamp conversion rejects this local completion claim. | Shared timestamp parser | parser tests |
| R4 | Existing malformed payload diagnostics remain stable. | `test_parse_odate_with_malformed_time_class_raises` still matches `odate unix time is malformed: time_latest`. | Reintroducing raw Python conversion text or changing the message rejects this local completion claim. | Parser diagnostics | parser tests |
| R5 | Missing timestamp metadata remains a missing-valid-time failure. | `test_parse_odate_without_time_class_raises` still expects `valid unix time`. | Treating no-time-class markup as a malformed class rejects this local completion claim. | Parser diagnostics | parser tests |
| R6 | Module timestamp wrappers remain compatible. | Timestamp caller coverage passed 1753 tests across site, site-member, private-message, forum-post, forum-thread, forum-post-revision, page, and direct parser suites. | Regressing caller-specific timestamp context, row parsing, page history parsing, message parsing, member parsing, forum parsing, or ListPages parsing rejects this local completion claim. | Timestamp caller workflows | affected unit suites |
| R7 | No live site state or private material is needed. | All regressions use unit-level synthetic HTML and mocked response fixtures. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, parser tests, timestamp caller tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `558b3e8 fix(odate): validate time class shape`.

- RED: `uv run --extra test pytest tests/unit/parsers/test_odate_parser.py::TestOdateParse::test_parse_odate_with_ambiguous_time_class_shape_raises -q` failed before the fix because `time_time_1702814400` was accepted and reported `DID NOT RAISE`.
- GREEN focused: `uv run --extra test pytest tests/unit/parsers/test_odate_parser.py::TestOdateParse::test_parse_odate_with_ambiguous_time_class_shape_raises -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/parsers/test_odate_parser.py -q` passed 9 tests.
- `uv run --extra test pytest tests/unit/parsers/test_odate_parser.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_private_message.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py -q` passed 1753 tests.
- `uv run --extra test pytest tests/unit -q` passed 3698 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `odate_parse(...)` raises `ValueError("odate unix time is malformed: time_time_1702814400")` for `class="odate time_time_1702814400"`.
- `odate_parse(...)` raises `ValueError("odate unix time is malformed: time_1702814400_time_")` for `class="odate time_1702814400_time_"`.
- Valid `time_1702814400`, epoch `time_0`, recent, old, and multiple ordinary class inputs still parse to the same `datetime.fromtimestamp(...)` values.
- Existing `time_latest` malformed payload diagnostics remain stable.
- Missing `time_...` metadata still raises the existing missing-valid-time error.
- Existing module wrappers can still catch shared-parser `ValueError` and add their own site, page, thread, post, message, member, revision, or field context.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Tightening a shared parser could affect many module parsers. Mitigation: the accepted token shape is the generated Wikidot timestamp convention, and timestamp caller coverage passed 1753 tests.
- Risk: A caller might have relied on malformed repeated-prefix class tokens. Mitigation: those tokens are not valid timestamp metadata; accepting them fabricates time values from corrupted generated markup.
- Risk: This could be confused with Issue 317. Mitigation: Issue 317 covered raw conversion-text diagnostics for malformed payloads; this slice covers malformed class shapes that were silently accepted.
- Risk: Missing timestamp metadata could be confused with malformed timestamp metadata. Mitigation: the no-time-token branch remains unchanged and covered.

## Dependencies

- BeautifulSoup continues to expose `class` values from generated `span.odate` markup.
- Valid Wikidot timestamp metadata continues to use numeric `time_...` classes.
- Module parsers continue to treat shared timestamp parser failures as `ValueError` at their boundaries.

## Open Questions

None for this local slice. Missing `class` attributes on arbitrary direct parser inputs remain a separate shared-parser boundary if concrete evidence selects it.

## Upstream-Safe Motivation

The shared timestamp parser is small but central. Since many generated-module parsers rely on it after locating structural `span.odate` metadata, it should parse only the exact timestamp class shape Wikidot emits and reject malformed `time_` tokens instead of normalizing them into plausible timestamps.

## Local Evidence, Not For Upstream Paste

- Local timestamp drafts repeatedly established `odate_parse(...)` as shared infrastructure for recent changes, member lists, private messages, forum threads, forum posts, page history, ListPages rows, and forum post revisions.
- Issue 317 stabilized the direct malformed payload diagnostic, but the direct RED test here showed `time_time_1702814400` still became a valid timestamp before the exact-shape fix.
- This slice only validates the shared odate time-class shape. It does not change request behavior, module parser scoping, caller-specific exception wrapping, valid timestamp parsing, cache behavior, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, private access material, generated timestamp markup from real sites, real user names, and private site history out of upstream discussion.
