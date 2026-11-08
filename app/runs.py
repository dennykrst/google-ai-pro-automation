"""Run history: one row per account run plus the files it produced.

Tabel `runs` dan `artifacts` sudah ada di skema sejak awal tetapi tidak pernah
diisi, jadi riwayat run hanya bisa ditebak dari nama file di `artifacts/`. Modul
ini yang mengisi keduanya dan membacanya kembali untuk UI.

Semua path di sini divalidasi ada di dalam `artifacts_dir` sebelum dipakai, supaya
`/api/log?run=` tidak bisa dipakai membaca file lain di disk.
"""

from __future__ import annotations

import re
import secrets as _rand
import time
from pathlib import Path

from . import db
from .config import settings

PROBLEM = re.compile(r"(GAGAL|gagal|STOP|Traceback|Something went wrong|ditolak|"
                     r"tidak terbaca|tidak masuk|gagal tersimpan)")
EGRESS = re.compile(r"EGRESS\s+(\S+)\s+·\s+([A-Z]{2})")


def problem_line(path: Path, limit: int = 200) -> str:
    """Baris terakhir yang menandakan kegagalan — penyebab paling dekat."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    for line in reversed(lines):
        if PROBLEM.search(line):
            return line.strip()[:limit]
    return ""


def egress_of(path: Path) -> tuple[str, str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "", ""
    hits = EGRESS.findall(text)
    return hits[-1] if hits else ("", "")


async def start(acc_id: str, start_step: int) -> str:
    run_id = "run_" + _rand.token_hex(6)
    await db.execute(
        "INSERT INTO runs (id, account_id, started_at, status, start_step)"
        " VALUES (?,?,?,?,?)",
        (run_id, acc_id, int(time.time()), "running", start_step),
    )
    return run_id


async def add_artifact(run_id: str, kind: str, path: str | Path, step: int = 0) -> None:
    await db.execute(
        "INSERT INTO artifacts (id, run_id, step, kind, path, created_at)"
        " VALUES (?,?,?,?,?,?)",
        ("art_" + _rand.token_hex(6), run_id, step, kind, str(path), int(time.time())),
    )


async def finish(run_id: str, status: str, log_path: Path | None = None) -> None:
    error, ip, country = "", "", ""
    if log_path is not None:
        error = problem_line(log_path)
        ip, country = egress_of(log_path)
    await db.execute(
        "UPDATE runs SET ended_at = ?, status = ?, error = ?, egress_ip = ?,"
        " egress_country = ? WHERE id = ?",
        (int(time.time()), status, error, ip, country, run_id),
    )


async def add_shots(run_id: str, since: int, limit: int = 20) -> int:
    """Screenshot yang dibuat selama run ini (subprocess menulisnya sendiri)."""
    added = 0
    try:
        files = sorted(settings.artifacts_dir.glob("flow_*.png"))
    except OSError:
        return 0
    for path in files:
        try:
            if path.stat().st_mtime < since - 1:
                continue
        except OSError:
            continue
        if added >= limit:
            break
        await add_artifact(run_id, "shot", path)
        added += 1
    return added


async def list_for_account(acc_id: str, limit: int = 5) -> list[dict]:
    runs = await db.fetch_all(
        "SELECT * FROM runs WHERE account_id = ? ORDER BY started_at DESC LIMIT ?",
        (acc_id, limit),
    )
    out: list[dict] = []
    for row in runs:
        arts = await db.fetch_all(
            "SELECT kind, path FROM artifacts WHERE run_id = ? ORDER BY created_at",
            (row["id"],),
        )
        out.append({
            "id": row["id"],
            "started_at": row["started_at"],
            "ended_at": row["ended_at"],
            "status": row["status"],
            "error": row["error"],
            "egress": " · ".join(x for x in (row["egress_ip"], row["egress_country"]) if x),
            "log": next((a["path"] for a in arts if a["kind"] == "log"), ""),
            "shots": [a["path"] for a in arts if a["kind"] == "shot"],
        })
    return out


def _inside_artifacts(path: Path) -> bool:
    try:
        path.resolve().relative_to(settings.artifacts_dir.resolve())
    except (ValueError, OSError):
        return False
    return path.exists()


async def log_path(run_id: str) -> Path | None:
    row = await db.fetch_one(
        "SELECT path FROM artifacts WHERE run_id = ? AND kind = 'log'", (run_id,))
    if not row:
        return None
    path = Path(row["path"])
    return path if _inside_artifacts(path) else None


async def shot_path(run_id: str, index: int) -> Path | None:
    rows = await db.fetch_all(
        "SELECT path FROM artifacts WHERE run_id = ? AND kind = 'shot' ORDER BY created_at",
        (run_id,),
    )
    if index < 0 or index >= len(rows):
        return None
    path = Path(rows[index]["path"])
    return path if _inside_artifacts(path) else None
