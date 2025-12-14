"""
SwitchMapperのテスト
"""
import pytest
from pathlib import Path
import tempfile
import json

from src.mapper.switch_mapper import SwitchMapper


class TestSwitchMapper:
    """SwitchMapperクラスのテスト"""

    def test_init_with_default_mapping(self):
        """デフォルトマッピングでの初期化テスト"""
        mapper = SwitchMapper()
        mapping = mapper.get_mapping()

        assert len(mapping) == 16
        assert mapping["0000"] == "01"
        assert mapping["1111"] == "16"

    def test_init_with_custom_mapping_file(self):
        """カスタムマッピングファイルでの初期化テスト"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            custom_mapping = {"0000": "99", "1111": "88"}
            json.dump(custom_mapping, f)
            f.flush()

            mapper = SwitchMapper(mapping_file=Path(f.name))
            mapping = mapper.get_mapping()

            assert mapping["0000"] == "99"
            assert mapping["1111"] == "88"

    def test_init_with_nonexistent_file(self):
        """存在しないファイルでの初期化テスト（デフォルトにフォールバック）"""
        mapper = SwitchMapper(mapping_file=Path("/nonexistent/path.json"))
        mapping = mapper.get_mapping()

        # デフォルトマッピングが使用される
        assert len(mapping) == 16

    def test_parse_alert_valid_patterns(self):
        """有効なalertパターンの解析テスト"""
        mapper = SwitchMapper()

        # 全パターンテスト
        test_cases = [
            ("00009999", "01"),
            ("00019999", "02"),
            ("00109999", "03"),
            ("00119999", "04"),
            ("01009999", "05"),
            ("01019999", "06"),
            ("01109999", "07"),
            ("01119999", "08"),
            ("10009999", "09"),
            ("10019999", "10"),
            ("10109999", "11"),
            ("10119999", "12"),
            ("11009999", "13"),
            ("11019999", "14"),
            ("11109999", "15"),
            ("11119999", "16"),
        ]

        for alert, expected_program_id in test_cases:
            result = mapper.parse_alert(alert)
            assert result == expected_program_id, f"Failed for alert={alert}"

    def test_parse_alert_with_nine(self):
        """"9"を含むalertの解析テスト"""
        mapper = SwitchMapper()

        # "9"は"0"として扱われる
        assert mapper.parse_alert("90009999") == "01"  # 9000 → 0000
        assert mapper.parse_alert("09009999") == "01"  # 0900 → 0000
        assert mapper.parse_alert("00909999") == "01"  # 0090 → 0000
        assert mapper.parse_alert("00099999") == "01"  # 0009 → 0000
        assert mapper.parse_alert("19109999") == "11"  # 1910 → 1010

    def test_parse_alert_all_nine(self):
        """すべて"9"のalertの解析テスト"""
        mapper = SwitchMapper()

        # すべて9の場合はNoneを返す
        result = mapper.parse_alert("99999999")
        assert result is None

    def test_parse_alert_invalid_length(self):
        """不正な長さのalertの解析テスト"""
        mapper = SwitchMapper()

        assert mapper.parse_alert("1234") is None  # 短すぎる
        assert mapper.parse_alert("123456789") is None  # 長すぎる
        assert mapper.parse_alert("") is None  # 空
        assert mapper.parse_alert(None) is None  # None

    def test_parse_alert_invalid_characters(self):
        """不正な文字を含むalertの解析テスト"""
        mapper = SwitchMapper()

        assert mapper.parse_alert("12349999") is None  # 2, 3, 4が不正
        assert mapper.parse_alert("abcd9999") is None  # 英字が不正

    def test_get_program_id_for_switches(self):
        """個別スイッチ状態からのプログラムID取得テスト"""
        mapper = SwitchMapper()

        # 正常ケース
        assert mapper.get_program_id_for_switches(0, 0, 0, 0) == "01"
        assert mapper.get_program_id_for_switches(0, 0, 0, 1) == "02"
        assert mapper.get_program_id_for_switches(1, 0, 1, 0) == "11"
        assert mapper.get_program_id_for_switches(1, 1, 1, 1) == "16"

    def test_get_program_id_for_switches_invalid(self):
        """不正なスイッチ状態のテスト"""
        mapper = SwitchMapper()

        # 0/1以外の値
        assert mapper.get_program_id_for_switches(2, 0, 0, 0) is None
        assert mapper.get_program_id_for_switches(0, -1, 0, 0) is None
        assert mapper.get_program_id_for_switches(0, 0, 9, 0) is None

    def test_switch_pattern_to_program_id_calculation(self):
        """パターン計算のテスト"""
        mapper = SwitchMapper()

        # 2進数→10進数+1の計算が正しいか
        # 0000 = 0 → 01
        # 0001 = 1 → 02
        # 1010 = 10 → 11
        # 1111 = 15 → 16

        assert mapper._switch_pattern_to_program_id("0000") == "01"
        assert mapper._switch_pattern_to_program_id("0001") == "02"
        assert mapper._switch_pattern_to_program_id("1010") == "11"
        assert mapper._switch_pattern_to_program_id("1111") == "16"


class TestSwitchMapperEdgeCases:
    """SwitchMapperのエッジケーステスト"""

    def test_mapping_file_invalid_json(self):
        """不正なJSONファイルでの初期化テスト"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("invalid json {")
            f.flush()

            # 不正なJSONの場合、デフォルトマッピングにフォールバック
            mapper = SwitchMapper(mapping_file=Path(f.name))
            mapping = mapper.get_mapping()

            assert len(mapping) == 16

    def test_alert_with_different_suffix(self):
        """下位4桁が9999でないalertのテスト"""
        mapper = SwitchMapper()

        # 下位4桁が9999でなくても処理される（警告ログのみ）
        result = mapper.parse_alert("10100000")
        assert result == "11"

    def test_get_mapping_returns_copy(self):
        """get_mappingがコピーを返すことのテスト"""
        mapper = SwitchMapper()

        mapping1 = mapper.get_mapping()
        mapping2 = mapper.get_mapping()

        # 異なるオブジェクトであることを確認
        assert mapping1 is not mapping2

        # 変更しても元のマッピングに影響しない
        mapping1["0000"] = "XX"
        assert mapper.get_mapping()["0000"] == "01"
