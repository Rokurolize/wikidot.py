# PR Draft: Parse Meta Tags With HTML Parser

## Summary

`Page.metas` parsed `EditMetaModule` output with one exact regex that only matched escaped tags shaped as `&lt;meta name="..." content="..."/&gt;`. That missed valid meta markup when attributes appeared in another order, when content was empty, when the response included literal `<meta>` tags, or when attribute values contained HTML entities.

The fix decodes only escaped tag delimiters, parses the response body with BeautifulSoup, and unescapes extracted `name` and `content` attribute values after parsing. This preserves the public `Page.metas` dictionary API while making the getter tolerant of normal HTML serialization differences.

## Related Issue

Drafted from local rollout evidence; no upstream issue filed yet.

## Changes

- Parse `EditMetaModule` bodies with BeautifulSoup instead of an exact regex.
- Support escaped and literal `<meta>` tags in the same response body.
- Support reversed `name` / `content` attribute order.
- Preserve empty meta content values instead of dropping them.
- Decode HTML entities in meta names and contents without breaking quoted attribute content.
- Add a regression test for flexible meta markup and entity decoding.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Performance/reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Testing

Local implementation commit: `3a4e96e fix(page): parse meta tags with html parser`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_metas_getter_parses_decoded_flexible_markup -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 71 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 530 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`

## Acceptance Criteria

- `Page.metas` returns the same `dict[str, str]` public shape as before.
- Escaped `&lt;meta .../&gt;` tags and literal `<meta .../>` tags are both parsed.
- Meta tags are parsed when `content` appears before `name`.
- Empty `content=""` values are preserved as empty strings.
- Entity-encoded values such as `Tom &amp;amp; Jerry` are returned as normal text.
- Entity-encoded quotes in attribute values do not corrupt parsing.
- Existing meta setter batching behavior remains unchanged.

## Upstream-Safe Motivation

Meta tags are part of browser-free page publishing and verification workflows. A getter that depends on one exact escaped attribute order makes post-save metadata checks fragile, while an HTML parser handles normal serialization variations without changing the public API.

## Local Evidence, Not For Upstream Paste

- Local rollout `019e7a39-505b-76b3-bfb4-b68be3c71fb9` included a browser-free publishing script that manually set metadata and meta tags after saving pages.
- Local rollout evidence recorded meta values such as `codex-source-branch`, `codex-source-revision`, `codex-source-updated-at`, `codex-japanese-source-sha256`, and `codex-target-id` as part of practical publishing workflows.
- The local feature draft in [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md) includes meta tags as a first-class publish workflow input.
- The local meta batching draft in [007-pr-batch-meta-tag-updates.md](007-pr-batch-meta-tag-updates.md) improves meta writes; this draft improves the matching read/verification path.

## Additional Notes

The implementation intentionally does not unescape the full response body before parsing, because doing so can turn `&quot;` inside an attribute into raw quotes before the HTML parser sees the tag. It decodes tag delimiters first, then unescapes extracted attribute values.
