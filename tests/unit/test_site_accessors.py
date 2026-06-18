"""Siteアクセサのユニットテスト"""

from typing import Any

import pytest

from wikidot.module.site import Site, SiteForumAccessor, SitePageAccessor, SitePagesAccessor


class TestSiteAccessorsInit:
    """Siteアクセサ初期化のテスト"""

    @pytest.mark.parametrize("accessor_cls", [SitePagesAccessor, SitePageAccessor, SiteForumAccessor])
    def test_init_accepts_site(self, mock_site_no_http: Site, accessor_cls: Any) -> None:
        """Siteアクセサ初期化時のsiteは保持する"""
        accessor = accessor_cls(mock_site_no_http)

        assert accessor.site is mock_site_no_http

    @pytest.mark.parametrize("accessor_cls", [SitePagesAccessor, SitePageAccessor, SiteForumAccessor])
    @pytest.mark.parametrize("site", [None, True, "test-site", {"unix_name": "test-site"}, object()])
    def test_init_rejects_malformed_site(self, accessor_cls: Any, site: Any) -> None:
        """Siteアクセサ初期化時のsiteはSiteだけ受け付ける"""
        with pytest.raises(ValueError, match="site must be a Site"):
            accessor_cls(site)
