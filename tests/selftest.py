"""Self-test, stdlib only. Run: .venv/bin/python tests/selftest.py"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Jangan sentuh data asli: uji jalan di direktori sementara.
_TMP = Path(tempfile.mkdtemp(prefix="gai-selftest-"))
os.environ["GAI_DATA_DIR"] = str(_TMP)

from app import db, runs, secrets, totp, vault  # noqa: E402
from app.config import settings  # noqa: E402
from app.models import AccountCreate  # noqa: E402

# RFC 6238 Appendix B: secret "12345678901234567890" (ASCII), SHA-1, 8 digits.
RFC_SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"


def test_totp_rfc_vectors() -> None:
    cases = {59: "287082", 1111111109: "081804", 1234567890: "005924", 2000000000: "279037"}
    for at, expected in cases.items():
        assert totp.code(RFC_SECRET, at=at) == expected, (at, totp.code(RFC_SECRET, at=at))


def test_totp_shapes() -> None:
    assert totp.code("") == ""
    assert totp.code("not-base32!!") == ""
    assert totp.code("jbsw y3dp ehpk 3pxp") != ""
    assert 1 <= totp.seconds_left() <= 30
    assert totp.wait_hint(at=0) == 0


def test_email_normalisation() -> None:
    a = AccountCreate(email="Some.One@Gmail.COM", password="x")
    assert a.email == "some.one@gmail.com"
    for bad in ("nope", "a@b", "@b.com", "a b@c.com"):
        try:
            AccountCreate(email=bad, password="x")
        except Exception:
            continue
        raise AssertionError(f"accepted bad email {bad!r}")


def test_secrets_roundtrip() -> None:
    ref = "selftest:roundtrip"
    secrets.delete(ref)
    assert secrets.get(ref) == ""
    secrets.put(ref, "p@ss-with-symbols-9=X")
    assert secrets.get(ref) == "p@ss-with-symbols-9=X"
    secrets.put(ref, "overwritten")
    assert secrets.get(ref) == "overwritten"
    secrets.delete(ref)
    assert secrets.get(ref) == ""


def test_runs_history() -> None:
    """Setiap run dicatat: status, ringkasan penyebab gagal, egress, dan path log."""

    async def run() -> None:
        await db.migrate()
        await vault.add_account("runs.test@gmail.com", "pw", "")
        acc = (await db.fetch_all(
            "SELECT id FROM accounts WHERE email = ?", ("runs.test@gmail.com",)))[0]["id"]

        log = settings.artifacts_dir / "run_acc_fixture01_1700000000.log"
        log.write_text(
            "akun runs.test@gmail.com · acc\n"
            "[10:00:01] EGRESS 1.2.3.4 · US · Example Org\n"
            "[10:00:05] KARTU  kolom CVC meleset — ulang\n"
            "[10:00:06] KARTU  kartu gagal tersimpan\n"
            "[10:00:06] STOP   layer belum tuntas\n",
            encoding="utf-8",
        )

        run_id = await runs.start(acc, 1)
        await runs.add_artifact(run_id, "log", log)
        await runs.finish(run_id, "failed", log)

        rows = await runs.list_for_account(acc)
        assert rows and rows[0]["status"] == "failed", rows
        assert rows[0]["error"].endswith("layer belum tuntas"), rows[0]["error"]
        assert rows[0]["egress"] == "1.2.3.4 · US", rows[0]["egress"]
        assert rows[0]["log"].endswith("run_acc_fixture01_1700000000.log")
        assert rows[0]["ended_at"] >= rows[0]["started_at"]

        found = await runs.log_path(run_id)
        assert found is not None and found.exists(), found

        # Path di luar artifacts/ harus ditolak, meskipun tercatat di DB.
        escape = await runs.start(acc, 1)
        await runs.add_artifact(escape, "log", "/etc/hosts")
        assert await runs.log_path(escape) is None

    asyncio.run(run())


def test_newest_log_parsing() -> None:
    """Nama file run dipakai untuk memulihkan acc_id setelah console restart."""
    from app.runner import queue

    path = settings.artifacts_dir / "run_acc_fixture01_1700000000.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("[10:00:06] STOP layer belum tuntas\n", encoding="utf-8")

    found = queue.newest_log()
    assert found is not None, "log fixture tidak terbaca"
    acc_id, newest = found
    assert acc_id == "acc_fixture01", acc_id
    assert newest.name == "run_acc_fixture01_1700000000.log", newest.name
    assert "STOP" in queue.tail(newest)


def test_db_migrate() -> None:
    async def run() -> None:
        await db.migrate()
        await db.migrate()  # idempotent
        row = await db.fetch_one("SELECT COUNT(*) AS n FROM accounts")
        assert row is not None and row["n"] == 0
        cols = {r["name"] for r in await db.fetch_all("PRAGMA table_info(accounts)")}
        assert {"email", "secret_ref", "totp_ref", "step", "expiry_date"} <= cols

    asyncio.run(run())


def main() -> int:
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    print("---", "all passed" if not failures else f"{failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
