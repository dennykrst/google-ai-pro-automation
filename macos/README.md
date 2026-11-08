# macOS

```bash
cd macos
./run.sh
```

Yang dilakukan skrip ini:

1. `cd` ke akar project (semua kode ada di `app/`, `tasks/`, `tests/`).
2. Mencari `python3.13` (PATH dulu, lalu `/opt/homebrew/bin`).
3. Membuat `.venv` bila belum ada, lalu memasang `requirements.lock` dengan
   `--require-hashes` — setiap wheel dicocokkan sha256-nya.
4. Menjalankan console di `127.0.0.1:8765` (ubah dengan `PORT=9000 ./run.sh`).

Prasyarat: **Google Chrome** asli di `/Applications` dan egress **US**.
Buka `http://127.0.0.1:8765/` — tidak perlu token.

Token hanya relevan kalau console sengaja dibuka ke jaringan:
`GAI_BIND_HOST=0.0.0.0 GAI_ALLOW_REMOTE=1 ./run.sh`, lalu pakai `?t=` dari log
boot (juga tersimpan di `~/Library/Application Support/GoogleAIAutomation/console.token`).

Punya data lama (versi Keychain)? Salin sekali:

```bash
../.venv/bin/python ../tools/import_keychain.py
```
