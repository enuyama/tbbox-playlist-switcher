"""
HTTPサーバモジュール
満空灯制御装置からのHTTPリクエストを受信してプログラム切り替えをトリガーする
"""
import re
from typing import Callable, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from src.utils.logger import logger


class HTTPServer:
    """
    HTTPリクエストを受信するサーバ

    満空灯制御装置（linkbase）からのHTTP GETリクエストを受信し、
    スイッチ状態に応じてコールバック関数を呼び出す
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        callback: Optional[Callable[[str], bool]] = None
    ):
        """
        HTTPServerの初期化

        Args:
            host: 待ち受けホスト（デフォルト: "0.0.0.0"）
            port: 待ち受けポート（デフォルト: 8080）
            callback: リクエスト受信時のコールバック関数
                      callback(alert: str) -> bool の形式
                      alertは8桁のパラメータ文字列
        """
        self.host = host
        self.port = port
        self.callback = callback
        self.app = FastAPI(title="TBBOX Playlist Switcher")
        self._setup_routes()

    def _setup_routes(self) -> None:
        """ルートのセットアップ"""

        @self.app.get("/api/control")
        async def control(
            alert: Optional[str] = Query(None, description="8桁のスイッチ状態パラメータ"),
            id: Optional[str] = Query(None, description="SIMカードID（オプション）")
        ):
            """
            スイッチ状態を受信してプログラム切り替えを実行

            Args:
                alert: 8桁のスイッチ状態（例: "10109999"）
                id: SIMカードID（ログ用、オプション）

            Returns:
                JSONResponse: 処理結果
            """
            logger.info(f"リクエスト受信: alert={alert}, id={id}")

            # alertパラメータの検証
            error = self._validate_alert(alert)
            if error:
                logger.warning(f"パラメータエラー: {error}")
                raise HTTPException(status_code=400, detail=error)

            # すべて9の場合は何もしない（状態問い合わせとして扱う）
            if re.fullmatch(r"9+", alert):
                logger.info("すべて9のため、処理をスキップします")
                return JSONResponse(
                    content={"status": "ok", "message": "No action (all 9s)"},
                    status_code=200
                )

            # コールバック実行
            if self.callback:
                try:
                    success = self.callback(alert)
                    if success:
                        # 上位4桁からプログラムIDを推測してレスポンスに含める
                        switch_pattern = alert[:4]
                        program_id = self._calculate_program_id(switch_pattern)
                        logger.info(f"プログラム切り替え成功: {program_id}")
                        return JSONResponse(
                            content={"status": "ok", "program": program_id},
                            status_code=200
                        )
                    else:
                        logger.error("プログラム切り替え失敗")
                        raise HTTPException(
                            status_code=500,
                            detail="Program_switch_failed"
                        )
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"コールバック実行中にエラー: {e}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Internal_error: {str(e)}"
                    )
            else:
                logger.warning("コールバックが設定されていません")
                return JSONResponse(
                    content={"status": "ok", "message": "No callback configured"},
                    status_code=200
                )

        @self.app.get("/health")
        async def health():
            """ヘルスチェックエンドポイント"""
            return JSONResponse(
                content={"status": "healthy"},
                status_code=200
            )

    def _validate_alert(self, alert: Optional[str]) -> Optional[str]:
        """
        alertパラメータを検証

        Args:
            alert: 検証対象のalertパラメータ

        Returns:
            エラーメッセージ（エラーがない場合はNone）
        """
        # alertが無い
        if not alert:
            return "Parameter_not_found"

        # alertの桁数が異常（8桁でない）
        if len(alert) != 8:
            return "Invalid_parameter_length"

        # alertに0/1/9以外が含まれる
        if re.search(r"[^019]", alert):
            return "Parameter_contains_invalid_value"

        # 下位4桁が9999でない場合は警告ログ（エラーにはしない）
        if alert[4:] != "9999":
            logger.warning(f"下位4桁が9999ではありません: {alert[4:]}")

        return None

    def _calculate_program_id(self, switch_pattern: str) -> str:
        """
        スイッチパターンからプログラムIDを計算

        Args:
            switch_pattern: 4桁のスイッチ状態（例: "1010"）

        Returns:
            プログラムID（"01"～"16"）
        """
        # "9"を"0"として扱う（未定義状態はOFFとみなす）
        pattern = switch_pattern.replace("9", "0")

        # 2進数として解釈
        try:
            pattern_number = int(pattern, 2)
            program_id = f"{pattern_number + 1:02d}"
            return program_id
        except ValueError:
            return "01"

    def set_callback(self, callback: Callable[[str], bool]) -> None:
        """
        コールバック関数を設定

        Args:
            callback: リクエスト受信時のコールバック関数
        """
        self.callback = callback

    def get_app(self) -> FastAPI:
        """
        FastAPIアプリケーションインスタンスを取得

        Returns:
            FastAPI: アプリケーションインスタンス
        """
        return self.app

    def run(self) -> None:
        """
        サーバを起動（ブロッキング）

        uvicornを使用してサーバを起動する
        """
        import uvicorn

        logger.info(f"HTTPサーバを起動します: http://{self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port)
