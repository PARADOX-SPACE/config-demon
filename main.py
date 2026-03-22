import os
import time
from datetime import datetime
from pathlib import Path

import requests
import toml

CDN_HOST = os.getenv("CDN_HOST")
CDN_PORT = os.getenv("CDN_PORT")
FORK_ID = os.getenv("FORK_ID", "paradox-fork")

BASE_DIR = Path(__file__).resolve().parent

CONFIG_PATH = Path("/config.toml")

CDN_MANIFEST = f"http://{CDN_HOST}:{CDN_PORT}/fork/{FORK_ID}/manifest"
WATCH_INTERVAL = 5


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


def main():
    last_version = None

    while True:
        try:
            build_info = get_latest_build()

            if build_info["version"] != last_version:
                update_build_section(build_info)
                last_version = build_info["version"]

        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")

        time.sleep(WATCH_INTERVAL)


if __name__ == "__main__":
    main()
