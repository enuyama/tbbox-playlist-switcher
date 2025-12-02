"""
GPIOMonitorのテスト
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.gpio.monitor import GPIOMonitor


class TestGPIOMonitor:
    """GPIOMonitorクラスのテストケース"""

    @pytest.fixture
    def pin_mapping(self):
        """テスト用のピンマッピング"""
        return {
            18: "01",
            23: "02",
            24: "03"
        }

    @pytest.fixture
    def callback_mock(self):
        """コールバック関数のモック"""
        return Mock()

    @patch('src.gpio.monitor.GPIO_AVAILABLE', False)
    def test_init_without_gpio(self, pin_mapping, callback_mock):
        """GPIO未使用環境での初期化テスト"""
        monitor = GPIOMonitor(pin_mapping, callback_mock)

        assert monitor.pin_mapping == pin_mapping
        assert monitor.callback == callback_mock
        assert monitor._is_monitoring is False

    @patch('src.gpio.monitor.GPIO_AVAILABLE', False)
    def test_setup_mock_mode(self, pin_mapping, callback_mock):
        """モックモードでのセットアップテスト"""
        monitor = GPIOMonitor(pin_mapping, callback_mock)

        # モックモードではエラーが発生しないことを確認
        monitor.setup()

    @patch('src.gpio.monitor.GPIO_AVAILABLE', False)
    def test_cleanup_mock_mode(self, pin_mapping, callback_mock):
        """モックモードでのクリーンアップテスト"""
        monitor = GPIOMonitor(pin_mapping, callback_mock)

        # モックモードではエラーが発生しないことを確認
        monitor.cleanup()

    @patch('src.gpio.monitor.GPIO_AVAILABLE', False)
    def test_gpio_callback(self, pin_mapping, callback_mock):
        """GPIOコールバックのテスト"""
        monitor = GPIOMonitor(pin_mapping, callback_mock)

        # GPIOピン18の変化をシミュレート
        monitor._gpio_callback(18)

        # コールバックが呼ばれたことを確認
        callback_mock.assert_called_once_with(18, "01")

    @patch('src.gpio.monitor.GPIO_AVAILABLE', False)
    def test_gpio_callback_unknown_pin(self, pin_mapping, callback_mock):
        """未登録ピンに対するGPIOコールバックのテスト"""
        monitor = GPIOMonitor(pin_mapping, callback_mock)

        # 未登録のGPIOピン99の変化をシミュレート
        monitor._gpio_callback(99)

        # コールバックが呼ばれないことを確認
        callback_mock.assert_not_called()

    @patch('src.gpio.monitor.GPIO_AVAILABLE', False)
    def test_context_manager(self, pin_mapping, callback_mock):
        """コンテキストマネージャーとしての利用テスト"""
        with GPIOMonitor(pin_mapping, callback_mock) as monitor:
            assert monitor is not None
            assert monitor._is_monitoring is False
