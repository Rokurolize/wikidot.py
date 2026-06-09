# PR Draft: Validate Deleted User Data-ID Range

## Summary

`user_parse(...)` is the shared `printuser` parser used by site membership, site applications, private messages, page votes, forum metadata, profile-adjacent fixtures, and downstream browser-free ledgers. Issue 301 made present non-integer deleted-user `data-id` values fail with parser context, and Issue 647 made direct `User` and `DeletedUser` records reject negative IDs. One generated-parser boundary still leaked through: a deleted-user element with parseable but impossible `data-id="-1"` reached `DeletedUser.__post_init__`, which raised the direct object invariant `id must be non-negative or None` instead of a parser-context diagnostic naming the generated field and observed value.

This change validates the deleted-user `data-id` range inside `user_parse(...)` immediately after integer conversion and before constructing `DeletedUser`. Missing `data-id` still uses the existing compatibility fallback ID `0`, valid non-negative generated IDs still parse, and direct `DeletedUser(id=-1)` constructor validation remains unchanged.

## Outcome

Generated deleted-user markup can no longer return or indirectly construct impossible negative user identity state. Callers now get `ValueError("deleted user id is malformed: -1")` from the shared parser boundary for malformed generated deleted-user markup, while successful regular-user, deleted-user, anonymous-user, guest-user, and Wikidot-system-user parsing remains unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free user parsing across member lists, applications, private messages, page votes, forum threads/posts/revisions, profile fixtures, deleted-user ledgers, or local adapters where generated `printuser` identity fields must be valid before object construction.

## Current Evidence

Local rollout-backed work repeatedly identified shared user parsing and user identity carriers as practical cross-module surfaces. Existing local drafts cover regular-user `onclick` ID context, malformed deleted-user `data-id` conversion, direct user-record ID types and non-negative ranges, QuickModule user IDs, member-lookup user filters, retained/cached user ownership, and many caller-specific user fields.

This slice is not a duplicate of [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md), which covers present non-integer deleted-user `data-id` values and deliberately preserves missing `data-id` as ID `0`. It is also not a duplicate of [316-pr-regular-user-onclick-id-context.md](316-pr-regular-user-onclick-id-context.md), which covers regular-user `onclick` parsing, or [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), which covers direct `User` and `DeletedUser` constructor invariants. This slice validates a generated deleted-user parser field that was parseable as an integer but invalid as Wikidot user identity.

No upstream issue was filed from this local workspace.

## Changes

- Reject deleted-user `data-id` values below zero inside `user_parse(...)`.
- Preserve `ValueError("deleted user id is malformed: ...")` as the parser-boundary diagnostic family for malformed generated deleted-user IDs.
- Preserve missing deleted-user `data-id` compatibility as ID `0`.
- Preserve valid positive generated deleted-user IDs.
- Preserve direct `DeletedUser` constructor validation and messages.
- Preserve regular-user, anonymous-user, guest-user, Wikidot-system-user, and adjacent user-consuming workflows.

## Type Of Change

- Parser hardening
- Shared user identity validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A deleted-user `printuser` element with generated `data-id="-1"` must fail inside `user_parse(...)` before constructing `DeletedUser`. |
| R2 | The negative generated deleted-user ID diagnostic must include the observed raw value and use the parser-context message `deleted user id is malformed: -1`. |
| R3 | Missing deleted-user `data-id` must still parse as compatibility ID `0`. |
| R4 | Valid generated deleted-user IDs must still parse to `DeletedUser` with the same ID. |
| R5 | Non-integer deleted-user `data-id` values must keep the existing parser-context diagnostic. |
| R6 | Direct `DeletedUser(id=-1)` constructor validation must remain responsible for direct local object state. |
| R7 | Adjacent user parser callers and repository quality gates must remain green. |
| R8 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw private `printuser` markup, upstream Issues, upstream PRs, or pushes. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `data-id="-1"` fails before a `DeletedUser` is constructed. | `test_parse_deleted_user_with_negative_data_id_raises` failed RED because the value reached `DeletedUser.__post_init__`, then passed GREEN after the parser-side non-negative guard was added. | Returning `DeletedUser(id=-1)`, deferring to the constructor, or silently converting the value to `0` rejects this local completion claim. | Shared user parser | `src/wikidot/util/parser/user.py`, `tests/unit/parsers/test_user_parser.py` |
| R2 | The exception message names the generated deleted-user field and raw value. | The regression matches `deleted user id is malformed: -1`. | Raising only `id must be non-negative or None`, omitting the raw value, or using an unrelated parser message rejects this local completion claim. | Parser diagnostics | `tests/unit/parsers/test_user_parser.py` |
| R3 | Missing `data-id` remains compatibility ID `0`. | Focused GREEN included `test_parse_deleted_user_without_data_id`. | Rejecting missing `data-id` or changing the fallback value rejects this local completion claim. | Deleted-user compatibility | `tests/unit/parsers/test_user_parser.py` |
| R4 | Valid generated IDs still parse. | Focused GREEN included `test_parse_deleted_user_with_id`; full user parser coverage passed. | Rejecting positive IDs or changing successful deleted-user records rejects this local completion claim. | Successful deleted-user parsing | `tests/unit/parsers/test_user_parser.py` |
| R5 | Present non-integer `data-id` behavior remains stable. | Focused GREEN included `test_parse_deleted_user_with_malformed_data_id_raises`. | Reclassifying non-integer values through constructor errors or dropping the raw observed value rejects this local completion claim. | Existing Issue 301 behavior | `tests/unit/parsers/test_user_parser.py` |
| R6 | Direct constructor validation remains unchanged. | This slice does not edit `src/wikidot/module/user.py`; Issue 647 remains the direct record invariant owner. | Changing direct `DeletedUser(id=-1)` semantics in this slice rejects this local completion claim. | Direct user records | `src/wikidot/module/user.py` |
| R7 | Adjacent behavior stays green. | User parser, adjacent user-consuming tests, full unit, ruff, ruff format, mypy, pyright, and `git diff --check` passed. | Any test, lint, format, type, or whitespace failure rejects this local completion claim. | Repository quality gates | `tests/unit`, `src`, `tests` |
| R8 | No private or live-site material is needed. | The regression uses synthetic deleted-user HTML and a mock client only. | Using credentials, cookies, auth JSON, raw private markup, live Wikidot actions, upstream Issues, upstream PRs, or pushes rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `9a3d448 fix(user): validate deleted user data id range`.

- RED: `uv run pytest tests/unit/parsers/test_user_parser.py::TestUserParserDeletedUser::test_parse_deleted_user_with_negative_data_id_raises -q` failed before the fix because `data-id="-1"` reached `DeletedUser.__post_init__` and raised `id must be non-negative or None`.
- GREEN focused: `uv run pytest tests/unit/parsers/test_user_parser.py::TestUserParserDeletedUser::test_parse_deleted_user_with_id tests/unit/parsers/test_user_parser.py::TestUserParserDeletedUser::test_parse_deleted_user_without_data_id tests/unit/parsers/test_user_parser.py::TestUserParserDeletedUser::test_parse_deleted_user_with_malformed_data_id_raises tests/unit/parsers/test_user_parser.py::TestUserParserDeletedUser::test_parse_deleted_user_with_negative_data_id_raises -q` passed 4 tests.
- `uv run pytest tests/unit/parsers/test_user_parser.py -q` passed 19 tests.
- `uv run pytest tests/unit/parsers/test_user_parser.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_private_message.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py tests/unit/test_site_application.py tests/unit/test_page_votes.py -q` passed 1896 tests.
- `uv run pytest tests/unit -q` passed 3603 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `user_parse(...)` raises `ValueError("deleted user id is malformed: -1")` for a deleted-user `printuser` element with `data-id="-1"`.
- Missing deleted-user `data-id` still returns `DeletedUser(id=0)`.
- Valid generated deleted-user IDs still return `DeletedUser` with the parsed ID.
- Existing non-integer deleted-user `data-id` diagnostics remain contextual and include the raw value.
- Direct `DeletedUser` constructor validation remains unchanged.
- Regular-user, anonymous-user, guest-user, Wikidot-system-user, and adjacent user-consuming workflows remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Tightening deleted-user parsing could break compatibility for unknown deleted users. Mitigation: missing `data-id` still maps to ID `0`; only explicit negative generated IDs are rejected.
- Risk: The parser guard could be confused with direct `DeletedUser` constructor validation. Mitigation: this slice only validates generated parser input before object construction; direct record invariants stay in `src/wikidot/module/user.py`.
- Risk: Error-message drift could make generated-field triage harder. Mitigation: negative generated IDs reuse the existing deleted-user parser diagnostic family introduced for malformed `data-id` values.

## Dependencies

- Existing `user_parse(...)` branch selection for deleted users remains unchanged.
- Existing `DeletedUser` constructor validation remains responsible for direct local object state.
- Existing mock-client parser tests remain sufficient; no live Wikidot action or new dependency is required.

## Open Questions

None for this local slice. Future work should continue with fresh duplicate-checked parser boundaries, response-shape validation, direct input validation, result ergonomics, or measured complexity candidates outside deleted-user generated `data-id` range handling.

## Upstream-Safe Motivation

Shared `printuser` parsing feeds many browser-free workflows. If generated deleted-user markup contains an explicit negative identity value, wikidot.py should reject that generated field with parser context instead of leaking a generic direct-record invariant to callers. The change keeps the long-standing unknown-deleted-user fallback while making malformed generated identity data visible at the boundary that observed it.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established shared user parsing and user identity records as practical cross-module surfaces across site membership, applications, private messages, page votes, and forum metadata.
- Existing local drafts covered non-integer deleted-user `data-id` values and direct negative `DeletedUser` IDs; they did not cover parseable but impossible generated deleted-user IDs such as `data-id="-1"`.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw generated markup from real sites, private message/forum content, and live account details out of upstream discussion.
