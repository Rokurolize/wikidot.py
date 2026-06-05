# PR Draft: Report Malformed Odate Time Classes

## Summary

`wikidot.util.parser.odate.odate_parse(...)` is the shared parser for Wikidot `span.odate` markup across recent changes, member lists, private messages, forum threads, forum posts, page history, ListPages rows, and forum post revisions. Recent local slices added caller-level context for malformed `span.odate` values in those generated module parsers, but the shared parser itself still leaked raw Python integer conversion text for a present malformed class such as `time_latest`.

This local slice keeps valid timestamp parsing and the existing missing-time-class `ValueError` unchanged. It only catches the direct shared-parser conversion failure and raises `ValueError("odate unix time is malformed: time_latest")`, so direct parser callers and tests can distinguish a present malformed time class from absent timestamp metadata.

## Outcome

Malformed shared `odate_parse(...)` `time_...` classes now fail with stable parser-level text instead of raw `int(...)` conversion output.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who parse generated Wikidot timestamp metadata in browser-free audit, archival, moderation, import, source collection, forum, page, member, or messaging workflows.

## Related Issue

Builds on timestamp parser-boundary drafts [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), [287-pr-private-message-detail-timestamp-value-context.md](287-pr-private-message-detail-timestamp-value-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [296-pr-forum-post-list-timestamp-context.md](296-pr-forum-post-list-timestamp-context.md), [298-pr-forum-post-list-edit-timestamp-context.md](298-pr-forum-post-list-edit-timestamp-context.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), and [305-pr-listpages-timestamp-context.md](305-pr-listpages-timestamp-context.md). Those drafts intentionally kept the shared parser unchanged while adding module-local context. This slice complements them by making direct `odate_parse(...)` failures stable without replacing caller-specific wrappers.

No upstream issue was filed from this local workspace.

## Changes

- Wrap the shared `time_...` integer conversion in `odate_parse(...)`.
- Raise `ValueError("odate unix time is malformed: <class>")` when a present `time_...` class cannot be parsed as an integer.
- Preserve valid timestamp parsing for epoch, recent, old, and multiple-class inputs.
- Preserve `ValueError("odate element does not contain a valid unix time")` for `span.odate` values without a `time_...` class.
- Preserve module-specific wrappers that catch shared parser `ValueError` and add caller context.
- Add a focused parser regression for `class="odate time_latest"`.

## Type Of Change

- Bug fix / diagnostics improvement
- Shared timestamp parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A present malformed `time_...` class must fail with a stable parser-level malformed-time `ValueError`. |
| R2 | The malformed-time error must include the observed class value and must not expose raw Python integer conversion text. |
| R3 | Missing `time_...` metadata must keep the existing missing-valid-time `ValueError` behavior. |
| R4 | Valid `odate_parse(...)` timestamp parsing must remain unchanged. |
| R5 | Module caller wrappers for recent changes, members, messages, forum, page history, and ListPages timestamps must remain compatible. |
| R6 | Broad unit, lint, format, type, and whitespace gates must remain green before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `odate_parse(...)` raises `ValueError` for `<span class="odate time_latest">Dec 17 2023</span>`. | `TestOdateParse.test_parse_odate_with_malformed_time_class_raises` expects `ValueError`. | Returning a timestamp, leaking raw conversion text, or hiding the observed `time_latest` value rejects this local completion claim. | `src/wikidot/util/parser/odate.py` | `tests/unit/parsers/test_odate_parser.py` |
| R2 | The exception message is stable and specific to the malformed class value. | The focused regression matches `odate unix time is malformed: time_latest`. | Reporting only `invalid literal for int()` rejects this local completion claim because it depends on Python internals. | Shared timestamp parser diagnostics | `tests/unit/parsers/test_odate_parser.py` |
| R3 | `span.odate` without a `time_...` class remains a missing-valid-time parser failure. | Existing parser regression `test_parse_odate_without_time_class_raises` still expects `valid unix time`. | Treating absent timestamp metadata as a malformed class would break caller semantics. | Shared timestamp parser diagnostics | `tests/unit/parsers/test_odate_parser.py` |
| R4 | Valid timestamp classes still parse through existing public parser behavior. | `tests/unit/parsers/test_odate_parser.py` passed 7 tests, including epoch, recent, old, and multiple-class cases. | Regressing timestamp conversion or `datetime.fromtimestamp(...)` behavior rejects this local completion claim. | Shared timestamp parser | `tests/unit/parsers/test_odate_parser.py` |
| R5 | Adjacent shared timestamp caller wrappers stay green. | Shared timestamp caller suite passed 495 tests across site, site-member, private-message, forum-post, forum-thread, forum-post-revision, and page tests. | Regressing module-specific timestamp context, parser wrappers, page metadata parsing, forum metadata parsing, message parsing, member parsing, ListPages parsing, or page history parsing rejects this local completion claim. | Shared timestamp parser callers | `tests/unit/test_site.py`; `tests/unit/test_site_member.py`; `tests/unit/test_private_message.py`; `tests/unit/test_forum_post.py`; `tests/unit/test_forum_thread.py`; `tests/unit/test_forum_post_revision.py`; `tests/unit/test_page.py` |
| R6 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `bcae743 fix(odate): report malformed time classes`.

- RED: `uv run --extra test pytest tests/unit/parsers/test_odate_parser.py::TestOdateParse::test_parse_odate_with_malformed_time_class_raises -q` failed before the fix because the parser raised raw `ValueError("invalid literal for int() with base 10: 'latest'")` for `time_latest`.
- GREEN: `uv run --extra test pytest tests/unit/parsers/test_odate_parser.py::TestOdateParse::test_parse_odate_with_malformed_time_class_raises -q` passed 1 test.
- `uv run --extra test pytest tests/unit/parsers/test_odate_parser.py -q` passed 7 tests.
- `uv run --extra test pytest tests/unit/parsers/test_odate_parser.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_private_message.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py -q` passed 495 tests.
- `uv run --extra test pytest tests/unit -q` passed 880 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- `odate_parse(...)` raises `ValueError("odate unix time is malformed: time_latest")` for a present malformed `time_latest` class.
- The parser does not expose raw Python integer conversion text for present malformed `time_...` classes.
- Missing `time_...` metadata still raises `ValueError("odate element does not contain a valid unix time")`.
- Valid timestamp classes still parse to the same `datetime.fromtimestamp(...)` values.
- Existing module-specific wrappers can still catch shared-parser `ValueError` and add their own site, page, thread, post, message, member, revision, or field context.
- No live Wikidot action, upstream Issue, upstream PR, push, raw generated timestamp markup from real sites, private access material, local rollout paths, or private account details are required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Changing a shared parser could affect many modules. Mitigation: the change is limited to the direct conversion failure branch, and broad timestamp caller tests passed.
- Risk: Caller wrappers could rely on the chained raw conversion text. Mitigation: wrappers already add their own field and value context, and exception chaining is preserved with `from exc`.
- Risk: Missing timestamp metadata could be confused with malformed timestamp values. Mitigation: the existing no-time-class branch remains unchanged and covered.

## Dependencies

- BeautifulSoup continues to expose `class` values from generated `span.odate` markup.
- Valid Wikidot timestamp metadata continues to use numeric `time_...` classes.
- Module parsers continue to treat shared timestamp parser failures as `ValueError` at their boundaries.

## Open Questions

None for this local slice. Missing `class` attributes on arbitrary direct parser inputs remain a separate shared-parser boundary if concrete evidence selects it.

## Upstream-Safe Motivation

The shared timestamp parser is small but central: many generated-module parsers rely on it after locating structural `span.odate` metadata. When a `time_...` class is present but malformed, direct parser users should see stable library-level text that names the malformed class, not raw Python conversion wording. Module wrappers still own site and row context; this slice only makes the shared parser's own direct failure clearer.

## Local Evidence, Not For Upstream Paste

- Recent local timestamp drafts repeatedly converted module-level `time_latest` failures from raw shared-parser `ValueError` into contextual module failures while intentionally leaving `odate_parse(...)` unchanged.
- The immediate RED failure showed direct `odate_parse(...)` still exposed raw integer conversion text for `time_latest`.
- The full unit suite and broad shared timestamp caller slice stayed green after preserving valid timestamp behavior and caller wrappers.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, private access material, generated timestamp markup from real sites, real user names, and private site history out of upstream discussion.

## Additional Notes

This is a shared parser diagnostics fix. It does not change request behavior, module parser scoping, caller-specific exception wrapping, valid timestamp parsing, cache behavior, live Wikidot behavior, or any upstream filing state.
