# Roadmap — handler & UI

Disusun dari kenyataan kode hari ini, bukan daftar keinginan umum. Kolom "butuh"
menyebut bagian yang sudah ada supaya pekerjaannya jelas.

## Sudah dikerjakan (2026-11-08)

- **Riwayat run per akun** — `runs.py` mengisi tabel `runs`/`artifacts`; dialog
  *log* menampilkan 5 run terakhir (waktu, status, egress, ringkasan gagal,
  jumlah screenshot) dan bisa membaca log run mana pun.
- **Baca log run lama** — `GET /api/log/{acc_id}?run=` dengan validasi path ada di
  dalam `artifacts/`.
- **Stepper 8 langkah** per akun di kolom status.
- **Cari email + filter status** di atas tabel akun.
- **Aksi massal** — centang baris → `POST /queue/run` (`ids`).
- **Kolom "berakhir"** dari `accounts.expiry_date`, diisi saat discovery dan
  setelah cancel terverifikasi.

## 1. Ringan, nilai besar (bisa dikerjakan tanpa mengubah alur)

| # | Item | Kenapa | Butuh |
|---|---|---|---|
| 1 | **Unduh / salin log** — tombol di dialog riwayat | "lihat log" sudah ada; tinggal simpan ke file | `GET /api/log?run=` (ada) + tombol `download` |
| 2 | **Hapus riwayat lama** (mis. run > 30 hari) | `runs`/`artifacts` tumbuh terus | `DELETE /api/runs/{id}` + pembersihan file |
| 3 | **Sorot baris yang sedang jalan** dengan animasi halus | Status `running` sudah ada, tapi tidak menonjol | `tr.running` di CSS |

## 2. Handler baru

| # | Handler | Perilaku | Catatan |
|---|---|---|---|
| 4 | `resume` eksplisit | Tombol "lanjut dari langkah N" di UI | `subscribe_flow.py` sudah menerima `--from`; tinggal diteruskan dari `queue._run` |
| 5 | `recovery` | Isi email pemulihan / lewati prompt kalau diminta | `login.pass_screens()` sudah punya cabang `SKIP_SEL` |
| 6 | `card verify` | Setelah `cancel`, cek kartu benar-benar hilang dari akun dan catat hasilnya (bukan cuma log) | `detach_on_google()` sudah mengembalikan bool — simpan ke DB |
| 7 | `retry policy` | Maks 2 percobaan per handler + jeda naik, bukan ulang seluruh alur | bungkus pemanggilan handler di `run_layers()` |
| 8 | `expiry cache` | Sebelum run, baca `expiry_date` dari DB; kalau sudah 24 bulan, langsung cancel | menghindari run 3 layer yang pasti ditolak |
| 9 | `preflight` | Cek: kartu aktif ada, profil Chrome bisa dibuka, egress US, akun belum `subscribed` | gagal cepat dengan pesan jelas, bukan di tengah checkout |

## 3. Observability

| # | Item | Kenapa |
|---|---|---|
| 10 | Durasi per handler + tingkat keberhasilan di header | Tahu apakah masalahnya sistematis atau per akun |
| 11 | Notifikasi lokal saat run selesai/gagal (macOS `osascript`, Windows toast) | Run panjang; user tidak perlu menatap tab |
| 12 | Export CSV (email, status, tanggal akhir, exit code) | Rekap stok akun |
| 13 | Agregasi `runs` di header (mis. 7 hari terakhir: 4 sukses / 3 gagal) | `runs` sekarang terisi; tinggal di-query |

## 4. Keamanan & operasional

| # | Item | Kenapa |
|---|---|---|
| 14 | Enkripsi opsional `secrets.json` (passphrase → kunci turunan) | Kalau file ikut tersalin ke backup/sinkronisasi |
| 15 | Deteksi instance ganda (lock file di data dir) | Dua konsol bisa menjalankan akun yang sama bersamaan |
| 16 | Rotasi/segarkan `console.token` dari UI | Token sekarang hanya di file + log boot |
| 17 | CI: `ruff` + `tests/selftest.py` di GitHub Actions | Refactor UI/handler gampang merusak hal kecil |
| 18 | Hapus profil Chrome akun `subscribed` (opsional, manual) | Profil menyimpan cookie login; mengurangi jejak di disk |

## Yang sengaja **tidak** dikerjakan

- Login paralel. Login Google serentak dari satu egress mempercepat turunnya
  reputasi IP; antrean serial dipertahankan.
- Menyimpan nomor kartu utuh di DB. `secrets.json` / referensi di DB sudah cukup
  dan menjaga `/api` tidak pernah mengembalikan PAN.
- Bypass captcha. Titik itu tetap diserahkan ke manusia di jendela Chrome.
