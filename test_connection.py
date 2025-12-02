#!/usr/bin/env python3
"""
TBBOX接続テストスクリプト

TBBOXへの接続とログインが正常に行えるかを確認します。
このテストが成功すれば、main.pyでもTBBOXとの通信が正常に動作します。

使用方法:
    python test_connection.py
"""
import sys

from src.tbbox.client import TBBOXClient
from src.utils.logger import logger


def main():
    """メイン関数"""
    logger.info("=" * 60)
    logger.info("TBBOX接続テストを開始します")
    logger.info("=" * 60)

    # TBBOXクライアントを作成
    client = TBBOXClient()

    # 接続テスト
    logger.info("TBBOXに接続を試みます...")
    if client.connect():
        logger.info("✅ TBBOXへの接続に成功しました！")
        logger.info("")
        logger.info("次のステップ:")
        logger.info("  1. GPIO動作確認: python test_gpio.py")
        logger.info("  2. 統合テスト: python main.py")
        client.close()
        return 0
    else:
        logger.error("❌ TBBOXへの接続に失敗しました")
        logger.error("")
        logger.error("以下を確認してください：")
        logger.error("  1. TBBOXの電源が入っているか")
        logger.error("  2. TBBOXとRaspberry Piが同じネットワークにいるか")
        logger.error("  3. .envファイルのTBBOX_IPが正しいか")
        logger.error("  4. .envファイルのTBBOX_LOGIN_COMMANDが正しいか")
        logger.error("  5. Viplex Expressが接続していないか（TBBOXは同時接続不可）")
        return 1


if __name__ == "__main__":
    sys.exit(main())
