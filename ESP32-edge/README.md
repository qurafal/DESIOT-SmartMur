Repositori ini memuat kode sumber C++ mikrokontroler ESP32 yang dikembangkan untuk rekayasa sistem *Internet of Things* (IoT) terdistribusi di lingkungan akademik Teknik Komputer Universitas Indonesia. Perangkat ini beroperasi pada lapisan *edge*, bertugas mengakuisisi data lingkungan secara fisik dan menggerakkan mekanisme aktuator atap jemuran otomatis.

## 1. Konfigurasi Perangkat Keras (Pinout)

Sistem ini membutuhkan penyambungan pin GPIO ESP32 ke berbagai modul sensor dan aktuator fisik. Berikut adalah pemetaan perangkat keras berdasarkan kode utama:

* **Sensor Suhu dan Kelembapan (DHT11):** Pin Data terhubung ke **GPIO 15**.
* **Sensor Berat (Modul HX711):** Pin Data (DT) terhubung ke **GPIO 16**, dan Pin Clock (SCK) terhubung ke **GPIO 17**.
* **Sensor Cahaya (LDR):** Terhubung ke pin analog **GPIO 4**.
* **Sensor Hujan:** Terhubung ke pin analog **GPIO 5**.
* **Motor Servo (MG90S/Setara):** Terhubung ke **GPIO 18** (dikendalikan via sinyal PWM perangkat keras pada frekuensi 50Hz).

## 2. Dependensi Pustaka (Libraries)

Sebelum melakukan kompilasi (*compile*) menggunakan Arduino IDE atau PlatformIO, pastikan Anda telah memasang pustaka eksternal berikut:

* `WiFi.h`: Pustaka bawaan core ESP32 untuk konektivitas jaringan.
* `PubSubClient.h`: Klien MQTT ringan untuk pengiriman dan penerimaan pesan.
* `ESP32Servo.h`: Pengendali motor servo yang dialokasikan khusus untuk *timer* perangkat keras ESP32.
* `HX711.h`: Pustaka pembacaan modul penguat sinyal *load cell*.
* `DHT.h`: Pustaka antarmuka untuk sensor suhu dan kelembapan lingkungan.

## 3. Konfigurasi Jaringan dan Broker

Skrip ini memerlukan penyesuaian parameter jaringan sebelum diunggah (*flashing*) ke dalam papan ESP32. Ubah variabel berikut pada bagian atas berkas kode sumber agar sesuai dengan topologi jaringan lokal Anda:

```cpp
const char* ssid = "SSID_ANDA";             // SSID WiFi lokal
const char* password = "PASS_ANDA";    // Kata sandi WiFi lokal
const char* mqtt_server = "IP_RASPBERRY_PI"; // Alamat IP statis Raspberry Pi (Broker)
const int mqtt_port = 1883;               // Port standar Mosquitto MQTT
```

## 4. Arsitektur Komunikasi MQTT

Perangkat ini terhubung dengan broker MQTT secara terus-menerus (*keep-alive*) dan menangani dua alur pertukaran data utama:

### A. Pengiriman Data Telemetri (Publish)
* **Topik:** `sensor/cuaca`
* **Interval:** Setiap 3.000 milidetik (3 detik).
* **Fungsi:** Mengirimkan *payload* berformat JSON yang memuat seluruh nilai bacaan sensor secara terkini beserta status bukaan mekanis atap.

**Struktur Payload JSON:**
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

### B. Penerimaan Perintah Kendali (Subscribe)
* **Topik:** `sensor/control`
* **Fungsi:** Mendengarkan instruksi *string* mentah dari sistem orkestrasi pusat (n8n) untuk menggerakkan aktuator pelindung jemuran.
* **Parameter yang Diterima:**
  * `buka`: Memutar servo ke sudut 0° (menarik atap pelindung, jemuran terbuka).
  * `tutup`: Memutar servo ke sudut 180° (mendorong atap pelindung, jemuran terlindungi).

## 5. Instruksi Instalasi dan Flashing

1. Buka berkas utama kode C++ menggunakan IDE pilihan Anda.
2. Pastikan pengaturan *Board* diatur ke modul ESP32 yang sesuai (misalnya: `DOIT ESP32 DEVKIT V1`).
3. Sesuaikan konstanta kalibrasi pada variabel `calibration_factor` agar bacaan massa *load cell* akurat dalam satuan kilogram.
4. Hubungkan ESP32 ke komputer, pilih *port* serial yang tepat, lalu klik **Upload**.