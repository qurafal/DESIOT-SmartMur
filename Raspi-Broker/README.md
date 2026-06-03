Repositori ini memuat konfigurasi dan skrip operasional untuk Raspberry Pi yang diimplementasikan sebagai *gateway* komunikasi dalam proyek rekayasa *Internet of Things* (IoT) di lingkungan akademik Teknik Komputer Universitas Indonesia. Perangkat ini beroperasi pada lapisan tengah (*middleware*), menghubungkan simpul sensor lokal dengan peladen awan dan mesin orkestrasi pusat.

## 1. Peran dan Fungsi Teknis

Raspberry Pi dalam topologi sistem ini menjalankan dua peran infrastruktur yang krusial:
* **MQTT Broker Lokal:** Menjalankan layanan *daemon* Mosquitto untuk menampung publikasi data sensor berfrekuensi tinggi dari ESP32 dan mendistribusikan perintah kendali ke aktuator.
* **Simpul Jaringan Privat (VPN Node):** Terhubung ke dalam *mesh network* Netbird dengan alamat IP statis `100.117.143.2`. Konfigurasi ini menjamin peladen (Virtual Machine) dan mesin n8n (Laptop) dapat melakukan *subscribe* ke topik MQTT secara aman dari luar jaringan lokal (NAT) tanpa memerlukan konfigurasi *port forwarding*.

---

## 2. Struktur Berkas
```text
Raspi-Broker/
└── main.py         # Skrip Python utama penanganan lalu lintas MQTT lokal
```
---

## 3. Prasyarat Sistem dan Dependensi

Sebelum menjalankan skrip fungsional, pastikan sistem operasi Raspberry Pi telah terpasang paket infrastruktur dasar berikut:

### A. Instalasi Mosquitto Broker
Layanan inti MQTT harus diaktifkan terlebih dahulu di level sistem operasi pada port standar `1883`:
```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

### B. Instalasi Library Python
Skrip pengelola pesan ini menggunakan **Python 3**. Instal Library klien MQTT melalui *package manager* bawaan Python:
```bash
pip install paho-mqtt
```

---

## 4. Panduan Eksekusi Skrip

1. Akses terminal Raspberry Pi Anda (melalui SSH atau secara langsung), lalu masuk ke folder

2. **Jalankan Script:**
   Jalankan skrip secara langsung untuk memantau lalu lintas pesan masuk dan keluar secara *real-time*:
```bash
   python3 main.py
   ```

---

## 5. Pemetaan Topik MQTT

Sebagai pusat pertukaran data, broker ini memfasilitasi lalu lintas pesan pada dua topik utama:
* **Topik `sensor/cuaca` (Ingress):** Menerima *payload* JSON berisi parameter lingkungan (suhu, kelembapan, intensitas hujan, cahaya, dan massa pakaian) dari ESP32 setiap 3 detik. Data ini kemudian diserap oleh Virtual Machine.
