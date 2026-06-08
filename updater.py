import json
from pathlib import Path
from dataclasses import dataclass
from urllib.request import urlopen

@dataclass
class UpdateInfo:
    has_update: bool
    current_version: str
    latest_version: str
    download_url: str
    notes: str
    message: str

def parse_version(v: str):
    return tuple(int(x) for x in v.strip().split("."))

def load_local_version(path="version.json"):
    p = Path(path)
    if not p.exists():
        return {
            "version": "0.0.0",
            "update_check_url": "",
            "download_url": "",
            "notes": ""
        }
    return json.loads(p.read_text(encoding="utf-8"))

def check_update(path="version.json") -> UpdateInfo:
    local = load_local_version(path)
    current = local.get("version", "0.0.0")
    update_check_url = local.get("update_check_url", "")

    if not update_check_url:
        return UpdateInfo(
            has_update=False,
            current_version=current,
            latest_version=current,
            download_url="",
            notes="",
            message="尚未設定 update_check_url。之後你把 version.json 放到 GitHub / OneDrive 後，再填入網址即可。"
        )

    try:
        with urlopen(update_check_url, timeout=10) as response:
            remote = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return UpdateInfo(
            has_update=False,
            current_version=current,
            latest_version=current,
            download_url="",
            notes="",
            message=f"檢查更新失敗：{e}"
        )

    latest = remote.get("version", current)
    has_update = parse_version(latest) > parse_version(current)

    return UpdateInfo(
        has_update=has_update,
        current_version=current,
        latest_version=latest,
        download_url=remote.get("download_url", ""),
        notes=remote.get("notes", ""),
        message="發現新版本" if has_update else "目前已是最新版本"
    )
