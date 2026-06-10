# PR Draft: Validate Odate Time Class ASCII Payload

## Summary

`wikidot.util.parser.odate.odate_parse(...)` reads generated Wikidot timestamp metadata from `span.odate` class tokens such as `time_1702814400`. Issue 317 made malformed payloads such as `time_latest` diagnostic, and Issue 733 made repeated or suffix `time_` class shapes fail instead of being normalized. One accepted-value gap remained: the exact `time_...` payload check used `str.isdecimal()`, and Python treats Unicode decimal digit glyphs such as `\uff11` as decimal. A generated class such as `time_\uff11\uff17\uff10\uff12\uff18\uff11\uff14\uff14\uff10\uff10` was therefore accepted and converted to Unix timestamp `1702814400`.

This change requires the payload after `time_` to be ASCII decimal text before integer conversion. Valid generated ASCII timestamp classes keep the same behavior. Unicode digit-like payloads now raise the existing parser-level malformed-time error instead of being silently normalized into timestamps.

## Outcome

The shared odate parser no longer fabricates timestamps from generated `time_...` class payloads that contain non-ASCII decimal glyphs.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who parse generated Wikidot timestamp metadata in browser-free audit, archival, moderation, import, source collection, forum, page, member, ListPages, or messaging workflows.

## Current Evidence

Local rollout-backed drafts repeatedly identify `odate_parse(...)` as shared infrastructure underneath recent changes, member lists, private messages, forum threads, forum posts, page history, ListPages rows, and forum post revisions.

This slice is not a duplicate of [317-pr-odate-time-class-context.md](317-pr-odate-time-class-context.md). Issue 317 covers malformed payload diagnostics for values such as `time_latest` that Python cannot convert to integers.

This slice is not a duplicate of [733-pr-validate-odate-time-class-shape.md](733-pr-validate-odate-time-class-shape.md). Issue 733 covers repeated or trailing `time_` markers such as `time_time_1702814400` and `time_1702814400_time_`. This slice covers exact `time_...` class tokens whose payload contains Unicode decimal digit glyphs that `isdecimal()` and `int(...)` accept.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [317-pr-odate-time-class-context.md](317-pr-odate-time-class-context.md) and [733-pr-validate-odate-time-class-shape.md](733-pr-validate-odate-time-class-shape.md), plus the timestamp caller-context drafts for recent changes, members, private messages, forum, page-history, ListPages, and forum post revisions.

## Changes

- Require the payload after the exact `time_` prefix to be ASCII and decimal before calling `int(...)`.
- Preserve valid generated ASCII timestamp class parsing.
- Preserve existing malformed payload diagnostics such as `time_latest`.
- Preserve existing repeated/suffix shape diagnostics from Issue 733.
- Add a regression test that a fullwidth timestamp payload raises instead of returning a `datetime`.

## Type Of Change

- Bug fix
- Shared timestamp parser hardening
- Generated scalar hardening
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `odate_parse(...)` must reject exact `time_...` classes whose payload contains non-ASCII decimal glyphs. |
| R2 | The malformed-time diagnostic must preserve the observed class token. |
| R3 | Valid ASCII `time_<digits>` classes must continue to parse to the same `datetime.fromtimestamp(...)` values. |
| R4 | Existing malformed payload diagnostics, including `time_latest`, must remain unchanged. |
| R5 | Existing repeated/suffix `time_` class-shape diagnostics from Issue 733 must remain unchanged. |
| R6 | Module caller wrappers for recent changes, members, messages, forum, page history, and ListPages timestamps must remain compatible. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | RED/GREEN, full odate parser tests, timestamp caller tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `time_\uff11\uff17\uff10\uff12\uff18\uff11\uff14\uff14\uff10\uff10` fails as malformed. | `test_parse_odate_with_non_ascii_decimal_time_payload_raises` failed RED with `DID NOT RAISE`, then passed after adding the ASCII payload guard. | Returning `datetime.fromtimestamp(1702814400)` rejects this local completion claim. | Shared timestamp parser | `src/wikidot/util/parser/odate.py`, `tests/unit/parsers/test_odate_parser.py` |
| R2 | The exception reports `odate unix time is malformed: time_\uff11\uff17\uff10\uff12\uff18\uff11\uff14\uff14\uff10\uff10`. | The regression asserts the malformed-time error includes the full observed class token. | Omitting the class token, reporting raw Python conversion text, or silently treating it as missing metadata rejects this local completion claim. | Parser diagnostics | parser tests |
| R3 | Valid ASCII timestamp classes remain stable. | Focused GREEN included valid timestamp, epoch, and multiple-class cases; the full odate parser file passed 10 tests. | Regressing valid timestamp conversion rejects this local completion claim. | Shared timestamp parser | parser tests |
| R4 | Existing malformed payload diagnostics remain stable. | Focused GREEN included `time_latest`. | Changing `time_latest` diagnostics rejects this local completion claim. | Parser diagnostics | parser tests |
| R5 | Repeated/suffix class-shape diagnostics remain stable. | Focused GREEN included `time_time_1702814400` and `time_1702814400_time_`. | Re-accepting repeated/suffix `time_` markers rejects this local completion claim. | Shared timestamp parser | parser tests |
| R6 | Module timestamp wrappers remain compatible. | Timestamp caller coverage passed 1801 tests across site, site-member, private-message, forum-post, forum-thread, forum-post-revision, page, and direct parser suites. | Regressing caller-specific timestamp context, row parsing, page history parsing, message parsing, member parsing, forum parsing, or ListPages parsing rejects this local completion claim. | Timestamp caller workflows | affected unit suites |
| R7 | No live site state or private material is needed. | The regression uses unit-level synthetic HTML only. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | RED/GREEN, parser tests, timestamp caller tests, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `2df1690 fix(odate): validate time class ascii payload`.

- RED: `uv run pytest tests/unit/parsers/test_odate_parser.py::TestOdateParse::test_parse_odate_with_non_ascii_decimal_time_payload_raises -q --tb=short` failed before the fix with `DID NOT RAISE` because the fullwidth timestamp payload was accepted.
- GREEN focused: `uv run pytest tests/unit/parsers/test_odate_parser.py::TestOdateParse::test_parse_odate_with_non_ascii_decimal_time_payload_raises tests/unit/parsers/test_odate_parser.py::TestOdateParse::test_parse_odate_with_ambiguous_time_class_shape_raises tests/unit/parsers/test_odate_parser.py::TestOdateParse::test_parse_odate_with_malformed_time_class_raises tests/unit/parsers/test_odate_parser.py::TestOdateParse::test_parse_valid_odate tests/unit/parsers/test_odate_parser.py::TestOdateParse::test_parse_odate_epoch tests/unit/parsers/test_odate_parser.py::TestOdateParse::test_parse_odate_with_multiple_classes -q --tb=short` passed 7 tests.
- `uv run pytest tests/unit/parsers/test_odate_parser.py -q --tb=short` passed 10 tests.
- `uv run pytest tests/unit/parsers/test_odate_parser.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_private_message.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py -q --tb=short` passed 1801 tests.
- `uv run pytest tests/unit -q --tb=short` passed 3775 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no change-propagation, cognitive-load, duplication, accidental-complexity, dependency, domain-model, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker. Code pre-commit evidence reported `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.139.0"`, local clawpatch commit `d89ca91`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `odate_parse(...)` raises `ValueError("odate unix time is malformed: time_...")` for an exact `time_...` class whose timestamp payload uses fullwidth decimal glyphs.
- The parser does not return `datetime.fromtimestamp(1702814400)` for the fullwidth payload `\uff11\uff17\uff10\uff12\uff18\uff11\uff14\uff14\uff10\uff10`.
- Valid ASCII `time_1702814400`, epoch `time_0`, recent, old, and multiple ordinary class inputs still parse to the same `datetime.fromtimestamp(...)` values.
- Existing `time_latest` malformed payload diagnostics remain stable.
- Existing repeated/suffix `time_` malformed class-shape diagnostics remain stable.
- Existing module wrappers can still catch shared-parser `ValueError` and add their own site, page, thread, post, message, member, revision, or field context.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Tightening a shared parser could affect many module parsers. Mitigation: the accepted generated token shape is ASCII `time_<digits>`, and timestamp caller coverage passed 1801 tests.
- Risk: This could be confused with Issue 317. Mitigation: Issue 317 covers malformed payloads that conversion rejects; this slice covers Unicode decimal payloads conversion accepts.
- Risk: This could be confused with Issue 733. Mitigation: Issue 733 covers repeated/suffix `time_` marker shapes; this slice covers exact-prefix payload scalar shape.
- Risk: Missing timestamp metadata could be confused with malformed timestamp metadata. Mitigation: the no-time-token branch remains unchanged and covered.

## Dependencies

- BeautifulSoup continues to expose `class` values from generated `span.odate` markup.
- Valid Wikidot timestamp metadata continues to use ASCII numeric `time_...` classes.
- Module parsers continue to treat shared timestamp parser failures as `ValueError` at their boundaries.

## Open Questions

None for this local slice. Missing `class` attributes on arbitrary direct parser inputs remain a separate shared-parser boundary if concrete evidence selects it.

## Upstream-Safe Motivation

The shared timestamp parser is small but central. Since many generated-module parsers rely on it after locating structural `span.odate` metadata, it should parse only the generated ASCII timestamp payload shape Wikidot emits and reject non-ASCII digit payloads instead of normalizing them into plausible timestamps.

## Local Evidence, Not For Upstream Paste

- The direct parser probe and RED test demonstrated prior behavior: fullwidth decimal timestamp payload text was accepted and returned a `datetime`.
- Existing local drafts covered shared odate malformed payload diagnostics and repeated/suffix time-class shape validation; they did not validate Unicode decimal digit normalization inside exact `time_...` payloads.
- This slice only validates the shared odate time-class payload shape. It does not change request behavior, module parser scoping, caller-specific exception wrapping, valid timestamp parsing, cache behavior, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, private access material, generated timestamp markup from real sites, real user names, and private site history out of upstream discussion.

## Additional Notes

This is a shared generated timestamp scalar parser fix. It preserves valid ASCII timestamp parsing and established malformed-shape diagnostics while preventing Python's Unicode decimal support from manufacturing ordinary timestamps out of malformed generated class metadata.
