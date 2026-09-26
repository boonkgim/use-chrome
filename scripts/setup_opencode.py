#!/usr/bin/env python3
"""Check or configure OpenCode's Playwright extension connection."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


EXTENSION_ID = "mmlmfjhmonkocbjadbfplnigmagldckm"


def default_config() -> Path:
    override = os.environ.get("OPENCODE_CONFIG")
    return Path(override).expanduser() if override else Path.home() / ".config/opencode/opencode.json"


def load_config(path: Path) -> dict:
    if not path.exists():
        return {"$schema": "https://opencode.ai/config.json"}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("OpenCode config must be a JSON object")
    return data


def configured_command(data: dict) -> list[str]:
    mcp = data.get("mcp", {})
    if not isinstance(mcp, dict):
        return []
    server = mcp.get("playwright", {})
    return server.get("command", []) if isinstance(server, dict) else []


def extension_installed(profile: str | None) -> bool | None:
    if not profile or sys.platform != "linux":
        return None
    root = Path.home() / ".config/google-chrome" / profile / "Extensions" / EXTENSION_ID
    return root.is_dir()


def check(path: Path, profile: str | None) -> int:
    command = configured_command(load_config(path))
    configured_profile = next(
        (item.split("=", 1)[1] for item in command if item.startswith("--profile-dir-name=")), None
    )
    print(json.dumps({
        "config": str(path),
        "playwright_extension_mode": "--extension" in command,
        "profile_dir_name": configured_profile,
        "extension_installed_in_profile": extension_installed(profile or configured_profile),
    }))
    return 0


def configure(path: Path, profile: str) -> int:
    if not profile or "/" in profile or "\\" in profile:
        raise ValueError("Use only the final directory name from Chrome's Profile Path")
    data = load_config(path)
    mcp = data.setdefault("mcp", {})
    if not isinstance(mcp, dict):
        raise ValueError("OpenCode's mcp setting must be a JSON object")
    server = mcp.get("playwright", {})
    if not isinstance(server, dict) or server.get("type", "local") != "local":
        raise ValueError("Existing mcp.playwright is not a local server; inspect it before changing it")
    command = [shutil.which("npx") or "npx", "-y", "@playwright/mcp@latest", "--extension", f"--profile-dir-name={profile}"]
    if server.get("command") == command and server.get("type") == "local" and server.get("enabled", True):
        print("OpenCode is already configured for this Chrome profile.")
        return 0
    if path.exists():
        backup = path.with_name(path.name + ".before-use-chrome-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
        backup.write_bytes(path.read_bytes())
        backup.chmod(0o600)
    server.update({"type": "local", "command": command, "enabled": True})
    mcp["playwright"] = server
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".use-chrome-tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.chmod(0o600)
    temp.replace(path)
    print(f"Configured {path} for Playwright extension mode in Chrome profile {profile!r}.")
    print("Restart OpenCode, then verify access to a signed-in page.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "configure"))
    parser.add_argument("--config", type=Path, default=default_config())
    parser.add_argument("--profile-dir-name", help="Last directory component of Chrome's Profile Path")
    args = parser.parse_args()
    try:
        if args.command == "configure":
            if not args.profile_dir_name:
                parser.error("configure requires --profile-dir-name")
            return configure(args.config, args.profile_dir_name)
        return check(args.config, args.profile_dir_name)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
