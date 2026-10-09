#!/usr/bin/env python3
"""Check or set up OpenCode's Playwright-CLI Chrome connection.

use-chrome now drives Chrome through `playwright-cli` (@playwright/cli) instead of an
MCP server, so there is no OpenCode `mcp` block to manage. This helper verifies the
CLI path and the extension-token secret, and can scaffold the token secret file. It
never reads or prints the token value.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

EXTENSION_ID = "mmlmfjhmonkocbjadbfplnigmagldckm"


def default_token_file() -> Path:
    override = os.environ.get("PLAYWRIGHT_EXTENSION_TOKEN_FILE")
    return Path(override).expanduser() if override else Path.home() / ".config/playwright-cli/extension-token"


def cli_on_path() -> bool:
    return shutil.which("playwright-cli") is not None


def token_file_present(path: Path) -> bool:
    if not path.is_file():
        return False
    # present + non-empty; never read or print the value
    try:
        return path.stat().st_size > 0
    except OSError:
        return False


def extension_installed(profile: str | None) -> bool | None:
    if not profile or sys.platform != "linux":
        return None
    root = Path.home() / ".config/google-chrome" / profile / "Extensions" / EXTENSION_ID
    return root.is_dir()


def check(token_file: Path, profile: str | None) -> int:
    print(json.dumps({
        "cli_installed": cli_on_path(),
        "token_file": str(token_file),
        "token_file_present": token_file_present(token_file),
        "extension_profile": profile,
        "extension_installed_in_profile": extension_installed(profile),
        "attach_command": f'export PLAYWRIGHT_MCP_EXTENSION_TOKEN="$(cut -d= -f2 {token_file})" && playwright-cli -s=chrome attach --extension',
    }, indent=2))
    return 0


def configure(token_file: Path, profile: str | None) -> int:
    # Scaffold the secret file if missing; never invent or print a token value.
    token_file.parent.mkdir(parents=True, exist_ok=True)
    if not token_file.exists():
        token_file.write_text("PLAYWRIGHT_MCP_EXTENSION_TOKEN=\n", encoding="utf-8")
        token_file.chmod(0o600)
        print(f"Created empty token secret {token_file}.")
        print("Paste the Playwright extension token into it (mode 0600), then attach:")
    else:
        print(f"Token secret already present at {token_file}.")
    print(f'export PLAYWRIGHT_MCP_EXTENSION_TOKEN="$(cut -d= -f2 {token_file})"')
    print("playwright-cli -s=chrome attach --extension")
    if profile:
        print(f"(profile: {profile}; extension installed there: {extension_installed(profile)})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "configure"))
    parser.add_argument("--token-file", type=Path, default=default_token_file())
    parser.add_argument("--profile-dir-name", help="Last directory component of Chrome's Profile Path")
    args = parser.parse_args()
    try:
        if args.command == "configure":
            return configure(args.token_file, args.profile_dir_name)
        return check(args.token_file, args.profile_dir_name)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
