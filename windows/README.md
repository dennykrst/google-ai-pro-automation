# Windows

```powershell
cd windows
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

Yang dilakukan skrip ini:

1. `Set-Location` ke akar project (semua kode ada di `app/`, `tasks/`, `tests/`).
2. Mencari Python 3.12+ (`py -3.13`, lalu `py -3`, lalu `python`).
3. Membuat `.venv` bila belum ada, lalu `pip install -r requirements.txt`.
4. Menjalankan console di `127.0.0.1:8765` (ubah dengan `$env:PORT=9000`).

Prasyarat: **Google Chrome** terpasang (Playwright memakai `channel="chrome"`,
jadi unduhan browser Playwright tidak diperlukan) dan egress **US**.
Buka `http://127.0.0.1:8765/` — tidak perlu token. Token hanya wajib kalau
console dibuka ke jaringan (`$env:GAI_ALLOW_REMOTE=1`).

Data dir di Windows: `%LOCALAPPDATA%\GoogleAIAutomation`

```
db.sqlite3        metadata akun/kartu
secrets.json      password, seed TOTP, nomor kartu, CVC (izin file 0600)
console.token     token console (hanya dipakai untuk akses dari luar loopback)
profiles\         profil Chrome per akun
artifacts\        log run + screenshot
```

Kalau Python belum ada: pasang dari python.org dan centang *Add python.exe to PATH*.

Catatan: `requirements.lock` (hash-pinned) dibuat di macOS; di Windows versi
tanpa hash dipakai karena wheel-nya beda platform.
