"""
TBBOXプレイリスト管理
プログラム切り替えコマンドの送信を管理
"""
from typing import Optional, Dict

from src.utils.logger import logger
from src.tbbox.client import TBBOXClient
from config import settings


class PlaylistController:
    """
    TBBOXのプレイリスト（プログラム）切り替えを制御するクラス

    プログラムIDに応じた16進数コマンドを送信して、
    TBBOXで再生するプログラムを切り替える
    """

    def __init__(self, client: Optional[TBBOXClient] = None):
        """
        PlaylistControllerの初期化

        Args:
            client: TBBOXクライアントインスタンス（Noneの場合は新規作成）
        """
        self.client = client or TBBOXClient()
        self.program_commands = self._load_program_commands()

        # プレイリスト制御用コマンド
        self.control_commands = {
            "pause": settings.PAUSE_COMMAND,
            "resume": settings.RESUME_COMMAND,
            "stop": settings.STOP_COMMAND
        }

        logger.info(f"PlaylistController初期化完了 (登録プログラム数: {len(self.program_commands)})")

    def _load_program_commands(self) -> Dict[str, str]:
        """
        プログラムIDと16進数コマンドのマッピングをロード

        Returns:
            Dict[str, str]: {プログラムID: 16進数コマンド}のマッピング
        """
        return settings.PROGRAM_COMMANDS

    def switch_program(self, program_id: str) -> bool:
        """
        指定されたプログラムに切り替え

        Args:
            program_id: プログラムID（"01"～"20"）

        Returns:
            bool: 切り替え成功時True、失敗時False
        """
        try:
            # プログラムIDの検証
            if program_id not in self.program_commands:
                logger.error(
                    f"無効なプログラムID: {program_id} "
                    f"(有効なID: {list(self.program_commands.keys())})"
                )
                return False

            # プログラムコマンドを取得
            program_command = self.program_commands[program_id]

            logger.info(f"プログラム '{program_id}' への切り替えを実行します")

            # コマンド送信（自動再接続・再送信機能付き）
            success = self.client.send_command(program_command)

            if success:
                logger.info(f"プログラム '{program_id}' への切り替えが完了しました")

                # プログラム切り替え後、音量を0%に設定
                # logger.info("音量を0%に設定します")
                # self.set_volume(0)

                return True
            else:
                logger.error(f"プログラム '{program_id}' への切り替えに失敗しました")
                return False

        except Exception as e:
            logger.error(f"プログラム切り替え中にエラーが発生しました: {e}")
            return False

    def pause(self) -> bool:
        """
        現在のプログラムを一時停止

        Returns:
            bool: 成功時True、失敗時False
        """
        try:
            logger.info("プログラムを一時停止します")
            success = self.client.send_command(self.control_commands["pause"])

            if success:
                logger.info("プログラムの一時停止が完了しました")
            else:
                logger.error("プログラムの一時停止に失敗しました")

            return success

        except Exception as e:
            logger.error(f"一時停止中にエラーが発生しました: {e}")
            return False

    def resume(self) -> bool:
        """
        一時停止中のプログラムを再開

        Returns:
            bool: 成功時True、失敗時False
        """
        try:
            logger.info("プログラムを再開します")
            success = self.client.send_command(self.control_commands["resume"])

            if success:
                logger.info("プログラムの再開が完了しました")
            else:
                logger.error("プログラムの再開に失敗しました")

            return success

        except Exception as e:
            logger.error(f"再開中にエラーが発生しました: {e}")
            return False

    def stop(self) -> bool:
        """
        現在のプログラムを停止

        Returns:
            bool: 成功時True、失敗時False
        """
        try:
            logger.info("プログラムを停止します")
            success = self.client.send_command(self.control_commands["stop"])

            if success:
                logger.info("プログラムの停止が完了しました")
            else:
                logger.error("プログラムの停止に失敗しました")

            return success

        except Exception as e:
            logger.error(f"停止中にエラーが発生しました: {e}")
            return False

    def set_volume(self, volume_percent: int) -> bool:
        """
        音量を設定

        Args:
            volume_percent: 音量パーセント（0-100、10刻み）

        Returns:
            bool: 成功時True、失敗時False
        """
        try:
            # 10刻みに丸める
            volume_percent = round(volume_percent / 10) * 10
            volume_percent = max(0, min(100, volume_percent))  # 0-100の範囲に制限

            volume_key = f"volume_{volume_percent}"

            if not hasattr(settings, f"VOLUME_{volume_percent}_COMMAND"):
                logger.error(f"音量設定 {volume_percent}% に対応するコマンドがありません")
                return False

            volume_command = getattr(settings, f"VOLUME_{volume_percent}_COMMAND")

            logger.info(f"音量を {volume_percent}% に設定します")
            success = self.client.send_command(volume_command)

            if success:
                logger.info(f"音量設定が完了しました: {volume_percent}%")
            else:
                logger.error(f"音量設定に失敗しました")

            return success

        except Exception as e:
            logger.error(f"音量設定中にエラーが発生しました: {e}")
            return False

    def close(self):
        """
        クライアント接続をクローズ
        """
        if self.client:
            self.client.close()

    def __enter__(self):
        """コンテキストマネージャーのエントリー"""
        if self.client:
            self.client.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーのイグジット"""
        self.close()