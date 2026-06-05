# PR Draft: Report Malformed User Profile ID Hrefs

## Summary

`UserCollection.from_names(...)`, exposed through `User.from_name(...)`, fetches Wikidot profile pages and parses a user ID from generated profile controls such as `account/messages#/new/<id>` or `userkarma.php/<id>`. Earlier local slices preserved rendered profile-title spacing and added requested-user/index context to missing or malformed profile parser failures. One adjacent scalar-value gap remained: when the ID control was present but its `href` contained a non-numeric ID segment such as `http://www.wikidot.com/userkarma.php/not-a-number`, the parser reported only `User ID is not found for requested user: ...` and discarded the observed href value.

This local slice keeps successful profile lookup, not-found skipping/raising, ID extraction from message and karma links, missing ID element diagnostics, missing profile-title diagnostics, avatar URL construction, collection ordering, and `User.from_name(...)` behavior unchanged. It distinguishes a missing/blank ID href from a present malformed href and raises `NoElementException` with requested user key, request index, `field=user_id`, and the observed href value when the href is present but cannot yield a numeric profile ID.

## Outcome

Malformed user profile ID hrefs now fail with value-aware profile context instead of being reported as a missing user ID.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who resolve Wikidot users by profile name for browser-free membership, attribution, moderation, indexing, or migration workflows.

## Related Issue

Builds on [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md) and [166-pr-user-profile-parse-context.md](166-pr-user-profile-parse-context.md). Those drafts established user profile lookup as a practical read path and added requested-user/index context for profile parser failures.

This slice also follows the scalar parser-boundary pattern from [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md), [237-pr-page-revision-number-parse-context.md](237-pr-page-revision-number-parse-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md), [309-pr-page-discussion-thread-id-context.md](309-pr-page-discussion-thread-id-context.md), [310-pr-site-id-context.md](310-pr-site-id-context.md), and [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a small profile parse-context helper that preserves the existing requested-user/index wording and can append field/value details.
- Keep missing ID elements and missing/blank ID hrefs on the existing missing-user-ID path.
- Convert present malformed ID hrefs into contextual `NoElementException`.
- Include requested user key, request index, `field=user_id`, and observed href value in the malformed-href error.
- Preserve valid ID extraction from `account/messages#/new/<id>` and `userkarma.php/<id>` links, including query/fragment suffixes.
- Preserve profile-title parsing, avatar URL construction, skipped/raised not-found behavior, collection ordering, `User.from_name(...)`, and `RequestUtil` behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- User profile parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A fetched profile page with a present profile ID control whose href has a non-numeric ID segment must fail at the user-profile parser boundary. |
| R2 | The malformed profile ID href error must identify the requested user key, request index, affected field, and observed href value. |
| R3 | Missing profile ID elements and missing/blank ID hrefs must remain distinct from present malformed hrefs. |
| R4 | Valid profile ID href parsing, profile-title parsing, avatar URL generation, not-found handling, ordering, and request behavior must remain compatible. |
| R5 | Focused, user-level, adjacent parser/request, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `UserCollection.from_names(...)` raises `NoElementException` for `href="http://www.wikidot.com/userkarma.php/not-a-number"`. | `TestUserCollection.test_from_names_malformed_id_href_raises` expects `NoElementException`. | Treating the malformed href as missing, leaking a raw scalar parse error, fabricating a user ID, or returning a `User` rejects this local completion claim. | `src/wikidot/module/user.py` | `tests/unit/test_user.py` |
| R2 | The error names `requested user: bad`, `index=1`, `field=user_id`, and the observed href value. | The focused regression matches all fields. | Omitting requested user, index, field, or observed href makes the failure ambiguous and rejects this local completion claim. | User profile diagnostics | `tests/unit/test_user.py` |
| R3 | Missing profile ID elements continue to raise the existing missing-element diagnostic, and missing/blank hrefs use the missing-ID branch. | Existing malformed profile tests remained green, including missing ID element and missing profile-title coverage. | Treating a missing element as a malformed scalar value would blur distinct failure modes and rejects this local completion claim. | User profile missing-field handling | `tests/unit/test_user.py` |
| R4 | Valid user profile lookup and adjacent request/user parser workflows remain green. | The full user suite passed 16 tests and the adjacent parser/user/requestutil suite passed 52 tests. | Regressing message-link IDs, karma-link IDs, query-suffix IDs, title spacing, skipped/raised not-found users, avatar URLs, `User.from_name(...)`, or request helper behavior rejects this local completion claim. | User lookup workflow | `tests/unit/test_user.py`; `tests/unit/parsers/test_user_parser.py`; `tests/unit/test_requestutil.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `2edfb8c fix(user): report malformed profile id hrefs`.

- RED: `uv run --extra test pytest tests/unit/test_user.py::TestUserCollection::test_from_names_malformed_id_href_raises -q` failed before the fix with `NoElementException: User ID is not found for requested user: bad (index=1)`.
- GREEN: `uv run --extra test pytest tests/unit/test_user.py::TestUserCollection::test_from_names_malformed_id_href_raises -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_user.py -q` passed 16 tests.
- `uv run --extra test pytest tests/unit/parsers/test_user_parser.py tests/unit/test_user.py tests/unit/test_requestutil.py -q` passed 52 tests.
- `uv run --extra test pytest tests/unit -q` passed 869 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- A fetched user profile whose present ID href contains a non-numeric ID segment raises `NoElementException`.
- The malformed profile ID href message includes requested user key, request index, `field=user_id`, and observed href value.
- Missing ID elements and missing/blank ID hrefs keep missing-field semantics.
- Valid profile ID extraction from supported profile controls remains unchanged.
- Profile-title spacing, avatar URL construction, skipped/raised not-found handling, collection ordering, `User.from_name(...)`, and request helper behavior remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real profile HTML, credentials, cookies, auth JSON, local rollout paths, or private user data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Treating missing hrefs as malformed could change existing missing-field semantics. Mitigation: this slice raises the value-aware malformed error only when a non-empty href is present but cannot be parsed.
- Risk: A helper could reword existing diagnostics unexpectedly. Mitigation: the helper preserves the existing requested-user/index format, and the full user suite remained green.
- Risk: Diagnostics could expose profile content. Mitigation: the error reports only the requested user key, request index, field name, and scalar href value, not raw profile HTML, page content, credentials, or local rollout paths.

## Dependencies

- Wikidot profile pages continue to expose a generated ID-bearing control through either `account/messages#/new/<id>` or `userkarma.php/<id>`.
- `UserCollection.from_names(...)` remains the source of truth for profile-page user lookup.
- Existing profile pages without a usable ID-bearing control continue to represent missing profile metadata rather than a malformed scalar value.

## Open Questions

None for this local slice. Broader profile-page parser normalization should remain separate unless a future concrete malformed fixture requires it.

## Upstream-Safe Motivation

User lookup is a read-heavy helper for membership, attribution, and moderation workflows. If Wikidot emits a present profile ID href that no longer contains a numeric ID, wikidot.py should fail with structured requested-user diagnostics and the observed scalar value instead of collapsing the problem into a missing-ID message. That keeps logs actionable without retaining raw profile HTML, credentials, local rollout paths, or private user data.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established user profile lookup as a practical read path and added requested-user/index context to malformed profile parser failures.
- Issue 166 explicitly covered malformed profile ID links but only required requested-user/index context; this follow-up adds the missing observed href value for present malformed hrefs.
- The immediate RED failure showed `href="http://www.wikidot.com/userkarma.php/not-a-number"` still raised `User ID is not found for requested user: bad (index=1)` without field/value context.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, real profile HTML, real user names, and private user data out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It preserves valid user lookup while preventing a malformed present profile ID href from losing the scalar value that operators need for diagnosis.
