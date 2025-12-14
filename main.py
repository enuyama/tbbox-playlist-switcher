"""
TBBOX Playlist Switcher - メインエントリーポイント

満空灯制御装置（linkbase）からのHTTPリクエストを受信し、
スイッチの状態に応じてTBBOXのプログラムを自動的に切り替えます。
"""
import signal
import sys

from config import settings
from src.http.server import HTTPServer
from src.mapper.switch_mapper import SwitchMapper
from src.tbbox.client import TBBOXClient
from src.tbbox.playlist import PlaylistController
from src.utils.logger import logger


class TBBOXPlaylistSwitcher:
    """TBBOX Playlist Switcherアプリケーションのメインクラス"""

    def __init__(self):
        """初期化"""
        self.http_server = None
        self.switch_mapper = None
        self.tbbox_client = None
        self.playlist_controller = None

    def on_alert_received(self, alert: str) -> bool:
        """
        HTTPリクエスト受信時のコールバック関数

        Args:
            alert: 8桁のalertパラメータ（例: "10109999"）

        Returns:
            bool: 処理成功時True、失敗時False
        """
        logger.info(f"alertを受信しました: {alert}")

        # alertをプログラムIDに変換
        program_id = self.switch_mapper.parse_alert(alert)

        if program_id is None:
            logger.warning("プログラムIDの取得に失敗しました（スキップ）")
            return True  # エラーではないのでTrueを返す

        logger.info(f"プログラム切り替えリクエスト: プログラムID={program_id}")

        # TBBOXプログラムを切り替える
        if self.playlist_controller:
            success = self.playlist_controller.switch_program(program_id)
            if not success:
                logger.error(f"プログラム '{program_id}' への切り替えに失敗しました")
                return False
            return True
        else:
            logger.error("PlaylistControllerが初期化されていません")
            return False

    def setup(self) -> None:
        """アプリケーションのセットアップ"""
        logger.info("=" * 60)
        logger.info("TBBOX Playlist Switcher を起動しています...")
        logger.info("=" * 60)

        try:
            # スイッチマッパーを初期化
            self.switch_mapper = SwitchMapper()
            mapping = self.switch_mapper.get_mapping()
            logger.info(f"スイッチマッピング: {len(mapping)}パターン登録済み")

            # TBBOX接続をスキップするかチェック
            if settings.TBBOX_SKIP_CONNECTION:
                logger.info("TBBOX接続はスキップされました（TBBOX_SKIP_CONNECTION=true）")
                self.tbbox_client = None
                self.playlist_controller = None
            else:
                # TBBOXクライアントを初期化
                logger.info("TBBOXクライアントを初期化しています...")
                self.tbbox_client = TBBOXClient()

                # TBBOXに接続
                if not self.tbbox_client.connect():
                    logger.error("TBBOXへの接続に失敗しました")
                    # 接続失敗してもHTTPサーバは起動（再接続は自動で試行される）
                    logger.warning("TBBOXに接続できませんが、HTTPサーバを起動します")

                # PlaylistControllerを初期化
                self.playlist_controller = PlaylistController(self.tbbox_client)
                logger.info("PlaylistControllerを初期化しました")

            # HTTPサーバをセットアップ
            self.http_server = HTTPServer(
                host=settings.HTTP_HOST,
                port=settings.HTTP_PORT,
                callback=self.on_alert_received
            )
            logger.info(
                f"HTTPサーバを設定しました: "
                f"http://{settings.HTTP_HOST}:{settings.HTTP_PORT}"
            )

        except Exception as e:
            logger.error(f"セットアップ中にエラーが発生しました: {e}")
            sys.exit(1)

    def run(self) -> None:
        """アプリケーションを実行"""
        try:
            logger.info(
                f"HTTPサーバを起動します。終了するにはCtrl+Cを押してください。"
            )
            logger.info(
                f"エンドポイント: http://{settings.HTTP_HOST}:{settings.HTTP_PORT}/api/control"
            )
            self.http_server.run()

        except KeyboardInterrupt:
            logger.info("ユーザーによって停止されました")
        except Exception as e:
            logger.error(f"実行中にエラーが発生しました: {e}")
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """クリーンアップ処理"""
        logger.info("クリーンアップを実行しています...")

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
