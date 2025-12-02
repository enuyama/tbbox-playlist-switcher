#!/usr/bin/env python3
"""
プログラム直接切り替えスクリプト

GPIOを使わずに、指定したプログラムに即座に切り替えます。
プログラム番号はスクリプト内でハードコード。

使用方法:
    python switch_program.py

プログラム番号の変更:
    スクリプト内の TARGET_PROGRAM_ID を変更してください
"""
import sys

from src.tbbox.client import TBBOXClient
from src.tbbox.playlist import PlaylistController
from src.utils.logger import logger


# ========================================
# 設定: ここでプログラム番号を指定
# ========================================
TARGET_PROGRAM_ID = "01"  # ← ここを変更するだけ（"01"～"20"）


def main():
    """メイン関数"""
    logger.info("=" * 60)
    logger.info(f"プログラム '{TARGET_PROGRAM_ID}' への切り替えを開始します")
    logger.info("=" * 60)

    try:
        # TBBOXクライアントを初期化
        logger.info("TBBOXクライアントを初期化しています...")
        client = TBBOXClient()

        # 接続
        logger.info("TBBOXに接続中...")
        if not client.connect():
            logger.error("❌ TBBOXへの接続に失敗しました")
            logger.error("")
            logger.error("以下を確認してください：")
            logger.error("  1. TBBOXの電源が入っているか")
            logger.error("  2. TBBOXとRaspberry Piが同じネットワークにいるか")
            logger.error("  3. .envファイルのTBBOX_IPが正しいか")
            logger.error("  4. .envファイルのTBBOX_LOGIN_COMMANDが正しいか")
            logger.error("  5. Viplex Expressが接続していないか（TBBOXは同時接続不可）")
            return 1

        # PlaylistControllerを初期化
        controller = PlaylistController(client)
        logger.info("PlaylistControllerを初期化しました")

        # プログラム切り替えを実行
        logger.info("")
        logger.info(f"プログラム '{TARGET_PROGRAM_ID}' への切り替えを実行します...")
        if controller.switch_program(TARGET_PROGRAM_ID):
            logger.info("")
            logger.info("=" * 60)
            logger.info(f"✅ プログラム '{TARGET_PROGRAM_ID}' への切り替えに成功しました")
            logger.info("=" * 60)
            controller.close()
            return 0
        else:
            logger.error("")
            logger.error("=" * 60)
            logger.error(f"❌ プログラム '{TARGET_PROGRAM_ID}' への切り替えに失敗しました")
            logger.error("=" * 60)
            logger.error("")
            logger.error("考えられる原因：")
            logger.error(f"  1. プログラム '{TARGET_PROGRAM_ID}' がTBBOXに存在しない")
            logger.error("  2. プログラム名が正しくない（2桁の数字形式: '01', '02', etc.）")
            logger.error("  3. TBBOXとの接続が切断された")
            controller.close()
            return 1

    except KeyboardInterrupt:
        logger.info("")
        logger.info("ユーザーによって中断されました")
        return 130
    except Exception as e:
        logger.error("")
        logger.error(f"予期しないエラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
