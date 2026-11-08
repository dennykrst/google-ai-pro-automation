# Google AI Pro Automation

Konsol lokal yang menuntaskan seluruh alur Google AI Pro 2 tahun untuk satu akun
sekaligus: login, pasang kartu kalau Google memintanya, ambil paket bertingkat,
cocokkan tanggal berakhir tiap langkah, batalkan perpanjangan, lalu tarik kembali
kartunya dari akun.

[English](README.md) · Bahasa Indonesia

Jalan di **macOS dan Windows**. Python 3.12+, dan Playwright mengendalikan **Google
Chrome asli** (`channel="chrome"`), bukan Chromium bawaan — dialog pembayaran Google
hanya berperilaku normal di sana.

Repo: <https://github.com/dennykrst/google-ai-pro-automation>

## Yang sebenarnya dikerjakan

Satu akun, satu proses, satu kali lewat handler berikut. Tidak ada tombol yang
ditekan sebelum layarnya dibaca, dan setiap langkah punya pemeriksaan yang berhenti
daripada menagih sesuatu yang tidak sesuai.

| # | Handler | Yang dilakukan | Yang dicek sebelum lanjut |
|---|---|---|---|
| 0 | `egress` | membuka layanan cek IP di dalam browser untuk melihat dari mana trafik keluar | negara wajib **US**; menunggu maksimal 120 detik |
| 1 | `login` | email → password → TOTP, termasuk captcha, prompt pemulihan, dan device prompt | URL sudah keluar dari `accounts.google.com` |
| 2 | `discover` | membaca tanggal berakhir yang berlaku dari dialog cancel **tanpa** mengonfirmasinya | 0 bln → paket 1 · 12 → paket 2 · 18 → paket 3 · 24 → coba paket 4 sekali |
| 3 | `bind card` | Add card → nomor, kedaluwarsa, CVC, nama, ZIP → simpan, hanya kalau dialog memintanya | tiap kolom dibaca ulang, nilai yang tidak menempel diketik lagi |
| 4 | `paket 1` | membuka dialog penawaran, membaca totalnya, menekan Subscribe | total `$0.00` atau label trial 12 bulan |
| 5 | `paket 2` | naik ke paket 18 bulan | tanggal berakhir dalam selisih sehari dari +18 bulan |
| 6 | `paket 3` | naik ke paket 24 bulan | tanggal berakhir dalam selisih sehari dari +24 bulan |
| 7 | `cancel` | Play → Manage → Cancel subscription → konfirmasi | status terbaca `Canceled` dan tanggal berakhir terlihat |
| 8 | `detach card` | menghapus kartu dari profil pembayaran akun | best effort; menunggu persetujuanmu sampai 300 detik |

Karena handler 2, run yang terputus aman diulang: konsol membaca apa yang benar-benar
aktif lalu melanjutkan dari titik itu, bukan mengulang dari awal.

## Asalnya

Ditulis ulang di atas dua proyek yang sudah ada, dengan penekanan pada kemudahan
diaudit dan ketahanan:

- <https://github.com/worldonlyu/Google_AI_Pro_2Year_ZeroCost_Auto> — runner Windows
  satu-klik (`.bat`) untuk tiga paket plus cancel.
- <https://github.com/ade1256/google-ai-pro-farming-2-years> — konsol lokal
  sebelumnya (macOS, secret di Keychain) yang menjadi kerangka proyek ini.

| | konsol sebelumnya | proyek ini |
|---|---|---|
| OS | macOS saja | **macOS + Windows**, satu inti, dua launcher |
| Secret | Keychain macOS lewat `security` — memunculkan prompt di terminal | **`secrets.json` lokal (0600)**, tanpa API OS, tanpa prompt |
| Antrean | satu run manual | antrean serial, *jalankan semua* dan *jalankan terpilih* |
| Melanjutkan | mulai dari awal | **discovery** membaca term yang aktif lalu memilih paket berikutnya |
| Guard biaya | cek dialog | `$0.00` **dan** cek tanggal per paket sebelum commit |
| Kartu | satu kartu global | **pool berputar**, yang paling lama tidak terpakai didahulukan |
| Setelah cancel | langganan berhenti | **kartu dilepas** dari akun, tetap disimpan untuk akun berikutnya |
| Log | scrollback | panel log di browser; run gagal **tidak dikosongkan**, baris penyebab disorot |
| Riwayat run | tidak ada | lima run terakhir per akun: status, egress, penyebab gagal, screenshot, log mana pun |
| Dependensi | bebas | 9 paket, `requirements.lock` **ber-hash sha256**, tanpa pyotp/keyring |
| Uji | manual | `tests/selftest.py` (TOTP RFC 6238, vault, riwayat run, i18n, kebijakan akses) |

Tambahan yang tidak ada di keduanya: `--dry` (berhenti sebelum setiap Subscribe),
pengisian kartu yang tahan autofill, dan masking — UI serta log tidak pernah
menampilkan nomor kartu utuh, CVC, atau password.

## Batasan yang disengaja

- Hanya mendengarkan di `127.0.0.1`. Cookie sesi diterbitkan otomatis; token hanya
  perlu kalau kamu sengaja membukanya ke jaringan (`GAI_ALLOW_REMOTE=1`).
- Tidak ada telemetri. Tidak ada panggilan keluar selain ke Google dan `ipwho.is`
  (cek negara).
- Beberapa momen tetap butuh kamu di HP: device prompt saat login, persetujuan
  hapus kartu, dan captcha gambar. Kalau dilewati, langganan tetap aktif dan cancel
  tetap jalan — hanya kartunya yang tertinggal di akun.
- Ini mengotomasi akun **milikmu sendiri**. Pakai untuk akun dan kartu kamu sendiri.

## Yang dibutuhkan

- **Google Chrome** terpasang.
- Egress US (VPN). Alur menunggu sampai 120 detik untuk negara yang benar, lalu berhenti.
- Python 3.12+ (`brew install python@3.13` di macOS, python.org di Windows).
- Akun (`email|password|seed-totp`) dan kartu (`nomor|MM/YY|CVC`) — keduanya masuk
  lewat UI dan tinggal di penyimpanan lokal.

## Menjalankan

```bash
git clone https://github.com/dennykrst/google-ai-pro-automation.git
cd google-ai-pro-automation
```

| OS | Perintah |
|---|---|
| macOS | `cd macos && ./run.sh` |
| Windows | `cd windows` lalu `powershell -ExecutionPolicy Bypass -File .\run.ps1` |

Kedua launcher membuat `.venv` bila belum ada, memasang dependensi, lalu menyajikan
konsol di `127.0.0.1:8765`. Cukup buka:

```
http://127.0.0.1:8765/
```

Data dir: macOS `~/Library/Application Support/GoogleAIAutomation`, Windows
`%LOCALAPPDATA%\GoogleAIAutomation`. Data dir lama `.../GaiConsole` dipindah otomatis
saat boot pertama, jadi akun, kartu, dan token ikut terbawa.

Kalau konsol dibuka ke jaringan (`GAI_BIND_HOST=0.0.0.0 GAI_ALLOW_REMOTE=1`), semua
request wajib token — nilainya ada di `console.token` di data dir dan dicetak saat
boot sebagai `?t=…`.

## Memakai konsolnya

1. Impor kartu: `nomor|MM/YY|CVC`, satu per baris atau satu per satu.
2. Impor akun: `email|password|seed-totp`, sama caranya.
3. Tekan **jalankan** pada akun, atau **jalankan semua** / centang baris lalu
   **jalankan terpilih**.

Header punya tombol **EN / ID**; defaultnya English. Tombol **bantuan** membuka
`/help` dengan isi serupa README ini, tapi rincian yang berguna ada di sebelah
tombolnya: daftar handler, arti penanda log, dan isi data dir.

| Kolom | Arti |
|---|---|
| `status` | `pending` → `running` → `subscribed` (cancel terverifikasi) · `failed` · `cancelled` · `dead` |
| delapan titik | langkah handler; titik hijau adalah langkah terakhir |
| `berakhir` | tanggal berakhir dari discovery atau cancel; `—` kalau belum terbaca |
| `otp` | kode TOTP yang berlaku dan sisa waktunya |
| `kartu` | brand dan empat digit terakhir saja |

Panel log menampilkan run yang sedang jalan **dan** run terakhir setelah selesai. Run
yang gagal tetap menampilkan lognya, menyorot baris penyebab, dan meringkasnya di
bawah panel. Tombol **log** di tiap baris membuka lima run terakhir — waktu, status,
egress, penyebab gagal, jumlah screenshot — dengan tombol untuk membaca log mana pun.

## Data dan akses

Semua tinggal di data dir; tidak ada yang ditulis di luar itu, dan tidak ada yang
keluar selain trafik Google dan cek IP.

| File | Isi |
|---|---|
| `db.sqlite3` | metadata akun dan kartu — tidak pernah nomor kartu atau CVC |
| `secrets.json` | password, seed TOTP, nomor kartu, CVC (mode 0600) |
| `console.token` | token akses, hanya dipakai untuk akses dari luar loopback |
| `profiles/` | satu profil Chrome per akun (cookie login) |
| `artifacts/` | log run dan screenshot tiap paket |

Aturan aksesnya singkat: header `Host` wajib loopback (ini yang menahan DNS
rebinding), `GET` dari loopback mendapat cookie sesi otomatis, `POST` tetap butuh
cookie itu, dan `Host` asing ditolak kecuali kamu memakai `GAI_ALLOW_REMOTE=1`.

Perlindungan `secrets.json` adalah izin file, bukan keychain sistem. Siapa pun yang
jalan sebagai user kamu bisa membacanya. Data lama di Keychain bisa disalin sekali
dengan `tools/import_keychain.py` (khusus macOS; aplikasi sendiri tidak menyentuhnya).

## Struktur

```
app/                 inti bersama (dipakai kedua OS)
  main.py            rute, antrean, /help, /lang
  config.py          settings, data dir per platform
  db.py              skema SQLite + migrasi idempoten
  runs.py            riwayat run dan artifact
  vault.py           akun & kartu (nilai di secrets.json)
  secrets.py         penyimpanan secret lokal (JSON 0600, tanpa API OS)
  i18n.py            teks UI: English + Indonesia
  totp.py            TOTP stdlib
  egress.py          cek negara egress
  security.py        kebijakan akses (loopback, cookie, token)
  runner/            browser, navigasi berulang, antrean
  sites/google_one/  login, checkout, discovery, hook, tokens
  templates/         index.html, help.en.html, help.id.html
macos/run.sh         launcher macOS (+ README)
windows/run.ps1      launcher Windows (+ README)
tasks/               subscribe_flow, cancel, probe
requirements.txt     daftar dependensi tanpa hash (Windows)
requirements.lock    lock ber-hash sha256 (macOS)
tests/selftest.py
tools/make_lock.py   membuat requirements.lock
tools/import_keychain.py  migrasi sekali jalan dari Keychain
docs/ROADMAP.md      apa yang sudah dan belum dikerjakan
```

Inti sengaja **tidak** diduplikasi ke `macos/` dan `windows/`: yang berbeda hanya
cara membuat venv, mencari Python/Chrome, dan data dir. Satu salinan kode berarti
satu tempat untuk memperbaiki bug.
