# Google AI Pro Automation

Konsol lokal untuk menjalankan alur **Google AI Pro 2 tahun tanpa biaya** pada
banyak akun Google sekaligus: login, pasang kartu, tiga lapis paket, verifikasi
tanggal, lalu cancel otomatis — satu akun per satu proses, berurutan.

Jalan di **macOS dan Windows**. Python 3.12+, Playwright yang mengendalikan
**Google Chrome asli** (`channel="chrome"`), bukan Chromium bawaan Playwright,
supaya dialog pembayaran Google tampil seperti pemakaian normal.

Repo: <https://github.com/dennykrst/google-ai-pro-automation>

## Apa yang dikerjakan

Satu klik per akun menjalankan rantai handler berikut. Semua handler membaca
layar dulu, baru menekan tombol — kalau angka atau tanggal tidak sesuai, alur
berhenti alih-alih menagih sesuatu yang salah.

| # | Handler | Yang dilakukan | Guard sebelum lanjut |
|---|---|---|---|
| 0 | `egress` | cek IP + negara lewat `ipwho.is` di dalam browser | wajib **US**, tunggu maks 120 s |
| 1 | `login` | email → password → TOTP, termasuk captcha, prompt pemulihan, device prompt | keluar dari `accounts.google.com` |
| 2 | `discover` | baca tanggal akhir langganan dari dialog cancel (tanpa konfirmasi) | 0 bln→L1 · 12→L2 · 18→L3 · 24→L4 sekali |
| 3 | `bind card` | Add card → nomor, kedaluwarsa, CVC, nama, ZIP → simpan | tiap kolom dibaca ulang, nilai salah diketik ulang |
| 4 | `layer 1` | buka dialog penawaran, tekan *Subscribe* | total `$0.00` / label *12-month free trial* |
| 5 | `layer 2` | upgrade ke paket 18 bulan | tanggal akhir ±18 bulan (±1 hari) |
| 6 | `layer 3` | upgrade ke paket 24 bulan | tanggal akhir ±24 bulan |
| 7 | `cancel` | Play → Manage → Cancel subscription → konfirmasi | status `Canceled` + tanggal berakhir |
| 8 | `detach card` | hapus kartu dari profil pembayaran akun | best effort, tunggu persetujuan di HP |

Yang membedakan dari "jalankan skrip lalu berharap": setiap handler punya
**guard** dan setiap kegagalan menyebutkan alasannya di log (`GUARD`, `VERIF`,
`KARTU`, `CANCEL`), jadi run yang gagal bisa didiagnosis tanpa menebak.

## Asal & pembeda

Ditulis ulang dari dua proyek yang sudah ada, dengan fokus pada ketahanan dan
kemudahan audit:

- <https://github.com/worldonlyu/Google_AI_Pro_2Year_ZeroCost_Auto> — runner
  Windows satu-klik (`.bat`) untuk tiga lapis paket + cancel.
- <https://github.com/ade1256/google-ai-pro-farming-2-years> — konsol lokal versi
  awal (macOS, secret di Keychain) yang menjadi kerangka proyek ini.

| Aspek | Versi awal (acuan) | Proyek ini |
|---|---|---|
| OS | macOS saja | **macOS + Windows** (satu inti, dua launcher) |
| Penyimpanan secret | macOS Keychain via CLI `security` — prompt di terminal | **`secrets.json` lokal 0600**, tanpa API OS, tanpa prompt |
| Antrean | satu run manual | antrean serial + tombol *jalankan semua* |
| Melanjutkan run terputus | mulai dari awal | **discovery** membaca term yang sedang berjalan lalu memilih layer |
| Guard biaya | cek dialog | `$0.00` **dan** cek tanggal per layer sebelum commit |
| Kartu | satu kartu global | **pool kartu berputar**, dipakai bergilir ke akun berikutnya |
| Setelah cancel | langganan berhenti | **kartu dilepas** dari akun, tetap tersimpan untuk akun berikutnya |
| Log | teks di terminal | panel log di browser; run gagal **tidak dikosongkan**, baris penyebab disorot |
| Dependensi | bebas | 9 paket, `requirements.lock` **ber-hash sha256**, tanpa pyotp/keyring |
| Uji | manual | `tests/selftest.py` (TOTP RFC 6238, vault, migrasi DB) |

Tambahan yang tidak ada di keduanya: **`--dry`** (berhenti sebelum setiap
*Subscribe*), **pengisian kartu yang tahan autofill**, dan **masking**: UI dan log
tidak pernah menampilkan nomor kartu utuh, CVC, atau password.

## Batasan yang disengaja

- Hanya mendengarkan di `127.0.0.1` dan wajib token 43 karakter (`?t=` → cookie).
- Tidak ada telemetri, tidak ada panggilan keluar selain Google dan `ipwho.is`.
- Beberapa titik tetap butuh manusia di HP (device prompt login, persetujuan hapus
  kartu, captcha gambar). Kalau tidak disetujui, langganan tetap aktif dan cancel
  tetap berjalan — hanya kartu tertinggal di akun.
- Alat ini mengotomasi akun yang **kamu** punya. Pakai hanya untuk akun dan kartu
  milik sendiri.

## Postur keamanan

Dependensi langsung dijaga seminimal mungkin — **9 paket**, semuanya
repositori kanonik:

| paket | pemelihara |
|---|---|
| fastapi, uvicorn | Encode / `fastapi/fastapi` |
| jinja2 | Pallets |
| pydantic, pydantic-settings | `pydantic/*` |
| aiosqlite | omnilib |
| psutil | Giampaolo Rodola |
| playwright | Microsoft |
| python-multipart | Encode |

Yang sengaja **tidak** dipakai:

- `keyring` / CLI `security` → secret disimpan sendiri di `secrets.json`, tanpa
  menyentuh Keychain atau API OS apa pun. Lihat catatan di bawah.
- `pyotp` → TOTP RFC 6238 ditulis dengan `hmac`+`base64` stdlib, diuji
  terhadap vektor RFC 6238 Appendix B (`tests/selftest.py`).
- `email-validator` → regex sederhana, cukup untuk alamat Google.
- `uvicorn[standard]` → `uvicorn` polos, membuang httptools/uvloop/watchfiles/
  websockets/pyyaml.

Pengerasan lain:

- `requirements.lock` di-pin penuh **dengan sha256**, dipasang lewat
  `pip install --require-hashes`. Rilis baru yang dibajak tidak bisa masuk
  tanpa hash cocok. Lock ini khusus macOS; Windows memakai `requirements.txt`.
- Console butuh token 43-char (`?t=` → cookie), dibandingkan constant-time.
  Tanpa token, daftar akun tidak bisa dibaca proses lokal lain.
- Data dir `0700`, `db.sqlite3`, `console.token` dan `secrets.json` `0600`.
- Password, seed TOTP, nomor kartu, dan CVC **hanya** di `secrets.json` di dalam
  data dir. Nol ketergantungan OS: modul `app/secrets.py` cuma menulis JSON
  (tulis atomik, mode 0600) — sama persis di macOS dan Windows. Tabel `accounts`
  menyimpan handle (`secret_ref`, `totp_ref`), bukan nilai.
- `privacy: /api` tidak pernah mengembalikan nomor kartu utuh atau CVC.

### Soal Keychain

Versi lama memakai Keychain macOS lewat CLI `security`. Itu dihapus total karena
dua hal: `add-generic-password -w` membaca nilai dari **terminal** (bukan stdin),
sehingga impor akun menggantung menunggu ketikan; dan tidak bisa dipakai di
Windows.

Perlindungan `secrets.json` = izin file, bukan kontrol akses per-aplikasi
Keychain. Punya data lama di Keychain? Salin **sekali** dengan skrip opsional:

```bash
.venv/bin/python tools/import_keychain.py    # macOS saja, tidak dipakai aplikasi
```

## Yang dibutuhkan

- **Google Chrome** asli terpasang.
- Egress **US** (VPN). Alur menunggu sampai 120 detik lalu berhenti kalau bukan US.
- Python 3.12+ (macOS: `brew install python@3.13`; Windows: python.org).
- Stok akun (`email|password|seed TOTP`) dan kartu (`nomor|MM/YY|CVC`) — keduanya
  masuk lewat UI, nilainya disimpan lokal di `secrets.json`.

## Jalankan

```bash
git clone https://github.com/dennykrst/google-ai-pro-automation.git
cd google-ai-pro-automation
```

| OS | Perintah |
|---|---|
| macOS | `cd macos && ./run.sh` |
| Windows | `cd windows` lalu `powershell -ExecutionPolicy Bypass -File .\run.ps1` |

Kedua launcher membuat `.venv` bila belum ada, memasang dependensi, lalu
menyajikan konsol di `127.0.0.1:8765`. Buka:

```
http://127.0.0.1:8765/?t=<isi console.token di data dir>
```

Data dir: macOS `~/Library/Application Support/GoogleAIAutomation`,
Windows `%LOCALAPPDATA%\GoogleAIAutomation`. Token juga dicetak di log saat boot.

Data dir lama (`.../GaiConsole`) dipindahkan otomatis sekali saat boot pertama,
jadi akun, kartu, dan token console tidak hilang setelah project di-rename.

## Cara pakai

1. Impor kartu: `nomor|MM/YY|CVC` (satu per baris atau satu per satu).
2. Impor akun: `email|password|seed_totp` (format sama).
3. Tekan **jalankan** pada akun, atau **jalankan semua** untuk antrean berurutan.

Konsol punya tiga bagian: **Akun** (status, OTP berjalan, password bisa
dilihat sekali klik, tombol jalankan/hapus), **Kartu** (pool kartu + berapa akun
memakainya), dan **Log run**.

Arti kolom di tabel akun:

| Kolom | Isi |
|---|---|
| `status` | `pending` → `running` → `subscribed` (cancel terverifikasi) / `failed` / `cancelled` / `dead` |
| titik di sebelah status | 8 langkah handler; titik hijau = langkah terakhir |
| `berakhir` | tanggal akhir langganan dari discovery/cancel; `—` kalau belum pernah terbaca |
| `otp` | kode TOTP yang sedang berlaku + bar sisa waktu |
| `kartu` | brand + 4 digit terakhir; nomor utuh tidak pernah dikirim ke browser |

Di atas tabel ada pencarian email, filter status, dan **jalankan terpilih**
(centang baris, atau centang header untuk memilih semua). Tombol **log** di tiap
baris membuka riwayat 5 run terakhir — waktu, status, egress, ringkasan penyebab
gagal, jumlah screenshot, dan tombol untuk membaca log run mana pun. Riwayat ini
disimpan di tabel `runs`/`artifacts`, jadi tetap ada setelah console di-restart.

Panel log menampilkan run yang sedang jalan **dan** run terakhir setelah selesai;
kalau run gagal, baris penyebabnya disorot dan diringkas di bawah panel, jadi log
tidak hilang sebelum sempat dibaca.

Tombol **bantuan** di header membuka `http://127.0.0.1:8765/help` — daftar handler,
format input, arti tiap penanda log, dan isi data dir, tanpa harus buka README.

Alur per akun: login → discovery term berjalan → layer 1–4 → guard tanggal →
cancel → lepas kartu dari akun (kartu tetap di vault untuk akun berikutnya).

Discovery memilih titik mulai sendiri: 0 bulan → layer 1, 12 → layer 2, 18 → layer 3,
24 → hanya mencoba layer 4 lalu cancel. Jadi run yang terputus aman diulang.

Dua titik tetap butuh tangan manusia di HP, dan keduanya ditunggu (5 menit login,
300 detik hapus kartu): device prompt saat login, dan persetujuan verifikasi saat
menghapus kartu. Kalau tidak disetujui, langganan tetap aktif 24 bulan dan cancel
tetap berjalan — hanya kartu tertinggal di akun.

## Struktur

```
app/                 inti bersama (dipakai kedua OS)
  main.py            rute halaman + antrean + /help
  config.py          settings, data dir per platform, token console
  db.py              skema SQLite + migrasi idempoten
  runs.py            riwayat run + artifact (log, screenshot) untuk UI
  vault.py           akun & kartu (nilai di secrets.json)
  secrets.py         penyimpanan secret lokal (JSON 0600, tanpa API OS)
  totp.py            TOTP stdlib
  egress.py          cek negara egress
  runner/            browser, navigasi berulang, antrean
  sites/google_one/  login, checkout, discovery, hook, tokens
  templates/index.html  konsol
  templates/help.html   panduan di dalam aplikasi
macos/run.sh         launcher macOS (+ README)
windows/run.ps1      launcher Windows (+ README)
tasks/               subscribe_flow, cancel, probe
requirements.txt     dependensi tanpa hash (Windows)
requirements.lock    dependensi ber-hash sha256 (macOS)
tests/selftest.py
tools/make_lock.py   bikin requirements.lock
tools/import_keychain.py  migrasi sekali jalan dari Keychain (opsional)
docs/ROADMAP.md      rencana handler & UI berikutnya
```

Inti sengaja **tidak** diduplikasi ke `macos/` dan `windows/`: yang berbeda cuma
cara membuat venv, mencari Python/Chrome, dan data dir. Satu salinan kode berarti
perbaikan bug tidak perlu ditulis dua kali.
