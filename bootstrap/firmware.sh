#!/usr/bin/env bash
# PX-Q1UD / PX-S1UD (Siano SMS2270) 用ファームウェア導入。
#   メインラインの smsdvb ドライバは動作にファーム isdbt_nova_12mhz_b0.inp を要求する。
set -euo pipefail

FW_DIR="/lib/firmware"
FW_NAME="isdbt_nova_12mhz_b0.inp"
FW_DEST="${FW_DIR}/${FW_NAME}"

log() { echo -e "\033[36m[RASEPG/fw]\033[0m $*"; }

if [[ -f "$FW_DEST" ]]; then
    log "ファーム導入済み: $FW_DEST"
    exit 0
fi

mkdir -p "$FW_DIR"

# FIRMWARE_URL 環境変数で上書き可能。既定は PX-S1UD Linux ドライバ配布物の内包ファーム。
CANDIDATES=(
    "${FIRMWARE_URL:-}"
    "https://raw.githubusercontent.com/tejav/px-s1ud-firmware/master/${FW_NAME}"
)

for url in "${CANDIDATES[@]}"; do
    [[ -z "$url" ]] && continue
    log "取得を試行: $url"
    if curl -fsSL "$url" -o "$FW_DEST"; then
        log "導入成功: $FW_DEST"
        # ドライバ再読込(存在すれば)
        modprobe -r smsdvb smsusb 2>/dev/null || true
        modprobe smsdvb 2>/dev/null || true
        exit 0
    fi
done

cat <<'MSG'
[RASEPG/fw] ファームウェアを自動取得できませんでした。
  PLEX PX-S1UD の Linux ドライバに含まれる
  "isdbt_nova_12mhz_b0.inp" を手動で /lib/firmware/ に置いてください。
  配置後: sudo modprobe -r smsdvb smsusb && sudo modprobe smsdvb
MSG
exit 1
