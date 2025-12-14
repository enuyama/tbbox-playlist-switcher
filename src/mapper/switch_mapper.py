"""
スイッチパターンマッパーモジュール
alertパラメータをプログラムIDに変換する
"""
import json
import re
from pathlib import Path
from typing import Dict, Optional

from src.utils.logger import logger


class SwitchMapper:
    """
    スイッチパターンをプログラムIDに変換するクラス

    4つのスイッチ（SW1-SW4）の組み合わせで16パターン（2^4）を
    プログラムID（"01"～"16"）にマッピングする
    """

    # デフォルトのマッピング設定ファイルパス
    DEFAULT_MAPPING_FILE = Path(__file__).parent.parent.parent / "config" / "switch_mapping.json"

    def __init__(self, mapping_file: Optional[Path] = None):
        """
        SwitchMapperの初期化

        Args:
            mapping_file: マッピング設定ファイルのパス（省略時はデフォルト）
        """
        self.mapping_file = mapping_file or self.DEFAULT_MAPPING_FILE
        self.pattern_to_program: Dict[str, str] = {}
        self._load_mapping()

    def _load_mapping(self) -> None:
        """マッピング設定ファイルを読み込む"""
        try:
            if self.mapping_file.exists():
                with open(self.mapping_file, "r", encoding="utf-8") as f:
                    self.pattern_to_program = json.load(f)
                logger.info(
                    f"スイッチマッピングを読み込みました: "
                    f"{len(self.pattern_to_program)}パターン"
                )
            else:
                # ファイルがない場合はデフォルトマッピングを生成
                self._generate_default_mapping()
                logger.warning(
                    f"マッピングファイルが見つかりません: {self.mapping_file}"
                    f" デフォルトマッピングを使用します"
                )
        except json.JSONDecodeError as e:
            logger.error(f"マッピングファイルの解析に失敗しました: {e}")
            self._generate_default_mapping()
        except Exception as e:
            logger.error(f"マッピングファイルの読み込みに失敗しました: {e}")
            self._generate_default_mapping()

    def _generate_default_mapping(self) -> None:
        """デフォルトのマッピングを生成"""
        self.pattern_to_program = {}
        for i in range(16):
            pattern = f"{i:04b}"  # 0000 ~ 1111
            program_id = f"{i + 1:02d}"  # 01 ~ 16
            self.pattern_to_program[pattern] = program_id

        logger.info("デフォルトマッピングを生成しました（16パターン）")

    def parse_alert(self, alert: str) -> Optional[str]:
        """
        alertパラメータを解析してプログラムIDを返す

        Args:
            alert: 8桁のalertパラメータ（例: "10109999"）

        Returns:
            プログラムID（"01"～"16"）、エラー時はNone
        """
        # 基本的な検証
        if not alert or len(alert) != 8:
            logger.error(f"無効なalertパラメータ: {alert}")
            return None

        # 上位4桁を取得
        switch_pattern = alert[:4]

        # 0/1/9以外の文字が含まれていないか確認
        if re.search(r"[^019]", switch_pattern):
            logger.error(f"不正な文字を含むパターン: {switch_pattern}")
            return None

        # すべて9の場合はNoneを返す（変更なし）
        if switch_pattern == "9999":
            logger.info("すべてのスイッチが未定義(9)のため、処理をスキップします")
            return None

        # プログラムIDに変換
        program_id = self._switch_pattern_to_program_id(switch_pattern)

        if program_id:
            logger.info(f"パターン '{switch_pattern}' → プログラムID '{program_id}'")

        return program_id

    def _switch_pattern_to_program_id(self, switch_pattern: str) -> Optional[str]:
        """
        スイッチパターンからプログラムIDを計算

        Args:
            switch_pattern: 4桁のスイッチ状態（例: "1010"）

        Returns:
            プログラムID（"01"～"16"）、エラー時はNone
        """
        # "9"を含む場合の処理
        if "9" in switch_pattern:
            # "9"を"0"に置換して計算（未定義=OFFとして扱う）
            normalized_pattern = switch_pattern.replace("9", "0")
            logger.debug(
                f"パターンに'9'を含むため正規化: "
                f"{switch_pattern} → {normalized_pattern}"
            )
        else:
            normalized_pattern = switch_pattern

        # マッピングから検索
        if normalized_pattern in self.pattern_to_program:
            return self.pattern_to_program[normalized_pattern]

        # マッピングにない場合は計算で求める
        try:
            # 2進数として解釈
            pattern_number = int(normalized_pattern, 2)
            program_id = f"{pattern_number + 1:02d}"

            # 有効範囲チェック（01～16）
            if 1 <= pattern_number + 1 <= 16:
                return program_id
            else:
                logger.error(f"プログラムIDが範囲外: {program_id}")
                return None

        except ValueError as e:
            logger.error(f"パターンの解析に失敗しました: {normalized_pattern}, {e}")
            return None

    def get_mapping(self) -> Dict[str, str]:
        """
        現在のマッピングを取得

        Returns:
            Dict[str, str]: {パターン: プログラムID}のマッピング
        """
        return self.pattern_to_program.copy()

    def get_program_id_for_switches(
        self,
        sw1: int,
        sw2: int,
        sw3: int,
        sw4: int
    ) -> Optional[str]:
        """
        個別のスイッチ状態からプログラムIDを取得

        Args:
            sw1: スイッチ1の状態（0 or 1）
            sw2: スイッチ2の状態（0 or 1）
            sw3: スイッチ3の状態（0 or 1）
            sw4: スイッチ4の状態（0 or 1）

        Returns:
            プログラムID（"01"～"16"）、エラー時はNone
        """
        # 入力値の検証
        for i, sw in enumerate([sw1, sw2, sw3, sw4], 1):
            if sw not in (0, 1):
                logger.error(f"スイッチ{i}の値が不正です: {sw}")
                return None

        # パターン文字列を生成
        pattern = f"{sw1}{sw2}{sw3}{sw4}"

        return self._switch_pattern_to_program_id(pattern)
