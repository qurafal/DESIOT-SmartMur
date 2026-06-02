import paho.mqtt.client as mqtt

# --- KONFIGURASI JARINGAN & TOPIK ---
# Menggunakan IP Netbird Raspberry Pi tempat broker Mosquitto berada
RASPI_IP = "100.117.143.2" 
MQTT_PORT = 1883
TOPIC_CONTROL = "sensor/control"

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[INFO] Laptop berhasil terhubung ke Broker MQTT.")
        # Mulai berlangganan ke topik kontrol dari n8n
        client.subscribe(TOPIC_CONTROL)
        print(f"[INFO] Sedang mendengarkan pergerakan pada topik: {TOPIC_CONTROL}")
        print("[INFO] Menunggu kiriman data dari n8n... (Tekan Ctrl+C untuk keluar)")
    else:
        print(f"[ERROR] Gagal terhubung ke broker, kode status: {rc}")

def on_message(client, userdata, msg):
    try:
        # Mengubah payload bytes menjadi string teks biasa
        payload = msg.payload.decode("utf-8").strip()
        print(f"[KONTROL MASUK] Menerima data dari topik {msg.topic}: {payload}")
        
    except Exception as e:
        print(f"[ERROR] Gagal membaca pesan: {e}")

# Inisialisasi client menggunakan Callback API versi 2 (sesuai standar pustaka terbaru)
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

try:
    print(f"[INFO] Mencoba menghubungkan ke {RASPI_IP}...")
    client.connect(RASPI_IP, MQTT_PORT, 60)
    # Loop_forever membuat skrip terus siaga di terminal laptop kamu
    client.loop_forever()
except TimeoutError:
    print(f"[FATAL] Batas waktu habis. Perangkat broker di {RASPI_IP} tidak merespons.")
except Exception as e:
    print(f"[FATAL] Gagal menjalankan pengujian: {e}")