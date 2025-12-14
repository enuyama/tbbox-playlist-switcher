# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

TBBOX Playlist Switcherは、Raspberry Pi上で動作するアプリケーションです。満空灯制御装置（linkbase）からのHTTPリクエストを受信し、スイッチの状態に応じてTBBOXのプログラムを自動的に切り替えます。

## アーキテクチャ

### コアコンポーネント

1. **HTTPサーバ** (`src/http/server.py`)
   - FastAPI + uvicornを使用したHTTPサーバ
   - 満空灯制御装置からのHTTP GETリクエストを受信
   - `/api/control`エンドポイントでスイッチ状態を受信

2. **スイッチマッパー** (`src/mapper/switch_mapper.py`)
   - alertパラメータ（8桁）をプログラムID（"01"-"16"）に変換
   - 4つのスイッチの組み合わせで16パターンに対応
   - `config/switch_mapping.json`のマッピング設定を使用

3. **TBBOXクライアント** (`src/tbbox/`)
   - `client.py`: TBBOXの認証とセッション管理を処理
   - `playlist.py`: TCP/IP経由でプログラム切り替えコマンドを送信

4. **設定管理** (`config/`)
   - `settings.py`: HTTPサーバ設定、TBBOX接続情報を管理
   - `switch_mapping.json`: スイッチパターンとプログラムIDのマッピング定義

### アプリケーションフロー

```
[満空灯制御装置] --HTTP GET--> [HTTPサーバ] → [スイッチマッパー] → [TBBOXクライアント] → [TBBOX]
```

## HTTP API仕様

### エンドポイント

#### プログラム切り替え
```
GET /api/control?alert={8桁パラメータ}&id={SIMカードID}
```

**パラメータ:**
- `alert`: 8桁の数字（上位4桁がスイッチ状態、下位4桁は"9999"固定）
  - 各桁: 0=OFF, 1=ON, 9=非表示
- `id`: SIMカードID（オプション、ログ用）

**レスポンス:**
- 成功: `{"status": "ok", "program": "XX"}`
- エラー: `{"error": "エラーメッセージ"}`

#### ヘルスチェック
```
GET /health
```

### スイッチパターン対応表

| パターン | SW1 | SW2 | SW3 | SW4 | alert値 | プログラムID |
|---------|-----|-----|-----|-----|---------|--------------|
| 1 | 0 | 0 | 0 | 0 | 00009999 | 01 |
| 2 | 0 | 0 | 0 | 1 | 00019999 | 02 |
| 3 | 0 | 0 | 1 | 0 | 00109999 | 03 |
| 4 | 0 | 0 | 1 | 1 | 00119999 | 04 |
| 5 | 0 | 1 | 0 | 0 | 01009999 | 05 |
| 6 | 0 | 1 | 0 | 1 | 01019999 | 06 |
| 7 | 0 | 1 | 1 | 0 | 01109999 | 07 |
| 8 | 0 | 1 | 1 | 1 | 01119999 | 08 |
| 9 | 1 | 0 | 0 | 0 | 10009999 | 09 |
| 10 | 1 | 0 | 0 | 1 | 10019999 | 10 |
| 11 | 1 | 0 | 1 | 0 | 10109999 | 11 |
| 12 | 1 | 0 | 1 | 1 | 10119999 | 12 |
| 13 | 1 | 1 | 0 | 0 | 11009999 | 13 |
| 14 | 1 | 1 | 0 | 1 | 11019999 | 14 |
| 15 | 1 | 1 | 1 | 0 | 11109999 | 15 |
| 16 | 1 | 1 | 1 | 1 | 11119999 | 16 |

## 開発コマンド

### セットアップ
```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数テンプレートのコピー
cp .env.example .env
# .envファイルを編集してTBBOX接続情報を記入
```

### 環境変数設定（.env）

**HTTPサーバ設定:**
- `HTTP_HOST`: HTTPサーバの待ち受けホスト（デフォルト: 0.0.0.0）
- `HTTP_PORT`: HTTPサーバの待ち受けポート（デフォルト: 8080）

**TBBOX接続設定:**
- `TBBOX_IP`: TBBOXデバイスのIPアドレス
- `TBBOX_PORT`: TBBOXのポート番号（デフォルト: 5503）
- `TBBOX_DEVICE_SN`: デバイスのシリアル番号
- `TBBOX_USERNAME`: ログインユーザー名（デフォルト: 123456）
- `TBBOX_PASSWORD`: ログインパスワード（デフォルト: 123456）
- `TBBOX_LOGIN_COMMAND`: ログインコマンド（16進数）

設定後、「T Card Login Protocol Calculation」ツールを使用してログインコマンドを生成し、`TBBOX_LOGIN_COMMAND`に設定してください。

### 実行
```bash
# アプリケーションの起動
python main.py
```

### テスト
```bash
# 全テストの実行
pytest tests/

# 特定のテストファイルを実行
pytest tests/test_switch_mapper.py
pytest tests/test_http_server.py

# カバレッジ付きで実行
pytest --cov=src tests/
```

### 手動テスト（curl）
```bash
# 正常系: スイッチ1と3がON → プログラム11に切り替え
curl "http://localhost:8080/api/control?alert=10109999&id=test123"

# ヘルスチェック
curl "http://localhost:8080/health"
```

## TBBOX通信プロトコル

### プロトコル仕様
- **通信方式**: TCP/IP
- **デフォルトポート**: 5503
- **データ形式**: 16進数コマンド

### 認証
- TB 3.0以降、すべてのコマンド送信前にログインが必須
- ログインに必要な情報：
  - デバイスSN
  - ユーザー名
  - パスワード
- これらの情報は`.env`ファイルで管理
- ログインコマンドは「T Card Login Protocol Calculation」ツールで生成

### 主要機能コマンド

#### プログラム切り替え（01-16）
- プログラム名を"01"、"02"..."16"の形式で命名
- 各プログラムに対応する16進数コマンドが`config/settings.py`に定義済み

#### 音量調整
- 0%から100%まで10%刻みで調整可能
- 各音量レベルに対応する16進数コマンドが定義済み

#### 再生制御
- **一時停止**: `41564f4e0200000051521e000c0400000000000000000702`
- **再生再開**: `41564f4e0200000051521e000a0400000000000000000502`
- **停止**: `41564f4e0200000051521e000b0400000000000000000602`

### 接続制約
- TBBOXは同時に1つのログイン接続のみサポート
- Viplex ExpressとこのアプリケーションはTBBOXに同時接続できない

## 主要技術

- **FastAPI**: HTTPサーバフレームワーク
- **uvicorn**: ASGIサーバ
- **socket**: TBBOXとのTCP/IP通信
- **python-dotenv**: 環境変数管理
- **pydantic**: 設定値のバリデーション

## エラーハンドリング

### HTTPリクエストエラー
- alertパラメータなし: 400 `Parameter_not_found`
- alertが8桁でない: 400 `Invalid_parameter_length`
- alertに不正な文字: 400 `Parameter_contains_invalid_value`
- プログラム切り替え失敗: 500 `Program_switch_failed`

### TBBOX接続エラー
- 初回接続失敗時: エラーログを出力し、3秒後に再接続を試行（最大5回）
- 接続中に切断された場合: 自動再接続を試行

### プログラム切り替えエラー
- 存在しないプログラムID: エラーログを出力し、切り替えをスキップ
- コマンド送信失敗: エラーログを出力し、再送信を試行（最大3回）

## linkbase側の設定

満空灯制御装置（linkbase）の`/opt/light/config.json`で、本アプリのエンドポイントを設定:

```json
{
    "GET_URL": "http://localhost:8080/api/control",
    "SIM_ID": "XXXXXXXXXX",
    "Mode": "4",
    "MONITOR_INTERVAL": 0.2
}
```

**ポイント:**
- `GET_URL`: 本アプリのエンドポイント（同一マシンなので`localhost:8080`）
- `Mode`: `"4"`（全ポート通知モード）に設定

## 重要な注意事項

- アプリケーションはRaspberry Pi上で継続的に動作するよう設計されています
- HTTPサーバはポート8080で待ち受けます（linkbaseがポート80を使用するため）
- スイッチパターンのマッピングは`config/switch_mapping.json`で定義されています
- TBBOX接続情報（IP、ポート、SN、認証情報）は`.env`ファイルで管理
- `.env`ファイルには機密情報が含まれるため、絶対にコミットしないこと（.gitignoreに追加必須）
- すべてのログ出力は`src/utils/logger.py`で管理されています
- エントリポイントは`main.py`で、すべてのコンポーネントを統合します
- TBBOXのプログラム名は必ず"01"から"16"の2桁数字形式で命名すること
