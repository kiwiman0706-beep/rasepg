#!/bin/bash -e
# chroot 内: インストーラを実行して録画サーバを構成する。
# (docker イメージの構築/取得は行わない。実機の初回起動時 firstboot で実施)
export RASEPG_ROOT=/opt/rasepg
bash /opt/rasepg/bootstrap/install.sh
