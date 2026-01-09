"""
ロギング設定モジュール
アプリケーション全体で使用する統一されたロガーを提供します。
"""
import logging
import sys
from pathlib import Path
from config import settings


def setup_logger(name: str = "tbbox_switcher", level: int = logging.INFO) -> logging.Logger:
    """
    ロガーをセットアップする

    Args:
        name: ロガーの名前
        level: ログレベル（デフォルト：INFO）

    Returns:
        設定済みのロガーインスタンス
    """
    logger = logging.getLogger(name)

    # 既に設定済みの場合はそのまま返す
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # コンソールハンドラーを作成
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # フォーマッターを作成
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # ハンドラーをロガーに追加
    logger.addHandler(console_handler)

    return logger


# デフォルトロガーインスタンス
# .envのLOG_LEVELを読み込んで設定
log_level_str = settings.LOG_LEVEL.upper()
log_level_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}
log_level = log_level_map.get(log_level_str, logging.INFO)
logger = setup_logger(level=log_level)
