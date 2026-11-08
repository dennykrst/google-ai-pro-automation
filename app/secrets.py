"""Local secret store: one JSON file. Nothing platform-specific in here.

Dulu nilai disimpan di macOS Keychain lewat CLI `security`, yang punya dua
masalah: `add-generic-password -w` membaca nilai dari *terminal* (bukan stdin) di
macOS baru sehingga impor akun menggantung menunggu ketikan, dan seluruh modul
jadi tidak bisa dipakai di Windows.

Sekarang nilai hidup di `<data_dir>/secrets.json` (0600, di dalam data dir 0700)
dan dibaca langsung dari disk — sama persis di macOS, Windows, dan Linux.

Trade-off, jujur: perlindungannya izin file, bukan kontrol akses per-aplikasi
Keychain. Apa pun yang jalan sebagai user kamu bisa membacanya. Gantinya: tidak
ada prompt, tidak ada perintah OS, dan tidak ada yang disimpan di luar data dir.

Punya data lama di Keychain? Jalankan sekali `tools/import_keychain.py` (khusus
macOS) untuk menyalinnya ke file ini. Aplikasi sendiri tidak pernah menyentuh
Keychain.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
import threading
from pathlib import Path

from .config import settings

_LOCK = threading.RLock()
_data: dict[str, str] | None = None


def _path() -> Path:
    return settings.data_dir / "secrets.json"


def _load() -> dict[str, str]:
    global _data
    if _data is not None:
        return _data
    path = _path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        _data = {str(k): str(v) for k, v in raw.items()} if isinstance(raw, dict) else {}
    except Exception:
        _data = {}
    if os.name == "posix":
        try:
            path.chmod(0o600)     # tolerates a file copied in with loose modes
        except OSError:
            pass
    return _data


def _save(data: dict[str, str]) -> None:
    """Atomic write: a half-written file would lose every card at once."""
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".secrets-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        if os.name == "posix":
            os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def put(ref: str, value: str) -> None:
    with _LOCK:
        data = _load()
        data[ref] = value
        _save(data)


def get(ref: str) -> str:
    with _LOCK:
        return _load().get(ref, "")


def delete(ref: str) -> None:
    with _LOCK:
        data = _load()
        if data.pop(ref, None) is not None:
            _save(data)


def exists(ref: str) -> bool:
    return bool(get(ref))
