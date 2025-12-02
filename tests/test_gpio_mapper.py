"""
GPIOMapperのテスト
"""
import pytest
import json
from pathlib import Path
from src.mapper.gpio_mapper import GPIOMapper


class TestGPIOMapper:
    """GPIOMapperクラスのテストケース"""

    @pytest.fixture
    def temp_mapping_file(self, tmp_path):
        """一時的なマッピングファイルを作成"""
        mapping_data = {
            "18": "01",
            "23": "02",
            "24": "03"
        }
        mapping_file = tmp_path / "gpio_mapping.json"
        with open(mapping_file, 'w') as f:
            json.dump(mapping_data, f)
        return mapping_file

    def test_load_mapping(self, temp_mapping_file):
        """マッピングファイルの読み込みテスト"""
        mapper = GPIOMapper(config_path=str(temp_mapping_file))

        pin_mapping = mapper.get_pin_mapping()

        assert len(pin_mapping) == 3
        assert pin_mapping[18] == "01"
        assert pin_mapping[23] == "02"
        assert pin_mapping[24] == "03"

    def test_get_pins(self, temp_mapping_file):
        """GPIOピン番号のリスト取得テスト"""
        mapper = GPIOMapper(config_path=str(temp_mapping_file))

        pins = mapper.get_pins()

        assert len(pins) == 3
        assert 18 in pins
        assert 23 in pins
        assert 24 in pins

    def test_get_program_id(self, temp_mapping_file):
        """プログラムID取得テスト"""
        mapper = GPIOMapper(config_path=str(temp_mapping_file))

        assert mapper.get_program_id(18) == "01"
        assert mapper.get_program_id(23) == "02"
        assert mapper.get_program_id(24) == "03"
        assert mapper.get_program_id(99) is None

    def test_file_not_found(self, tmp_path):
        """存在しないファイルを指定した場合のテスト"""
        non_existent_file = tmp_path / "non_existent.json"

        with pytest.raises(FileNotFoundError):
            GPIOMapper(config_path=str(non_existent_file))

    def test_invalid_json(self, tmp_path):
        """不正なJSONファイルを指定した場合のテスト"""
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("This is not valid JSON")

        with pytest.raises(json.JSONDecodeError):
            GPIOMapper(config_path=str(invalid_file))
