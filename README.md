# Google AI Pro Automation

A local console that runs the whole Google AI Pro 2-year flow for one account at
a time: sign in, bind a card when Google asks for one, take the stacked offers,
check the end date after every step, cancel the renewal, then take the card back
off the account.

English · [Bahasa Indonesia](README.id.md)

It runs on **macOS and Windows**. Python 3.12+, and Playwright drives **real Google
Chrome** (`channel="chrome"`) rather than a bundled Chromium — the payment dialog
only behaves normally there.

Repo: <https://github.com/dennykrst/google-ai-pro-automation>

## What it actually does

One account, one process, one pass through these handlers. Nothing is clicked
before the screen has been read, and every step has a check that aborts instead of
charging something unexpected.

| # | Handler | What it does | Check before continuing |
|---|---|---|---|
| 0 | `egress` | loads an IP service inside the browser to see where traffic exits | country must be **US**; waits up to 120 s |
| 1 | `login` | email → password → TOTP, including captcha, recovery prompts and device prompts | URL has left `accounts.google.com` |
| 2 | `discover` | reads the current end date from the cancel dialog *without* confirming it | 0 mo → offer 1 · 12 → offer 2 · 18 → offer 3 · 24 → try offer 4 once |
| 3 | `bind card` | Add card → number, expiry, CVC, holder, ZIP → save, only when the dialog asks | each field is read back and retyped if it did not stick |
| 4 | `offer 1` | opens the offer dialog, reads the total, presses Subscribe | total `$0.00` or the 12-month trial label |
| 5 | `offer 2` | upgrades to the 18-month term | end date within a day of +18 months |
| 6 | `offer 3` | upgrades to the 24-month term | end date within a day of +24 months |
| 7 | `cancel` | Play → Manage → Cancel subscription → confirm | status reads `Canceled` and the end date is visible |
| 8 | `detach card` | removes the card from the account's payment profile | best effort; waits up to 300 s for your approval |

Because of handler 2, a run that was interrupted is safe to repeat: the console
reads what is actually active and picks up from there instead of starting over.

## Where it comes from

Written from scratch on top of two existing projects, with an emphasis on being
auditable and hard to break:

- <https://github.com/worldonlyu/Google_AI_Pro_2Year_ZeroCost_Auto> — a one-click
  Windows runner (`.bat`) for the three offers plus cancel.
- <https://github.com/ade1256/google-ai-pro-farming-2-years> — the earlier local
  console (macOS, secrets in the Keychain) that this project grew out of.

| | earlier console | this project |
|---|---|---|
| OS | macOS only | **macOS + Windows**, one shared core, two launchers |
| Secrets | macOS Keychain via `security` — prompts in the terminal | **local `secrets.json` (0600)**, no OS API, no prompt |
| Queue | one run at a time, by hand | serial queue, *run all* and *run selected* |
| Resuming | starts from the beginning | **discovery** reads the live term and picks the next offer |
| Cost guard | dialog check | `$0.00` **and** a date check per offer before committing |
| Cards | one global card | **rotating pool**, least-recently-used wins |
| After cancel | subscription stops | **card is detached** from the account, kept for the next one |
| Logs | scrollback | log panel in the browser; a failed run is **not cleared**, the cause line is highlighted |
| Run history | none | last five runs per account: status, egress, reason, screenshots, any log |
| Dependencies | loose | 9 packages, `requirements.lock` **sha256-pinned**, no pyotp/keyring |
| Tests | manual | `tests/selftest.py` (TOTP RFC 6238, vault, runs, i18n, access policy) |

Extras neither project has: `--dry` (stop before every Subscribe), card entry that
survives browser autofill, and masking — the UI and logs never show a full card
number, CVC or password.

## Deliberate limits

- Binds to `127.0.0.1` only. A session cookie is issued automatically; the token is
  only needed when you deliberately open it to the network (`GAI_ALLOW_REMOTE=1`).
- No telemetry. No outbound calls beyond Google and `ipwho.is` (the country check).
- A few moments still need you on the phone: the login device prompt, the approval
  to remove a card, and an image captcha. Skipping them leaves the subscription
  active and the cancel still runs — only the card stays on the account.
- This automates accounts **you own**. Use it for your own accounts and cards.

## Requirements

- **Google Chrome** installed.
- US egress (VPN). The flow waits up to 120 s for the right country, then stops.
- Python 3.12+ (`brew install python@3.13` on macOS, python.org on Windows).
- Accounts (`email|password|totp-secret`) and cards (`number|MM/YY|CVC`) — both go in
  through the UI and stay in the local secret store.

## Run it

```bash
git clone https://github.com/dennykrst/google-ai-pro-automation.git
cd google-ai-pro-automation
```

| OS | Command |
|---|---|
| macOS | `cd macos && ./run.sh` |
| Windows | `cd windows` then `powershell -ExecutionPolicy Bypass -File .\run.ps1` |

Both launchers create `.venv` if needed, install dependencies, and serve the
console on `127.0.0.1:8765`. Just open:

```
http://127.0.0.1:8765/
```

Data dir: macOS `~/Library/Application Support/GoogleAIAutomation`, Windows
`%LOCALAPPDATA%\GoogleAIAutomation`. An older `.../GaiConsole` data dir is moved
automatically on the first boot, so accounts, cards and token carry over.

If you open the console to the network (`GAI_BIND_HOST=0.0.0.0 GAI_ALLOW_REMOTE=1`),
every request needs the token — it is in `console.token` in the data dir and
printed at boot as `?t=…`.

## Using the console

1. Import cards: `number|MM/YY|CVC`, one per line or one at a time.
2. Import accounts: `email|password|totp-secret`, same idea.
3. Press **run** on an account, or **run all** / tick rows and **run selected**.

The header has an **EN / ID** switch; English is the default. The **help** button
opens `/help`, which is the same content as this file but with the details worth
having next to the buttons: handler list, log markers, data dir.

| Column | Meaning |
|---|---|
| `status` | `pending` → `running` → `subscribed` (cancel verified) · `failed` · `cancelled` · `dead` |
| eight dots | handler step; the green dot is the last one that ran |
| `ends` | end date read during discovery or cancel; `—` if never read |
| `otp` | current TOTP code and its remaining time |
| `card` | brand and last four digits only |

The log panel shows the live run **and** the last run after it ends. A failed run
keeps its log on screen, highlights the cause line and summarises it underneath.
The **log** button on each row opens the last five runs — time, status, egress,
failure reason, screenshot count — with a button to read any of those logs.

## Data and access

Everything lives in the data dir; nothing else is written and nothing leaves the
machine except the Google traffic and the IP check.

| File | Contents |
|---|---|
| `db.sqlite3` | account and card metadata — never the card number or CVC |
| `secrets.json` | passwords, TOTP secrets, card numbers, CVC (mode 0600) |
| `console.token` | access token, only used for non-loopback access |
| `profiles/` | one Chrome profile per account (login cookies) |
| `artifacts/` | run logs and per-offer screenshots |

Access rules, briefly: the `Host` header must be loopback (that is what blocks DNS
rebinding), loopback `GET` requests get a session cookie automatically, `POST`
still requires that cookie, and a foreign `Host` is refused unless you opt in with
`GAI_ALLOW_REMOTE=1`.

The protection for `secrets.json` is file permissions, not a system keychain.
Anyone running as your user can read it. Old Keychain data can be copied over once
with `tools/import_keychain.py` (macOS only; the app itself never touches it).

## Layout

```
app/                 shared core (both OSes)
  main.py            routes, queue, /help, /lang
  config.py          settings, per-platform data dir
  db.py              SQLite schema + idempotent migrations
  runs.py            run history and artifacts
  vault.py           accounts & cards (values in secrets.json)
  secrets.py         local secret store (JSON 0600, no OS API)
  i18n.py            UI strings: English + Indonesian
  totp.py            stdlib TOTP
  egress.py          country check
  security.py        access policy (loopback, cookie, token)
  runner/            browser, navigation retries, queue
  sites/google_one/  login, checkout, discovery, hook, tokens
  templates/         index.html, help.en.html, help.id.html
macos/run.sh         macOS launcher (+ README)
windows/run.ps1      Windows launcher (+ README)
tasks/               subscribe_flow, cancel, probe
requirements.txt     unpinned dependency list (Windows)
requirements.lock    sha256-pinned lock (macOS)
tests/selftest.py
tools/make_lock.py   builds requirements.lock
tools/import_keychain.py  one-off migration from the Keychain
docs/ROADMAP.md      what is done and what is next
```

The core is deliberately **not** duplicated into `macos/` and `windows/`: only the
venv setup, the Python/Chrome lookup and the data dir differ. One copy of the code
means one place to fix a bug.
