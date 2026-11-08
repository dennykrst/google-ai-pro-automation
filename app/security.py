"""Console access control: localhost-first, token only where it earns its keep.

Kenapa dulu token? Karena `127.0.0.1` bukan batas keamanan:

* proses lokal lain (atau skrip apa pun milik user) bisa memanggil port ini;
* halaman web jahat bisa memakai **DNS rebinding** supaya `evil.com` menunjuk ke
  127.0.0.1, lalu membaca isi console;
* form lintas situs bisa memicu POST (hapus akun, jalankan run) tanpa diminta.

Token menutup ketiganya, tapi harganya: harus menyalin `?t=…` dari log. Sekarang
aturannya empat baris:

1. `Host` wajib loopback (`127.0.0.1`, `::1`, `localhost`) — ini yang menahan
   DNS rebinding. Host lain ditolak kecuali `GAI_ALLOW_REMOTE=1`.
2. Untuk host loopback, **GET/HEAD** langsung diterbitkan cookie — buka
   `http://127.0.0.1:8765/` tanpa `?t=`.
3. **POST tetap butuh cookie/token yang sudah ada.** Cookie `samesite=strict` tidak
   ikut pada request lintas situs, dan kita tidak menerbitkannya di POST, jadi
   form dari halaman lain tetap ditolak.
4. Token wajib kalau console dibuka ke luar loopback (`GAI_ALLOW_REMOTE=1`) atau
   kalau `GAI_REQUIRE_TOKEN=1` dipasang.
"""

from __future__ import annotations

import secrets

from fastapi import Cookie, HTTPException, Query, Request, status

from .config import settings

COOKIE_NAME = "gai_token"

LOCAL_NAMES = {"127.0.0.1", "::1", "localhost"}
SAFE_METHODS = {"GET", "HEAD"}

ALLOW = "allow"        # kredensial sah (cookie/token/header)
ISSUE = "issue"        # loopback + GET: terbitkan cookie sendiri
DENY = "deny"          # Host bukan loopback dan remote tidak diizinkan
REQUIRE = "require"    # butuh token, tidak ada yang sah


def host_is_local(host: str | None) -> bool:
    """True untuk Host header yang menunjuk mesin ini, false untuk yang lain.

    Bentuk yang diterima: `127.0.0.1:8765`, `localhost:8765`, `[::1]:8765`, `::1`.
    `127.0.0.1.nip.io` sengaja **tidak** lolos: itu domain orang lain yang
    kebetulan resolve ke loopback.
    """
    name = (host or "").strip().lower()
    if not name:
        return False
    if name.startswith("["):                     # [::1]:8765
        name = name[1:].split("]", 1)[0]
    elif name.count(":") == 1:                   # 127.0.0.1:8765
        name = name.split(":", 1)[0]
    return name in LOCAL_NAMES


def token_matches(candidate: str | None, expected: str) -> bool:
    if not candidate or not expected:
        return False
    return secrets.compare_digest(candidate, expected)


def decide(
    host: str | None,
    credential_ok: bool,
    *,
    method: str,
    require_token: bool,
    allow_remote: bool,
) -> str:
    """Keputusan murni (tanpa HTTP) supaya bisa diuji di selftest."""
    local = host_is_local(host)
    if not local and not allow_remote:
        return DENY
    if credential_ok:
        return ALLOW
    if local and not require_token and method.upper() in SAFE_METHODS:
        return ISSUE
    return REQUIRE


async def guard_request(
    request: Request,
    t: str | None = Query(default=None),
    gai_token: str | None = Cookie(default=None),
) -> None:
    """Dependency untuk semua rute yang menyentuh data akun/kartu."""
    header = request.headers.get("x-console-token")
    supplied = t or header or gai_token
    ok = token_matches(supplied, settings.console_token)

    verdict = decide(
        request.headers.get("host"),
        ok,
        method=request.method,
        require_token=settings.require_token,
        allow_remote=settings.allow_remote,
    )
    if verdict == DENY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="host tidak diizinkan — set GAI_ALLOW_REMOTE=1 bila memang perlu")
    if verdict == REQUIRE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token required")
    if verdict == ISSUE:
        request.state.set_cookie_token = settings.console_token
    elif t and not token_matches(gai_token, settings.console_token):
        request.state.set_cookie_token = t
