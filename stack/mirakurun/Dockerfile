# Mirakurun + recdvb(--b25) + libarib25 + pcsclite
# PX-Q1UD(Siano/DVB) を recdvb で扱い、B-CAS を arib25/pcscd で解除する構成。
FROM chinachu/mirakurun:latest

USER root

# recdvb / libarib25 のビルドに必要なもの
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        git ca-certificates build-essential autoconf automake libtool pkg-config \
        cmake g++ \
        libpcsclite-dev pcsc-tools \
        dpkg-dev; \
    rm -rf /var/lib/apt/lists/*

# libarib25 (B-CAS 解除ライブラリ)
RUN set -eux; \
    git clone --depth=1 https://github.com/tsukumijima/libarib25.git /tmp/libarib25; \
    cd /tmp/libarib25; \
    cmake .; \
    make -j"$(nproc)"; \
    make install; \
    ldconfig; \
    rm -rf /tmp/libarib25

# recdvb (DVB 版 recpt1 / --b25 対応)
RUN set -eux; \
    git clone --depth=1 https://github.com/dogeel/recdvb.git /tmp/recdvb || \
    git clone --depth=1 https://github.com/tsukumijima/recdvb.git /tmp/recdvb; \
    cd /tmp/recdvb; \
    ./autogen.sh || true; \
    ./configure --enable-b25; \
    make -j"$(nproc)"; \
    make install; \
    rm -rf /tmp/recdvb

USER mirakurun
