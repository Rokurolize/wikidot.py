from typing import Any
from unittest.mock import MagicMock

import pytest

from wikidot.module.page_source import PageSource


@pytest.mark.parametrize("wiki_text", ["", "source text"])
def test_page_source_accepts_string_wiki_text(wiki_text: str) -> None:
    source = PageSource(page=MagicMock(), wiki_text=wiki_text)

    assert source.wiki_text == wiki_text


@pytest.mark.parametrize("wiki_text", [None, True, 1, ["source"]])
def test_page_source_rejects_non_string_wiki_text(wiki_text: Any) -> None:
    with pytest.raises(ValueError, match="wiki_text must be a string"):
        PageSource(page=MagicMock(), wiki_text=wiki_text)
