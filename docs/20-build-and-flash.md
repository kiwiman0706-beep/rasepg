# SD カードイメージの作成と書き込み

イメージの入手方法は 2 通りあります。**A が「ややこしい操作なし」の本命**です。

## A. 完成イメージを使う(推奨)

### A-1. GitHub Actions でイメージを自動ビルド

1. この GitHub リポジトリの **Actions** タブを開く
2. **Build SD image** ワークフローを選び **Run workflow**(または `v*` タグを push)
3. 完了(約1〜2時間)後、実行結果の **Artifacts** から `rasepg-image`(`rasepg-*.img.xz`)をダウンロード

> ビルドは pi-gen(公式イメージビルダ)を GitHub のクラウド上で実行します。手元PCの環境構築は不要です。

### A-2. SD カードへ書き込む

1. [Raspberry Pi Imager](https://www.raspberrypi.com/software/) をインストール
2. 「OS を選ぶ」→「カスタムイメージを使う」→ ダウンロードした `.img.xz` を選択
3. ⚙️(歯車)で **WiFi・ホスト名・SSH・ユーザー** を設定しておくと、以降は完全に Web だけで完結
   - ※ 有線LANなら WiFi 設定は不要
4. 書き込み → SD を Pi に挿して起動

### A-3. 初回起動

- 初回起動時に自動で Docker イメージの構築/取得とサービス起動が走ります(数分〜十数分)。
- 完了後:
  - 管理パネル: `http://<PiのIP または ホスト名>.local:9000`
  - 録画UI(EPGStation): `http://<PiのIP>:8888`

以降の設定(保存先/NAS/エンコード/チャンネルスキャン等)はすべて Web から。→ `docs/30-usage.md`

## B. 既存の Raspberry Pi OS に手動導入(上級者向け)

すでに Raspberry Pi OS Lite (64bit) が動いている場合:

```bash
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/kiwiman0706-beep/rasepg.git
cd rasepg
sudo bash bootstrap/install.sh
sudo reboot
```

再起動後、初回起動処理が走り、A-3 と同じ状態になります。

## メモ

- イメージは `arm64` / Raspberry Pi OS Bookworm ベース。Pi4・Pi5 で利用可能。
- 設定内容(保存先・NAS 認証・エンコード)は `/etc/rasepg/` に保存され、SD を差し替えても再設定は Web からやり直せます。
