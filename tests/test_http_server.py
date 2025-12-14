"""
HTTPServerのテスト
"""
import pytest
from fastapi.testclient import TestClient

from src.http.server import HTTPServer


class TestHTTPServer:
    """HTTPServerクラスのテスト"""

    @pytest.fixture
    def server(self):
        """テスト用サーバインスタンスを作成"""
        return HTTPServer(host="127.0.0.1", port=8080)

    @pytest.fixture
    def client(self, server):
        """テスト用クライアントを作成"""
        return TestClient(server.get_app())

    def test_health_endpoint(self, client):
        """ヘルスチェックエンドポイントのテスト"""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_control_endpoint_valid_alert(self, client):
        """有効なalertパラメータでのテスト"""
        callback_called = []

        def mock_callback(alert: str) -> bool:
            callback_called.append(alert)
            return True

        # コールバックを設定
        server = HTTPServer(callback=mock_callback)
        test_client = TestClient(server.get_app())

        response = test_client.get("/api/control?alert=10109999&id=test123")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["program"] == "11"
        assert len(callback_called) == 1
        assert callback_called[0] == "10109999"

    def test_control_endpoint_missing_alert(self, client):
        """alertパラメータがない場合のテスト"""
        response = client.get("/api/control")

        assert response.status_code == 400
        assert response.json()["detail"] == "Parameter_not_found"

    def test_control_endpoint_empty_alert(self, client):
        """alertパラメータが空の場合のテスト"""
        response = client.get("/api/control?alert=")

        assert response.status_code == 400
        assert response.json()["detail"] == "Parameter_not_found"

    def test_control_endpoint_invalid_length(self, client):
        """alertパラメータの長さが不正な場合のテスト"""
        # 短すぎる
        response = client.get("/api/control?alert=1234")
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid_parameter_length"

        # 長すぎる
        response = client.get("/api/control?alert=123456789")
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid_parameter_length"

    def test_control_endpoint_invalid_characters(self, client):
        """alertパラメータに不正な文字が含まれる場合のテスト"""
        response = client.get("/api/control?alert=12349999")

        assert response.status_code == 400
        assert response.json()["detail"] == "Parameter_contains_invalid_value"

    def test_control_endpoint_all_nines(self, client):
        """すべて9のalertパラメータのテスト"""
        callback_called = []

        def mock_callback(alert: str) -> bool:
            callback_called.append(alert)
            return True

        server = HTTPServer(callback=mock_callback)
        test_client = TestClient(server.get_app())

        response = test_client.get("/api/control?alert=99999999")

        assert response.status_code == 200
        assert response.json()["message"] == "No action (all 9s)"
        # コールバックは呼ばれない
        assert len(callback_called) == 0

    def test_control_endpoint_callback_failure(self):
        """コールバックが失敗した場合のテスト"""
        def failing_callback(alert: str) -> bool:
            return False

        server = HTTPServer(callback=failing_callback)
        client = TestClient(server.get_app())

        response = client.get("/api/control?alert=10109999")

        assert response.status_code == 500
        assert response.json()["detail"] == "Program_switch_failed"

    def test_control_endpoint_callback_exception(self):
        """コールバックが例外を発生させた場合のテスト"""
        def exception_callback(alert: str) -> bool:
            raise ValueError("Test exception")

        server = HTTPServer(callback=exception_callback)
        client = TestClient(server.get_app())

        response = client.get("/api/control?alert=10109999")

        assert response.status_code == 500
        assert "Internal_error" in response.json()["detail"]

    def test_control_endpoint_no_callback(self, client):
        """コールバックが設定されていない場合のテスト"""
        response = client.get("/api/control?alert=10109999")

        assert response.status_code == 200
        assert response.json()["message"] == "No callback configured"

    def test_control_endpoint_with_id_parameter(self):
        """idパラメータ付きのテスト"""
        callback_alerts = []

        def mock_callback(alert: str) -> bool:
            callback_alerts.append(alert)
            return True

        server = HTTPServer(callback=mock_callback)
        client = TestClient(server.get_app())

        response = client.get(
            "/api/control?alert=00019999&id=8942310222000544338"
        )

        assert response.status_code == 200
        assert response.json()["program"] == "02"

    def test_set_callback(self):
        """set_callbackメソッドのテスト"""
        server = HTTPServer()

        callback_calls = []

        def new_callback(alert: str) -> bool:
            callback_calls.append(alert)
            return True

        server.set_callback(new_callback)
        client = TestClient(server.get_app())

        response = client.get("/api/control?alert=11119999")

        assert response.status_code == 200
        assert len(callback_calls) == 1

    def test_calculate_program_id(self):
        """プログラムID計算のテスト"""
        server = HTTPServer()

        # 正常パターン
        assert server._calculate_program_id("0000") == "01"
        assert server._calculate_program_id("0001") == "02"
        assert server._calculate_program_id("1010") == "11"
        assert server._calculate_program_id("1111") == "16"

        # "9"を含むパターン（"0"として扱う）
        assert server._calculate_program_id("9000") == "01"
        assert server._calculate_program_id("1919") == "11"  # 1010


class TestHTTPServerAllPatterns:
    """全16パターンのテスト"""

    @pytest.fixture
    def server_with_callback(self):
        """コールバック付きサーバを作成"""
        received_alerts = []

        def callback(alert: str) -> bool:
            received_alerts.append(alert)
            return True

        server = HTTPServer(callback=callback)
        server.received_alerts = received_alerts
        return server

    @pytest.mark.parametrize(
        "alert,expected_program",
        [
            ("00009999", "01"),
            ("00019999", "02"),
            ("00109999", "03"),
            ("00119999", "04"),
            ("01009999", "05"),
            ("01019999", "06"),
            ("01109999", "07"),
            ("01119999", "08"),
            ("10009999", "09"),
            ("10019999", "10"),
            ("10109999", "11"),
            ("10119999", "12"),
            ("11009999", "13"),
            ("11019999", "14"),
            ("11109999", "15"),
            ("11119999", "16"),
        ],
    )
    def test_all_valid_patterns(
        self, server_with_callback, alert, expected_program
    ):
        """全16パターンが正しく処理されることをテスト"""
        client = TestClient(server_with_callback.get_app())

        response = client.get(f"/api/control?alert={alert}")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["program"] == expected_program


class TestHTTPServerValidation:
    """バリデーションのテスト"""

    @pytest.fixture
    def server(self):
        return HTTPServer()

    def test_validate_alert_valid(self, server):
        """有効なalertの検証テスト"""
        assert server._validate_alert("10109999") is None
        assert server._validate_alert("00009999") is None
        assert server._validate_alert("11119999") is None
        assert server._validate_alert("99999999") is None

    def test_validate_alert_none(self, server):
        """Noneのalertの検証テスト"""
        assert server._validate_alert(None) == "Parameter_not_found"

    def test_validate_alert_empty(self, server):
        """空のalertの検証テスト"""
        assert server._validate_alert("") == "Parameter_not_found"

    def test_validate_alert_invalid_length(self, server):
        """不正な長さのalertの検証テスト"""
        assert server._validate_alert("123") == "Invalid_parameter_length"
        assert server._validate_alert("123456789") == "Invalid_parameter_length"

    def test_validate_alert_invalid_chars(self, server):
        """不正な文字を含むalertの検証テスト"""
        assert (
            server._validate_alert("12349999")
            == "Parameter_contains_invalid_value"
        )
        assert (
            server._validate_alert("abcd9999")
            == "Parameter_contains_invalid_value"
        )
