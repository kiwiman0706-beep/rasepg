"""ホスト操作(subprocess ラッパ)。root で動く systemd サービスから呼ばれる想定。"""
from __future__ import annotations
import json
import shlex
import subprocess
from pathlib import Path

from . import config


def run(cmd: list[str] | str, timeout: int = 120) -> tuple[int, str]:
    """コマンド実行して (returncode, 標準出力+標準エラー) を返す。"""
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return 127, f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"timeout: {' '.join(cmd)}"


# ---------- Docker スタック ----------
def compose(*args: str, profile: str = "", timeout: int = 300) -> tuple[int, str]:
    base = ["docker", "compose", "-f", str(config.STACK_DIR / "docker-compose.yml")]
    if profile:
        base += ["--profile", profile]
    return run(base + list(args), timeout=timeout)


def _backend() -> str:
    return config.load().get("tuner_backend", "mirakurun")


def _stop_tuners() -> None:
    # profile 指定サービスも確実に停止するため両 profile を付与
    run(["docker", "compose", "-f", str(config.STACK_DIR / "docker-compose.yml"),
         "--profile", "mirakurun", "--profile", "mirakc",
         "stop", "mirakurun", "mirakc"], timeout=120)


def stack_up() -> tuple[int, str]:
    # 選択中の backend のみ起動(もう片方は停止)。mariadb/epgstation は常時。
    _stop_tuners()
    return compose("up", "-d", profile=_backend(), timeout=1800)


def stack_down() -> tuple[int, str]:
    # 両 profile を含めて確実に停止
    return run(
        ["docker", "compose", "-f", str(config.STACK_DIR / "docker-compose.yml"),
         "--profile", "mirakurun", "--profile", "mirakc", "down"], timeout=300)


def stack_restart(service: str = "") -> tuple[int, str]:
    return compose("restart", *( [service] if service else [] ), profile=_backend())


def set_backend(backend: str) -> tuple[int, str]:
    """チューナー backend(mirakurun/mirakc)を切替え、EPGStation 接続先を書き換えて再起動。"""
    if backend not in {"mirakurun", "mirakc"}:
        return 1, "unknown backend"
    cfg = config.load()
    cfg["tuner_backend"] = backend
    config.save(cfg)
    _set_epgstation_backend(backend)
    _stop_tuners()
    code, out = compose("up", "-d", profile=backend, timeout=1800)
    compose("restart", "epgstation")
    return code, out


def _set_epgstation_backend(backend: str) -> None:
    """EPGStation config.yml の mirakurunPath を選択 backend に書き換える。"""
    cfg_path = config.STACK_DIR / "epgstation" / "config.yml"
    if not cfg_path.exists():
        return
    lines = cfg_path.read_text().splitlines()
    for i, line in enumerate(lines):
        if line.lstrip().startswith("mirakurunPath:"):
            indent = line[: len(line) - len(line.lstrip())]
            lines[i] = f"{indent}mirakurunPath: 'http://{backend}:40772'"
            break
    cfg_path.write_text("\n".join(lines) + "\n")


def stack_ps() -> list[dict]:
    code, out = compose("ps", "--format", "json")
    if code != 0:
        return []
    services = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            services.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return services


def logs(service: str, tail: int = 200) -> str:
    _, out = compose("logs", "--tail", str(tail), service, timeout=60)
    return out


# ---------- ストレージ / マウント ----------
def block_devices() -> list[dict]:
    code, out = run(
        ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL"]
    )
    if code != 0:
        return []
    try:
        data = json.loads(out)
        return data.get("blockdevices", [])
    except json.JSONDecodeError:
        return []


def mount_local(device: str, mountpoint: str) -> tuple[int, str]:
    Path(mountpoint).mkdir(parents=True, exist_ok=True)
    return run(["mount", device, mountpoint])


def write_nas_credentials(user: str, password: str, domain: str = "") -> None:
    lines = [f"username={user}", f"password={password}"]
    if domain:
        lines.append(f"domain={domain}")
    config.NAS_CRED.parent.mkdir(parents=True, exist_ok=True)
    config.NAS_CRED.write_text("\n".join(lines) + "\n")
    config.NAS_CRED.chmod(0o600)


FSTAB_MARK = "# RASEPG-NAS (managed)"


def update_fstab_nas(host: str, share: str, mountpoint: str) -> None:
    """NAS の SMB マウントを /etc/fstab に登録(RASEPG 管理行のみ差し替え)。"""
    Path(mountpoint).mkdir(parents=True, exist_ok=True)
    unc = f"//{host}/{share}"
    entry = (
        f"{FSTAB_MARK}\n"
        f"{unc} {mountpoint} cifs "
        f"credentials={config.NAS_CRED},uid=1000,gid=1000,iocharset=utf8,"
        f"vers=3.0,nofail,x-systemd.automount,_netdev 0 0\n"
    )
    fstab = Path("/etc/fstab")
    existing = fstab.read_text().splitlines(keepends=True) if fstab.exists() else []
    kept, skip = [], False
    for line in existing:
        if line.strip() == FSTAB_MARK:
            skip = True
            continue
        if skip:
            skip = False
            continue
        kept.append(line)
    fstab.write_text("".join(kept) + entry)


def mount_nas(mountpoint: str) -> tuple[int, str]:
    run(["systemctl", "daemon-reload"])
    return run(["mount", mountpoint], timeout=60)


# ---------- .env 生成(compose 用) ----------
def write_env(cfg: dict) -> None:
    lines = [
        "# RASEPG Admin により自動生成。手動編集は上書きされます。",
        f"TZ={cfg['tz']}",
        f"RECORDED_TMP={cfg['recorded_tmp']}",
        f"RECORDED_NAS={cfg['recorded_nas']}",
        f"RASEPG_HEIGHT={cfg['enc_height']}",
        f"RASEPG_VBITRATE={cfg['enc_vbitrate']}",
        f"RASEPG_ABITRATE={cfg['enc_abitrate']}",
        f"RASEPG_CRF={cfg['enc_crf']}",
        f"RASEPG_PRESET={cfg['enc_preset']}",
        "DB_NAME=epgstation",
        "DB_USER=epgstation",
        "DB_PASSWORD=epgstation",
        "DB_ROOT_PASSWORD=rasepg-root",
    ]
    config.ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.ENV_FILE.write_text("\n".join(lines) + "\n")


# ---------- システム情報 ----------
def cpu_temp() -> str:
    p = Path("/sys/class/thermal/thermal_zone0/temp")
    if p.exists():
        try:
            return f"{int(p.read_text().strip()) / 1000:.1f}°C"
        except (ValueError, OSError):
            pass
    return "N/A"


def dvb_adapters() -> list[str]:
    d = Path("/dev/dvb")
    if not d.exists():
        return []
    return sorted(x.name for x in d.iterdir() if x.name.startswith("adapter"))


def bcas_status() -> str:
    code, out = run(["pcsc_scan", "-r"], timeout=8)
    if code == 0 and out.strip():
        return out.strip().splitlines()[0]
    code2, out2 = run(["systemctl", "is-active", "pcscd"])
    return f"pcscd: {out2.strip()}"


def disk_usage(path: str) -> str:
    code, out = run(["df", "-h", path], timeout=10)
    if code != 0:
        return "N/A"
    rows = out.strip().splitlines()
    return rows[-1] if len(rows) > 1 else "N/A"


def set_hostname(name: str) -> tuple[int, str]:
    return run(["hostnamectl", "set-hostname", name])


def set_timezone(tz: str) -> tuple[int, str]:
    return run(["timedatectl", "set-timezone", tz])


def wifi_connect(ssid: str, psk: str) -> tuple[int, str]:
    return run(["nmcli", "device", "wifi", "connect", ssid, "password", psk], timeout=60)


def channel_scan() -> tuple[int, str]:
    backend = _backend()
    if backend == "mirakurun":
        return compose(
            "exec", "-T", "mirakurun",
            "mirakurun", "config", "channels", "scan", "--type", "GR",
            profile="mirakurun", timeout=1800,
        )
    # mirakc は API スキャンを持たないため、config.yml の channels を手動設定/転記する。
    # (Mirakurun で一度スキャンし、channels.yml の channel 値を mirakc/config.yml へ転記が簡単)
    return (
        0,
        "mirakc はチャンネルを config.yml で管理します。Mirakurun で一度スキャンして "
        "channels.yml を作り、その channel 値を stack/mirakc/config.yml に転記してください "
        "(詳細は docs/30-usage.md)。",
    )
