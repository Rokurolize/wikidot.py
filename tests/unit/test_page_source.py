from typing import Any

import pytest

from wikidot.module.page_source import PageSource


@pytest.mark.parametrize("wiki_text", ["", "source text"])
def test_page_source_accepts_string_wiki_text(mock_page_no_http: Any, wiki_text: str) -> None:
    source = PageSource(page=mock_page_no_http, wiki_text=wiki_text)

    assert source.page is mock_page_no_http
    assert source.wiki_text == wiki_text


@pytest.mark.parametrize("page", [None, True, "test-page", {"fullname": "test-page"}, object()])
def test_page_source_rejects_malformed_page(page: Any) -> None:
    with pytest.raises(ValueError, match="page must be a Page"):
        PageSource(page=page, wiki_text="source text")


@pytest.mark.parametrize("wiki_text", [None, True, 1, ["source"]])
def test_page_source_rejects_non_string_wiki_text(mock_page_no_http: Any, wiki_text: Any) -> None:
    with pytest.raises(ValueError, match="wiki_text must be a string"):
        PageSource(page=mock_page_no_http, wiki_text=wiki_text)
