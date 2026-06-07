"""SearchPagesQueryのユニットテスト"""

from typing import Any
from unittest.mock import MagicMock

import pytest

from wikidot.module.page import SearchPagesQuery
from wikidot.module.user import User


class TestSearchPagesQueryInit:
    """SearchPagesQueryの初期化テスト"""

    def test_default_values(self):
        """デフォルト値のテスト"""
        query = SearchPagesQuery()
        assert query.pagetype == "*"
        assert query.category == "*"
        assert query.tags is None
        assert query.parent is None
        assert query.link_to is None
        assert query.created_at is None
        assert query.updated_at is None
        assert query.created_by is None
        assert query.rating is None
        assert query.votes is None
        assert query.name is None
        assert query.fullname is None
        assert query.range is None
        assert query.order == "created_at desc"
        assert query.offset == 0
        assert query.limit is None
        assert query.perPage == 250
        assert query.separate == "no"
        assert query.wrapper == "no"

    def test_custom_values(self):
        """カスタム値のテスト"""
        query = SearchPagesQuery(
            pagetype="normal",
            category="scp",
            tags="tale",
            order="rating desc",
            limit=100,
        )
        assert query.pagetype == "normal"
        assert query.category == "scp"
        assert query.tags == "tale"
        assert query.order == "rating desc"
        assert query.limit == 100

    def test_tags_as_list(self):
        """タグをリストで指定するテスト"""
        query = SearchPagesQuery(tags=["scp", "safe", "humanoid"])
        assert query.tags == ["scp", "safe", "humanoid"]


class TestSearchPagesQueryAsDict:
    """SearchPagesQuery.as_dict()のテスト"""

    def test_basic_as_dict(self):
        """基本的なas_dictのテスト"""
        query = SearchPagesQuery()
        result = query.as_dict()
        # デフォルト値がNoneでないものが含まれる
        assert "pagetype" in result
        assert result["pagetype"] == "*"
        assert "category" in result
        assert result["category"] == "*"
        assert "order" in result
        assert result["order"] == "created_at desc"
        # Noneの値は含まれない
        assert "tags" not in result
        assert "parent" not in result
        assert "limit" not in result

    def test_as_dict_with_custom_values(self):
        """カスタム値でのas_dictのテスト"""
        query = SearchPagesQuery(
            category="scp",
            tags="keter",
            limit=50,
            offset=10,
        )
        result = query.as_dict()
        assert result["category"] == "scp"
        assert result["tags"] == "keter"
        assert result["limit"] == 50
        assert result["offset"] == 10

    def test_as_dict_tags_list_conversion(self):
        """タグリストが文字列に変換されるテスト"""
        query = SearchPagesQuery(tags=["scp", "euclid", "humanoid"])
        result = query.as_dict()
        assert result["tags"] == "scp euclid humanoid"

    def test_as_dict_tags_list_requires_strings(self):
        """タグリストの要素は文字列だけ受け付ける"""
        import pytest

        invalid_tags: Any = ["scp", 3]

        query = SearchPagesQuery(tags=invalid_tags)
        with pytest.raises(ValueError, match="tags list entries must be strings"):
            query.as_dict()

    def test_as_dict_tags_string_unchanged(self):
        """タグ文字列がそのまま保持されるテスト"""
        query = SearchPagesQuery(tags="scp euclid")
        result = query.as_dict()
        assert result["tags"] == "scp euclid"

    def test_as_dict_created_by_user_conversion(self):
        """created_byのUserオブジェクトがユーザーUNIX名に変換されるテスト"""
        user = User(
            client=MagicMock(),
            id=12345,
            name="Test User",
            unix_name="test-user",
            avatar_url="https://www.wikidot.com/avatar.php?userid=12345",
        )
        query = SearchPagesQuery(created_by=user)
        result = query.as_dict()
        assert result["created_by"] == "test-user"

    def test_as_dict_excludes_none_values(self):
        """None値が除外されるテスト"""
        query = SearchPagesQuery(
            category="test",
            tags=None,
            limit=None,
        )
        result = query.as_dict()
        assert "category" in result
        assert "tags" not in result
        assert "limit" not in result

    def test_as_dict_includes_zero_values(self):
        """0値が含まれるテスト"""
        query = SearchPagesQuery(offset=0)
        result = query.as_dict()
        assert "offset" in result
        assert result["offset"] == 0


class TestSearchPagesQueryUseCases:
    """SearchPagesQueryの実用的なユースケーステスト"""

    def test_scp_search_query(self):
        """SCP記事検索クエリのテスト"""
        query = SearchPagesQuery(
            category="scp",
            tags=["scp", "keter"],
            order="rating desc",
            limit=100,
        )
        result = query.as_dict()
        assert result["category"] == "scp"
        assert result["tags"] == "scp keter"
        assert result["order"] == "rating desc"
        assert result["limit"] == 100

    def test_paginated_search_query(self):
        """ページネーション付き検索クエリのテスト"""
        query = SearchPagesQuery(
            offset=100,
            limit=50,
            perPage=50,
        )
        result = query.as_dict()
        assert result["offset"] == 100
        assert result["limit"] == 50
        assert result["perPage"] == 50

    def test_date_filtered_search_query(self):
        """日付フィルタ付き検索クエリのテスト"""
        query = SearchPagesQuery(
            created_at=">=2020-01-01",
            updated_at="<=2023-12-31",
        )
        result = query.as_dict()
        assert result["created_at"] == ">=2020-01-01"
        assert result["updated_at"] == "<=2023-12-31"

    def test_rating_filtered_search_query(self):
        """評価フィルタ付き検索クエリのテスト"""
        query = SearchPagesQuery(
            rating=">=50",
            votes=">=10",
        )
        result = query.as_dict()
        assert result["rating"] == ">=50"
        assert result["votes"] == ">=10"

    def test_fullname_search_query(self):
        """フルネーム検索クエリのテスト"""
        query = SearchPagesQuery(
            fullname="scp-173",
        )
        result = query.as_dict()
        assert result["fullname"] == "scp-173"


class TestSearchPagesQueryValidation:
    """SearchPagesQueryのバリデーションテスト"""

    def test_invalid_parameter_raises_value_error(self):
        """無効なパラメータでValueErrorが発生すること"""
        import pytest

        invalid_params: dict[str, Any] = {"invalid_param": "value"}

        with pytest.raises(ValueError, match="Invalid query parameters"):
            SearchPagesQuery(**invalid_params)

    def test_multiple_invalid_parameters_raises_value_error(self):
        """複数の無効なパラメータでValueErrorが発生すること"""
        import pytest

        invalid_params: dict[str, Any] = {"invalid_param1": "value1", "invalid_param2": "value2"}

        with pytest.raises(ValueError, match="Invalid query parameters"):
            SearchPagesQuery(**invalid_params)

    def test_mixed_valid_invalid_parameters_raises_value_error(self):
        """有効なパラメータと無効なパラメータが混在する場合にValueErrorが発生すること"""
        import pytest

        invalid_params: dict[str, Any] = {"category": "scp", "invalid_param": "value"}

        with pytest.raises(ValueError, match="Invalid query parameters"):
            SearchPagesQuery(**invalid_params)

    def test_per_page_must_be_positive(self):
        """perPageは正の値だけ受け付ける"""
        import pytest

        with pytest.raises(ValueError, match="perPage must be positive"):
            SearchPagesQuery(perPage=0)

    def test_offset_must_be_non_negative(self):
        """offsetは0以上だけ受け付ける"""
        import pytest

        with pytest.raises(ValueError, match="offset must be non-negative"):
            SearchPagesQuery(offset=-1)

    def test_offset_must_be_integer(self):
        """offsetは整数だけ受け付ける"""
        import pytest

        invalid_offset: Any = "0"

        with pytest.raises(ValueError, match="offset must be an integer or None"):
            SearchPagesQuery(offset=invalid_offset)

    def test_limit_must_be_integer(self):
        """limitは整数またはNoneだけ受け付ける"""
        import pytest

        invalid_limit: Any = "50"

        with pytest.raises(ValueError, match="limit must be an integer or None"):
            SearchPagesQuery(limit=invalid_limit)

    def test_per_page_must_be_integer(self):
        """perPageは整数またはNoneだけ受け付ける"""
        import pytest

        invalid_per_page: Any = 50.5

        with pytest.raises(ValueError, match="perPage must be an integer or None"):
            SearchPagesQuery(perPage=invalid_per_page)

    def test_pagination_values_reject_booleans(self):
        """ページネーション値はboolを整数として受け付けない"""
        import pytest

        invalid_values: list[tuple[dict[str, Any], str]] = [
            ({"offset": True}, "offset must be an integer or None"),
            ({"offset": False}, "offset must be an integer or None"),
            ({"limit": True}, "limit must be an integer or None"),
            ({"limit": False}, "limit must be an integer or None"),
            ({"perPage": True}, "perPage must be an integer or None"),
            ({"perPage": False}, "perPage must be an integer or None"),
        ]
        for kwargs, message in invalid_values:
            with pytest.raises(ValueError, match=message):
                SearchPagesQuery(**kwargs)

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"pagetype": True}, "pagetype must be a string or None"),
            ({"category": ["scp"]}, "category must be a string or None"),
            ({"parent": 123}, "parent must be a string or None"),
            ({"link_to": False}, "link_to must be a string or None"),
            ({"created_at": 123}, "created_at must be a string or None"),
            ({"updated_at": object()}, "updated_at must be a string or None"),
            ({"rating": 5}, "rating must be a string or None"),
            ({"votes": {"min": 10}}, "votes must be a string or None"),
            ({"name": True}, "name must be a string or None"),
            ({"fullname": ["scp-173"]}, "fullname must be a string or None"),
            ({"range": 100}, "range must be a string or None"),
            ({"order": ["rating desc"]}, "order must be a string or None"),
            ({"separate": True}, "separate must be a string or None"),
            ({"wrapper": object()}, "wrapper must be a string or None"),
        ],
    )
    def test_string_query_fields_must_be_strings_or_none(self, kwargs: dict[str, Any], message: str):
        """文字列系のListPages条件はstrまたはNoneだけ受け付ける"""
        with pytest.raises(ValueError, match=message):
            SearchPagesQuery(**kwargs)

    def test_all_valid_parameters_work(self):
        """すべて有効なパラメータは正常に動作すること"""
        query = SearchPagesQuery(
            pagetype="normal",
            category="scp",
            tags="tale",
            parent="scp-001",
            link_to="scp-002",
            created_at=">=2020-01-01",
            updated_at="<=2023-12-31",
            created_by="test-user",
            rating=">=50",
            votes=">=10",
            name="test-page",
            fullname="scp-173",
            range="1-100",
            order="rating desc",
            offset=10,
            limit=50,
            perPage=100,
            separate="yes",
            wrapper="yes",
        )
        result = query.as_dict()
        assert result["category"] == "scp"
        assert result["tags"] == "tale"
