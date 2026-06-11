import re

from .table import char_table


class StringUtil:
    SITE_UNIX_NAME_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")

    @staticmethod
    def to_unix(target_str: str) -> str:
        """Convert a string to Unix format

        Parameters
        ----------
        target_str: str
            String to convert

        Returns
        -------
        str
            Converted string
        """
        # MEMO: legacy wikidotの実装に合わせている
        if not isinstance(target_str, str):
            raise ValueError("target_str must be a string")

        # 特殊文字の変換辞書の作成
        table = str.maketrans(char_table.special_char_map)
        # 変換実施
        target_str = target_str.translate(table)

        # lowercaseへの変換
        target_str = target_str.lower()

        # ascii以外の文字を削除
        target_str = re.sub(r"[^a-z0-9\-:_]", "-", target_str)
        target_str = re.sub(r"^_", ":_", target_str)
        target_str = re.sub(r"(?<!:)_", "-", target_str)
        target_str = re.sub(r"^-*", "", target_str)
        target_str = re.sub(r"-*$", "", target_str)
        target_str = re.sub(r"-{2,}", "-", target_str)
        target_str = re.sub(r":{2,}", ":", target_str)
        target_str = target_str.replace(":-", ":")
        target_str = target_str.replace("-:", ":")
        target_str = target_str.replace("_-", "_")
        target_str = target_str.replace("-_", "_")

        # 先頭と末尾の:を削除
        target_str = re.sub(r"^:", "", target_str)
        target_str = re.sub(r":$", "", target_str)

        return target_str

    @staticmethod
    def validate_site_unix_name(site_name: str) -> None:
        """Validate a Wikidot site UNIX name before interpolating it into a host."""
        if not isinstance(site_name, str):
            raise ValueError("site_name must be a string")
        if not StringUtil.SITE_UNIX_NAME_PATTERN.fullmatch(site_name):
            raise ValueError(f"Invalid Wikidot site UNIX name: {site_name!r}")
