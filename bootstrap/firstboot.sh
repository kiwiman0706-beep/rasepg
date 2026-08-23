#!/usr/bin/env bash
# 初回起動時に一度だけ実行。Docker イメージを構築/取得してスタックを起動する。
# (イメージ構築はネットワーク必須で時間がかかるため、イメージ焼き込み時ではなく初回起動で行う)
set -euo pipefail
RASEPG_ROOT="${RASEPG_ROOT:-/opt/rasepg}"
STACK="$RASEPG_ROOT/stack"
MARK="/etc/rasepg/.firstboot-done"

log() { echo -e "\033[36m[RASEPG/firstboot]\033[0m $*"; }

mkdir -p /etc/rasepg

# ファーム未導入なら再試行
bash "$RASEPG_ROOT/bootstrap/firmware.sh" || true

# .env が無ければ雛形から
[[ -f "$STACK/.env" ]] || cp "$STACK/.env.example" "$STACK/.env"

# 保存先ディレクトリを確保(未マウントでもローカルに作る)
# shellcheck disable=SC1091
set -a; source "$STACK/.env"; set +a
mkdir -p "${RECORDED_TMP:-/mnt/ssd/recorded}" "${RECORDED_NAS:-/mnt/nas}" || true

log "Docker イメージを構築/取得します(初回のみ・数分〜十数分)"
docker compose -f "$STACK/docker-compose.yml" pull || true
docker compose -f "$STACK/docker-compose.yml" build || true
docker compose -f "$STACK/docker-compose.yml" up -d

touch "$MARK"
log "初回セットアップ完了。管理パネル: http://<IP>:9000  録画UI: http://<IP>:8888"
