#!/usr/bin/env bash
# RASEPG インストーラ
#   素の Raspberry Pi OS Lite (64bit) を録画サーバに変える。
#   pi-gen(イメージビルド)からも、既存 Pi 上でも同じスクリプトで動く。
#
#   使い方(既存 Pi の場合):
#     git clone https://github.com/kiwiman0706-beep/rasepg
#     cd rasepg && sudo bash bootstrap/install.sh
set -euo pipefail

RASEPG_ROOT="${RASEPG_ROOT:-/opt/rasepg}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONF_DIR="/etc/rasepg"

log() { echo -e "\033[36m[RASEPG]\033[0m $*"; }

if [[ $EUID -ne 0 ]]; then echo "root で実行してください (sudo)"; exit 1; fi

log "1/7 APT パッケージ導入"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
    ca-certificates curl git \
    pcscd pcsc-tools libpcsclite1 \
    cifs-utils \
    python3 python3-venv python3-pip \
    network-manager \
    docker.io docker-compose-plugin

log "2/7 Docker / pcscd 有効化"
systemctl enable docker || true
systemctl enable pcscd || true
# 稼働中システムでのみ即時起動(pi-gen の chroot では起動しない)
if [[ -d /run/systemd/system ]]; then
    systemctl start docker || true
    systemctl start pcscd || true
fi

log "3/7 リポジトリを ${RASEPG_ROOT} へ配置"
mkdir -p "$RASEPG_ROOT"
# pi-gen では /opt/rasepg に直接展開済みのこともあるためコピーは冪等に
if [[ "$REPO_DIR" != "$RASEPG_ROOT" ]]; then
    cp -a "$REPO_DIR/." "$RASEPG_ROOT/"
fi

log "4/7 Siano ファームウェア(PX-Q1UD)導入"
bash "$RASEPG_ROOT/bootstrap/firmware.sh" || log "  ※ファーム導入は後で再実行できます"

log "5/7 RASEPG Admin (Python) セットアップ"
python3 -m venv "$RASEPG_ROOT/stack/admin/venv"
"$RASEPG_ROOT/stack/admin/venv/bin/pip" install --upgrade pip
"$RASEPG_ROOT/stack/admin/venv/bin/pip" install -r "$RASEPG_ROOT/stack/admin/requirements.txt"
mkdir -p "$CONF_DIR"

log "6/7 systemd サービス登録"
install -m 644 "$RASEPG_ROOT/bootstrap/rasepg-admin.service"    /etc/systemd/system/
install -m 644 "$RASEPG_ROOT/bootstrap/rasepg-firstboot.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable rasepg-admin.service
systemctl enable rasepg-firstboot.service

log "7/7 初期 .env 生成"
if [[ ! -f "$RASEPG_ROOT/stack/.env" ]]; then
    cp "$RASEPG_ROOT/stack/.env.example" "$RASEPG_ROOT/stack/.env"
fi

log "完了。次回起動時に firstboot が Docker イメージを構築/取得し、"
log "管理パネルは http://<ラズパイのIP>:9000 で開けます。"
log "初期ログイン: admin / (パスワードは /etc/rasepg/config.json に生成されます)"
