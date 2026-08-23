"""RASEPG Admin — 録画サーバをブラウザだけで管理する Web パネル。"""
from __future__ import annotations
import secrets
from pathlib import Path

from fastapi import FastAPI, Form, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config, sysops

BASE = Path(__file__).resolve().parent
app = FastAPI(title="RASEPG Admin")
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))
security = HTTPBasic()


def auth(creds: HTTPBasicCredentials = Depends(security)) -> str:
    cfg = config.load()
    ok_user = secrets.compare_digest(creds.username, cfg["admin_user"])
    ok_pass = secrets.compare_digest(creds.password, cfg["admin_password"])
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証に失敗しました",
            headers={"WWW-Authenticate": "Basic"},
        )
    return creds.username


def _flash(tab: str, msg: str) -> RedirectResponse:
    return RedirectResponse(url=f"/?tab={tab}&msg={msg}", status_code=303)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, tab: str = "dashboard", msg: str = "", _: str = Depends(auth)):
    cfg = config.load()
    ctx = {
        "request": request,
        "cfg": cfg,
        "tab": tab,
        "msg": msg,
        "services": sysops.stack_ps(),
        "temp": sysops.cpu_temp(),
        "adapters": sysops.dvb_adapters(),
        "bcas": sysops.bcas_status(),
        "devices": sysops.block_devices(),
        "disk_tmp": sysops.disk_usage(cfg["recorded_tmp"]),
        "disk_nas": sysops.disk_usage(cfg["recorded_nas"]),
    }
    return templates.TemplateResponse("index.html", ctx)


# ---------- サービス制御 ----------
@app.post("/services/{action}")
def services(action: str, service: str = Form(""), _: str = Depends(auth)):
    if action == "up":
        sysops.stack_up()
    elif action == "down":
        sysops.stack_down()
    elif action == "restart":
        sysops.stack_restart(service)
    return _flash("services", f"サービス操作: {action} 実行しました")


@app.get("/logs/{service}", response_class=HTMLResponse)
def view_logs(service: str, request: Request, _: str = Depends(auth)):
    if service not in {"mirakurun", "epgstation", "mariadb"}:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        "logs.html",
        {"request": request, "service": service, "logs": sysops.logs(service)},
    )


# ---------- 保存先 / ストレージ ----------
@app.post("/storage/tmp")
def storage_tmp(device: str = Form(""), path: str = Form(...), _: str = Depends(auth)):
    cfg = config.load()
    if device:
        sysops.mount_local(device, path)
    cfg["recorded_tmp"] = path
    config.save(cfg)
    sysops.write_env(cfg)
    return _flash("storage", "一時保存先を更新しました")


@app.post("/storage/nas")
def storage_nas(
    host: str = Form(...), share: str = Form(...), user: str = Form(...),
    password: str = Form(...), domain: str = Form(""),
    mountpoint: str = Form(...), _: str = Depends(auth),
):
    cfg = config.load()
    sysops.write_nas_credentials(user, password, domain)
    sysops.update_fstab_nas(host, share, mountpoint)
    code, out = sysops.mount_nas(mountpoint)
    cfg.update({
        "nas_host": host, "nas_share": share, "nas_user": user,
        "nas_domain": domain, "recorded_nas": mountpoint, "nas_enabled": True,
    })
    config.save(cfg)
    sysops.write_env(cfg)
    ok = "成功" if code == 0 else f"失敗: {out[:200]}"
    return _flash("storage", f"NAS マウント {ok}")


# ---------- エンコード ----------
@app.post("/encode")
def encode(
    encode_mode: str = Form("hw"), enc_height: str = Form("720"),
    enc_vbitrate: str = Form("2000k"), enc_abitrate: str = Form("128k"),
    enc_crf: str = Form("23"), enc_preset: str = Form("veryfast"),
    _: str = Depends(auth),
):
    cfg = config.load()
    cfg.update({
        "encode_mode": encode_mode, "enc_height": enc_height,
        "enc_vbitrate": enc_vbitrate, "enc_abitrate": enc_abitrate,
        "enc_crf": enc_crf, "enc_preset": enc_preset,
    })
    config.save(cfg)
    sysops.write_env(cfg)
    sysops.stack_restart("epgstation")
    return _flash("encode", "エンコード設定を反映しました(EPGStation 再起動)")


# ---------- システム ----------
@app.post("/system/hostname")
def sys_hostname(hostname: str = Form(...), _: str = Depends(auth)):
    sysops.set_hostname(hostname)
    return _flash("system", "ホスト名を変更しました")


@app.post("/system/timezone")
def sys_tz(tz: str = Form(...), _: str = Depends(auth)):
    cfg = config.load()
    sysops.set_timezone(tz)
    cfg["tz"] = tz
    config.save(cfg)
    sysops.write_env(cfg)
    return _flash("system", "タイムゾーンを変更しました")


@app.post("/system/wifi")
def sys_wifi(ssid: str = Form(...), psk: str = Form(...), _: str = Depends(auth)):
    code, out = sysops.wifi_connect(ssid, psk)
    ok = "接続しました" if code == 0 else f"失敗: {out[:200]}"
    return _flash("system", f"WiFi {ok}")


@app.post("/system/password")
def sys_password(password: str = Form(...), _: str = Depends(auth)):
    cfg = config.load()
    cfg["admin_password"] = password
    cfg["setup_done"] = True
    config.save(cfg)
    return _flash("system", "管理パスワードを変更しました")


@app.post("/system/scan")
def sys_scan(_: str = Depends(auth)):
    code, out = sysops.channel_scan()
    sysops.stack_restart("mirakurun")
    ok = "完了" if code == 0 else f"失敗: {out[:200]}"
    return _flash("dashboard", f"チャンネルスキャン {ok}")
