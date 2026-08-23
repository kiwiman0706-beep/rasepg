"""RASEPG Admin の設定・パス管理。設定は /etc/rasepg/config.json に保存。"""
from __future__ import annotations
import json
import os
import secrets
from pathlib import Path

RASEPG_ROOT = Path(os.environ.get("RASEPG_ROOT", "/opt/rasepg"))
STACK_DIR = RASEPG_ROOT / "stack"
ENV_FILE = STACK_DIR / ".env"

CONF_DIR = Path(os.environ.get("RASEPG_CONF_DIR", "/etc/rasepg"))
CONF_FILE = CONF_DIR / "config.json"
NAS_CRED = CONF_DIR / "nas.cred"

DEFAULTS: dict = {
    "tz": "Asia/Tokyo",
    # チューナーサーバ backend: mirakurun(既定/情報量多) | mirakc(軽量)
    "tuner_backend": "mirakurun",
    # 保存先
    "recorded_tmp": "/mnt/ssd/recorded",
    "recorded_nas": "/mnt/nas",
    # NAS(SMB)
    "nas_host": "",
    "nas_share": "",
    "nas_user": "",
    "nas_domain": "",
    "nas_enabled": False,
    # エンコード
    "encode_mode": "remux",       # remux | hw | sw
    "enc_height": "720",
    "enc_vbitrate": "2000k",
    "enc_abitrate": "128k",
    "enc_crf": "23",
    "enc_preset": "veryfast",
    # 管理パネル認証
    "admin_user": "admin",
    "admin_password": "",         # 空なら初回に生成
    "setup_done": False,
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    if CONF_FILE.exists():
        try:
            cfg.update(json.loads(CONF_FILE.read_text()))
        except (json.JSONDecodeError, OSError):
            pass
    if not cfg.get("admin_password"):
        cfg["admin_password"] = secrets.token_urlsafe(9)
        save(cfg)
    return cfg


def save(cfg: dict) -> None:
    CONF_DIR.mkdir(parents=True, exist_ok=True)
    CONF_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
    os.chmod(CONF_FILE, 0o600)
