"""
TBBOX Playlist Switcher - メインエントリーポイント

Raspberry PiのGPIOピンの状態を監視し、
ピンの変化に応じてTBBOXのプログラムを自動的に切り替えます。
"""
import signal
import sys
from pathlib import Path

from src.gpio.monitor import GPIOMonitor
from src.mapper.gpio_mapper import GPIOMapper
from src.tbbox.client import TBBOXClient
from src.tbbox.playlist import PlaylistController
from src.utils.logger import logger


class TBBOXPlaylistSwitcher:
    """TBBOX Playlist Switcherアプリケーションのメインクラス"""

    def __init__(self):
        """初期化"""
        self.gpio_monitor = None
        self.gpio_mapper = None
        self.tbbox_client = None
        self.playlist_controller = None

    def on_gpio_change(self, pin: int, program_id: str) -> None:
        """
        GPIO変化時のコールバック関数

        Args:
            pin: 変化したGPIOピン番号
            program_id: 切り替え先のプログラムID
        """
        logger.info(f"プログラム切り替えリクエスト: ピン={pin}, プログラムID={program_id}")

        # TBBOXプログラムを切り替える
        if self.playlist_controller:
            success = self.playlist_controller.switch_program(program_id)
            if not success:
                logger.error(f"プログラム '{program_id}' への切り替えに失敗しました")
        else:
            logger.error("PlaylistControllerが初期化されていません")

    def setup(self) -> None:
        """アプリケーションのセットアップ"""
        logger.info("=" * 60)
        logger.info("TBBOX Playlist Switcher を起動しています...")
        logger.info("=" * 60)

        try:
            # GPIOマッピングを読み込む
            self.gpio_mapper = GPIOMapper()
            pin_mapping = self.gpio_mapper.get_pin_mapping()

            if not pin_mapping:
                logger.error("GPIOマッピングが空です。config/gpio_mapping.jsonを確認してください。")
                sys.exit(1)

            logger.info(f"監視対象ピン: {list(pin_mapping.keys())}")
            logger.info(f"ピンマッピング: {pin_mapping}")

            # TBBOXクライアントを初期化
            logger.info("TBBOXクライアントを初期化しています...")
            self.tbbox_client = TBBOXClient()

            # TBBOXに接続
            if not self.tbbox_client.connect():
                logger.error("TBBOXへの接続に失敗しました")
                # 接続失敗してもGPIO監視は続行（再接続は自動で試行される）
                logger.warning("TBBOXに接続できませんが、GPIO監視を開始します")

            # PlaylistControllerを初期化
            self.playlist_controller = PlaylistController(self.tbbox_client)
            logger.info("PlaylistControllerを初期化しました")

            # GPIOモニターをセットアップ
            self.gpio_monitor = GPIOMonitor(pin_mapping, self.on_gpio_change)
            self.gpio_monitor.setup()

        except Exception as e:
            logger.error(f"セットアップ中にエラーが発生しました: {e}")
            sys.exit(1)

    def run(self) -> None:
        """アプリケーションを実行"""
        try:
            logger.info("GPIO監視を開始しました。終了するにはCtrl+Cを押してください。")
            self.gpio_monitor.start()

        except KeyboardInterrupt:
            logger.info("ユーザーによって停止されました")
        except Exception as e:
            logger.error(f"実行中にエラーが発生しました: {e}")
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """クリーンアップ処理"""
        logger.info("クリーンアップを実行しています...")

        if self.gpio_monitor:
            self.gpio_monitor.cleanup()

        if self.playlist_controller:
            self.playlist_controller.close()
            logger.info("PlaylistControllerをクローズしました")

        if self.tbbox_client:
            self.tbbox_client.close()
            logger.info("TBBOXクライアントをクローズしました")

        logger.info("=" * 60)
        logger.info("TBBOX Playlist Switcher を終了しました")
        logger.info("=" * 60)

    def signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        logger.info(f"シグナル {signum} を受信しました")
        if self.gpio_monitor:
            self.gpio_monitor.stop()
        self.cleanup()
        sys.exit(0)


def main():
    """メイン関数"""
    app = TBBOXPlaylistSwitcher()

    # シグナルハンドラーを設定
    signal.signal(signal.SIGINT, app.signal_handler)
    signal.signal(signal.SIGTERM, app.signal_handler)

    # アプリケーションを起動
    app.setup()
    app.run()


if __name__ == "__main__":
    main()
