# Sistem Pemantauan dan Otomasi Jemuran Pintar Berbasis IoT dan AI

**Video Presentasi Tugas**: [Tonton di YouTube](https://youtu.be/jNlBGO228oM)

Repositori ini memuat seluruh aset kode sumber, konfigurasi infrastruktur, dan dokumentasi rekayasa untuk proyek *Internet of Things* (IoT) terdistribusi yang dikembangkan di lingkungan akademik Teknik Komputer Universitas Indonesia. Sistem ini dirancang untuk memantau kondisi lingkungan penjemuran pakaian dan memberikan perlindungan mekanis secara otomatis terhadap perubahan cuaca presipitasi (hujan), dengan mengintegrasikan mikrokontroler, protokol ringan MQTT, mesin otomasi, dan analisis kecerdasan buatan.

## 1. Arsitektur Infrastruktur (Laporan Teknis)

Proyek ini mengadopsi arsitektur tiga lapis (*Edge, Gateway, Server*) yang memisahkan beban kerja komputasi pada perangkat keras yang berbeda.

| Komponen | Lapisan | Peran dan Fungsi Teknis |
| :--- | :--- | :--- |
| **ESP32** | *Edge Device* | Membaca data dari 5 instrumen sensor fisik dan menggerakkan aktuator motor servo. Berkomunikasi melalui MQTT lokal. |
| **Raspberry Pi** | *Gateway* | Menjalankan Mosquitto Broker sebagai pusat lalu lintas pesan MQTT pada topik `sensor/cuaca` dan `sensor/control`. |
| **Skrip Python (VM)** | *Application Server* | Menjalankan *multi-threading* untuk pemrosesan AI (Gemini), integrasi pengunggahan data ke Supabase, dan *long-polling* bot Telegram. |
| **n8n Engine** | *Orchestration* | Berjalan di dalam kontainer Docker (Laptop) untuk mengeksekusi logika kondisional buka/tutup atap guna mencegah *spam* perintah servo. |
| **Supabase** | *Database (Cloud)* | DBMS terpusat untuk menyimpan tabel *log* sensor mentah dan hasil kalkulasi prediksi LLM. |
| **Metabase** | *Analytics* | Berjalan di dalam kontainer Docker (Laptop) sebagai dasbor visual untuk memantau indikator performa utama dan grafik linier penurunan berat pakaian. |

---

## 2. Topologi Jaringan dan Isolasi Keamanan (Netbird VPN)

Sistem ini mengintegrasikan perangkat jaringan lokal di rumah (ESP32 dan Raspberry Pi) dengan perangkat eksternal (Virtual Machine dan Laptop). Untuk mengamankan jalur komunikasi data tanpa mengekspos *port* ke internet publik, proyek ini menggunakan **Netbird** (*Peer-to-Peer Mesh VPN* berbasis WireGuard).

* **Alamat IP Terpusat:** Seluruh perangkat komputasi diinstal agen Netbird dan disatukan ke dalam satu jaringan privat maya. Raspberry Pi bertindak sebagai pusat broker MQTT dengan alamat IP statis internal VPN `100.117.143.2`.
* Skrip aplikasi pada Virtual Machine dan konfigurasi *node* MQTT pada n8n di laptop diwajibkan untuk mengarah ke alamat IP internal VPN tersebut.

---

## 3. Skema Basis Data Relasional (Supabase)

Proyek ini mendayagunakan Supabase untuk penyimpanan data runtun waktu (*time-series*) dengan dua tabel utama:

1. **`log_jemuran`**: 
   Menyimpan data mentah periodik dari perangkat *edge*. Kolom yang dialokasikan: `id` (UUID), `waktu` (timestamptz), `suhu` (float), `kelembapan` (float), `cahaya` (integer), `intensitas_hujan` (integer), dan `berat` (float).
2. **`ai_prediksi_jemuran`**: 
   Menyimpan hasil inferensi dari Gemini AI. Kolom yang dialokasikan: `id` (UUID), `waktu_prediksi` (timestamptz), `log_id_referensi` (Foreign Key), `status_jemuran` (teks), `estimasi_menit` (integer), dan `alasan` (teks).

---

## 4. Panduan Memulai Cepat (*Deployment*)

Berkas konfigurasi spesifik untuk ESP32, Raspberry Pi, dan Skrip Virtual Machine terdapat pada masing-masing sub-direktori beserta panduan instalasi independennya.

Untuk menjalankan layanan infrastruktur orkestrasi dan analitik di laptop (n8n dan Metabase), pastikan *daemon* Docker sudah beroperasi dan jalankan perintah berikut. Keduanya menggunakan parameter *Named Volume* (`-v`) agar data proyek bersifat permanen dan tidak hilang apabila kontainer dihapus.

### A. Menjalankan n8n Engine
```bash
docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n:latest
```

### B. Menjalankan Metabase
Perintah ini diinjeksi dengan argumen `JAVA_OPTS` untuk membatasi penggunaan RAM maksimal di 1 GB
```bash
docker run -d --name metabase -p 3000:3000 -m 1g -e "JAVA_OPTS=-Xmx350m -Xms150m" -v metabase_data:/metabase.db metabase/metabase:latest
```

---

## 5. Manajemen Kredensial dan Variabel Lingkungan

Repositori ini diatur untuk mengabaikan direktori lingkungan virtual (`VENV/`) dan berkas konfigurasi lokal. Anda wajib mengonfigurasi variabel sistem sebelum mengeksekusi layanan Python.

1. Salin format dari `.env.example` dan buat berkas baru bernama `.env`.
2. Isi nilai dari parameter berikut:
   * `TELEGRAM_TOKEN` (BotFather)
   * `GEMINI_API_KEY` (Google AI Studio)
   * `SUPABASE_URL`
   * `SUPABASE_SERVICE_ROLE_KEY`
3. Pastikan berkas `.env` sudah terdaftar di dalam `.gitignore` untuk mencegah kebocoran kunci akses ke penyimpanan publik.