# Sistem Pemantauan dan Otomasi Jemuran Pintar Berbasis IoT dan AI

Proyek ini merupakan implementasi sistem *Internet of Things* (IoT) terdistribusi yang dirancang untuk memantau kondisi lingkungan penjemuran pakaian dan memberikan perlindungan mekanis secara otomatis terhadap perubahan cuaca (hujan). Sistem ini mengintegrasikan mikrokontroler, protokol pesan ringan (MQTT), otomasi berbasis aturan (*rule-based*), serta analisis prediktif menggunakan kecerdasan buatan (LLM).

## 1. Gambaran Umum (Overview)

Sistem ini menyelesaikan masalah efisiensi penjemuran dengan menyediakan fitur utama:
* **Akuisisi Data Real-Time:** Membaca suhu, kelembapan, intensitas cahaya, curah hujan, dan berat beban jemuran.
* **Otomasi Proteksi Atap:** Menutup atap pelindung secara instan ketika sensor mendeteksi intensitas hujan di atas ambang batas.
* **Analisis AI Prediktif:** Menggunakan Gemini API untuk mengalkulasi estimasi waktu pengeringan pakaian berdasarkan korelasi variabel cuaca dan penurunan berat.
* **Notifikasi dan Interaksi:** Menyediakan antarmuka bot Telegram untuk pelaporan status dan dasbor Metabase untuk pemantauan tren historis.

---

## 2. Arsitektur Infrastruktur (Laporan Teknis)

Proyek ini mengadopsi arsitektur tiga lapis (*Edge, Gateway, Server*) yang saling terhubung melalui jaringan lokal dan *Virtual Private Network* (Netbird).

| Komponen | Lapisan | Peran dan Fungsi Teknis |
| :--- | :--- | :--- |
| **ESP32** | *Edge Device* | Membaca data dari 5 sensor fisik dan menggerakkan aktuator motor servo. Berkomunikasi via MQTT lokal. |
| **Raspberry Pi** | *Gateway* | Menjalankan Mosquitto Broker sebagai pusat lalu lintas pesan MQTT (Topik: `sensor/cuaca` & `sensor/control`). |
| **Skrip Python (VM)** | *Application Server* | Menjalankan *multi-threading* untuk pemrosesan AI (Gemini), pengunggahan data ke Supabase, dan *long-polling* bot Telegram. |
| **n8n Engine** | *Orchestration* | Berjalan di Docker (Laptop) untuk mengeksekusi logika kondisional buka/tutup atap guna mencegah *spam* perintah servo. |
| **Supabase** | *Database (Cloud)* | DBMS terpusat untuk menyimpan tabel *log* sensor mentah dan hasil kalkulasi prediksi LLM. |
| **Metabase** | *Analytics* | Berjalan di Docker (Laptop) sebagai dasbor visual untuk memantau indikator performa dan grafik tren penurunan berat air. |

---

## 3. Topologi Jaringan dan Keamanan (Netbird VPN)

Mengingat sistem ini mengintegrasikan perangkat jaringan lokal (ESP32 dan Raspberry Pi di rumah) dengan perangkat eksternal (Virtual Machine dan Laptop), proyek ini menggunakan **Netbird** (*Peer-to-Peer Mesh VPN* berbasis WireGuard) untuk mengamankan jalur komunikasi data.

* **Isolasi Keamanan:** Penggunaan Netbird memungkinkan VM dan Laptop untuk berkomunikasi dengan broker Mosquitto di Raspberry Pi secara aman tanpa perlu melakukan konfigurasi *Port Forwarding* yang berisiko pada *router* penyedia layanan internet lokal.
* **Alamat IP Terpusat:** Seluruh perangkat komputasi diinstal agen Netbird dan disatukan ke dalam satu jaringan privat maya. Pada arsitektur ini, Raspberry Pi dialokasikan sebagai pusat broker MQTT dengan alamat IP statis internal VPN `100.117.143.2`. Skrip pada VM dan n8n pada Laptop wajib diarahkan ke alamat IP tersebut.

---

## 4. Skema Basis Data (Supabase)

Proyek ini menggunakan basis data relasional di Supabase dengan dua tabel utama:

1. **`log_jemuran`**: 
   Menyimpan data mentah periodik dari perangkat. Kolom yang digunakan: `id`, `waktu` (timestamptz), `suhu` (float), `kelembapan` (float), `cahaya` (integer), `intensitas_hujan` (integer), dan `berat` (integer).
2. **`ai_prediksi_jemuran`**: 
   Menyimpan hasil inferensi dari Gemini AI. Kolom yang digunakan: `id`, `waktu_prediksi` (timestamptz), `log_id_referensi` (Foreign Key), `status_jemuran` (teks), `estimasi_menit` (integer), dan `alasan` (teks).

---

## 5. Panduan Memulai (*Deployment*)

Berkas konfigurasi spesifik untuk ESP32, Raspberry Pi, dan Skrip VM terdapat pada direktori masing-masing beserta panduan instalasinya.

Untuk menjalankan layanan infrastruktur lokal (n8n dan Metabase) di laptop, pastikan Docker sudah terpasang dan jalankan perintah berikut di terminal:

### A. Menjalankan n8n Engine
Perintah ini menggunakan *Named Volume* (`n8n_data`) agar konfigurasi *workflow* tidak hilang saat kontainer dihentikan.
```bash
docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n:latest
```

### B. Menjalankan Metabase (Mode Aman RAM)
Perintah ini membatasi penggunaan memori kontainer maksimal 512 MB untuk mencegah terjadinya kebocoran memori (*Out of Memory* / *Black Screen*) pada sistem *host*.
```bash
docker run -d --name metabase -p 3000:3000 -m 512m -e "JAVA_OPTS=-Xmx350m -Xms150m" -v metabase_data:/metabase.db metabase/metabase:latest
```

---

## 6. Keamanan dan Kredensial

Repositori ini tidak menyertakan kunci API produksi. Sebelum menjalankan skrip Python pada VM, Anda wajib membuat berkas `.env` yang merujuk pada format `.env.example` dan mengisi variabel berikut:
* `TELEGRAM_TOKEN`
* `GEMINI_API_KEY`
* `SUPABASE_URL`
* `SUPABASE_SERVICE_ROLE_KEY`