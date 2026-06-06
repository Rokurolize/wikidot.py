# PR Draft: Validate Page Constructor Nullable Metadata

## Summary

`Page` stores page-level creator, updater, last-commenter, and timestamp metadata from ListPages rows, create-page fallbacks, local fixtures, and rehydrated page inventories. These fields are nullable in practice: generated ListPages rows can omit `commented_by_linked` and `commented_at`, local page fixtures already use `None`, and valid create-page fallback state supplies real users and `datetime` values. The direct `Page(...)` constructor still accepted malformed non-null metadata such as booleans, strings, dictionaries, epoch integers, lists, or arbitrary objects, allowing invalid state to survive until later workflows observed confusing attribute or date assumptions.

This change validates the nullable page metadata fields during `Page.__post_init__`. `created_by`, `updated_by`, and `commented_by` now accept only `AbstractUser` instances or `None`; `created_at`, `updated_at`, and `commented_at` accept only `datetime` instances or `None`. Malformed values raise field-specific diagnostics such as `ValueError("created_by must be an AbstractUser or None")` and `ValueError("created_at must be a datetime or None")`. The `Page` dataclass annotations and docstring now match the already-observed nullable behavior.

## Outcome

Directly constructed `Page` objects fail early when optional user/timestamp metadata is malformed, while preserving `None` for unavailable page metadata and preserving valid `AbstractUser` and `datetime` values from parsers, fixtures, and create-page fallback state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free page inventories, ListPages metadata ledgers, source/revision/file/vote workflows, local fixtures, or rehydrated `Page` objects.

## Current Evidence

Local rollout-backed drafts already treat parser-side page metadata and adjacent creator/timestamp fields as operationally important. [306-pr-listpages-user-context.md](306-pr-listpages-user-context.md) documents malformed ListPages user parsing for `created_by_linked`, `updated_by_linked`, and `commented_by_linked`; [305-pr-listpages-timestamp-context.md](305-pr-listpages-timestamp-context.md) covers generated timestamp diagnostics. Adjacent direct record constructors already validate non-null creator/time fields in [458-pr-validate-forum-thread-creator-time-fields.md](458-pr-validate-forum-thread-creator-time-fields.md), [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), [464-pr-validate-forum-post-revision-creator-time-fields.md](464-pr-validate-forum-post-revision-creator-time-fields.md), and [467-pr-validate-page-revision-creator-time-fields.md](467-pr-validate-page-revision-creator-time-fields.md). [461-pr-validate-forum-post-edit-metadata-fields.md](461-pr-validate-forum-post-edit-metadata-fields.md) is the nearest nullable analogue: `edited_by` and `edited_at` preserve `None` while rejecting malformed non-null metadata.

Those prior slices are not duplicates. Issues 305 and 306 validate parser diagnostics, not direct constructor state. Issues 458, 459, 464, and 467 validate required creator/time metadata on forum and revision records where `None` is invalid. Issue 461 validates nullable forum-post edit metadata only. Issues 481 through 486 validate direct `Page` identity, count, rating, parent fullname, tags, and site fields. None validates direct `Page(created_by/created_at/updated_by/updated_at/commented_by/commented_at=...)` construction.

## Related Issue / Non-Duplicate Analysis

Builds directly on [305-pr-listpages-timestamp-context.md](305-pr-listpages-timestamp-context.md), [306-pr-listpages-user-context.md](306-pr-listpages-user-context.md), [461-pr-validate-forum-post-edit-metadata-fields.md](461-pr-validate-forum-post-edit-metadata-fields.md), [467-pr-validate-page-revision-creator-time-fields.md](467-pr-validate-page-revision-creator-time-fields.md), and the recent direct `Page` constructor hardening in [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md) through [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md).

No upstream issue was filed from this local workspace.

## Changes

- Add nullable page user metadata validation for `created_by`, `updated_by`, and `commented_by`.
- Add nullable page timestamp metadata validation for `created_at`, `updated_at`, and `commented_at`.
- Preserve `None` for unavailable page-level metadata.
- Preserve regular, deleted, anonymous, guest, and system users by validating against `AbstractUser`.
- Update `Page` dataclass annotations and docstring to match the actual nullable constructor/parser behavior.
- Add constructor tests for valid missing metadata, valid user/timestamp metadata, malformed non-null user metadata, and malformed non-null timestamp metadata.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Nullable metadata typing correction
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(created_by=...)`, `Page(updated_by=...)`, and `Page(commented_by=...)` must accept only `AbstractUser` instances or `None`. |
| R2 | `Page(created_at=...)`, `Page(updated_at=...)`, and `Page(commented_at=...)` must accept only `datetime` instances or `None`. |
| R3 | Missing page-level metadata represented by `None` must remain valid for all six fields. |
| R4 | Valid `User` metadata and valid `datetime` metadata must remain accepted and stored without coercion. |
| R5 | This slice must not change ListPages parsing, user parsing, timestamp parsing, page source/revision/file/vote acquisition, create-page fallback semantics, page site validation, tag syntax, `rating_percent`, cached state, live request behavior, or required creator/time validation on non-page records. |
| R6 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, constructor tests, adjacent page/site/page-file/page-vote/page-revision tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed non-null user metadata fails at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_user_metadata` failed RED for 15 malformed field/value combinations because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, integers, strings, dictionaries, arbitrary objects, or duck-typed user-like data rejects this local completion claim. | `Page` constructor user metadata | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Malformed non-null timestamp metadata fails at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_timestamp_metadata` failed RED for 15 malformed field/value combinations because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, epoch integers, date strings, lists, or arbitrary objects rejects this local completion claim. | `Page` constructor timestamp metadata | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | `None` remains accepted for every page-level metadata field. | `TestPageInit.test_init_accepts_missing_user_and_timestamp_metadata` passed RED and GREEN. | Rejecting missing page metadata rejects this local completion claim because valid ListPages rows and local fixtures already depend on nullable fields. | Nullable page metadata | `tests/unit/test_page_constructor.py` |
| R4 | Valid real metadata remains accepted and stored. | `TestPageInit.test_init_accepts_valid_user_and_timestamp_metadata` passed RED and GREEN with a real `User` and `datetime`. | Coercing, replacing, or rejecting valid metadata rejects this local completion claim. | Stored page metadata | `tests/unit/test_page_constructor.py` |
| R5 | Existing page workflows remain green. | Constructor tests passed 94 tests; adjacent page/site/page-file/page-vote/page-revision tests passed 818 tests; full unit tests passed 2076 tests. | Regressing parser-created pages, direct page fixtures, page collection behavior, page source/revision/file/vote workflows, site workflows, or unrelated constructor validators rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_page_revision.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `add8c11 fix(page): validate nullable metadata`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_missing_user_and_timestamp_metadata tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_user_and_timestamp_metadata tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_user_metadata tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_timestamp_metadata -q` failed 30 malformed non-null metadata cases before the fix; each malformed case reported `DID NOT RAISE`, while the 2 valid metadata cases passed.
- GREEN: the same focused command passed 32 tests after nullable metadata validation was added.
- `uv run pytest tests/unit/test_page_constructor.py -q` passed 94 tests.
- `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_page_revision.py -q` passed 818 tests.
- `uv run pytest tests/unit -q` passed 2076 tests.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed.
- `uv run ruff format --check src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 46 existing full-tree test typing errors outside this slice, including `rating_percent=None` fixture mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client/mock typing, invalid test cookie arguments, and existing site test mock typing issues. The changed source file and touched test module pass pyright together.

## Acceptance Criteria

- `Page(created_by=True)`, `Page(created_by=12345)`, `Page(created_by="test-user")`, `Page(created_by={"id": 12345})`, and `Page(created_by=object())` raise `ValueError("created_by must be an AbstractUser or None")`; the same malformed values fail for `updated_by` and `commented_by` with the field name adjusted.
- `Page(created_at=True)`, `Page(created_at=1700000000)`, `Page(created_at="2023-01-01")`, `Page(created_at=[])`, and `Page(created_at=object())` raise `ValueError("created_at must be a datetime or None")`; the same malformed values fail for `updated_at` and `commented_at` with the field name adjusted.
- `None` remains accepted for `created_by`, `created_at`, `updated_by`, `updated_at`, `commented_by`, and `commented_at`.
- Valid `User` and `datetime` values remain accepted and are stored without coercion.
- Existing parser-created pages, direct page fixtures, page collection behavior, page lookup behavior, page source/revision/file/vote workflows, and site workflows remain green.
- The new tests use unit-level code only and do not validate ListPages parsing, parser-side user/timestamp diagnostics, page site behavior, tag syntax, `rating_percent`, cached state, live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Page metadata fields are often consumed far away from construction: inventories, ledgers, filtering, display, and fallback-created page records may later assume user-like or datetime-like state. Preserving `None` for unavailable metadata while rejecting malformed non-null values keeps direct construction aligned with parser behavior and adjacent nullable metadata validation without changing live Wikidot behavior.

## Local Evidence

- Local rollout evidence used page creator/updater/commenter and timestamp metadata in ListPages-derived page inventories, source/revision workflows, and create-page fallback state.
- Existing local drafts covered parser-side user/timestamp diagnostics and adjacent direct record creator/time validation, but did not cover direct nullable page metadata fields.
- Existing unit fixtures already relied on `None` being valid for these six page-level fields, so this change validates only malformed non-null values.
- This slice does not change parser extraction, page write behavior, collection inference behavior, query serialization, page ID/source/revision/file/vote acquisition logic, cached state, live Wikidot behavior, site client internals, `rating_percent`, tags, parent fullname, or URL syntax validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The validator uses `AbstractUser`, not only `User`, because the shared user parser can produce regular, deleted, anonymous, guest, and system user representations. This mirrors the adjacent page revision and forum validation pattern while keeping nullable page metadata behavior intact.
