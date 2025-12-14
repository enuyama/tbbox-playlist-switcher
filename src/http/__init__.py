"""
HTTPサーバモジュール
満空灯制御装置からのHTTPリクエストを受信し、プログラム切り替えをトリガーする
"""
from src.http.server import HTTPServer

__all__ = ["HTTPServer"]
