#!/usr/bin/env python3
"""
GPIO動作テストスクリプト

GPIOピンの監視が正常に動作するかを確認します。
このテストが成功すれば、main.pyでもGPIO検出が正常に動作します。

使用方法:
    python test_gpio.py

配線:
    - GPIO 18 (物理ピン12) ←→ GND (物理ピン14) をスイッチで接続
    - GPIO 23 (物理ピン16) ←→ GND (物理ピン14) をスイッチで接続
    - GPIO 24 (物理ピン18) ←→ GND (物理ピン14) をスイッチで接続

終了:
    Ctrl+C で終了
"""
import RPi.GPIO as GPIO
import time
import sys


# 使用するGPIOピン（config/gpio_mapping.jsonと同じ）
TEST_PINS = [18, 23, 24]


def gpio_callback(pin):
    """GPIO変化時のコールバック"""
    print(f"✅ GPIO {pin} が検出されました！（物理ピン: {get_physical_pin(pin)}）")


def get_physical_pin(gpio_pin):
    """GPIOピン番号から物理ピン番号を取得"""
    mapping = {18: 12, 23: 16, 24: 18}
    return mapping.get(gpio_pin, "不明")


def main():
    """メイン関数"""
    print("=" * 60)
    print("GPIO動作テストを開始します")
    print("=" * 60)
    print()
    print("テスト対象のピン：")
    for pin in TEST_PINS:
        print(f"  - GPIO {pin}（物理ピン {get_physical_pin(pin)}）")
    print()
    print("設定:")
    print("  - プルアップ/ダウン: PUD_DOWN")
    print("  - エッジ検出: RISING (LOW→HIGH)")
    print("  - デバウンス: 300ms")
    print()
    print("各GPIOピンをGNDに接続すると検出されます。")
    print("終了するには Ctrl+C を押してください。")
    print("=" * 60)
    print()

    try:
        # GPIO初期化
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # 各ピンを設定
        for pin in TEST_PINS:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(pin, GPIO.RISING, callback=gpio_callback, bouncetime=300)
            print(f"✓ GPIO {pin} の監視を開始しました")

        print()
        print("スイッチを押してテストしてください...")
        print()

        # 無限ループで待機
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nテストを終了します")
        print()
        print("次のステップ:")
        print("  1. TBBOX接続確認が未実施の場合: python test_connection.py")
        print("  2. 両方のテストが成功した場合: python main.py")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print()
        print("エラーの原因:")
        print("  - GPIO権限がない → sudo usermod -a -G gpio $USER を実行して再起動")
        print("  - 配線が間違っている → 配線を確認してください")
        return 1
    finally:
        GPIO.cleanup()
        print("GPIOクリーンアップ完了")

    return 0


if __name__ == "__main__":
    sys.exit(main())
