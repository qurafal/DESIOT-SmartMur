# Server Aplikasi dan AI (Virtual Machine)

Folder ini berisi skrip Python utama (`main.py`) yang dieksekusi di dalam lingkungan Virtual Machine (VM) ataupun laptop. Modul ini bertindak sebagai pengolah data tingkat menengah (*middleware*) dan otak analitik dari sistem jemuran pintar.

## 1. Peran dan Fungsi Teknis

Skrip pada lapisan ini beroperasi secara *multi-threading* untuk menjalankan tiga fungsi utama secara paralel tanpa memblokir satu sama lain:
* **Pemrosesan Kecerdasan Buatan (AI):** Menerima data sensor via MQTT, memfilter muatan (mengabaikan proses AI jika berat < 500 gram untuk efisiensi API), dan memanggil Gemini API secara asinkron guna mengalkulasi estimasi waktu pengeringan.
* **Integrasi Database Cloud:** Menerima muatan JSON dari broker dan melakukan penyisipan data (*data insertion*) ke dalam tabel `log_jemuran` dan `ai_prediksi_jemuran` di Supabase.
* **Layanan Telegram Bot (Long-Polling):** Menjalankan *thread* khusus untuk mendengarkan pesan masuk dari Telegram (perintah `/status`) dan memberikan respons berisikan data cuaca dan metrik AI terakhir.

---

## 2. Struktur Berkas
```text
server-vm/
├── main.py               # Skrip utama multi-threading
├── .env.example          # Kerangka variabel lingkungan (tanpa token asli)
└── README.md             # Dokumentasi ini
```

---

## 3. Prasyarat Sistem dan Dependensi

Skrip ini membutuhkan **Python 3.8** atau versi yang lebih baru. Anda wajib menginstal pustaka eksternal berikut melalui terminal VM sebelum mengeksekusi kode:

```bash
pip install paho-mqtt requests python-dotenv
```

---

## 4. Konfigurasi Lingkungan (Environment Variables)

Skrip ini membaca kredensial rahasia dari berkas `.env`. Anda wajib membuat berkas `.env` di dalam folder ini (sejajar dengan `main.py`) dan mengisi token sesuai dengan format berikut:

---

## 5. Panduan Menjalankan Skrip

1. Masuk ke direktori server-vm di dalam terminal:

2. **Jalankan Script:**
   ```bash
   python3 main.py
   ```
---
