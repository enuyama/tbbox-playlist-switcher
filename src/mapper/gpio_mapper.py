"""
GPIOマッピングモジュール
gpio_mapping.jsonからGPIOピンとプログラムIDのマッピングを読み込む
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

from src.utils.logger import logger


class GPIOMapper:
    """GPIOピンとプログラムIDのマッピングを管理するクラス"""

    def __init__(self, config_path: str = None):
        """
        GPIOMapperの初期化

        Args:
            config_path: gpio_mapping.jsonのパス（指定しない場合はデフォルトパス）
        """
        if config_path is None:
            # デフォルトパスを設定（プロジェクトルート/config/gpio_mapping.json）
            # src/mapper/gpio_mapper.py から見たプロジェクトルート
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "gpio_mapping.json"
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self._mapping: Dict[int, str] = {}
        self._load_config()

    def _load_config(self) -> None:
        """gpio_mapping.jsonから設定を読み込む"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 文字列のキーを整数に変換
            self._mapping = {
                int(pin): program_id for pin, program_id in data.items()
            }

            logger.info(f"GPIOマッピングを読み込みました: {self._mapping}")

        except FileNotFoundError:
            logger.error(
                f"GPIOマッピングファイルが見つかりません: {self.config_path}"
            )
            raise
        except json.JSONDecodeError as e:
            logger.error(
                f"GPIOマッピングファイルのJSON解析に失敗しました: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"GPIOマッピングの読み込み中にエラーが発生しました: {e}"
            )
            raise

    def get_pin_mapping(self) -> Dict[int, str]:
        """
        GPIOピンとプログラムIDのマッピングを取得

        Returns:
            {pin番号: プログラムID}の辞書
        """
        return self._mapping.copy()

    def get_pins(self) -> List[int]:
        """
        監視対象のGPIOピン番号のリストを取得

        Returns:
            GPIOピン番号のリスト
        """
        return list(self._mapping.keys())

    def get_program_id(self, pin: int) -> Optional[str]:
        """
        指定されたGPIOピンに対応するプログラムIDを取得

        Args:
            pin: GPIOピン番号

        Returns:
            プログラムID（存在しない場合はNone）
        """
        return self._mapping.get(pin)
