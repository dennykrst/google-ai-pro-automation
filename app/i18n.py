"""UI language: English by default, Indonesian on request.

Semua teks yang tampil di web ada di sini — bukan di template — supaya dua bahasa
tidak pernah menyimpang. Default English; ganti lewat tombol EN/ID di header
(cookie `gai_lang`), atau set `GAI_LANGUAGE=id` untuk default Indonesia.

Catatan: log run (`tasks/*.py`) tetap berbahasa Indonesia. Itu keluaran diagnostik
dari proses terpisah, bukan bagian UI.
"""

from __future__ import annotations

from fastapi import Request

from .config import settings

LANG_COOKIE = "gai_lang"
LANGS = ("en", "id")
DEFAULT = "en"

TEXTS: dict[str, dict[str, str]] = {
    "en": {
        # ── chrome / header ────────────────────────────────────────────────
        "app.name": "Google AI Pro Automation",
        "app.tagline": "local vault & runner",
        "nav.help": "help",
        "nav.run_all": "run all",
        "nav.stop": "stop",
        "stats.pair": "{accounts} accounts · {cards} cards",
        "state.running": "running: {id}",
        "state.queued": "{n} queued",
        "state.idle": "idle",
        "state.offline": "connection lost",
        # ── accounts panel ────────────────────────────────────────────────
        "accounts.title": "Accounts",
        "accounts.hint": "One per line: <code>email|password|totp-secret</code>. "
                         "Passwords and seeds stay in the data dir (file mode 0600); "
                         "the page only ever shows the current code.",
        "accounts.import": "Import",
        "accounts.add": "Add",
        "accounts.email": "email",
        "accounts.password": "password",
        "accounts.seed": "TOTP secret (optional)",
        "accounts.search": "search email…",
        "accounts.filter": "filter status",
        "accounts.filter_all": "all statuses",
        "accounts.run_selected": "run selected",
        "accounts.run_selected_n": "run selected ({n})",
        "accounts.pick_all": "select every account",
        "accounts.pick_one": "select {email}",
        "accounts.show_pw": "show password for {email}",
        "accounts.reveal": "show",
        "accounts.hide": "hide",
        "accounts.reveal_failed": "(failed)",
        "accounts.empty": "no accounts yet",
        "accounts.col_email": "email",
        "accounts.col_password": "password",
        "accounts.col_otp": "otp",
        "accounts.col_card": "card",
        "accounts.col_expiry": "ends",
        "accounts.col_status": "status",
        "accounts.run": "run",
        "accounts.delete": "delete",
        "accounts.history": "run history",
        "accounts.history_short": "log",
        "accounts.step_title": "step {step} of 8",
        "accounts.no_card": "none",
        "accounts.confirm_delete": "delete {email}?",
        # ── cards panel ───────────────────────────────────────────────────
        "cards.title": "Cards",
        "cards.hint": "One per line: <code>number|MM/YY|CVC</code>. Number and CVC go to "
                      "the local store (file mode 0600); only the last four digits are "
                      "shown. Cards rotate: the account takes the active card that has "
                      "gone longest unused.",
        "cards.import": "Import",
        "cards.add": "Add",
        "cards.number": "card number",
        "cards.exp": "MM/YY",
        "cards.cvc": "CVC",
        "cards.col_card": "card",
        "cards.col_exp": "exp",
        "cards.col_used": "used",
        "cards.col_status": "status",
        "cards.used": "{n} accounts",
        "cards.disable": "disable",
        "cards.enable": "enable",
        "cards.empty": "no cards yet",
        "cards.confirm_disable": "disable {label}? accounts using it will be released.",
        "cards.confirm_delete": "delete card {label}?",
        # ── log panel ─────────────────────────────────────────────────────
        "log.title": "Run log",
        "log.follow_on": "auto-scroll: on",
        "log.follow_off": "auto-scroll: off",
        "log.empty": "(no run yet)",
        "log.state_running": "running",
        "log.state_failed": "failed (log kept)",
        "log.state_stopped": "stopped",
        "log.state_done": "done",
        "log.failed_hint": "last run failed · {why}",
        "log.failed_hint_bare": "last run failed · log kept below so you can read it",
        # ── history dialog ────────────────────────────────────────────────
        "hist.title": "Run history",
        "hist.close": "close",
        "hist.loading": "loading…",
        "hist.empty": "no run recorded yet",
        "hist.failed_load": "could not load history",
        "hist.show_log": "show log",
        "hist.shots": "{n} screenshots",
        "hist.log_empty": "(empty log)",
        "hist.log_failed": "(could not load log)",
        # ── flash messages (server side) ──────────────────────────────────
        "flash.close": "close",
        "msg.accounts_imported": "{added} accounts added",
        "msg.accounts_imported_skipped": "{added} accounts added, {skipped} skipped",
        "msg.cards_imported": "{added} cards added",
        "msg.cards_imported_skipped": "{added} cards added, {skipped} skipped",
        "msg.account_added": "{email} added",
        "msg.account_updated": "{email} was already there — updated",
        "msg.account_invalid": "invalid line: {value}",
        "msg.account_deleted": "account deleted",
        "msg.card_added": "{label} added",
        "msg.card_exists": "{label} is already in the vault",
        "msg.card_invalid": "card number is not valid",
        "msg.card_bad_format": "card format is not valid",
        "msg.card_deleted": "card deleted, accounts released",
        "msg.card_status": "card status changed",
        "msg.queued": "{n} accounts queued",
        "msg.queue_ok": "queued",
        "msg.queue_dup": "already queued or running",
        "msg.stop_sent": "stop sent",
    },
    "id": {
        # ── chrome / header ────────────────────────────────────────────────
        "app.name": "Google AI Pro Automation",
        "app.tagline": "vault & runner lokal",
        "nav.help": "bantuan",
        "nav.run_all": "jalankan semua",
        "nav.stop": "stop",
        "stats.pair": "{accounts} akun · {cards} kartu",
        "state.running": "jalan: {id}",
        "state.queued": "{n} antre",
        "state.idle": "idle",
        "state.offline": "koneksi terputus",
        # ── accounts panel ────────────────────────────────────────────────
        "accounts.title": "Akun",
        "accounts.hint": "Satu per baris: <code>email|password|seed-totp</code>. Password "
                         "dan seed tetap di data dir (mode file 0600); halaman ini hanya "
                         "menampilkan kode yang sedang berlaku.",
        "accounts.import": "Impor",
        "accounts.add": "Tambah",
        "accounts.email": "email",
        "accounts.password": "password",
        "accounts.seed": "seed TOTP (opsional)",
        "accounts.search": "cari email…",
        "accounts.filter": "filter status",
        "accounts.filter_all": "semua status",
        "accounts.run_selected": "jalankan terpilih",
        "accounts.run_selected_n": "jalankan terpilih ({n})",
        "accounts.pick_all": "pilih semua akun",
        "accounts.pick_one": "pilih {email}",
        "accounts.show_pw": "lihat password {email}",
        "accounts.reveal": "lihat",
        "accounts.hide": "sembunyikan",
        "accounts.reveal_failed": "(gagal)",
        "accounts.empty": "belum ada akun",
        "accounts.col_email": "email",
        "accounts.col_password": "password",
        "accounts.col_otp": "otp",
        "accounts.col_card": "kartu",
        "accounts.col_expiry": "berakhir",
        "accounts.col_status": "status",
        "accounts.run": "jalankan",
        "accounts.delete": "hapus",
        "accounts.history": "riwayat run",
        "accounts.history_short": "log",
        "accounts.step_title": "langkah {step} dari 8",
        "accounts.no_card": "belum",
        "accounts.confirm_delete": "hapus {email}?",
        # ── cards panel ───────────────────────────────────────────────────
        "cards.title": "Kartu",
        "cards.hint": "Satu per baris: <code>nomor|MM/YY|CVC</code>. Nomor dan CVC masuk "
                      "penyimpanan lokal (mode file 0600); yang tampil hanya empat digit "
                      "terakhir. Kartu dipakai bergilir: akun mengambil kartu aktif yang "
                      "paling lama tidak terpakai.",
        "cards.import": "Impor",
        "cards.add": "Tambah",
        "cards.number": "nomor kartu",
        "cards.exp": "MM/YY",
        "cards.cvc": "CVC",
        "cards.col_card": "kartu",
        "cards.col_exp": "exp",
        "cards.col_used": "dipakai",
        "cards.col_status": "status",
        "cards.used": "{n} akun",
        "cards.disable": "matikan",
        "cards.enable": "hidupkan",
        "cards.empty": "belum ada kartu",
        "cards.confirm_disable": "matikan {label}? akun yang memakainya akan dilepas.",
        "cards.confirm_delete": "hapus kartu {label}?",
        # ── log panel ─────────────────────────────────────────────────────
        "log.title": "Log run",
        "log.follow_on": "auto-scroll: on",
        "log.follow_off": "auto-scroll: off",
        "log.empty": "(belum ada run)",
        "log.state_running": "berjalan",
        "log.state_failed": "gagal (log disimpan)",
        "log.state_stopped": "dihentikan",
        "log.state_done": "selesai",
        "log.failed_hint": "run terakhir gagal · {why}",
        "log.failed_hint_bare": "run terakhir gagal · log dibiarkan di bawah untuk dibaca",
        # ── history dialog ────────────────────────────────────────────────
        "hist.title": "Riwayat run",
        "hist.close": "tutup",
        "hist.loading": "memuat…",
        "hist.empty": "belum ada run tercatat",
        "hist.failed_load": "gagal memuat riwayat",
        "hist.show_log": "lihat log",
        "hist.shots": "{n} screenshot",
        "hist.log_empty": "(log kosong)",
        "hist.log_failed": "(gagal memuat log)",
        # ── flash messages (server side) ──────────────────────────────────
        "flash.close": "tutup",
        "msg.accounts_imported": "{added} akun masuk",
        "msg.accounts_imported_skipped": "{added} akun masuk, {skipped} dilewati",
        "msg.cards_imported": "{added} kartu masuk",
        "msg.cards_imported_skipped": "{added} kartu masuk, {skipped} dilewati",
        "msg.account_added": "{email} ditambahkan",
        "msg.account_updated": "{email} sudah ada — diperbarui",
        "msg.account_invalid": "baris tidak valid: {value}",
        "msg.account_deleted": "akun dihapus",
        "msg.card_added": "{label} ditambahkan",
        "msg.card_exists": "{label} sudah ada di vault",
        "msg.card_invalid": "nomor kartu tidak valid",
        "msg.card_bad_format": "format kartu tidak valid",
        "msg.card_deleted": "kartu dihapus, akun dilepas",
        "msg.card_status": "status kartu diubah",
        "msg.queued": "{n} akun masuk antrean",
        "msg.queue_ok": "masuk antrean",
        "msg.queue_dup": "sudah antre atau berjalan",
        "msg.stop_sent": "stop dikirim",
    },
}


def resolve(request: Request | None = None) -> str:
    """Language for this request: cookie → setting → default."""
    if request is not None:
        code = (request.cookies.get(LANG_COOKIE) or "").lower()
        if code in LANGS:
            return code
    code = (settings.language or "").lower()
    return code if code in LANGS else DEFAULT


def t(key: str, lang: str = DEFAULT, **params: object) -> str:
    table = TEXTS.get(lang) or TEXTS[DEFAULT]
    text = table.get(key) or TEXTS[DEFAULT].get(key) or key
    if not params:
        return text
    try:
        return text.format(**params)
    except (KeyError, IndexError):
        return text


def js_strings(lang: str) -> dict[str, str]:
    """Subset yang dipakai JavaScript runtime (bukan untuk HTML)."""
    keys = (
        "state.running", "state.queued", "state.idle", "state.offline",
        "accounts.run_selected", "accounts.run_selected_n",
        "accounts.reveal", "accounts.hide", "accounts.reveal_failed",
        "log.follow_on", "log.follow_off", "log.empty",
        "log.state_running", "log.state_failed", "log.state_stopped", "log.state_done",
        "log.failed_hint", "log.failed_hint_bare",
        "hist.title", "hist.loading", "hist.empty", "hist.failed_load",
        "hist.show_log", "hist.shots", "hist.log_empty", "hist.log_failed",
    )
    return {k: t(k, lang) for k in keys}
