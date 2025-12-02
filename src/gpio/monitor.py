"""
GPIO監視モジュール
Raspberry PiのGPIOピンの状態変化を監視し、イベントをトリガーする
"""
from typing import Callable, Dict
import time

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    # Raspberry Pi以外の環境ではモックを使用
    GPIO_AVAILABLE = False
    GPIO = None

from src.utils.logger import logger
from config import settings


class GPIOMonitor:
    """
    GPIOピンの状態変化を監視するクラス

    割り込みを使用してGPIOピンの状態変化を検出し、
    ピンが変化したときにコールバック関数を呼び出す
    """

    def __init__(self, pin_mapping: Dict[int, str], callback: Callable[[int, str], None]):
        """
        GPIOMonitorの初期化

        Args:
            pin_mapping: {pin番号: プログラムID}のマッピング
            callback: ピン変化時に呼び出されるコールバック関数
                      callback(pin: int, program_id: str)の形式
        """
        self.pin_mapping = pin_mapping
        self.callback = callback
        self._is_monitoring = False

        if not GPIO_AVAILABLE:
            logger.warning("RPi.GPIOが利用できません。モックモードで動作します。")
            logger.warning("実際のGPIO監視は行われません。")

    def _get_gpio_constant(self, constant_name: str):
        """
        文字列設定をGPIO定数に変換する

        Args:
            constant_name: GPIO定数の文字列名
                          (例: "PUD_DOWN", "RISING", "FALLING")

        Returns:
            対応するGPIO定数

        Raises:
            AttributeError: 無効な定数名の場合
        """
        if not GPIO_AVAILABLE:
            return None

        try:
            return getattr(GPIO, constant_name)
        except AttributeError:
            logger.error(
                f"無効なGPIO定数名: {constant_name}"
            )
            raise

    def setup(self) -> None:
        """GPIOピンのセットアップを行う"""
        if not GPIO_AVAILABLE:
            logger.info("モックモード: GPIO setup をスキップします")
            return

        try:
            # GPIOモードを設定（BCM番号を使用）
            GPIO.setmode(GPIO.BCM)

            # 警告を無効化
            GPIO.setwarnings(False)

            # GPIO設定を取得
            pull_resistor = self._get_gpio_constant(
                settings.GPIO_PULL_RESISTOR
            )
            edge_detection = self._get_gpio_constant(
                settings.GPIO_EDGE_DETECTION
            )
            debounce_time = settings.GPIO_DEBOUNCE_TIME

            # 各ピンをセットアップ
            for pin in self.pin_mapping.keys():
                try:
                    # 入力ピンとして設定
                    GPIO.setup(pin, GPIO.IN, pull_up_down=pull_resistor)

                    # エッジ検出の割り込みを追加
                    GPIO.add_event_detect(
                        pin,
                        edge_detection,
                        callback=self._gpio_callback,
                        bouncetime=debounce_time
                    )

                    logger.info(f"GPIO{pin}を監視対象として設定しました")

                except Exception as e:
                    logger.error(f"GPIO{pin}のセットアップに失敗しました: {e}")
                    raise

            logger.info(
                f"GPIO監視を開始しました "
                f"(監視ピン: {list(self.pin_mapping.keys())}, "
                f"エッジ検出: {settings.GPIO_EDGE_DETECTION}, "
                f"デバウンス: {debounce_time}ms)"
            )

        except Exception as e:
            logger.error(f"GPIOセットアップ中にエラーが発生しました: {e}")
            self.cleanup()
            raise

    def _gpio_callback(self, pin: int) -> None:
        """
        GPIOピンの状態変化時に呼び出されるコールバック関数

        Args:
            pin: 変化したGPIOピン番号
        """
        program_id = self.pin_mapping.get(pin)

        if program_id is None:
            logger.warning(f"未登録のGPIOピン{pin}が検出されました")
            return

        logger.info(f"GPIO{pin}の変化を検出しました → プログラムID: {program_id}")

        try:
            # ユーザー定義のコールバックを実行
            self.callback(pin, program_id)
        except Exception as e:
            logger.error(f"コールバック実行中にエラーが発生しました: {e}")

    def start(self) -> None:
        """
        GPIO監視を開始する

        このメソッドは呼び出されるとブロックし、監視を継続する
        """
        self._is_monitoring = True
        logger.info("GPIO監視を開始します")

        try:
            while self._is_monitoring:
                # メインループ（割り込みベースなので待機のみ）
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("キーボード割り込みを検出しました")
            self.stop()

    def stop(self) -> None:
        """GPIO監視を停止する"""
        self._is_monitoring = False
        logger.info("GPIO監視を停止します")

    def cleanup(self) -> None:
        """GPIOリソースをクリーンアップする"""
        if not GPIO_AVAILABLE:
            logger.info("モックモード: GPIO cleanup をスキップします")
            return

        try:
            GPIO.cleanup()
            logger.info("GPIOクリーンアップが完了しました")
        except Exception as e:
            logger.error(f"GPIOクリーンアップ中にエラーが発生しました: {e}")

    def __enter__(self):
        """コンテキストマネージャーのエントリー"""
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーのイグジット"""
        self.stop()
        self.cleanup()
