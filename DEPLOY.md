# TBBOX Playlist Switcher - デプロイ・セットアップ手順

このドキュメントでは、Raspberry PiへのTBBOX Playlist Switcherのデプロイとセットアップ手順を説明します。

## 目次
- [前提条件](#前提条件)
- [1. Raspberry Piの準備](#1-raspberry-piの準備)
- [2. プロジェクトファイルの転送](#2-プロジェクトファイルの転送)
- [3. Python環境のセットアップ](#3-python環境のセットアップ)
- [4. 環境変数の設定](#4-環境変数の設定)
- [5. 動作確認](#5-動作確認)
- [6. 自動起動の設定](#6-自動起動の設定)
- [7. トラブルシューティング](#7-トラブルシューティング)

---

## 前提条件

### ハードウェア
- Raspberry Pi（Raspberry Pi 3以降推奨）
- microSDカード（16GB以上推奨）
- 電源アダプタ
- ネットワーク接続（有線LAN推奨）

### ソフトウェア
- Raspberry Pi OS（Debian系）
- Python 3.9以上
- インターネット接続（初回セットアップ時）

### ネットワーク情報（事前に確認）
- Raspberry PiのIPアドレス
- TBBOXのIPアドレスとポート番号
- （オプション）満空灯制御装置（linkbase）のIPアドレス

---

## 1. Raspberry Piの準備

### 1.1 OSのインストール

Raspberry Pi OSが未インストールの場合、Raspberry Pi Imagerを使用してインストールします。

1. [Raspberry Pi Imager](https://www.raspberrypi.com/software/)をダウンロード
2. microSDカードにRaspberry Pi OS（推奨：Lite版）を書き込む
3. SSH有効化（オプション設定でSSHを有効にする）
4. ユーザー名とパスワードを設定

### 1.2 初回起動とネットワーク設定

```bash
# Raspberry Piにログイン（デフォルトユーザー：pi）
ssh pi@<raspberry_pi_ip>

# システムアップデート
sudo apt update
sudo apt upgrade -y

# 必要なパッケージのインストール
sudo apt install -y git python3-pip python3-venv
```

### 1.3 固定IPアドレスの設定（推奨）

```bash
# ネットワーク設定ファイルを編集
sudo nano /etc/dhcpcd.conf

# 以下を追記（例：192.168.0.100に固定）
interface eth0
static ip_address=192.168.0.100/24
static routers=192.168.0.1
static domain_name_servers=192.168.0.1 8.8.8.8

# 再起動して設定を反映
sudo reboot
```

---

## 2. プロジェクトファイルの転送

### 方法1: Gitリポジトリからクローン（推奨）

```bash
# ホームディレクトリに移動
cd ~

# リポジトリをクローン
git clone <repository_url> tbbox-playlist-switcher

# プロジェクトディレクトリに移動
cd tbbox-playlist-switcher
```

### 方法2: ローカルからSCPで転送

開発マシンから実行：

```bash
# プロジェクトディレクトリ全体を転送
scp -r /path/to/tbbox-playlist-switcher pi@<raspberry_pi_ip>:~/

# Raspberry Piにログイン後、ディレクトリに移動
ssh pi@<raspberry_pi_ip>
cd ~/tbbox-playlist-switcher
```

---

## 3. Python環境のセットアップ

### 3.1 仮想環境の作成

```bash
# プロジェクトディレクトリで実行
cd ~/tbbox-playlist-switcher

# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# (venv)が表示されることを確認
```

### 3.2 依存パッケージのインストール

```bash
# pipをアップグレード
pip install --upgrade pip

# 必要なパッケージをインストール
pip install -r requirements.txt
```

### 3.3 インストール確認

```bash
# インストールされたパッケージを確認
pip list

# 以下が含まれていることを確認
# - fastapi
# - uvicorn
# - python-dotenv
# - pydantic
```

---

## 4. 環境変数の設定

### 4.1 .envファイルの作成

```bash
# .env.exampleをコピー
cp .env.example .env

# .envファイルを編集
nano .env
```

### 4.2 必須設定項目

`.env`ファイルに以下を設定：

```bash
# TBBOX接続設定
TBBOX_IP=192.168.0.58          # TBBOXのIPアドレス
TBBOX_PORT=16603               # TBBOXのポート番号（デフォルト: 5503）

# TBBOX接続をスキップする場合（テスト時など）
TBBOX_SKIP_CONNECTION=false    # 本番環境ではfalse

# ログインコマンド（16進数）
# 「T Card Login Protocol Calculation」ツールで生成したコマンドを設定
TBBOX_LOGIN_COMMAND=41564f4e...（生成したコマンド全体）

# HTTPサーバ設定（オプション）
HTTP_HOST=0.0.0.0              # 全インターフェースで待ち受け
HTTP_PORT=8080                 # ポート番号（linkbaseがポート80を使用するため）

# ログ設定（オプション）
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR
```

### 4.3 ログインコマンドの生成

1. 「T Card Login Protocol Calculation」ツールを使用
2. 以下の情報を入力：
   - デバイスSN
   - ユーザー名（デフォルト: admin）
   - パスワード
3. 生成された16進数コマンドを`TBBOX_LOGIN_COMMAND`に設定

### 4.4 スイッチマッピングの確認

```bash
# スイッチマッピング設定を確認
cat config/switch_mapping.json

# 必要に応じて編集
nano config/switch_mapping.json
```

---

## 5. 動作確認

### 5.1 アプリケーションの起動

```bash
# 仮想環境が有効化されていることを確認
source venv/bin/activate

# アプリケーションを起動
python main.py

# 以下のようなログが表示されることを確認
# ============================================================
# TBBOX Playlist Switcher を起動しています...
# ============================================================
# HTTPサーバを起動します。終了するにはCtrl+Cを押してください。
# エンドポイント: http://0.0.0.0:8080/api/control
```

### 5.2 ヘルスチェック

別のターミナルから、または開発マシンから実行：

```bash
# ヘルスチェック
curl http://<raspberry_pi_ip>:8080/health

# レスポンス例: {"status": "ok"}
```

### 5.3 動作テスト

```bash
# プログラム切り替えテスト（スイッチ1と3がON → プログラム11）
curl "http://<raspberry_pi_ip>:8080/api/control?alert=10109999&id=test123"

# レスポンス例: {"status": "ok", "program": "11"}
```

### 5.4 ログの確認

```bash
# アプリケーションのログを確認
# main.pyを実行したターミナルに出力されます
```

---

## 6. 自動起動の設定

systemdサービスとして登録し、Raspberry Pi起動時に自動的にアプリケーションを起動します。

### 6.1 サービスファイルの作成

```bash
# サービスファイルを作成
sudo nano /etc/systemd/system/tbbox-playlist-switcher.service
```

以下の内容を記述：

```ini
[Unit]
Description=TBBOX Playlist Switcher
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/tbbox-playlist-switcher
Environment="PATH=/home/pi/tbbox-playlist-switcher/venv/bin"
ExecStart=/home/pi/tbbox-playlist-switcher/venv/bin/python main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

注意: `User`と`WorkingDirectory`のパスは実際の環境に合わせて変更してください。

### 6.2 サービスの有効化と起動

```bash
# サービスファイルを再読み込み
sudo systemctl daemon-reload

# サービスを有効化（起動時に自動起動）
sudo systemctl enable tbbox-playlist-switcher.service

# サービスを開始
sudo systemctl start tbbox-playlist-switcher.service

# サービスの状態を確認
sudo systemctl status tbbox-playlist-switcher.service
```

### 6.3 サービス管理コマンド

```bash
# サービスを停止
sudo systemctl stop tbbox-playlist-switcher.service

# サービスを再起動
sudo systemctl restart tbbox-playlist-switcher.service

# ログを確認
sudo journalctl -u tbbox-playlist-switcher.service -f
```

---

## 7. トラブルシューティング

### 問題1: TBBOXに接続できない

**症状**: `TBBOXへの接続に失敗しました` のエラーメッセージ

**原因と対策**:
1. TBBOXのIPアドレスとポート番号を確認
   ```bash
   # TBBOXにpingが通るか確認
   ping <TBBOX_IP>
   ```

2. `.env`ファイルの設定を確認
   ```bash
   cat .env | grep TBBOX_IP
   cat .env | grep TBBOX_PORT
   ```

3. TBBOXが既に他のクライアント（Viplex Express等）に接続されていないか確認
   - TBBOXは同時に1つの接続のみサポート

4. ファイアウォール設定を確認
   ```bash
   # Raspberry Pi側のファイアウォールを無効化（テスト用）
   sudo ufw disable
   ```

### 問題2: HTTPリクエストが受信できない

**症状**: curlでアクセスできない

**原因と対策**:
1. サービスが起動しているか確認
   ```bash
   sudo systemctl status tbbox-playlist-switcher.service
   ```

2. ポート8080が使用されているか確認
   ```bash
   sudo netstat -tulpn | grep 8080
   ```

3. ファイアウォールでポート8080が開いているか確認
   ```bash
   sudo ufw allow 8080
   ```

### 問題3: プログラム切り替えが動作しない

**症状**: HTTPリクエストは成功するが、TBBOXのプログラムが切り替わらない

**原因と対策**:
1. ログインコマンドが正しいか確認
   - 「T Card Login Protocol Calculation」ツールで再生成

2. TBBOXのプログラム名が"01"～"16"の形式になっているか確認

3. ログを確認して詳細なエラーメッセージを確認
   ```bash
   sudo journalctl -u tbbox-playlist-switcher.service -n 50
   ```

### 問題4: サービスが自動起動しない

**原因と対策**:
1. サービスが有効化されているか確認
   ```bash
   sudo systemctl is-enabled tbbox-playlist-switcher.service
   ```

2. サービスファイルのパスが正しいか確認
   ```bash
   cat /etc/systemd/system/tbbox-playlist-switcher.service
   ```

3. 依存関係を確認（ネットワーク起動後に実行されるか）
   ```bash
   # サービスファイルに After=network.target が含まれているか確認
   ```

### 問題5: 依存パッケージのインストール失敗

**原因と対策**:
1. pipを最新バージョンにアップグレード
   ```bash
   pip install --upgrade pip
   ```

2. システムパッケージが不足している場合
   ```bash
   sudo apt install -y python3-dev build-essential
   ```

3. 仮想環境を再作成
   ```bash
   deactivate
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

---

## 付録: linkbase側の設定

満空灯制御装置（linkbase）の`/opt/light/config.json`で、本アプリのエンドポイントを設定します。

```json
{
    "GET_URL": "http://<raspberry_pi_ip>:8080/api/control",
    "SIM_ID": "XXXXXXXXXX",
    "Mode": "4",
    "MONITOR_INTERVAL": 0.2
}
```

**設定項目**:
- `GET_URL`: Raspberry Piで動作している本アプリのエンドポイント
- `Mode`: `"4"`（全ポート通知モード）に設定

---

## セキュリティに関する注意事項

1. **.envファイルの保護**
   - `.env`ファイルには機密情報が含まれるため、適切なパーミッションを設定
   ```bash
   chmod 600 .env
   ```

2. **ファイアウォール設定**
   - 不要なポートは閉じる
   - 必要最小限のポートのみ開放（8080番ポート）

3. **SSH設定**
   - デフォルトパスワードを変更
   - SSH鍵認証の使用を推奨
   - 不要な場合はSSHポートの変更も検討

---

## お問い合わせ

問題が解決しない場合は、以下の情報を添えて管理者に連絡してください：

- エラーメッセージ（ログから抜粋）
- `.env`ファイルの設定（機密情報は除く）
- Raspberry Piのシステム情報（`uname -a`）
- Pythonバージョン（`python3 --version`）
