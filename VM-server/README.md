# Server Aplikasi dan AI (Virtual Machine)

Folder ini berisi skrip Python utama (`main.py`) yang dieksekusi di dalam lingkungan Virtual Machine (VM). Modul ini bertindak sebagai pengolah data tingkat menengah (*middleware*) dan otak analitik dari sistem jemuran pintar.

## 1. Peran dan Fungsi Teknis

Skrip pada lapisan ini beroperasi secara *multi-threading* untuk menjalankan tiga fungsi utama secara paralel tanpa memblokir satu sama lain:
* **Pemrosesan Kecerdasan Buatan (AI):** Menerima data sensor via MQTT, memfilter muatan (mengabaikan proses AI jika berat < 500 gram untuk efisiensi API), dan memanggil Gemini API secara asinkron guna mengalkulasi estimasi waktu pengeringan.
* **Integrasi Basis Data Cloud:** Menerima muatan JSON dari broker dan melakukan penyisipan data (*data insertion*) ke dalam tabel `log_jemuran` dan `ai_prediksi_jemuran` di Supabase.
* **Layanan Telegram Bot (Long-Polling):** Menjalankan *thread* khusus untuk mendengarkan pesan masuk dari Telegram (perintah `/status`) dan memberikan respons berisikan data cuaca dan metrik AI terakhir.

---

## 2. Struktur Berkas
```text
server-vm/
├── main.py               # Skrip utama multi-threading
├── .env.example          # Kerangka variabel lingkungan (tanpa token asli)
└── README.md             # Dokumentasi ini
```
*(Catatan: Folder ini tidak menggunakan `requirements.txt`, instalasi dependensi dilakukan secara manual).*

---

## 3. Prasyarat Sistem dan Dependensi

Skrip ini membutuhkan **Python 3.8** atau versi yang lebih baru. Karena tidak menggunakan berkas *requirements*, Anda wajib menginstal pustaka eksternal berikut melalui terminal VM sebelum mengeksekusi kode:

```bash
pip install paho-mqtt requests python-dotenv
```

---

## 4. Konfigurasi Lingkungan (Environment Variables)

Skrip ini membaca kredensial rahasia dari berkas `.env`. Anda wajib membuat berkas `.env` di dalam folder ini (sejajar dengan `main.py`) dan mengisi token sesuai dengan format berikut:

```text
# Buat file bernama .env dan isi dengan kredensial Anda
GEMINI_API_KEY=masukkan_kunci_api_gemini_anda_di_sini
SUPABASE_URL=masukkan_url_proyek_supabase_anda_di_sini
SUPABASE_SERVICE_ROLE_KEY=masukkan_kunci_service_role_supabase_di_sini
TELEGRAM_TOKEN=masukkan_token_bot_telegram_di_sini
```
**Peringatan Keamanan:** Berkas `.env` tidak boleh diunggah ke *version control* (GitHub). Pastikan berkas tersebut telah terdaftar di dalam `.gitignore`.

---

## 5. Panduan Menjalankan Skrip

1. Masuk ke direktori server-vm di dalam terminal:
   ```bash
   cd server-vm
   ```

2. **Mode Uji Coba (Debugging):**
   Untuk melihat *log* proses AI dan penerimaan MQTT secara langsung di terminal:
   ```bash
   python3 main.py
   ```

3. **Mode Produksi (Background Service):**
   Agar skrip tetap berjalan meskipun koneksi SSH ke VM ditutup, gunakan `nohup` atau daftarkan sebagai *service*:
   ```bash
   nohup python3 main.py > vm_process.log 2>&1 &
   ```

---

## 6. Peringatan Penting (Konflik Telegram)

Metode *long-polling* Telegram API tidak mengizinkan satu token bot digunakan oleh dua pendengar yang berbeda secara bersamaan. 
* Jika Anda sebelumnya menjalankan `main.py` ini di laptop lokal untuk proses pengembangan, **pastikan skrip di laptop sudah dimatikan secara total** sebelum menjalankan skrip di VM.
* Kegagalan mematikan skrip ganda akan menyebabkan perebutan pesan (*race condition*), di mana bot Telegram akan merespons perintah `/status` secara acak atau tidak merespons sama sekali karena konflik penarikan antrean pesan (offset).