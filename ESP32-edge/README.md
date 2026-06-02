# Simpul Sensor dan Aktuator (ESP32)

Folder ini berisi kode sumber C++ untuk mikrokontroler ESP32. Perangkat ini bertindak sebagai *edge device* yang bertugas mengakuisisi data lingkungan secara fisik dan menggerakkan mekanisme atap jemuran otomatis.

## 1. Konfigurasi Perangkat Keras (Pinout)

Berdasarkan pengaturan variabel pada berkas utama, berikut adalah pemetaan pin GPIO ESP32 yang harus dihubungkan ke masing-masing modul sensor dan aktuator:
* **Sensor Suhu dan Kelembapan (DHT11):** Terhubung ke GPIO 15.
* **Sensor Berat (Modul HX711):** Pin Data (DT) terhubung ke GPIO 16, dan Pin Clock (SCK) terhubung ke GPIO 17.
* **Sensor Cahaya (LDR):** Terhubung ke pin analog GPIO 4.
* **Sensor Hujan:** Terhubung ke pin analog GPIO 5.
* **Aktuator Motor Servo (MG90S):** Terhubung ke GPIO 18 untuk menerima sinyal PWM 50Hz.

## 2. Dependensi Pustaka (Libraries)

Untuk melakukan kompilasi kode ini (menggunakan Arduino IDE atau PlatformIO), pastikan pustaka pihak ketiga berikut telah terpasang pada lingkungan pengembangan Anda:
* `WiFi.h`: Pustaka bawaan core ESP32.
* `PubSubClient.h`: Mengelola koneksi klien MQTT.
* `ESP32Servo.h`: Mengontrol rotasi servo secara presisi menggunakan timer perangkat keras ESP32.
* `HX711.h`: Membaca modul penguat sinyal load cell.
* `DHT.h`: Menguraikan data dari sensor suhu dan kelembapan DHT11.

## 3. Konfigurasi Jaringan dan Broker

Sebelum melakukan pengunggahan (*flashing*) kode ke mikrokontroler ESP32, Anda wajib menyesuaikan konstanta jaringan pada bagian atas skrip agar perangkat dapat terhubung ke rute lokal:

```cpp
const char* ssid = "LOCK_IN";             // Sesuaikan dengan SSID WiFi lokal
const char* password = "yasayasetuju";    // Sesuaikan dengan kata sandi WiFi
const char* mqtt_server = "192.168.1.35"; // Pastikan IP ini sesuai dengan alamat statis Raspberry Pi saat ini
const int mqtt_port = 1883;
```

## 4. Spesifikasi Komunikasi MQTT

ESP32 ini berinteraksi dengan broker lokal menggunakan mekanisme penerbitan (*publish*) dan langganan (*subscribe*) pada dua topik berikut:

### A. Pengiriman Data (Topik: `sensor/cuaca`)
ESP32 melakukan pembacaan seluruh sensor dan mengirimkan paket data JSON setiap 3 detik (3000 milidetik) ke broker. 
Struktur *payload* JSON yang dikirimkan:
```json
{
  "suhu": 25.3,
  "kelembapan": 65,
  "cahaya": 80,
  "intensitas_hujan": 40,
  "berat": 2.50,
  "servo_status": "buka",
  "timestamp": 123456789
}
```

### B. Penerimaan Perintah (Topik: `sensor/control`)
Setelah berhasil terhubung, perangkat akan mendengarkan perintah kendali dari mesin otomasi pusat (n8n). 
Instruksi yang dieksekusi:
* `buka`: Menggerakkan servo ke posisi 0 derajat (menarik atap pelindung).
* `tutup`: Menggerakkan servo ke posisi 180 derajat (menutup atap pelindung).