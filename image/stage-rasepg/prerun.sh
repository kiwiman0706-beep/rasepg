#!/bin/bash -e
# 直前ステージ(stage2 lite)の rootfs を引き継ぐ
if [ ! -d "${ROOTFS_DIR}" ]; then
	copy_previous
fi
