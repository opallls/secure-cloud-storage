# 🔒 Secure Cloud File Storage

Sistem penyimpanan file aman berbasis cloud yang menerapkan **enkripsi hybrid AES-256 + RSA-2048** di sisi klien, terintegrasi dengan **Google Drive API** sebagai layanan cloud gratis. Proyek ini dibuat untuk studi kasus mata kuliah **Keamanan Informasi**, dengan judul:

> **"Analisis Performa dan Keamanan Enkripsi AES vs RSA pada Layanan Cloud Gratis"**

Seluruh data yang dikirim dan disimpan di cloud selalu dalam bentuk ciphertext — Google Drive maupun pihak lain yang tidak berwenang tidak dapat membaca isi file asli.

---

## ✨ Fitur

- 🔐 Enkripsi **AES-256-CBC** untuk isi file
- 🔑 Enkripsi **RSA-2048-OAEP** untuk melindungi kunci AES (skema hybrid)
- ☁️ Upload & download file terenkripsi ke **Google Drive API** (OAuth 2.0, scope `drive.file`)
- ✅ Verifikasi integritas file menggunakan **hash SHA-256**
- 🖥️ Antarmuka **CLI** (`app.py`) dan **web** (`streamlit_app.py`) dengan autentikasi login
- 📊 Benchmark performa AES vs RSA (waktu, CPU, RAM, throughput, ukuran ciphertext) dengan ekspor CSV & grafik

---

## 🏗️ Arsitektur Sistem

Seluruh proses kriptografi (pembangkitan kunci, enkripsi, dekripsi, verifikasi integritas) berjalan **sepenuhnya di sisi klien**. Yang melintasi jaringan menuju Google Drive hanyalah ciphertext — private key RSA tidak pernah meninggalkan mesin lokal.

```
User
  │
  ▼
Upload File (CLI / Web)
  │
  ▼
AES-256 Encryption (data)  +  RSA-2048 Encryption (AES key)
  │
  ▼
file.enc  +  file.key.enc
  │
  ▼
Upload ke Google Drive (OAuth 2.0, scope: drive.file)
  │
  ▼
[ ... tersimpan di cloud ... ]
  │
  ▼
Download ciphertext
  │
  ▼
RSA Decrypt (buka AES key)  →  AES Decrypt (buka file)
  │
  ▼
Verifikasi SHA-256
  │
  ▼
File Asli
```

📄 Diagram arsitektur lengkap tersedia di `docs/architecture.png` dan pada laporan proyek.

---

## 🧰 Tech Stack

| Komponen | Teknologi |
|---|---|
| Bahasa | Python 3.11+ |
| Kriptografi | [pycryptodome](https://pycryptodome.readthedocs.io/) (AES-256-CBC, RSA-2048-OAEP) |
| Cloud Storage | Google Drive API v3 + OAuth 2.0 |
| Web UI | [Streamlit](https://streamlit.io/) + [streamlit-authenticator](https://github.com/mkhorasani/Streamlit-Authenticator) |
| Profiling | psutil |
| Analisis & Visualisasi | pandas, matplotlib |

---

## 📁 Struktur Proyek

```
secure-cloud-storage/
├── app.py                 # Entry point CLI
├── streamlit_app.py        # Entry point Web UI (dengan login)
├── encrypt.py               # Fungsi enkripsi AES-256 & RSA-2048
├── decrypt.py                # Fungsi dekripsi AES-256 & RSA-2048
├── google_drive.py            # Autentikasi OAuth 2.0 + upload/download Drive
├── utils.py                    # Hashing, key management, helper
├── benchmark.py                  # Uji performa AES vs RSA + ekspor CSV/grafik
├── requirements.txt
├── credentials/                   # ⚠️ TIDAK di-commit ke Git (lihat Setup di bawah)
│   ├── credentials.json             # OAuth client (dari Google Cloud Console)
│   ├── token.json                     # Token OAuth (dibuat otomatis saat login pertama)
│   ├── auth_config.yaml                # Kredensial login web (hash bcrypt)
│   ├── rsa_private.pem                   # RSA private key (dibuat otomatis)
│   └── rsa_public.pem                      # RSA public key (dibuat otomatis)
├── data/
│   ├── input/                              # File yang akan diupload
│   └── output/                               # Hasil file yang didekripsi
├── results/
│   ├── manifest.json                          # Metadata file (file_id, hash)
│   ├── benchmark.csv                            # Hasil benchmark
│   └── charts/                                    # Grafik hasil benchmark
└── .gitignore
```

---

## ⚙️ Setup & Instalasi

### 1. Clone repository
```bash
git clone https://github.com/opallls/secure-cloud-storage.git
cd secure-cloud-storage
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Buat kredensial Google Drive API (wajib, tidak disertakan di repo)
Karena `credentials/` dikecualikan dari Git demi keamanan, Anda perlu membuat kredensial sendiri:

1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Buat project baru → aktifkan **Google Drive API**
3. Buka **Google Auth Platform** → lengkapi **OAuth consent screen** (App name bebas, tambahkan email Anda sebagai **Test user**)
4. Buka menu **Clients** → **Create Client** → pilih **Desktop app**
5. Download file JSON hasilnya, simpan sebagai `credentials/credentials.json`

### 4. Buat kredensial login web (untuk `streamlit_app.py`)
```bash
python gen_password.py
```
Salin hash yang muncul ke `credentials/auth_config.yaml`:
```yaml
credentials:
  usernames:
    demo:
      email: demo@example.com
      name: Demo User
      password: "<HASH_DARI_gen_password.py>"
cookie:
  name: secure_storage_auth
  key: ganti_dengan_string_acak_panjang
  expiry_days: 1
```

> RSA keypair (`rsa_private.pem` / `rsa_public.pem`) akan **dibuat otomatis** saat aplikasi pertama kali dijalankan.

---

## ▶️ Menjalankan Aplikasi

### CLI
```bash
python app.py
```

### Web UI
```bash
python -m streamlit run streamlit_app.py
```
Buka `http://localhost:8501`, login menggunakan kredensial yang dibuat di langkah setup.

### Benchmark AES vs RSA
```bash
python benchmark.py
```
Hasil tersimpan di `results/benchmark.csv` dan grafik di `results/charts/`.

---

## 🛡️ Konfigurasi Keamanan

- **Enkripsi**: AES-256-CBC (data) + RSA-2048-OAEP (kunci) — skema hybrid
- **Autentikasi**: Login berbasis hash bcrypt (streamlit-authenticator), bukan password plaintext
- **Transport**: HTTPS/TLS otomatis melalui pustaka resmi Google API Client
- **IAM**: OAuth 2.0 scope `drive.file` — prinsip *least privilege*, aplikasi hanya bisa mengakses file yang dibuatnya sendiri
- **Integritas**: Verifikasi SHA-256 pada setiap proses download & dekripsi
- **Secrets management**: Seluruh kredensial (`credentials/`) dikecualikan dari version control melalui `.gitignore`

---

## 📊 Ringkasan Hasil Benchmark

| Ukuran Data | AES-256 Throughput | RSA-2048 (maks ~190 byte/operasi) |
|---|---|---|
| 1 KB | 0.07 MB/s | Waktu relatif stabil (~0.002s enkripsi) |
| 1 MB | 127.22 MB/s | Tidak dapat mengenkripsi langsung (butuh hybrid) |
| 5 MB | 256.61 MB/s | Tidak dapat mengenkripsi langsung (butuh hybrid) |

Detail lengkap analisis performa dan keamanan tersedia pada laporan proyek (`docs/Laporan_AES_vs_RSA_Cloud.docx`).

---

## ⚠️ Catatan Keamanan

Repository ini **tidak menyertakan** kredensial apa pun (`credentials/*`, token OAuth, RSA private key). Setiap pengguna wajib membuat kredensialnya sendiri mengikuti langkah **Setup** di atas. Ini adalah praktik keamanan standar (secrets tidak boleh masuk version control), bukan bagian yang belum selesai.

---

## 👤 Author

Dibuat sebagai tugas Project Case Study — Mata Kuliah Keamanan Informasi.

## 📄 Lisensi

Proyek ini dibuat untuk keperluan akademik.
