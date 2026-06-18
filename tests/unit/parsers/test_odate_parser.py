"""odateパーサーのユニットテスト"""

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

import pytest
from bs4 import BeautifulSoup

from wikidot.util.parser.odate import odate_parse


class TestOdateParse:
    """odate_parse関数のテスト"""

    def test_parse_valid_odate(self, odate_html_factory: Callable[[int], str]) -> None:
        """有効なodate要素をパースできる"""
        # 2023-12-17 12:00:00 UTC = 1702814400
        html = odate_html_factory(1702814400)
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.odate")
        assert elem is not None

        result = odate_parse(elem)

        assert isinstance(result, datetime)
        assert result == datetime.fromtimestamp(1702814400, timezone.utc).replace(tzinfo=None)

    def test_parse_odate_epoch(self, odate_html_factory: Callable[[int], str]) -> None:
        """Unix epoch (0) をパースできる"""
        html = odate_html_factory(0)
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.odate")
        assert elem is not None

        result = odate_parse(elem)

        assert result == datetime.fromtimestamp(0, timezone.utc).replace(tzinfo=None)

    def test_parse_odate_with_multiple_classes(self, odate_html_multiple_classes: str) -> None:
        """複数クラスを持つodate要素をパースできる"""
        soup = BeautifulSoup(odate_html_multiple_classes, "lxml")
        elem = soup.select_one("span.odate")
        assert elem is not None

        result = odate_parse(elem)

        assert isinstance(result, datetime)
        assert result == datetime.fromtimestamp(1702828800, timezone.utc).replace(tzinfo=None)

    def test_parse_odate_without_time_class_raises(self, odate_html_no_time: str) -> None:
        """time_クラスがない場合はValueErrorを発生させる"""
        soup = BeautifulSoup(odate_html_no_time, "lxml")
        elem = soup.select_one("span.odate")
        assert elem is not None

        with pytest.raises(ValueError) as exc_info:
            odate_parse(elem)

        assert "valid unix time" in str(exc_info.value)

    @pytest.mark.parametrize("odate_element", [None, "not-tag", 123, object()])
    def test_parse_odate_rejects_non_tag_inputs(self, odate_element: Any) -> None:
        """bs4.Tag以外の入力は属性アクセス前に拒否する"""
        with pytest.raises(ValueError, match="odate_element must be bs4.Tag"):
            odate_parse(odate_element)

    def test_parse_odate_without_class_attribute_raises_value_error(self) -> None:
        """class属性がないタグはraw KeyErrorではなくodateパーサーエラーにする"""
        soup = BeautifulSoup("<span>Dec 17 2023</span>", "lxml")
        elem = soup.select_one("span")
        assert elem is not None

        with pytest.raises(ValueError) as exc_info:
            odate_parse(elem)

        assert "valid unix time" in str(exc_info.value)

    def test_parse_odate_with_malformed_time_class_raises(self) -> None:
        """time_クラスが非数値ならraw変換例外を露出しない"""
        soup = BeautifulSoup('<span class="odate time_latest">Dec 17 2023</span>', "lxml")
        elem = soup.select_one("span.odate")
        assert elem is not None

        with pytest.raises(ValueError, match="odate unix time is malformed: time_latest"):
            odate_parse(elem)

    @pytest.mark.parametrize("time_class", ["time_time_1702814400", "time_1702814400_time_"])
    def test_parse_odate_with_ambiguous_time_class_shape_raises(self, time_class: str) -> None:
        """time_接頭辞が複数含まれるクラスはタイムスタンプとして正規化しない"""
        soup = BeautifulSoup(f'<span class="odate {time_class}">Dec 17 2023</span>', "lxml")
        elem = soup.select_one("span.odate")
        assert elem is not None

        with pytest.raises(ValueError, match=rf"odate unix time is malformed: {time_class}"):
            odate_parse(elem)

    def test_parse_odate_with_non_ascii_decimal_time_payload_raises(self) -> None:
        """Non-ASCII decimal glyphs are not valid generated timestamp payloads."""
        time_class = "time_\uff11\uff17\uff10\uff12\uff18\uff11\uff14\uff14\uff10\uff10"
        soup = BeautifulSoup(f'<span class="odate {time_class}">Dec 17 2023</span>', "lxml")
        elem = soup.select_one("span.odate")
        assert elem is not None

        with pytest.raises(ValueError, match=rf"odate unix time is malformed: {time_class}"):
            odate_parse(elem)

    def test_parse_odate_recent_timestamp(self, odate_html_factory: Callable[[int], str]) -> None:
        """最近のタイムスタンプをパースできる"""
        # 2024-01-01 00:00:00 UTC = 1704067200
        html = odate_html_factory(1704067200)
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.odate")
        assert elem is not None

        result = odate_parse(elem)

        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1

    def test_parse_odate_old_timestamp(self, odate_html_factory: Callable[[int], str]) -> None:
        """古いタイムスタンプをパースできる"""
        # 2007-06-21 00:00:00 UTC (SCP wiki creation date)
        html = odate_html_factory(1182384000)
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.odate")
        assert elem is not None

        result = odate_parse(elem)

        assert result.year == 2007
        assert result.month == 6
        assert result.day == 21
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
