# PR Draft: Validate Odate Parser Element Input

## Summary

`wikidot.util.parser.odate.odate_parse(...)` now validates its direct parser input before reading BeautifulSoup attributes. Non-`bs4.Tag` values raise `ValueError("odate_element must be bs4.Tag")`, and classless tags reuse the existing parser-level missing timestamp error instead of leaking `KeyError("class")`.

The change is intentionally narrow: valid `span.odate time_<digits>` parsing, malformed `time_...` diagnostics, missing `time_...` behavior for ordinary odate spans, and caller-specific timestamp wrappers remain unchanged.

## Problem Statement

`odate_parse(odate_element)` is the shared parser for generated Wikidot timestamp metadata. Earlier local slices hardened malformed `time_...` class values, repeated prefix shapes, and non-ASCII timestamp payloads, but the function still assumed the caller supplied a BeautifulSoup tag with a `class` attribute. Direct calls such as `odate_parse(None)`, `odate_parse("not-tag")`, or `odate_parse(<span>...</span>)` leaked raw `TypeError` or `KeyError` before the parser could report its own contract.

That failure shape is inconsistent with the surrounding parser hardening work. A reusable shared parser should fail with stable library-level `ValueError` text when the input is not parseable as Wikidot odate metadata.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify `odate_parse(...)` as shared infrastructure underneath recent changes, member lists, private messages, forum threads, forum posts, page history, ListPages rows, and forum post revisions: [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), [287-pr-private-message-detail-timestamp-value-context.md](287-pr-private-message-detail-timestamp-value-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [296-pr-forum-post-list-timestamp-context.md](296-pr-forum-post-list-timestamp-context.md), [298-pr-forum-post-list-edit-timestamp-context.md](298-pr-forum-post-list-edit-timestamp-context.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), and [305-pr-listpages-timestamp-context.md](305-pr-listpages-timestamp-context.md).

This slice is not a duplicate of [317-pr-odate-time-class-context.md](317-pr-odate-time-class-context.md). Issue 317 covered a present malformed `time_latest` class after the class attribute was already available.

This slice is not a duplicate of [733-pr-validate-odate-time-class-shape.md](733-pr-validate-odate-time-class-shape.md). Issue 733 covered repeated or trailing `time_` markers such as `time_time_1702814400`.

This slice is not a duplicate of [769-pr-validate-odate-time-class-ascii-payload.md](769-pr-validate-odate-time-class-ascii-payload.md). Issue 769 covered exact `time_...` payloads that Python would otherwise normalize from Unicode decimal glyphs.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Direct utility calls to `odate_parse(...)`.
- Shared timestamp parsing beneath recent changes, member lists, private messages, forum thread lists and details, forum post lists and edit metadata, page revisions, ListPages fields, and forum post revisions.
- Local fixtures, generated parsers, and downstream scripts that reuse the odate parser directly before adding caller-specific context.

## Proposed Fix

- Add a runtime guard that rejects non-`bs4.Tag` values before subscript access.
- Replace direct `odate_element["class"]` access with safe class lookup.
- Preserve the existing missing-valid-time `ValueError("odate element does not contain a valid unix time")` when a tag has no usable `time_...` class.
- Add focused regressions for representative non-tag inputs and a classless tag.

## Implementation Notes

Implemented locally in commit `a787fab fix(odate): validate parser element input`.

The implementation adds one input guard and uses safe class lookup in `src/wikidot/util/parser/odate.py`:

```python
if not isinstance(odate_element, bs4.Tag):
    raise ValueError("odate_element must be bs4.Tag")

_odate_classes = odate_element.get("class", [])
```

The RED regressions called `odate_parse(...)` with `None`, `"not-tag"`, `123`, `object()`, and a BeautifulSoup `<span>` with no `class` attribute. Before the fix, those cases leaked raw `TypeError` or `KeyError`; after the fix, non-tags raise the stable type `ValueError`, and the classless tag raises the existing missing-valid-time parser error.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Direct non-`bs4.Tag` `odate_parse(...)` calls fail with stable validation before class access. | `TestOdateParse.test_parse_odate_rejects_non_tag_inputs` failed RED for 4 values with raw `TypeError`, then passed GREEN after the guard. | Reaching `odate_element["class"]`, leaking `TypeError`, coercing inputs, or returning a timestamp rejects this claim. |
| A tag without a `class` attribute fails with parser-level `ValueError` instead of raw `KeyError`. | `TestOdateParse.test_parse_odate_without_class_attribute_raises_value_error` failed RED with `KeyError("class")`, then passed GREEN with the existing missing-valid-time message. | Leaking `KeyError`, fabricating a timestamp, or treating absent timestamp metadata as a malformed `time_...` class rejects this claim. |
| Valid and previously hardened odate parsing remains unchanged. | `tests/unit/parsers/test_odate_parser.py` passed 15 tests. | Regressing valid timestamps, epoch parsing, multiple classes, `time_latest`, repeated/suffix `time_` shapes, non-ASCII payload rejection, or missing `time_...` behavior rejects this claim. |
| Shared timestamp caller workflows remain stable. | Timestamp caller suites passed 1901 tests across parser, site, site-member, private-message, forum-post, forum-thread, forum-post-revision, and page tests. | Regressing caller-specific timestamp context, row parsing, page history parsing, message parsing, member parsing, forum parsing, ListPages parsing, or odate wrappers rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3903 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `a787fab fix(odate): validate parser element input`.

- RED: `uv run pytest tests/unit/parsers/test_odate_parser.py::TestOdateParse::test_parse_odate_rejects_non_tag_inputs tests/unit/parsers/test_odate_parser.py::TestOdateParse::test_parse_odate_without_class_attribute_raises_value_error -q --tb=short` failed before the fix with 4 raw `TypeError` failures and 1 raw `KeyError("class")`.
- GREEN focused: the same command passed 5 tests.
- Parser coverage: `uv run pytest tests/unit/parsers/test_odate_parser.py -q --tb=short` passed 15 tests.
- Timestamp caller coverage: `uv run pytest tests/unit/parsers/test_odate_parser.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_private_message.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py -q --tb=short` passed 1901 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3903 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `odate_parse(None)`, `"not-tag"`, `123`, and arbitrary objects raise `ValueError("odate_element must be bs4.Tag")`.
- `odate_parse(...)` on a BeautifulSoup tag without a `class` attribute raises `ValueError("odate element does not contain a valid unix time")`.
- The rejection happens before raw subscript, integer conversion, timestamp construction, or string coercion.
- Valid generated `time_<digits>` classes still parse to the same `datetime.fromtimestamp(...)` values.
- Existing malformed `time_...` diagnostics from Issues 317, 733, and 769 remain unchanged.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: A caller may have relied on raw `TypeError` or `KeyError` from invalid direct parser inputs. Mitigation: the documented parameter is a BeautifulSoup tag and repo validation style consistently prefers stable `ValueError` for malformed public inputs.
- Risk: Treating classless tags as missing timestamp metadata could hide the absence of a class attribute. Mitigation: this preserves the existing parser distinction: no usable `time_...` metadata means no valid Unix time, while malformed present `time_...` classes still get malformed-time diagnostics.
- Risk: A broader parser shape validator could reject unusual BeautifulSoup objects. Mitigation: this slice only rejects non-tags and makes missing `class` safe; it does not alter valid parsed HTML class handling.

## Dependencies

- BeautifulSoup continues to expose generated HTML tags as `bs4.Tag` instances.
- Valid Wikidot timestamp metadata continues to use generated `time_<digits>` classes.
- Module parsers continue to own caller-specific context around shared `ValueError` failures.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, result ergonomics, cache ownership checks, cross-owner batch checks, or complexity candidates outside this now-covered odate element-input boundary.

## Rationale for Upstream Suitability

The shared odate parser is small but central. Stable validation for invalid direct inputs makes parser failures easier to route, aligns with existing wikidot.py validation style, and preserves all valid generated timestamp behavior. The patch is low risk because it adds only a guard and safe attribute lookup around a high-use utility.

## Local Evidence

- Local rollout-backed timestamp drafts repeatedly established `odate_parse(...)` as shared infrastructure for recent changes, member lists, private messages, forum threads, forum posts, page history, ListPages rows, and forum post revisions.
- Existing local drafts covered malformed timestamp payloads, class-token shape, and Unicode decimal payload normalization. They did not cover direct non-tag inputs or a missing `class` attribute before parser class iteration.
- This slice only validates direct parser element input. It does not change request behavior, module parser scoping, caller-specific exception wrapping, valid timestamp parsing, cache behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw page content, raw response bodies, private site data, and private source text out of upstream discussion.
