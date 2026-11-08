"""Persistent Chrome context. One profile dir per account, never shared."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from playwright.async_api import BrowserContext, Playwright

ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-default-browser-check",
    "--webrtc-ip-handling-policy=disable_non_proxied_udp",
    # Kartu harus menerima ketikan apa adanya. Tanpa ini Chrome (macOS) memakai
    # Keychain sebagai password store dan menyodorkan password akun ke kolom
    # kartu — CVC pun berisi password, bukan 3 digit.
    "--password-store=basic",
    "--disable-save-password-bubble",
    "--disable-features=PasswordManagerOnboarding,AutofillServerCommunication,"
    "AutofillEnableAccountWalletStorage",
]


def disable_autofill(profile_dir: Path) -> None:
    """Switch off password manager and card autofill inside the profile.

    The flags alone do not stop the suggestion UI on an already-created profile,
    so the prefs are merged in before Chrome starts; Chrome rewrites this file on
    exit, which is why it has to be written every launch.
    """
    prefs_path = profile_dir / "Default" / "Preferences"
    prefs_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        prefs = json.loads(prefs_path.read_text(encoding="utf-8"))
        if not isinstance(prefs, dict):
            prefs = {}
    except Exception:
        prefs = {}
    prefs["credentials_enable_service"] = False
    prefs.setdefault("profile", {})["password_manager_enabled"] = False
    prefs.setdefault("profile", {})["password_manager_leak_detection"] = False
    prefs.setdefault("autofill", {})["credit_card_enabled"] = False
    prefs.setdefault("autofill", {})["profile_enabled"] = False
    try:
        prefs_path.write_text(json.dumps(prefs), encoding="utf-8")
    except Exception:
        pass


async def launch(
    p: Playwright,
    profile_dir: Path,
    *,
    headless: bool = False,
    proxy: dict[str, Any] | None = None,
) -> BrowserContext:
    profile_dir.mkdir(parents=True, exist_ok=True)
    disable_autofill(profile_dir)
    return await p.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        channel="chrome",
        headless=headless,
        locale="en-US",
        timezone_id="America/Los_Angeles",
        viewport={"width": 1440, "height": 900},
        proxy=proxy,
        args=ARGS,
    )
