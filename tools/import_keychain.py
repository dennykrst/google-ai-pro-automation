"""One-time migration: copy secrets out of the macOS Keychain into secrets.json.

This script is the *only* place that still talks to the Keychain, and the app
never imports it. Run it once if you imported accounts/cards with the older
version:

    .venv/bin/python tools/import_keychain.py

Refs are read from the database, so everything the vault knows about is checked.
Values already present in secrets.json are left alone; missing ones are copied.
Missing Keychain items are not an error — a fresh install simply copies nothing.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import db, secrets  # noqa: E402
from app.config import settings  # noqa: E402

SERVICE = "GaiConsole"          # nama service Keychain versi lama


def keychain_get(ref: str) -> str:
    """Read one item. `find-generic-password` does not prompt for a value."""
    if sys.platform != "darwin":
        return ""
    try:
        proc = subprocess.run(
            ["security", "find-generic-password", "-s", SERVICE, "-a", ref, "-w"],
            capture_output=True, text=True, check=False, timeout=15,
        )
    except Exception:
        return ""
    return proc.stdout.rstrip("\n") if proc.returncode == 0 else ""


async def main() -> int:
    settings.ensure_dirs()
    await db.migrate()

    refs: list[str] = []
    for row in await db.fetch_all("SELECT secret_ref, totp_ref FROM accounts"):
        refs += [row["secret_ref"], row["totp_ref"]]
    for row in await db.fetch_all("SELECT number_ref, cvc_ref FROM cards"):
        refs += [row["number_ref"], row["cvc_ref"]]
    refs = [r for r in dict.fromkeys(refs) if r]

    if not refs:
        print("tidak ada akun/kartu di database — tidak ada yang perlu disalin")
        return 0

    copied = 0
    for ref in refs:
        if secrets.exists(ref):
            continue
        value = keychain_get(ref)
        if value:
            secrets.put(ref, value)
            copied += 1
            print(f"  {ref}: disalin")

    target = settings.data_dir / "secrets.json"
    print(f"{copied} dari {len(refs)} ref disalin ke {target}")
    if copied == 0:
        print("(item tidak ada di Keychain, atau sudah ada di secrets.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
