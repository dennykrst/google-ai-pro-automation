"""App factory. Boot order: dirs, token, migrations, routes."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from urllib.parse import quote

from . import db, runs, vault
from .config import settings
from .runner import queue
from .security import COOKIE_NAME, require_token

log = logging.getLogger("gai")


def _to(dest: str = "/", **params: str) -> RedirectResponse:
    """303 back to the page with the message URL-encoded.

    Notes carry user input (an email, a card brand), so they must be quoted —
    an unescaped `&` or `#` in a malformed import line would truncate the query
    string and drop the message entirely.
    """
    query = "&".join(f"{k}={quote(v)}" for k, v in params.items() if v)
    return RedirectResponse(f"{dest}?{query}" if query else dest, status_code=303)

HERE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(HERE / "templates"))


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings.ensure_dirs()
    token = settings.load_or_create_token()
    await db.migrate()
    queue.runner.start()
    log.warning("console: http://%s:%d/?t=%s", settings.bind_host, settings.bind_port, token)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Google AI Pro Automation", lifespan=lifespan,
                  docs_url=None, redoc_url=None)
    guard = [Depends(require_token)]

    @app.get("/healthz")
    async def healthz() -> JSONResponse:
        return JSONResponse({"ok": True})

    @app.get("/", dependencies=guard)
    async def index(request: Request, msg: str = "", err: str = ""):
        resp = templates.TemplateResponse(
            request,
            "index.html",
            {
                "accounts": await vault.accounts_view(),
                "cards": await vault.cards_view(),
                "msg": msg,
                "err": err,
                "pending": queue.runner.pending,
                "current": queue.runner.current,
            },
        )
        if getattr(request.state, "set_cookie_token", None):
            resp.set_cookie(COOKIE_NAME, request.state.set_cookie_token, httponly=True, samesite="strict")
        return resp

    @app.get("/help", dependencies=guard)
    async def help_page(request: Request):
        """Panduan di dalam aplikasi: handler, format input, arti log, data dir."""
        resp = templates.TemplateResponse(
            request,
            "help.html",
            {"data_dir": str(settings.data_dir)},
        )
        if getattr(request.state, "set_cookie_token", None):
            resp.set_cookie(COOKIE_NAME, request.state.set_cookie_token,
                            httponly=True, samesite="strict")
        return resp

    @app.get("/api/codes", dependencies=guard)
    async def codes() -> JSONResponse:
        rows = await db.fetch_all("SELECT id, totp_ref FROM accounts WHERE totp_ref != ''")
        out: dict[str, dict[str, object]] = {}
        for row in rows:
            seed = vault.secret_get(row["totp_ref"])
            out[row["id"]] = {"code": vault.totp.code(seed), "left": vault.totp.seconds_left()}
        return JSONResponse(out)

    @app.get("/api/secret/{acc_id}", dependencies=guard)
    async def secret(acc_id: str) -> JSONResponse:
        row = await db.fetch_one("SELECT secret_ref FROM accounts WHERE id = ?", (acc_id,))
        if not row or not row["secret_ref"]:
            return JSONResponse({"password": ""}, status_code=404)
        return JSONResponse({"password": vault.secret_get(row["secret_ref"])})

    @app.post("/accounts/import", dependencies=guard)
    async def accounts_import(blob: str = Form(default="")):
        notes = await vault.import_accounts(blob)
        added = sum(1 for n in notes if n.endswith("ditambahkan"))
        unusable = len(notes) - added
        text = f"{added} akun masuk" + (f", {unusable} dilewati" if unusable else "")
        return _to(msg=text)

    @app.post("/accounts/add", dependencies=guard)
    async def accounts_add(email: str = Form(...), password: str = Form(...), seed: str = Form(default="")):
        _, note = await vault.add_account(email, password, seed)
        return _to(msg=note)

    @app.post("/accounts/{acc_id}/delete", dependencies=guard)
    async def accounts_delete(acc_id: str):
        await vault.delete_account(acc_id)
        return _to(msg="akun dihapus")

    @app.post("/cards/import", dependencies=guard)
    async def cards_import(blob: str = Form(default="")):
        notes = await vault.import_cards(blob)
        added = sum(1 for n in notes if n.endswith("ditambahkan"))
        unusable = len(notes) - added
        text = f"{added} kartu masuk" + (f", {unusable} dilewati" if unusable else "")
        return _to(msg=text)

    @app.post("/cards/add", dependencies=guard)
    async def cards_add(number: str = Form(...), exp: str = Form(...), cvc: str = Form(...)):
        parsed = vault.parse_card(f"{number}|{exp}|{cvc}")
        if not parsed:
            return _to(err="format kartu tidak valid")
        _, note = await vault.add_card(*parsed)
        return _to(msg=note)

    @app.post("/cards/{card_id}/status", dependencies=guard)
    async def cards_status(card_id: str, dead: int = Form(...)):
        await vault.kill_card(card_id, dead=bool(dead))
        return _to(msg="status kartu diubah")

    @app.post("/cards/{card_id}/delete", dependencies=guard)
    async def cards_delete(card_id: str):
        await vault.delete_card(card_id)
        return _to(msg="kartu dihapus, akun dilepas")

    # ── runs ────────────────────────────────────────────────────────────────
    @app.post("/accounts/{acc_id}/run", dependencies=guard)
    async def accounts_run(acc_id: str):
        ok = await queue.runner.submit(acc_id)
        return _to(msg='masuk antrean' if ok else 'sudah antre/running')

    @app.post("/queue/run-all", dependencies=guard)
    async def queue_run_all():
        rows = await db.fetch_all(
            "SELECT id FROM accounts WHERE status != 'subscribed' AND card_id != '' AND totp_ref != ''"
            " ORDER BY created_at"
        )
        n = await queue.runner.submit_many([r["id"] for r in rows])
        return _to(msg=f"{n} akun masuk antrean")

    @app.post("/queue/run", dependencies=guard)
    async def queue_run_selected(ids: str = Form(default="")):
        wanted = [x.strip() for x in ids.split(",") if x.strip()]
        n = await queue.runner.submit_many(wanted)
        return _to(msg=f"{n} akun masuk antrean")

    @app.post("/queue/stop", dependencies=guard)
    async def queue_stop():
        await queue.runner.stop()
        return _to(msg="stop dikirim")

    @app.get("/api/queue", dependencies=guard)
    async def api_queue() -> JSONResponse:
        return JSONResponse({"current": queue.runner.current, "pending": queue.runner.pending})

    @app.get("/api/log/{acc_id}", dependencies=guard)
    async def api_log(acc_id: str, run: str = "") -> JSONResponse:
        """Log run tertentu (`?run=`) atau log terakhir akun itu."""
        path = await runs.log_path(run) if run else None
        path = path or queue.latest_log(acc_id)
        log = queue.tail(path) if path else ""
        return JSONResponse({"log": log, "size": len(log), "file": path.name if path else ""})

    @app.get("/api/runs/{acc_id}", dependencies=guard)
    async def api_runs(acc_id: str) -> JSONResponse:
        return JSONResponse({"runs": await runs.list_for_account(acc_id, limit=5)})

    @app.get("/api/state", dependencies=guard)
    async def api_state() -> JSONResponse:
        """One request per tick: OTP codes, queue, account rows and the live log.

        The page polls this instead of three separate endpoints, so a refresh
        costs one round trip and every panel is guaranteed to be from the same
        snapshot.
        """
        rows = await db.fetch_all(
            "SELECT id, email, totp_ref, status, step, step_message, expiry_date FROM accounts"
        )
        codes: dict[str, dict[str, object]] = {}
        for row in rows:
            if row["totp_ref"]:
                seed = vault.secret_get(row["totp_ref"])
                if seed:
                    codes[row["id"]] = {"code": vault.totp.code(seed), "left": vault.totp.seconds_left()}

        current = queue.runner.current
        # Setelah run berhenti (termasuk karena gagal) log-nya tetap disajikan.
        # Dulu hanya `current` yang dibaca, jadi panel di browser dikosongkan tepat
        # saat penyebab gagalnya baru muncul — tidak sempat dibaca siapa pun.
        target = current or queue.runner.last
        path = queue.latest_log(target) if target else None
        if path is None:                  # console baru restart: pakai log terbaru
            found = queue.newest_log()
            if found:
                target, path = found
        log, size, run_file, email, status = "", 0, "", "", ""
        if path:
            log = queue.tail(path, lines=200)
            size = len(log)
            run_file = path.name
        if target:
            row = await db.fetch_one("SELECT email, status FROM accounts WHERE id = ?", (target,))
            if row:
                email, status = row["email"], row["status"]
        if current:
            log_state = "running"
        elif target and target == queue.runner.last:
            log_state = queue.runner.last_status
        elif status:
            log_state = status
        else:
            log_state = "idle"

        return JSONResponse({
            "codes": codes,
            "current": current,
            "pending": queue.runner.pending,
            "accounts": {
                r["id"]: {"status": r["status"], "step": r["step"], "message": r["step_message"],
                          "expiry": r["expiry_date"]}
                for r in rows
            },
            "log": log,
            "logSize": size,
            "logAcc": target or "",
            "logEmail": email,
            "logRun": run_file,
            "logState": log_state,
        })

    return app


app = create_app()
