# Roadmap — handler & UI

Disusun dari kenyataan kode hari ini, bukan daftar keinginan umum. Kolom "butuh"
menyebut bagian yang sudah ada supaya pekerjaannya jelas.

## 1. Ringan, nilai besar (bisa dikerjakan tanpa mengubah alur)

| # | Item | Kenapa | Butuh |
|---|---|---|---|
| 1 | **Riwayat run per akun** — panel "riwayat" berisi 5 log terakhir + screenshot | Hari ini cuma log terakhir yang tampil; `run_*.log` lama menumpuk tanpa bisa dibuka dari UI | tabel `runs`/`artifacts` sudah ada di `app/db.py` tapi belum diisi; endpoint `/api/runs` |
| 2 | **Unduh / salin log** | Diagnosa jadi mudah dibagikan, tidak perlu buka Finder | `GET /api/log/{acc_id}?run=` + tombol di `#loghead` |
| 3 | **Stepper per akun** (8 titik, menyala sesuai `step`) | `step` sekarang cuma angka; user harus ingat artinya | `paintRows()` di `index.html`, data `step` sudah dikirim |
| 4 | **Cari & filter akun** (email / status) | 3 akun masih terbaca; 50 akun tidak | filter di `accounts_view()` atau di JS |
| 5 | **Aksi massal** (jalankan / tandai mati / hapus untuk baris terpilih) | `run-all` sekarang menjalankan semua akun yang belum `subscribed` | checkbox + endpoint POST batch |
| 6 | **Kolom "berakhir"** dari `accounts.expiry_date` | Tanggal akhir sebenarnya lebih berguna daripada status saja | kolom `expiry_date` sudah ada, tinggal diisi `discover` |

## 2. Handler baru

| # | Handler | Perilaku | Catatan |
|---|---|---|---|
| 7 | `resume` eksplisit | Tombol "lanjut dari langkah N" di UI | `subscribe_flow.py` sudah menerima `--from`; tinggal diteruskan dari `queue._run` |
| 8 | `recovery` | Isi email pemulihan / lewati prompt kalau diminta | `login.pass_screens()` sudah punya cabang `SKIP_SEL` |
| 9 | `card verify` | Setelah `cancel`, cek kartu benar-benar hilang dari akun dan catat hasilnya (bukan cuma log) | `detach_on_google()` sudah mengembalikan bool — simpan ke DB |
| 10 | `retry policy` | Maks 2 percobaan per handler + jeda naik, bukan ulang seluruh alur | bungkus pemanggilan handler di `run_layers()` |
| 11 | `expiry cache` | Sebelum run, baca `expiry_date` dari DB; kalau sudah 24 bulan, langsung cancel | menghindari run 3 layer yang pasti ditolak |
| 12 | `preflight` | Cek: kartu aktif ada, profil Chrome bisa dibuka, egress US, akun belum `subscribed` | gagal cepat dengan pesan jelas, bukan di tengah checkout |

## 3. Observability

| # | Item | Kenapa |
|---|---|---|
| 13 | Durasi per handler + tingkat keberhasilan di header | Tahu apakah masalahnya sistematis atau per akun |
| 14 | Notifikasi lokal saat run selesai/gagal (macOS `osascript`, Windows toast) | Run panjang; user tidak perlu menatap tab |
| 15 | Export CSV (email, status, tanggal akhir, exit code) | Rekap stok akun |
| 16 | `queue` menulis `runs` + `artifacts` | Dua tabel itu warisan skema; mengisinya membuat riwayat & screenshot bisa di-query |

## 4. Keamanan & operasional

| # | Item | Kenapa |
|---|---|---|
| 17 | Enkripsi opsional `secrets.json` (passphrase → kunci turunan) | Kalau file ikut tersalin ke backup/sinkronisasi |
| 18 | Deteksi instance ganda (lock file di data dir) | Dua konsol bisa menjalankan akun yang sama bersamaan |
| 19 | Rotasi/segarkan `console.token` dari UI | Token sekarang hanya di file + log boot |
| 20 | CI: `ruff` + `tests/selftest.py` di GitHub Actions | Refactor UI/handler gampang merusak hal kecil |
| 21 | Hapus profil Chrome akun `subscribed` (opsional, manual) | Profil menyimpan cookie login; mengurangi jejak di disk |

## Yang sengaja **tidak** dikerjakan

- Login paralel. Login Google serentak dari satu egress mempercepat turunnya
  reputasi IP; antrean serial dipertahankan.
- Menyimpan nomor kartu utuh di DB. `secrets.json` / referensi di DB sudah cukup
  dan menjaga `/api` tidak pernah mengembalikan PAN.
- Bypass captcha. Titik itu tetap diserahkan ke manusia di jendela Chrome.
