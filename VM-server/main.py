import os
import json
import threading
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
import requests

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

# --- KONFIGURASI JARINGAN & TOPIK ---
RASPI_IP = "100.117.143.2" 
TOPIC_SENSOR = "sensor/cuaca"
TOPIC_HASIL = "sensor/ai_result"

# KREDENSIAL TELEGRAM
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "TOKEN_BOT_KAMU_DI_SINI")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "CHAT_ID_KAMU_DI_SINI")

# KREDENSIAL GEMINI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_MODEL_FALLBACKS = [
    GEMINI_MODEL,
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
]

# KREDENSIAL SUPABASE
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

# VARIABEL STATE
ai_sedang_proses = False
ai_state_lock = threading.Lock()
state_lock = threading.Lock()
latest_sensor_data = None
latest_ai_prediction = None

def simpan_state_terbaru(sensor, log_row):
    global latest_sensor_data
    with state_lock:
        latest_sensor_data = {
            "waktu": datetime.now(timezone.utc).isoformat(),
            "log_id": log_row.get("id"),
            "suhu": sensor.get("suhu"),
            "kelembapan": sensor.get("kelembapan"),
            "cahaya": sensor.get("cahaya"),
            "intensitas_hujan": sensor.get("intensitas_hujan"),
            "berat": sensor.get("berat"),
            "servo_status": sensor.get("servo_status")
        }

def simpan_prediksi_terbaru(keputusan, prediksi_row):
    global latest_ai_prediction
    with state_lock:
        latest_ai_prediction = {
            "waktu_prediksi": datetime.now(timezone.utc).isoformat(),
            "prediksi_id": prediksi_row.get("id") if prediksi_row else None,
            "status_jemuran": keputusan.get("status_jemuran"),
            "estimasi_menit": keputusan.get("estimasi_menit"),
            "alasan": keputusan.get("alasan"),
        }

def buat_pesan_status_telegram():
    with state_lock:
        sensor = dict(latest_sensor_data) if latest_sensor_data else None
        prediksi = dict(latest_ai_prediction) if latest_ai_prediction else None

    if not sensor:
        return "[PERINGATAN] STATUS JEMURAN: Belum ada data sensor masuk dari perangkat."

    suhu = sensor.get("suhu", "-")
    kelembapan = sensor.get("kelembapan", "-")
    cahaya = sensor.get("cahaya", "-")
    hujan = sensor.get("intensitas_hujan", "-")
    berat = sensor.get("berat", "-")
    servo = sensor.get("servo_status", "-").upper()
    
    status_ai = prediksi.get("status_jemuran") if prediksi else "BELUM ADA PREDIKSI"
    estimasi = prediksi.get("estimasi_menit") if prediksi else "-"
    alasan = prediksi.get("alasan") if prediksi else "Belum ada analisis berkala."

    return (
        "STATUS JEMURAN REAL-TIME\n\n"
        f"Suhu: {suhu} C\n"
        f"Kelembapan: {kelembapan} %\n"
        f"Cahaya: {cahaya}\n"
        f"Intensitas Hujan: {hujan}\n"
        f"Berat Jemuran: {berat} kg\n"
        f"Status Atap: {servo}\n\n"
        "ANALISIS AI GEMINI:\n"
        f"Status: {status_ai}\n"
        f"Estimasi Kering: {estimasi} menit\n"
        f"Catatan: {alasan}"
    )

def proses_perintah_telegram():
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "TOKEN_BOT_KAMU_DI_SINI":
        print("[TELEGRAM] [PERINGATAN] Polling tidak aktif karena token belum dikonfigurasi.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    offset = 0

    print("[TELEGRAM] [INFO] Polling interaksi aktif. Menunggu perintah /status...")
    while True:
        try:
            response = requests.get(url, params={"timeout": 30, "offset": offset}, timeout=35)
            response.raise_for_status()
            data = response.json()

            for update in data.get("result", []):
                offset = update.get("update_id", offset) + 1
                message = update.get("message") or update.get("edited_message")
                if not message:
                    continue

                chat_id = str(message.get("chat", {}).get("id", ""))
                if TELEGRAM_CHAT_ID and TELEGRAM_CHAT_ID != "CHAT_ID_KAMU_DI_SINI" and chat_id != str(TELEGRAM_CHAT_ID):
                    continue

                text = (message.get("text") or "").strip().lower()
                if text.startswith("/status"):
                    balasan_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                    payload = {
                        'chat_id': chat_id,
                        'text': buat_pesan_status_telegram()
                    }
                    requests.post(balasan_url, json=payload, timeout=10)
                    print(f"[TELEGRAM] [INFO] Berhasil merespons permintaan status dari Chat ID: {chat_id}")

        except Exception as e:
            print(f"[TELEGRAM] [ERROR] Masalah pada polling: {e}")

def simpan_ke_supabase(nama_tabel, payload):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[SUPABASE] [PERINGATAN] SUPABASE_URL atau SUPABASE_KEY belum diatur.")
        return None

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{nama_tabel}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code >= 400:
        print(f"[SUPABASE] [ERROR] {nama_tabel} gagal dengan status {response.status_code}: {response.text}")
        response.raise_for_status()

    hasil = response.json()
    return hasil[0] if isinstance(hasil, list) and hasil else hasil

def simpan_log_jemuran_ke_supabase(sensor):
    waktu_sekarang = datetime.now(timezone.utc).isoformat()

    log_payload = {
        "waktu": waktu_sekarang,
        "suhu": float(sensor.get("suhu", 0)),
        "kelembapan": float(sensor.get("kelembapan", 0)),
        "cahaya": int(sensor.get("cahaya", 0)),
        "intensitas_hujan": int(sensor.get("intensitas_hujan", 0)),
        "berat": int(sensor.get("berat", 0)),
    }

    log_row = simpan_ke_supabase("log_jemuran", log_payload)
    if not log_row:
        print("[SUPABASE] [ERROR] Gagal menyimpan log_jemuran.")
        return None

    print(f"[SUPABASE] [INFO] Log berhasil disimpan. log_id={log_row.get('id')}")
    return log_row

def simpan_prediksi_ke_supabase(log_id, keputusan):
    waktu_sekarang = datetime.now(timezone.utc).isoformat()

    prediksi_payload = {
        "waktu_prediksi": waktu_sekarang,
        "log_id_referensi": log_id,
        "status_jemuran": keputusan.get("status_jemuran"),
        "estimasi_menit": int(keputusan.get("estimasi_menit", 0)),
        "alasan": keputusan.get("alasan"),
    }

    prediksi_row = simpan_ke_supabase("ai_prediksi_jemuran", prediksi_payload)
    if not prediksi_row:
        print("[SUPABASE] [ERROR] Gagal menyimpan ai_prediksi_jemuran.")
        return None

    print(f"[SUPABASE] [INFO] Prediksi berhasil disimpan. prediksi_id={prediksi_row.get('id')}")
    return prediksi_row

def proses_ai_gemini(data):
    prompt = f"""
    Kamu adalah sistem pakar jemuran otomatis.
    Tugasmu hanya menganalisis data sensor dan mengembalikan satu objek JSON valid.

    Aturan output:
    - Balas hanya JSON mentah, tanpa markdown, tanpa penjelasan tambahan, tanpa code fence.
    - Gunakan hanya key yang diminta.
    - Pastikan nilai estimasi_menit dan berat bertipe angka.

    Analisis data sensor berikut:
    - Suhu: {data.get('suhu')} C 
    - Kelembapan: {data.get('kelembapan')} %
    - Cahaya: {data.get('cahaya')}
    - Hujan: {data.get('intensitas_hujan')}
    - Berat Jemuran Saat Ini: {data.get('berat')} gram

    Kembalikan HANYA dalam format JSON berikut:
    {{
        "status_jemuran": "KERING/SEDANG/BASAH", 
        "estimasi_menit": 0, 
        "alasan": "Maksimal 15 Kata",
        "berat": {int(data.get('berat', 0))} 
    }}
    """

    if not GEMINI_API_KEY:
        print("[AI] [PERINGATAN] GEMINI_API_KEY belum diatur.")
        return None

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
    }

    last_error = None
    for model_name in GEMINI_MODEL_FALLBACKS:
        if not model_name:
            continue
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 404:
                last_error = f"model '{model_name}' tidak ditemukan"
                continue
            response.raise_for_status()
            data_json = response.json()
            hasil_teks = data_json["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(hasil_teks)
        except Exception as e:
            last_error = str(e)

    print(f"[AI] [ERROR] Kegagalan pemrosesan model: {last_error}")
    return None

def tangani_pesan_masuk(client, payload, log_row):
    global ai_sedang_proses
    try:
        print("[AI] [INFO] Memulai pemrosesan data sensor menggunakan Gemini API...")
        keputusan = proses_ai_gemini(payload)

        if keputusan:
            prediksi_row = simpan_prediksi_ke_supabase(log_row.get("id"), keputusan)
            simpan_prediksi_terbaru(keputusan, prediksi_row)

            paket = {"sensor": payload, "ai": keputusan}
            client.publish(TOPIC_HASIL, json.dumps(paket))
            print(f"[INFO] Hasil keputusan '{keputusan['status_jemuran']}' diterbitkan ke {TOPIC_HASIL}")

    except Exception as e:
        print(f"[ERROR] Gagal memproses pesan masuk: {e}")
    finally:
        with ai_state_lock:
            ai_sedang_proses = False

def on_message(client, userdata, msg):
    global ai_sedang_proses
    try:
        payload = json.loads(msg.payload.decode())
        print(f"[DATA] Menerima payload sensor: {payload}")

        log_row = simpan_log_jemuran_ke_supabase(payload)
        if not log_row:
            return

        simpan_state_terbaru(payload, log_row)
        
        berat = float(payload.get('berat', 0))
        if berat < 0.5:
            print(f"[INFO] Berat terdeteksi {berat} kg (di bawah batas ambang). AI Gemini dilewati.")
            return

        with ai_state_lock:
            if ai_sedang_proses:
                print("[INFO] AI sedang memproses antrean sebelumnya. Data baru dilewati.")
                return
            ai_sedang_proses = True

        worker = threading.Thread(target=tangani_pesan_masuk, args=(client, payload, log_row), daemon=True)
        worker.start()
            
    except Exception as e:
        print(f"[ERROR] Gagal memproses parsing data: {e}")

# --- KENDALI UTAMA ---
print("[INFO] Menginisialisasi sistem monitoring laptop...")

telegram_thread = threading.Thread(target=proses_perintah_telegram, daemon=True)
telegram_thread.start()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) 
client.on_message = on_message

try:
    print(f"[INFO] Menghubungkan ke Broker Raspi via Netbird ({RASPI_IP})...")
    client.connect(RASPI_IP, 1883, 60) 
    client.subscribe(TOPIC_SENSOR)
    print(f"[INFO] Sistem aktif. Menunggu kiriman data pada topik '{TOPIC_SENSOR}'...")
    client.loop_forever()
except TimeoutError:
    print(f"[FATAL] Batas waktu terlampaui. Perangkat {RASPI_IP} tidak merespons.")
except Exception as e:
    print(f"[FATAL] Terjadi kegagalan sistem: {e}")