# PR: Cache StringUtil special character translation table

## Summary

`StringUtil.to_unix(...)` should reuse the special-character translation table instead of rebuilding it for every name normalization call.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from prior parser and validation drafts. It does not change URL, profile, site-name, or generated-markup semantics. This slice only removes repeated local construction work from the shared string normalization helper.

## Problem Statement

`StringUtil.to_unix(...)` builds `str.maketrans(char_table.special_char_map)` on every call before translating a single string. The mapping is static module data, and `to_unix(...)` is called repeatedly by user/profile lookup code when constructing `https://www.wikidot.com/user:info/<unix-name>` URLs and fallback user records.

For bulk profile lookup, generated user ledgers, membership checks, moderation inventories, and migration tooling, rebuilding the same translation table for every requested name adds avoidable CPU work while providing no behavioral benefit.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free user/profile lookup, generated membership/user ledgers, moderation checks, and identity resolution as practical workflows. Existing drafts around user profile lookup, profile-title text fidelity, blank profile-title rejection, lookup-name validation, and direct user scalar validation all preserve `StringUtil.to_unix(...)` as the shared conversion path for requested usernames and returned profile titles.

The local timing check compared the previous per-call table-building pattern against the cached-table implementation on representative mixed ASCII and Unicode names:

```text
old_inline_table=12.763506s conversions=500000
cached_table=3.627659s conversions=500000
ratio=3.52x
```

The local fix is committed as `599c9af`.

## Affected Workflows

- `UserCollection.from_names(...)` URL construction for bulk profile lookup.
- `User.from_name(...)` and `client.user.get(...)` through the same lookup path.
- Fallback `User(..., unix_name=StringUtil.to_unix(name))` construction when a requested profile is not found and non-raising behavior is requested.
- Generated membership, moderation, migration, and audit tooling that normalizes many user-visible names.

## Proposed Fix

Create the `str.maketrans(...)` result once at module import:

```text
_SPECIAL_CHAR_TRANSLATION = str.maketrans(char_table.special_char_map)
```

Then call:

```text
target_str.translate(_SPECIAL_CHAR_TRANSLATION)
```

inside `StringUtil.to_unix(...)`.

## Implementation Notes

The patch leaves the existing normalization pipeline unchanged after translation:

- lowercase conversion
- non-ASCII replacement
- underscore/category handling
- leading/trailing separator cleanup
- repeated hyphen/colon collapse

No tests were added because the public behavior is already covered by the dedicated `StringUtil.to_unix(...)` suite and adjacent user/profile tests. This is a local constant extraction for performance, not a new public behavior.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_stringutil.py tests/unit/test_user.py -q
uv run pytest tests/unit/test_stringutil.py tests/unit/test_user.py tests/unit/test_client.py -q
uv run pytest tests/unit -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pyright
git diff --check
```

Observed results:

```text
string/user focused suite: 157 passed
string/user/client adjacent suite: 204 passed
full unit suite: 3944 passed
ruff: passed
format check: passed
mypy: passed with existing notes only
pyright: passed
diff whitespace: passed
```

Local timing evidence:

```text
old_inline_table=12.763506s conversions=500000
cached_table=3.627659s conversions=500000
ratio=3.52x
```

The focused complexity scan reported no `stringutil` hotspot after the change.

## Compatibility And Risk Notes

The change assumes `char_table.special_char_map` is static module data. Existing code treats it as a conversion table, not as runtime configuration. Callers that intentionally mutate `char_table.special_char_map` after import would no longer affect `StringUtil.to_unix(...)` in the same process; that behavior is not documented and would be unsafe for shared callers.

The patch does not change accepted input types, error messages, transliteration mappings, site-name validation, user lookup URLs, profile parsing, generated markup parsing, network behavior, authentication behavior, or live Wikidot interactions.

## Rationale For Upstream Suitability

This is a small, behavior-preserving performance cleanup in a shared utility. It avoids repeated construction of a large static translation table while relying on existing focused and adjacent tests to protect public conversion behavior.

## Acceptance Criteria

- `StringUtil.to_unix(...)` reuses a cached special-character translation table.
- Existing string normalization outputs remain unchanged for ASCII, accented Latin, Greek, Cyrillic, Japanese, category prefixes, underscores, colons, and empty strings.
- Existing non-string input validation remains unchanged.
- Existing user/profile lookup behavior remains unchanged.
- Full unit and static gates pass.

## Local Evidence, Not For Upstream Paste

- Local code commit: `599c9af`
- Thread workspace report records the timing check and full gate evidence for this slice.
- Clawpatch provenance was checked against local fork `d89ca91`, provider `codex`, state `missing`, `codex-cli 0.139.0`, and launcher SHA256 `61074d5ce62c253930498bdb5a517a1ca63e4263c9a9c251fb6f37cb78f7b4ec`.
- No credentials, cookies, tokens, auth JSON, browser profile data, raw generated HTML from real sites, private message bodies, page source text, private site data, or raw rollout paths were captured in this draft.
