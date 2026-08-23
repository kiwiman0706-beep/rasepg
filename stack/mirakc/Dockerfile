# mirakc(軽量・Rust) + recdvb(--b25) + libarib25
#   mirakc 公式イメージには EPG 解析用の mirakc-arib が同梱されるが、
#   PX-Q1UD(DVB) から TS を読み出す recdvb は含まれないため追加ビルドする。
#   ※ mirakc の既定イメージは Debian ベース。Alpine タグを使う場合はこの手順は使えない。
FROM mirakc/mirakc:latest

USER root

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        git ca-certificates build-essential autoconf automake libtool pkg-config \
        cmake g++ \
        libpcsclite-dev pcsc-tools; \
    rm -rf /var/lib/apt/lists/*

# libarib25 (B-CAS 解除)
RUN set -eux; \
    git clone --depth=1 https://github.com/tsukumijima/libarib25.git /tmp/libarib25; \
    cd /tmp/libarib25; cmake .; make -j"$(nproc)"; make install; ldconfig; \
    rm -rf /tmp/libarib25

# recdvb (DVB 版 recpt1, --b25 対応)
RUN set -eux; \
    git clone --depth=1 https://github.com/dogeel/recdvb.git /tmp/recdvb || \
    git clone --depth=1 https://github.com/tsukumijima/recdvb.git /tmp/recdvb; \
    cd /tmp/recdvb; ./autogen.sh || true; ./configure --enable-b25; \
    make -j"$(nproc)"; make install; \
    rm -rf /tmp/recdvb
