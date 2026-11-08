"""Settings. Everything path- or secret-bearing lives outside the repo.

Data dir dipilih per platform, jadi kode yang sama jalan di macOS dan Windows:

    macOS    ~/Library/Application Support/GoogleAIAutomation
    Windows  %LOCALAPPDATA%\\GoogleAIAutomation
    Linux    $XDG_DATA_HOME/GoogleAIAutomation (atau ~/.local/share/...)

`GAI_DATA_DIR` menimpa semuanya — dipakai selftest dan run sekali pakai.
"""

from __future__ import annotations

import os
import secrets
import stat
import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_NAME = "GoogleAIAutomation"
OLD_APP_NAME = "GaiConsole"      # nama data dir sebelum project di-rename


def _base_dir() -> Path:
    if sys.platform == "win32":
        root = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if root:
            return Path(root)
        return Path.home() / "AppData" / "Local"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")


def _default_data_dir() -> Path:
    new = _base_dir() / APP_NAME
    old = _base_dir() / OLD_APP_NAME
    # Sekali saja: data dir lama dipindah supaya akun, kartu dan token console
    # tidak hilang cuma karena project berganti nama.
    if not new.exists() and old.exists():
        try:
            old.rename(new)
        except OSError:
            pass
    return new


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GAI_", extra="ignore")

    data_dir: Path = _default_data_dir()
    bind_host: str = "127.0.0.1"
    bind_port: int = 8765

    # Google login flows: parallel logins from one egress burn reputation faster
    # than a sequential queue. Keep this at 1 unless measured otherwise.
    max_concurrent: int = 1

    # Seconds a single account run may take before the supervisor cancels it.
    run_timeout: int = 15 * 60

    console_token: str = ""

    @property
    def db_path(self) -> Path:
        return self.data_dir / "db.sqlite3"

    @property
    def profiles_dir(self) -> Path:
        return self.data_dir / "profiles"

    @property
    def artifacts_dir(self) -> Path:
        return self.data_dir / "artifacts"

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.profiles_dir, self.artifacts_dir):
            d.mkdir(parents=True, exist_ok=True)
        if sys.platform != "win32":
            try:
                self.data_dir.chmod(stat.S_IRWXU)  # 0700: profile dirs hold live cookies
            except OSError:
                pass

    def load_or_create_token(self) -> str:
        """Console token. Without it, any local process can read the account list."""
        path = self.data_dir / "console.token"
        if path.exists():
            token = path.read_text(encoding="ascii").strip()
            if token:
                self.console_token = token
                return token
        token = secrets.token_urlsafe(32)
        path.write_text(token, encoding="ascii")
        path.chmod(0o600)
        self.console_token = token
        return token


settings = Settings()
