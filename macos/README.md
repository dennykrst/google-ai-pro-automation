# macOS

```bash
cd macos
./run.sh
```

What the script does:

1. `cd` to the project root (all code lives in `app/`, `tasks/`, `tests/`).
2. Finds `python3.13` on `PATH`, then in `/opt/homebrew/bin`.
3. Creates `.venv` if missing, then installs `requirements.lock` with
   `--require-hashes` — every wheel is checked against its sha256.
4. Serves the console on `127.0.0.1:8765` (change with `PORT=9000 ./run.sh`).

Then just open <http://127.0.0.1:8765/> — no token needed on the same machine.

Requirements: **Google Chrome** in `/Applications`, and US egress.

The token only matters if you deliberately open the console to the network:
`GAI_BIND_HOST=0.0.0.0 GAI_ALLOW_REMOTE=1 ./run.sh`, then use the `?t=` printed at
boot (also stored in `~/Library/Application Support/GoogleAIAutomation/console.token`).

Old data from the Keychain-based version can be copied once with:

```bash
../.venv/bin/python ../tools/import_keychain.py
```

Full documentation: [../README.md](../README.md) · [../README.id.md](../README.id.md)
