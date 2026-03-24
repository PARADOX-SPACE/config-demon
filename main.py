import os
import time
from datetime import datetime
from pathlib import Path

import requests
import toml

CDN_HOST = os.getenv("CDN_HOST")
CDN_PORT = os.getenv("CDN_PORT", "8080")
FORK_ID = os.getenv("FORK_ID", "paradox-fork")

BASE_DIR = Path(__file__).resolve().parent
REPLAYS_DIR = BASE_DIR / "replays"

CONFIG_PATH = Path("/config.toml")

CDN_MANIFEST = f"http://{CDN_HOST}:{CDN_PORT}/fork/{FORK_ID}/manifest"
WATCH_INTERVAL = 5

MAX_REPLAYS = 40


def get_latest_build():
    resp = requests.get(CDN_MANIFEST, timeout=10)
    resp.raise_for_status()
    data = resp.json()["builds"]

    latest_hash = max(
        data.items(),
        key=lambda x: datetime.fromisoformat(x[1]["time"].replace("Z", "+00:00"))
    )[0]

    build = data[latest_hash]

    client_url = build["client"]["url"]
    manifest_url = f"http://{CDN_HOST}:{CDN_PORT}/fork/{FORK_ID}/version/{latest_hash}/manifest"

    return {
        "fork_id": FORK_ID,
        "version": latest_hash,
        "download_url": client_url,
        "manifest_url": manifest_url
    }


def update_build_section(build_info):
    cfg = toml.load(CONFIG_PATH)

    cfg["build"] = build_info

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        toml.dump(cfg, f)

    print(f"[{datetime.now()}] Updated build section to version {build_info['version']}")


def cleanup_replays():
    if not REPLAYS_DIR.exists():
        return

    files = list(REPLAYS_DIR.glob("*.zip"))

    if len(files) <= MAX_REPLAYS:
        return

    # сортируем по времени изменения (старые вперед)
    files.sort(key=lambda f: f.stat().st_mtime)

    to_delete = files[:len(files) - MAX_REPLAYS]

    for f in to_delete:
        try:
            f.unlink()
            print(f"[{datetime.now()}] Deleted old replay: {f.name}")
        except Exception as e:
            print(f"[{datetime.now()}] Failed to delete {f.name}: {e}")


def main():
    last_version = None

    while True:
        try:
            build_info = get_latest_build()

            if build_info["version"] != last_version:
                update_build_section(build_info)
                last_version = build_info["version"]

            cleanup_replays()

        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")

        time.sleep(WATCH_INTERVAL)


if __name__ == "__main__":
    main()
