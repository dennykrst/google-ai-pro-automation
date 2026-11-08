# Windows

```powershell
cd windows
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

What the script does:

1. `Set-Location` to the project root (all code lives in `app/`, `tasks/`, `tests/`).
2. Looks for Python 3.12+ (`py -3.13`, then `py -3`, then `python`).
3. Creates `.venv` if missing, then `pip install -r requirements.txt`.
4. Serves the console on `127.0.0.1:8765` (change with `$env:PORT=9000`).

Then just open <http://127.0.0.1:8765/> — no token needed on the same machine.

Requirements: **Google Chrome** installed (Playwright uses `channel="chrome"`, so
no extra browser download), and US egress.

Data dir on Windows: `%LOCALAPPDATA%\GoogleAIAutomation`

```
db.sqlite3        account/card metadata
secrets.json      passwords, TOTP secrets, card numbers, CVC (file mode 0600)
console.token     access token (only for access from outside loopback)
profiles\         one Chrome profile per account
artifacts\        run logs and screenshots
```

If Python is missing: install it from python.org and tick *Add python.exe to PATH*.

Note: `requirements.lock` is hash-pinned and built on macOS, so Windows uses the
unpinned list instead — the wheels differ per platform.

Full documentation: [../README.md](../README.md) · [../README.id.md](../README.id.md)
