# SIKASU — Sistem Informasi Kopi Arabika Sumatera Utara

Dashboard Streamlit untuk melihat data produksi kopi Arabika berdasarkan kabupaten dan kecamatan/desa.

## Fitur
- Koneksi ke database Neon PostgreSQL.
- Unggah data CSV atau gunakan data contoh untuk mencoba tampilan.
- Filter tahun dan kabupaten.
- Kartu ringkasan produksi.
- Diagram donat kontribusi kabupaten.
- Grafik batang perbandingan kabupaten.
- Grafik 10 kecamatan/desa tertinggi jika kolom kecamatan tersedia.
- Grafik tren tahunan jika tersedia lebih dari satu tahun.
- Tabel peringkat, tabel data, dan unduh CSV.
- Analisis deskriptif otomatis.

> **Catatan:** `sample_data.csv` adalah data simulasi untuk menguji aplikasi, bukan statistik resmi. Ganti dengan data penelitian atau data resmi kalian sebelum membuat kesimpulan.

## Cara unggah ke GitHub
1. Ekstrak ZIP.
2. Buat repository baru di https://github.com/new.
3. Unggah semua isi folder ke repository (termasuk folder `.streamlit` dan `assets`).
4. Commit changes.

## Deploy ke Streamlit
1. Buka https://share.streamlit.io.
2. Pilih **Create app**.
3. Pilih repository, branch `main`, dan file utama `app.py`.
4. Di **Advanced settings → Secrets**, masukkan:
   ```toml
   NEON_DATABASE_URL = "postgresql://USERNAME:PASSWORD@HOST/DBNAME?sslmode=require"
   ```
   Ganti dengan connection string dari Neon. Jangan unggah password ke GitHub.
5. Klik Deploy.

## Menggunakan Neon
1. Pada aplikasi, pilih sumber **Database Neon**.
2. Pilih tabel yang memuat kolom kabupaten dan produksi, lalu klik **Muat data dari Neon**.
3. Jika data berada di beberapa tabel, gunakan opsi **Query SQL** dan tulis satu query SELECT yang menggabungkan tabel-tabel itu.
4. Pilih pemetaan kolom di sidebar: kabupaten, kecamatan/desa (opsional), produksi, tahun (opsional), jenis kopi (opsional).
5. Pilih satuan sumber yang benar (ton, kg, atau kuintal).

## Menjalankan lokal (opsional)
```bash
pip install -r requirements.txt
streamlit run app.py
```

Untuk koneksi Neon lokal, buat `.streamlit/secrets.toml` dari contoh `secrets.toml.example` dan isi URL database sendiri. File rahasia tidak boleh di-commit.

## Format data minimal
| Kolom | Wajib | Contoh |
|---|---|---|
| Kabupaten | Ya | Dairi |
| Produksi | Ya | 1250 |
| Kecamatan/desa | Tidak | Sidikalang |
| Tahun | Tidak | 2024 |
| Jenis kopi | Tidak | Arabika |

Pastikan satuan konsisten, tahun jelas, dan data tidak terduplikasi. Analisis dashboard bersifat deskriptif, bukan penjelasan sebab-akibat.
