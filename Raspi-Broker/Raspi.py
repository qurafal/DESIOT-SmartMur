import paho.mqtt.client as mqtt
import json

# --- KONFIGURASI TOPIK & BROKER ---
LOCAL_BROKER = "localhost"  # Berjalan di Raspberry Pi itu sendiri
TOPIC_ESP = "sensor/cuaca"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[INFO] Raspberry Pi Bridge terhubung ke Broker Lokal.")
        client.subscribe(TOPIC_ESP)
        print(f"[INFO] Mendengarkan data sensor pada topik: {TOPIC_ESP}")
    else:
        print(f"[ERROR] Gagal terhubung ke broker, kode status: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8").strip()
        data = json.loads(payload)
        
        # Validasi format JSON dari ESP32 berdasarkan payload terbaru
        required_keys = ["suhu", "kelembapan", "cahaya", "intensitas_hujan", "berat", "servo_status", "timestamp"]
        if all(key in data for key in required_keys):
            print(f"[DATA VALID] Telemetry dari ESP32: {data}")
            # Data ini otomatis tersedia di broker lokal untuk diambil oleh laptop/n8n
        else:
            print(f"[PERINGATAN] Data tidak lengkap. Key yang diterima: {list(data.keys())}")

    except json.JSONDecodeError:
        print("[ERROR] Format data dari ESP32 bukan JSON valid.")
    except Exception as e:
        print(f"[ERROR] Terjadi kesalahan saat memproses pesan: {e}")

# --- INISIALISASI CLIENT MQTT ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(LOCAL_BROKER, 1883, 60)
    print("[INFO] Menjalankan fungsi bridge standby...")
    client.loop_forever()
except Exception as e:
    print(f"[FATAL] Gagal menjalankan bridge: {e}")