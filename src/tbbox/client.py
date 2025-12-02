"""
TBBOXクライアント
TBBOXデバイスとのTCP/IP通信と認証を管理
"""
import socket
import time
from typing import Optional
import binascii

from src.utils.logger import logger
from config import settings


class TBBOXClient:
    """
    TBBOXデバイスとの通信を管理するクライアント

    TCP/IP接続の確立、認証、コマンド送信、再接続処理を担当
    """

    def __init__(self):
        """
        TBBOXクライアントの初期化
        """
        self.host = settings.TBBOX_IP
        self.port = settings.TBBOX_PORT
        self.socket: Optional[socket.socket] = None
        self.is_connected = False
        self.is_authenticated = False
        self.max_retry = 5
        self.retry_delay = 3  # 秒

        logger.info(f"TBBOXクライアント初期化: {self.host}:{self.port}")

    def connect(self) -> bool:
        """
        TBBOXデバイスに接続

        Returns:
            bool: 接続成功時True、失敗時False
        """
        retry_count = 0

        while retry_count < self.max_retry:
            try:
                # 既存の接続があればクローズ
                if self.socket:
                    self.close()

                # ソケットを作成
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(10)  # 10秒のタイムアウト

                logger.info(f"TBBOXに接続中... ({self.host}:{self.port})")
                self.socket.connect((self.host, self.port))

                self.is_connected = True
                logger.info("TBBOXへの接続に成功しました")

                # ログイン処理
                if self._login():
                    return True
                else:
                    logger.error("ログインに失敗しました")
                    self.close()

            except socket.timeout:
                logger.error(f"接続タイムアウト (試行 {retry_count + 1}/{self.max_retry})")
            except ConnectionRefusedError:
                logger.error(f"接続が拒否されました (試行 {retry_count + 1}/{self.max_retry})")
            except Exception as e:
                logger.error(f"接続エラー: {e} (試行 {retry_count + 1}/{self.max_retry})")

            retry_count += 1
            if retry_count < self.max_retry:
                logger.info(f"{self.retry_delay}秒後に再接続を試行します...")
                time.sleep(self.retry_delay)

        logger.error(f"TBBOXへの接続に失敗しました ({self.max_retry}回試行)")
        return False

    def _login(self) -> bool:
        """
        TBBOXにログイン

        Returns:
            bool: ログイン成功時True、失敗時False
        """
        try:
            if not self.is_connected:
                logger.error("ログイン前に接続が必要です")
                return False

            logger.info("TBBOXにログイン中...")

            # ログインコマンドを送信
            login_command = settings.LOGIN_COMMAND
            success = self._send_raw_command(login_command)

            if success:
                self.is_authenticated = True
                logger.info("TBBOXへのログインに成功しました")
                return True
            else:
                logger.error("ログインコマンドの送信に失敗しました")
                return False

        except Exception as e:
            logger.error(f"ログイン中にエラーが発生しました: {e}")
            return False

    def _send_raw_command(self, hex_command: str) -> bool:
        """
        16進数コマンドを送信

        Args:
            hex_command: 16進数形式のコマンド文字列

        Returns:
            bool: 送信成功時True、失敗時False
        """
        try:
            if not self.socket or not self.is_connected:
                logger.error("接続が確立されていません")
                return False

            # 16進数文字列をバイナリに変換
            # スペースを削除してから変換
            hex_command = hex_command.replace(" ", "").replace("\n", "")
            command_bytes = binascii.unhexlify(hex_command)

            # コマンド送信
            self.socket.send(command_bytes)
            logger.debug(f"コマンド送信: {hex_command[:50]}...")

            # レスポンスを受信（オプション）
            try:
                response = self.socket.recv(1024)
                if response:
                    logger.debug(f"レスポンス受信: {binascii.hexlify(response).decode()[:50]}...")
            except socket.timeout:
                # タイムアウトは正常（レスポンスがない場合がある）
                pass

            return True

        except Exception as e:
            logger.error(f"コマンド送信中にエラーが発生しました: {e}")
            self.is_connected = False
            return False

    def send_command(self, hex_command: str, max_retry: int = 3) -> bool:
        """
        コマンドを送信（再送信機能付き）

        Args:
            hex_command: 16進数形式のコマンド文字列
            max_retry: 最大再送信回数

        Returns:
            bool: 送信成功時True、失敗時False
        """
        retry_count = 0

        while retry_count < max_retry:
            # 未接続の場合は再接続を試行
            if not self.is_connected or not self.is_authenticated:
                logger.warning("接続が切断されています。再接続を試行します...")
                if not self.connect():
                    logger.error("再接続に失敗しました")
                    return False

            # コマンド送信
            if self._send_raw_command(hex_command):
                return True

            retry_count += 1
            if retry_count < max_retry:
                logger.warning(f"コマンド送信失敗。再送信します (試行 {retry_count + 1}/{max_retry})")
                time.sleep(1)

        logger.error(f"コマンド送信に失敗しました ({max_retry}回試行)")
        return False

    def close(self):
        """
        接続をクローズ
        """
        if self.socket:
            try:
                self.socket.close()
                logger.info("TBBOXとの接続をクローズしました")
            except Exception as e:
                logger.error(f"接続クローズ中にエラーが発生しました: {e}")
            finally:
                self.socket = None
                self.is_connected = False
                self.is_authenticated = False

    def __enter__(self):
        """コンテキストマネージャーのエントリー"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーのイグジット"""
        self.close()