#include <Arduino.h>

#include <WiFi.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>
#include "HX711.h"
#include <DHT.h>

// ============================================================
// PROJECT: DESIOT - Smart Drying Rack System
// Sistem pengontrol jemuran otomatis berbasis IoT
// ============================================================
//
// STRUKTUR DATA JSON YANG DIKIRIM KE MQTT:
// {
//   "suhu": 25.3,             // Suhu dalam Celsius
//   "kelembapan": 65,         // Relative Humidity (RH) dalam Persen
//   "cahaya": 80,             // Intensitas cahaya dalam Persen (0-100%)
//   "intensitas_hujan": 40,   // Intensitas hujan dalam Persen (0-100%)
//   "berat": 2.50,            // Berat dalam Kilogram
//   "servo_status": "buka",   // Status jemuran: "buka" atau "tutup"
//   "timestamp": 123456789    // Waktu dalam Milidetik
// }
//
// PENJELASAN SENSOR:
// - DHT11: Mengukur suhu (°C) dan kelembapan udara (%)
// - LDR (Light Dependent Resistor): Mengukur intensitas cahaya (%)
// - Rain Sensor: Mengukur intensitas hujan (%)
// - HX711 + Load Cell: Mengukur berat beban (kg)
// - Servo MG90S: Mengontrol pembukaan/penutupan jemuran
// ============================================================

// --- KONFIGURASI WIFI & MQTT ---
const char* ssid = "LOCK_IN";         
const char* password = "yasayasetuju";   
// PASTIKAN IP INI SESUAI DENGAN IP RASPBERRY PI SAAT INI
const char* mqtt_server = "192.168.1.35"; 
const int mqtt_port = 1883;

WiFiClient espClient;
PubSubClient client(espClient);

// --- KONFIGURASI PIN SENSOR ---
const int pinCahaya = 4;  // LDR Analog (A0)
const int pinHujan  = 5;  // Hujan Analog (A0)

// --- KONFIGURASI SERVO AKTUATOR ---
const int SERVO_PIN = 18;           // Pin untuk Servo Motor
const int RAIN_THRESHOLD = 60;      // Threshold hujan (dalam %)
bool isServoActive = false;         // Status servo saat ini (false=buka, true=tutup)

// Deklarasi objek servo
Servo myservo;

// --- MQTT CONNECTION STATE ---
bool mqtt_connected = false;        // Status koneksi MQTT
unsigned long lastMqttAttempt = 0;  // Waktu terakhir coba konek MQTT
const unsigned long mqttRetryInterval = 10000;  // Coba koneksi setiap 10 detik

#define DHTPIN 15         // Pin Data DHT11
#define DHTTYPE DHT11     
DHT dht(DHTPIN, DHTTYPE);

#define DT_PIN 16         // Pin Data HX711
#define SCK_PIN 17        // Pin Clock HX711
HX711 scale;
float calibration_factor = -215430; // Nilai kalibrasi Anda

void setup_wifi() {
  delay(10);
  Serial.println("\n--- MEMULAI KONEKSI WIFI ---");
  WiFi.disconnect(true);
  delay(1000);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int counter = 0;
  while (WiFi.status() != WL_CONNECTED && counter < 20) { 
    delay(500);
    Serial.print(".");
    counter++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[SUKSES] Terhubung ke WiFi!");
  } else {
    Serial.println("\n[GAGAL] WiFi bermasalah. Cek Hotspot.");
  }
}

void reconnect() {
  // Fungsi reconnect yang tidak infinite retry
  // Coba koneksi hanya 1 kali, jika gagal tunggu interval sebelum coba lagi
  
  unsigned long currentTime = millis();
  
  // Hanya coba koneksi jika sudah melewati retry interval
  if (currentTime - lastMqttAttempt >= mqttRetryInterval) {
    lastMqttAttempt = currentTime;
    
    if (!client.connected()) {
      Serial.print("[MQTT] Mencoba koneksi ke broker...");
      if (client.connect("ESP32-Sakaa-SuperNode")) {
        Serial.println(" BERHASIL!");
        mqtt_connected = true;
        
        // Subscribe ke topic control setelah berhasil connect
        client.subscribe("sensor/control");
        Serial.println("[MQTT] Subscribe ke topic 'sensor/control'");
      } else {
        Serial.print(" GAGAL (rc=");
        Serial.print(client.state());
        Serial.println("). Coba lagi dalam 10 detik...");
        mqtt_connected = false;
      }
    } else {
      mqtt_connected = true;
    }
  }
}

// Callback function untuk menangani pesan MQTT yang diterima
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  // Convert payload ke string
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.print("[MQTT] Menerima pesan di topic '");
  Serial.print(topic);
  Serial.print("': ");
  Serial.println(message);
  
  // Handle topic sensor/control
  if (String(topic) == "sensor/control") {
    if (message == "buka") {
      // Buka jemuran (0°)
      myservo.write(0);
      isServoActive = false;
      Serial.println("[SERVO CONTROL] MEMBUKA JEMURAN (0°) - Perintah dari MQTT");
    } 
    else if (message == "tutup") {
      // Tutup jemuran (180°)
      myservo.write(180);
      isServoActive = true;
      Serial.println("[SERVO CONTROL] MENUTUP JEMURAN (180°) - Perintah dari MQTT");
    }
    else {
      Serial.println("[SERVO CONTROL] Perintah tidak dikenali. Gunakan 'buka' atau 'tutup'");
    }
  }
}

void controlServo(int rainPercentage) {
  // Fungsi untuk mengontrol servo berdasarkan intensitas hujan
  // Menggunakan ESP32Servo library
  // Jika hujan >= threshold, tutup jemuran (180°)
  // Jika hujan < threshold, buka jemuran (0°)
  
  bool shouldCloseServo = (rainPercentage >= RAIN_THRESHOLD);
  
  // Hanya ubah posisi servo jika ada perubahan status
  if (shouldCloseServo != isServoActive) {
    if (shouldCloseServo) {
      // Tutup jemuran (180°)
      myservo.write(180);
      Serial.println("[SERVO] MENUTUP JEMURAN (180°) - Hujan terdeteksi!");
      isServoActive = true;
    } else {
      // Buka jemuran (0°)
      myservo.write(0);
      Serial.println("[SERVO] MEMBUKA JEMURAN (0°) - Hujan sudah berhenti");
      isServoActive = false;
    }
    delay(1000); // Delay 1 detik agar servo punya waktu untuk bergerak penuh
  }
}

// Fungsi untuk membaca DHT11 dengan retry dan validasi
void readDHT11(float& suhu, int& kelembapan) {
  suhu = -1.0;
  kelembapan = -1;
  
  // Coba baca DHT11 hingga 3 kali
  for (int attempt = 1; attempt <= 3; attempt++) {
    float temp = dht.readTemperature();
    float humid_raw = dht.readHumidity();
    int humid = (int)humid_raw;
    
    Serial.print("[DHT11 Attempt ");
    Serial.print(attempt);
    Serial.print("] Raw Suhu: ");
    Serial.print(temp, 3);
    Serial.print("°C, Raw Kelembapan: ");
    Serial.print(humid_raw, 2);
    Serial.print("% (int: ");
    Serial.print(humid);
    Serial.println("%)");
    
    // Debug: cek apakah nilai NaN
    if (isnan(temp)) {
      Serial.println("[DHT11] ⚠ Suhu adalah NaN!");
    }
    if (isnan(humid_raw)) {
      Serial.println("[DHT11] ⚠ Kelembapan adalah NaN!");
    }
    
    // Validasi pembacaan
    if (!isnan(temp) && !isnan(humid_raw) && 
        temp >= -40 && temp <= 85 && 
        humid_raw >= 0 && humid_raw <= 100) {
      suhu = temp;
      kelembapan = humid;
      Serial.print("[DHT11] ✓ Pembacaan BERHASIL -> Suhu: ");
      Serial.print(suhu);
      Serial.print("°C, Kelembapan: ");
      Serial.print(kelembapan);
      Serial.println("%");
      return;
    }
    
    // Jika gagal, tunggu sebelum retry
    if (attempt < 3) {
      Serial.println("[DHT11] ✗ Pembacaan gagal, coba lagi...");
      delay(500);
    }
  }
  
  Serial.println("[DHT11] ✗✗✗ SEMUA PEMBACAAN GAGAL - Cek koneksi sensor!");
  Serial.println("[DHT11] DEBUG: Kemungkinan masalah:");
  Serial.println("  1. Sensor DHT11 tidak terhubung ke GPIO 15");
  Serial.println("  2. Kabel sensor putus atau longgar");
  Serial.println("  3. Sensor cacat atau rusak");
  Serial.println("  4. ESP32 memerlukan restart");
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Memulai Komunikasi Jaringan
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);  // Set callback untuk menangani pesan MQTT

  // Memulai Sensor DHT11
  dht.begin();
  delay(2000);  // DHT11 perlu waktu untuk stabilisasi setelah power on
  Serial.println("[DHT11] Sensor diinisialisasi. Tunggu stabilisasi...");
  
  // Memulai Sensor HX711
  scale.begin(DT_PIN, SCK_PIN);
  scale.set_scale(calibration_factor);
  scale.tare(); // Kalibrasi berat awal menjadi 0.00 kg
  
  // Inisialisasi Servo Motor (menggunakan ESP32Servo library)
  // Alokasikan timer PWM bawaan ESP32
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);
  
  // Set frekuensi standar servo (50Hz)
  myservo.setPeriodHertz(50);
  
  // Hubungkan servo ke GPIO 18 dengan pulse width 500-2400 microseconds
  myservo.attach(SERVO_PIN, 500, 2400);
  
  // Set posisi awal ke 0° (buka)
  myservo.write(0);
  isServoActive = false;
  Serial.println("[SERVO] Servo diinisialisasi di posisi buka (0°)");
  
  Serial.println("Semua sistem siap. Memulai pengiriman data...");
}

void loop() {
  // Coba reconnect (tanpa blocking jika gagal)
  if (!mqtt_connected) {
    reconnect();
  } else {
    client.loop();  // Hanya process MQTT jika sudah connected
  }

  // --- 1. BACA SENSOR CAHAYA (LDR Analog A0) ---
  int nilaiCahayaMentah = analogRead(pinCahaya); 
  // Konversi: Gelap (4095) -> 0%, Terang (0) -> 100%
  int persenCahaya = map(nilaiCahayaMentah, 4095, 0, 0, 100);
  persenCahaya = constrain(persenCahaya, 0, 100);

  // --- 2. BACA SENSOR HUJAN (Analog ke Persentase) ---
  int nilaiHujanMentah = analogRead(pinHujan);
  // Konversi: Kering (4095) -> 0%, Basah (0) -> 100%
  int persenHujan = map(nilaiHujanMentah, 4095, 0, 0, 100);
  persenHujan = constrain(persenHujan, 0, 100);
  
  // --- KONTROL SERVO BERDASARKAN SENSOR HUJAN ---
  // controlServo(persenHujan);

  // --- 3. BACA SENSOR DHT11 (Suhu & Kelembapan) dengan Retry ---
  float suhu;
  int kelembapan;
  readDHT11(suhu, kelembapan);

  // --- 4. BACA SENSOR BERAT (HX711) ---
  float beratKg = 0.00;
  if (scale.is_ready()) {
    beratKg = scale.get_units(10);
    if (beratKg > -0.01 && beratKg < 0.01) {
      beratKg = 0.00; 
    }
  } else {
    beratKg = -99.9; 
  }

  // --- 5. BUNGKUS KE DALAM JSON (HANYA ANGKA, TANPA SATUAN) ---
  char jsonBuffer[400]; 
  snprintf(jsonBuffer, sizeof(jsonBuffer), 
           "{\"suhu\": %.1f, \"kelembapan\": %d, \"cahaya\": %d, \"intensitas_hujan\": %d, \"berat\": %.2f, \"servo_status\": \"%s\", \"timestamp\": %lu}", 
           suhu, kelembapan, persenCahaya, persenHujan, beratKg, isServoActive ? "tutup" : "buka", millis());

  // --- 6. SELALU PRINT KE SERIAL MONITOR (DEBUGGING) ---
  Serial.print("[DATA] ");
  Serial.println(jsonBuffer);
  
  // --- 7. KIRIM KE RASPBERRY PI HANYA JIKA MQTT CONNECTED ---
  if (mqtt_connected) {
    if (client.publish("sensor/cuaca", jsonBuffer)) {
      Serial.println("[MQTT] Data terkirim ke Raspberry Pi");
    } else {
      Serial.println("[MQTT] Gagal mengirim data (queue penuh?)");
      mqtt_connected = false;  // Reset status jika publish gagal
    }
  } else {
    Serial.println("[MQTT] Tidak connected ke broker - data hanya di-print ke Serial");
  }

  // Kirim data setiap 3 detik
  delay(3000); 
}