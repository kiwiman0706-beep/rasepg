#!/bin/bash -e
# ホスト側: ステージに同梱したリポジトリ(files/rasepg)を rootfs の /opt/rasepg へ配置。
# files/rasepg はビルドワークフローが用意する(コンテナ内で完結させるため)。
SRC="$(dirname "$0")/files/rasepg"

install -d "${ROOTFS_DIR}/opt/rasepg"
rsync -a --delete \
	--exclude '.git' \
	--exclude 'stack/admin/venv' \
	"${SRC}/" "${ROOTFS_DIR}/opt/rasepg/"
