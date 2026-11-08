# Roadmap — handlers and UI

Grounded in what the code actually has, not a wish list. "Needs" points at the
part that already exists so the work is obvious.

## Done (2026-11-08 → 09)

- **Run history per account** — `app/runs.py` fills the `runs`/`artifacts` tables;
  the *log* button opens the last five runs (time, status, egress, failure reason,
  screenshot count) and can read any of their logs.
- **Read an older log** — `GET /api/log/{acc}?run=`, path validated against
  `artifacts/`.
- **Eight-step indicator** next to the status pill.
- **Search + status filter** above the accounts table.
- **Bulk actions** — tick rows → `POST /queue/run` (`ids`).
- **"ends" column** from `accounts.expiry_date`, filled by discovery and after a
  verified cancel.
- **Localized UI** — English by default, Indonesian on request (`app/i18n.py`,
  `/lang/{code}`, `help.en.html` / `help.id.html`).
- **Token-free local access** — loopback `Host` required, cookie issued on `GET`,
  `POST` still needs that cookie, token only for `GAI_ALLOW_REMOTE=1`.

## 1. Small, high value

| # | Item | Why | Needs |
|---|---|---|---|
| 1 | **Download / copy a log** — button in the history dialog | *show log* exists; saving it does not | `GET /api/log?run=` (done) + a `download` button |
| 2 | **Prune old history** (e.g. runs older than 30 days) | `runs`/`artifacts` only grow | `DELETE /api/runs/{id}` + file cleanup |
| 3 | **Subtle motion on the running row** | `running` exists but does not stand out | `tr.running` in CSS |
| 4 | **Remaining-time countdown on `ends`** | "2028-11-08" is less useful than "2 years, 1 month" | derived in JS, data already sent |

## 2. New handlers

| # | Handler | Behaviour | Note |
|---|---|---|---|
| 5 | explicit `resume` | "continue from step N" button in the UI | `subscribe_flow.py` already takes `--from`; pass it from `queue._run` |
| 6 | `recovery` | fill/confirm the recovery email when Google asks | `login.pass_screens()` already has the `SKIP_SEL` branch |
| 7 | `card verify` | after `cancel`, confirm the card is really gone and record the result | `detach_on_google()` already returns a bool — store it |
| 8 | `retry policy` | two attempts per handler with backoff, not a full re-run | wrap the handler calls in `run_layers()` |
| 9 | `expiry cache` | read `expiry_date` first; at 24 months go straight to cancel | avoids a run that can only be rejected |
| 10 | `preflight` | card active, profile opens, egress US, account not already `subscribed` | fail fast with a clear message instead of mid-checkout |

## 3. Observability

| # | Item | Why |
|---|---|---|
| 11 | Per-handler duration and success rate in the header | tells a systemic problem from a single bad account |
| 12 | Local notification when a run finishes or fails (macOS `osascript`, Windows toast) | runs are long; nobody wants to watch the tab |
| 13 | CSV export (email, status, end date, exit code) | stocktaking |
| 14 | Aggregate `runs` in the header (e.g. last 7 days: 4 ok / 3 failed) | `runs` is populated now, it just needs a query |

## 4. Security and operations

| # | Item | Why |
|---|---|---|
| 15 | Optional encryption of `secrets.json` (passphrase-derived key) | the file may end up in a backup or sync folder |
| 16 | Single-instance detection (lock file in the data dir) | two consoles could run the same account at once |
| 17 | Rotate `console.token` from the UI | it currently only changes on disk/boot |
| 18 | CI: `ruff` + `tests/selftest.py` on GitHub Actions | UI/handler refactors are easy to break quietly |
| 19 | Optional cleanup of Chrome profiles for `subscribed` accounts | profiles keep login cookies on disk |

## Deliberately not doing

- Parallel logins. Several Google logins at once from one egress burn IP reputation
  faster; the serial queue stays.
- Storing full card numbers in the database. `secrets.json` plus refs is enough and
  keeps `/api` from ever returning a PAN.
- Captcha bypass. That stays with the human in the Chrome window.
