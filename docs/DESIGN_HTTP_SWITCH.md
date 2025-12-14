# TBBOX Playlist Switcher 改修設計書

## 1. 改修概要

### 1.1 背景
現在のシステムはRaspberry PiのGPIOピンを直接監視してTBBOXのプログラムを切り替えている。
本改修では、外部システム（満空灯制御装置）からのHTTPリクエストを受信してプログラムを切り替える方式に変更する。

### 1.2 改修目的
- 満空灯制御装置（Pi-protect）の「通知モード4」によるHTTP送信を受信
- 4つのスイッチの組み合わせパターンで16コンテンツに対応
- GPIO監視機能を削除し、HTTPサーバ機能を追加

## 2. システムアーキテクチャ

### 2.1 現行アーキテクチャ
```
[GPIOピン] → [GPIO監視] → [プログラムマッパー] → [TBBOXクライアント] → [TBBOX]
```

### 2.2 新アーキテクチャ
```
[満空灯制御装置] --HTTP GET--> [HTTPサーバ] → [スイッチパターンマッパー] → [TBBOXクライアント] → [TBBOX]
```

## 3. 通信プロトコル仕様

### 3.1 HTTPリクエスト（受信）

満空灯制御装置から受信するHTTPリクエストのフォーマット:

```
GET /api/control?alert=[8桁のパラメータ]&id=[SIMカードID]
```

#### パラメータ詳細

| パラメータ | 説明 | 例 |
|-----------|------|-----|
| alert | 8桁の数字（上位4桁がスイッチ状態、下位4桁は"9999"固定） | `10109999` |
| id | SIMカードのID（オプション、ログ用） | `8981100000000000000` |

#### alertパラメータの構造

```
[SW1][SW2][SW3][SW4][9][9][9][9]
  ↑    ↑    ↑    ↑    ↑ 固定値
  │    │    │    │
  │    │    │    └── スイッチ4の状態 (0/1/9)
  │    │    └─────── スイッチ3の状態 (0/1/9)
  │    └──────────── スイッチ2の状態 (0/1/9)
  └───────────────── スイッチ1の状態 (0/1/9)
```

- `0`: 入力なし（OFF）
- `1`: 入力あり（ON）
- `9`: 状態非表示（このアプリでは無視または前回値保持）

### 3.2 HTTPレスポンス

| ステータス | 意味 | レスポンスボディ |
|-----------|------|------------------|
| 200 | 成功 | `{"status": "ok", "program": "XX"}` |
| 400 | パラメータエラー | `{"error": "エラーメッセージ"}` |
| 500 | 内部エラー | `{"error": "エラーメッセージ"}` |

## 4. スイッチパターンとコンテンツ対応表

4つのスイッチ（SW1-SW4）の組み合わせで16パターン（2^4 = 16）を表現する。

| パターン番号 | SW1 | SW2 | SW3 | SW4 | alert値 | プログラムID |
|-------------|-----|-----|-----|-----|---------|--------------|
| 1 | 0 | 0 | 0 | 0 | `00009999` | 01 |
| 2 | 0 | 0 | 0 | 1 | `00019999` | 02 |
| 3 | 0 | 0 | 1 | 0 | `00109999` | 03 |
| 4 | 0 | 0 | 1 | 1 | `00119999` | 04 |
| 5 | 0 | 1 | 0 | 0 | `01009999` | 05 |
| 6 | 0 | 1 | 0 | 1 | `01019999` | 06 |
| 7 | 0 | 1 | 1 | 0 | `01109999` | 07 |
| 8 | 0 | 1 | 1 | 1 | `01119999` | 08 |
| 9 | 1 | 0 | 0 | 0 | `10009999` | 09 |
| 10 | 1 | 0 | 0 | 1 | `10019999` | 10 |
| 11 | 1 | 0 | 1 | 0 | `10109999` | 11 |
| 12 | 1 | 0 | 1 | 1 | `10119999` | 12 |
| 13 | 1 | 1 | 0 | 0 | `11009999` | 13 |
| 14 | 1 | 1 | 0 | 1 | `11019999` | 14 |
| 15 | 1 | 1 | 1 | 0 | `11109999` | 15 |
| 16 | 1 | 1 | 1 | 1 | `11119999` | 16 |

### 4.1 パターン計算方法

スイッチ状態からプログラムIDへの変換ロジック:
```python
# SW1が最上位ビット、SW4が最下位ビット
pattern_number = (SW1 * 8) + (SW2 * 4) + (SW3 * 2) + (SW4 * 1)
program_id = f"{pattern_number + 1:02d}"  # "01" ~ "16"
```

### 4.2 送信側（満空灯制御装置）との対応

満空灯制御装置のソースコード（link_base）では以下の変換が行われている:

```python
INPUT_PORT = [8, 9, 10, 11]  # 物理ポート番号
rev_input = [1 - i for i in reversed(input_list)]
```

**物理ポートとalert桁位置の対応:**

| alert桁位置 | 本設計での名称 | 物理ポート番号 | 備考 |
|-------------|---------------|----------------|------|
| 1桁目 | SW1 | ポート11 | reversed()により逆順 |
| 2桁目 | SW2 | ポート10 | |
| 3桁目 | SW3 | ポート9 | |
| 4桁目 | SW4 | ポート8 | |

**入力値の反転について:**
- 送信側で `1 - i` により反転されている
- 物理的にON（接点クローズ）→ alert値は `0`
- 物理的にOFF（接点オープン）→ alert値は `1`

**受信側（本アプリ）での解釈:**
- alertの値をそのまま使用する（再反転は不要）
- `0` = OFF状態として扱う
- `1` = ON状態として扱う

## 5. ファイル構成（変更後）

```
tbbox-playlist-switcher/
├── main.py                      # エントリーポイント（修正）
├── config/
│   ├── __init__.py
│   ├── settings.py              # 設定（修正: HTTP関連追加）
│   └── switch_mapping.json      # スイッチパターンマッピング（新規）
├── src/
│   ├── __init__.py
│   ├── http/                    # HTTPサーバ（新規ディレクトリ）
│   │   ├── __init__.py
│   │   └── server.py            # HTTPサーバ実装
│   ├── mapper/
│   │   ├── __init__.py
│   │   └── switch_mapper.py     # スイッチパターンマッパー（新規）
│   ├── tbbox/                   # 変更なし
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── playlist.py
│   └── utils/
│       ├── __init__.py
│       └── logger.py
├── tests/
│   ├── __init__.py
│   ├── test_http_server.py      # HTTPサーバテスト（新規）
│   └── test_switch_mapper.py    # スイッチマッパーテスト（新規）
└── docs/
    └── DESIGN_HTTP_SWITCH.md    # 本設計書
```

### 5.1 削除対象ファイル

- `src/gpio/` ディレクトリ全体
- `src/mapper/gpio_mapper.py`
- `config/gpio_mapping.json`
- `tests/test_gpio_monitor.py`
- `tests/test_gpio_mapper.py`
- `test_gpio.py`

## 6. 主要コンポーネント設計

### 6.1 HTTPサーバ (`src/http/server.py`)

```python
class HTTPServer:
    """HTTPリクエストを受信するサーバ"""

    def __init__(self, host: str, port: int, callback: Callable):
        """
        Args:
            host: 待ち受けホスト（デフォルト: "0.0.0.0"）
            port: 待ち受けポート（デフォルト: 80）
            callback: リクエスト受信時のコールバック関数
        """
        pass

    def start(self) -> None:
        """サーバを起動"""
        pass

    def stop(self) -> None:
        """サーバを停止"""
        pass
```

#### エンドポイント
- `GET /api/control`: スイッチ状態を受信してプログラム切り替え
- `GET /health`: ヘルスチェック用（オプション）

### 6.2 スイッチパターンマッパー (`src/mapper/switch_mapper.py`)

```python
class SwitchMapper:
    """スイッチパターンをプログラムIDに変換"""

    def parse_alert(self, alert: str) -> Optional[str]:
        """
        alertパラメータを解析してプログラムIDを返す

        Args:
            alert: 8桁のalertパラメータ（例: "10109999"）

        Returns:
            プログラムID（"01"～"16"）、エラー時はNone
        """
        pass

    def _switch_pattern_to_program_id(self, sw1: int, sw2: int, sw3: int, sw4: int) -> str:
        """スイッチ状態からプログラムIDを計算"""
        pass
```

### 6.3 設定ファイル追加項目 (`config/settings.py`)

```python
# HTTPサーバ設定
HTTP_HOST = os.getenv("HTTP_HOST", "0.0.0.0")
HTTP_PORT = int(os.getenv("HTTP_PORT", "8080"))  # linkbaseがポート80を使用するため

# スイッチ状態で"9"を受信した場合の動作
# "ignore": 何もしない
# "keep_previous": 前回のスイッチ状態を保持して計算
SWITCH_NINE_BEHAVIOR = os.getenv("SWITCH_NINE_BEHAVIOR", "ignore")
```

### 6.4 マッピング設定ファイル (`config/switch_mapping.json`)

```json
{
  "0000": "01",
  "0001": "02",
  "0010": "03",
  "0011": "04",
  "0100": "05",
  "0101": "06",
  "0110": "07",
  "0111": "08",
  "1000": "09",
  "1001": "10",
  "1010": "11",
  "1011": "12",
  "1100": "13",
  "1101": "14",
  "1110": "15",
  "1111": "16"
}
```

## 7. アプリケーションフロー

### 7.1 起動シーケンス

```
1. 設定ファイル読み込み
2. TBBOXクライアント初期化・接続
3. PlaylistController初期化
4. SwitchMapper初期化
5. HTTPサーバ起動（ポート8080で待ち受け）
6. リクエスト待機
```

### 7.2 リクエスト処理フロー

```
1. HTTPリクエスト受信
   GET /api/control?alert=10109999&id=xxx

2. パラメータ検証
   - alertが8桁か確認
   - 各桁が0/1/9のいずれかか確認
   - 下位4桁が9999か確認

3. スイッチ状態解析
   - 上位4桁を取得: "1010"
   - "9"を含む場合の処理（設定に従う）

4. プログラムID決定
   - パターン計算: 1*8 + 0*4 + 1*2 + 0*1 = 10
   - プログラムID: "11"

5. TBBOX切り替え実行
   - PlaylistController.switch_program("11")

6. HTTPレスポンス返却
   {"status": "ok", "program": "11"}
```

## 8. エラーハンドリング

### 8.1 HTTPリクエストエラー

| エラー種別 | HTTPステータス | レスポンス |
|-----------|---------------|-----------|
| alertパラメータなし | 400 | `{"error": "Parameter_not_found"}` |
| alertが8桁でない | 400 | `{"error": "Invalid_parameter_length"}` |
| alertに0/1/9以外を含む | 400 | `{"error": "Parameter_contains_invalid_value"}` |
| すべてのスイッチが9 | 400 | `{"error": "All_switches_undefined"}` |

### 8.2 TBBOX通信エラー

- 接続エラー: 自動再接続を試行（既存実装を継続）
- コマンド送信エラー: 再送信を試行（既存実装を継続）
- エラー時はHTTP 500を返却

## 9. 環境変数設定（.env）

```bash
# TBBOXデバイスのIPアドレス
TBBOX_IP=192.168.1.100

# TBBOXのポート番号
TBBOX_PORT=5503

# デバイスのシリアル番号
TBBOX_DEVICE_SN=XXXXX

# ログインユーザー名
TBBOX_USERNAME=123456

# ログインパスワード
TBBOX_PASSWORD=123456

# ログインコマンド（16進数）
TBBOX_LOGIN_COMMAND=XXXX

# HTTPサーバ設定（linkbaseがポート80を使用するため8080を使用）
HTTP_HOST=0.0.0.0
HTTP_PORT=8080

# スイッチ"9"の動作（ignore / keep_previous）
SWITCH_NINE_BEHAVIOR=ignore

# ログレベル
LOG_LEVEL=INFO
```

## 10. 実装タスク

### 10.1 新規作成
- [ ] `src/http/__init__.py`
- [ ] `src/http/server.py` - HTTPサーバ実装
- [ ] `src/mapper/switch_mapper.py` - スイッチパターンマッパー
- [ ] `config/switch_mapping.json` - マッピング設定
- [ ] `tests/test_http_server.py` - HTTPサーバテスト
- [ ] `tests/test_switch_mapper.py` - マッパーテスト

### 10.2 修正
- [ ] `main.py` - HTTPサーバ起動に変更
- [ ] `config/settings.py` - HTTP関連設定追加
- [ ] `.env.example` - 新しい環境変数追加
- [ ] `CLAUDE.md` - ドキュメント更新
- [ ] `requirements.txt` - 依存関係変更（下記参照）

### 10.4 依存関係の変更 (`requirements.txt`)

**削除:**
```
RPi.GPIO==0.7.1  # GPIO不要のため削除
```

**追加:**
```
fastapi==0.104.1   # HTTPサーバフレームワーク
uvicorn==0.24.0    # ASGIサーバ
```

**理由:** 送信側（満空灯制御装置）がFastAPI + uvicornを使用しているため、同じ構成にすることで整合性を保つ。

### 10.3 削除
- [ ] `src/gpio/` ディレクトリ
- [ ] `src/mapper/gpio_mapper.py`
- [ ] `config/gpio_mapping.json`
- [ ] `tests/test_gpio_monitor.py`
- [ ] `tests/test_gpio_mapper.py`
- [ ] `test_gpio.py`

## 11. テスト方法

### 11.1 単体テスト

```bash
# 全テスト実行
pytest tests/

# 特定テスト実行
pytest tests/test_switch_mapper.py
pytest tests/test_http_server.py
```

### 11.2 手動テスト（curl）

```bash
# 正常系: スイッチ1と3がON → プログラム11に切り替え
curl "http://localhost:8080/api/control?alert=10109999&id=test123"

# 異常系: パラメータなし
curl "http://localhost:8080/api/control?alert="

# 異常系: 不正な値
curl "http://localhost:8080/api/control?alert=12109999"
```

## 12. 追加検討事項

### 12.1 "9"（状態非表示）の扱い

PDFの仕様では「9」は「状態非表示」を意味する。選択肢:

1. **ignore（推奨）**: "9"を含むリクエストは無視してエラーを返す
2. **keep_previous**: 前回のスイッチ状態を保持して計算に使用

→ 要件に応じて`SWITCH_NINE_BEHAVIOR`設定で切り替え可能にする

### 12.2 同時リクエストの処理

複数のHTTPリクエストが短時間で来た場合の処理:
- 最新のリクエストを優先
- デバウンス機能の検討（例: 300ms以内の重複リクエストは無視）

### 12.3 ヘルスチェックエンドポイント

監視用のヘルスチェックエンドポイントを追加するか検討:
```
GET /health
→ {"status": "healthy", "tbbox_connected": true}
```

## 13. 補足

### 13.1 既存TBBOXコマンドの継続使用

現在の`config/settings.py`に定義されているプログラムコマンド（01-20）はそのまま使用する。
16コンテンツへの対応なので、プログラム01-16のみ使用する。

### 13.2 linkbase側の設定変更

linkbase（満空灯制御装置）の`/opt/light/config.json`で、`GET_URL`を本アプリのエンドポイントに設定する必要がある。

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
