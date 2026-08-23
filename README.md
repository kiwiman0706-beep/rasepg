# RASEPG — ラズパイ TS抜き録画サーバー (nasne 風・Web管理)

Raspberry Pi 4 + PLEX PX-Q1UD を使った地デジ録画サーバーを、
**SDカードに焼いて挿すだけ／設定はブラウザだけ**で完結させるためのプロジェクトです。

- 録画バックエンド: **Mirakurun / mirakc**(recdvb + arib25 で B-CAS 解除・Webから切替可)
- 録画管理/番組表/自動エンコード: **EPGStation**
- 保存先(外付けSSD / NAS)・NAS接続・エンコード・WiFi・サービス起動停止:
  同梱の **RASEPG Admin(Web管理パネル)**
- 配布: **GitHub Actions で `.img.xz` を自動ビルド** → Raspberry Pi Imager で書き込み

> まず [`docs/00-consideration.md`](docs/00-consideration.md) に、元の構成案に対する
> **技術的な考察と設計判断**(チューナードライバ・保存先・エンコード方式・代替案)をまとめています。

## クイックスタート

1. **イメージを入手**: GitHub の **Actions → Build SD image → Run workflow** を実行し、
   完了後 Artifacts から `rasepg-*.img.xz` をダウンロード
   （詳細: [`docs/20-build-and-flash.md`](docs/20-build-and-flash.md)）
2. **書き込み**: Raspberry Pi Imager で「カスタムイメージ」として書き込み
   （歯車アイコンで WiFi/ホスト名/SSH を設定しておくと以降 Web だけで完結）
3. **起動**: SD を挿して電源ON。初回は自動でセットアップ(数分〜十数分)
4. **設定**: ブラウザで
   - 管理パネル `http://<IP>:9000`(保存先/NAS/エンコード等)
   - 録画UI `http://<IP>:8888`(EPGStation: 番組表・予約)
   （手順: [`docs/30-usage.md`](docs/30-usage.md)）

## 構成の要点(考察の結論)

| 項目 | 採用 | 理由 |
|---|---|---|
| チューナー | recdvb + メインライン `smsdvb` | PX-Q1UD は Siano系DVB準拠。専用ドライバ不要で安定 |
| 一時保存 | 外付けSSD(USB3) | SDカードは寿命/速度で不利 |
| エンコード | HW(`h264_v4l2m2m`)既定 + SW(x264)選択可 | 用途で軽量/高画質を切替 |
| 管理 | 専用 Web パネル + EPGStation | CLI 不要、ブラウザだけ |
| 配布 | pi-gen + GitHub Actions | 再現性のある自動イメージビルド |

## リポジトリ構成

```
rasepg/
├── docs/                     考察・ハード・イメージ作成・使い方
│   ├── 00-consideration.md   ★ 設計判断と代替案の考察
│   ├── 10-hardware.md
│   ├── 20-build-and-flash.md
│   └── 30-usage.md
├── stack/                    録画スタック(Docker)
│   ├── docker-compose.yml    Mirakurun / mirakc / EPGStation / MariaDB (profile切替)
│   ├── mirakurun/            Dockerfile(recdvb+arib25) と tuners/channels/server
│   ├── mirakc/               Dockerfile(recdvb) と config.yml (軽量backend)
│   ├── epgstation/           config.yml と エンコードスクリプト(HW/SW)
│   └── admin/                RASEPG Admin(FastAPI・ホストsystemdで動作)
├── bootstrap/                実機/イメージ共通のセットアップ
│   ├── install.sh            素のPi OS → 録画サーバ化
│   ├── firstboot.sh          初回起動でイメージ構築&起動
│   ├── firmware.sh           Siano ファーム導入
│   └── *.service             systemd ユニット
├── image/                    pi-gen カスタムイメージ定義
│   ├── config
│   └── stage-rasepg/
└── .github/workflows/build-image.yml   イメージ自動ビルド
```

## 注意 / 免責

- **TS のスクランブル解除(いわゆる「TS抜き」)** は B-CAS カードと arib25 による個人利用の一般的手法ですが、
  取り扱いはご自身の責任と適用法令の範囲で行ってください。本リポジトリは録画サーバ基盤(OSS構成)を提供するものです。
- 本リポジトリの構成・設定は実機/実チューナー/イメージビルドでの動作確認までは行っていません
  (電波・B-CAS・USBハード・GitHub Actions のビルド実行が必要なため)。
  初回は SSH でログ(`journalctl -u rasepg-firstboot`, `docker compose logs`)を確認できると安心です。
- チャンネル物理番号・serviceId は地域で異なるため、初回に**チャンネルスキャン**が必要です。
