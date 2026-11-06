import os
import time
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

from apscheduler.schedulers.background import BackgroundScheduler
from plyer import notification

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

scheduler = BackgroundScheduler()
scheduler.start() 


def get_current_time() -> str:
    """Mengambil waktu dan tanggal saat ini dari sistem laptop."""
    now = datetime.now().strftime("%H:%M:%S")
    return f"Waktu lokal laptop saat ini: {now}"

def open_program(nama_aplikasi: str) -> str:
    """Membuka aplikasi di laptop. Mendukung: vscode, capcut, browser, dan notepad."""
    app = nama_aplikasi.lower()
    try:
        if "vscode" in app or "code" in app:
            os.system("code") 
            return "Berhasil membuka VS Code."
        elif "capcut" in app:
            os.system("start capcut:") 
            return "Mencoba membuka CapCut."
        elif "browser" in app or "youtube" in app:
            os.system("start https://www.youtube.com")
            return "Berhasil membuka YouTube di browser."
        elif "notepad" in app:
            os.system("start notepad")
            return "Berhasil membuka Notepad."
        else:
            return f"Aplikasi {nama_aplikasi} belum diprogram di sistem."
    except Exception as e:
        return f"Gagal membuka aplikasi: {str(e)}"

# Fungsi ini yang diperbarui menggunakan Plyer
def tampilkan_popup(pesan: str):
    notification.notify(
        title="Asisten AI",
        message=pesan,
        app_name="Asisten Desktop",
        timeout=7 # Notifikasi tampil selama 7 detik
    )

def set_reminder(jam: int, menit: int, pesan: str) -> str:
    """
    Mengatur pengingat/alarm pada jam dan menit tertentu HARI INI.
    AI harus memecah waktu menjadi jam (integer 0-23) dan menit (integer 0-59).
    """
    scheduler.add_job(tampilkan_popup, 'cron', hour=jam, minute=menit, args=[pesan])
    return f"Pengingat berhasil disetel untuk {jam:02d}:{menit:02d} dengan pesan: '{pesan}'"

# ==========================================
# 3. KONFIGURASI AI
# ==========================================

tools_list = [get_current_time, open_program, set_reminder]

system_instruction = (
    "Kamu adalah asisten AI desktop pribadi yang ramah dan efisien. "
    "Kamu bisa membuka aplikasi laptop dan membuat pengingat jadwal. "
    "Jika pengguna meminta untuk diingatkan sesuatu, gunakan tool set_reminder dengan format jam (0-23) dan menit (0-59)."
)

# Inisialisasi Chat (Pastikan nama model sudah sesuai dengan yang berhasil sebelumnya)
chat = client.chats.create(
    model="bantuan/lucif-claude", # <--- SESUAIKAN JIKA PERLU
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=tools_list,
        temperature=0.7,
    )
)

print("=== ASISTEN AI DESKTOP (FASE 2 VERSI PLYER) ===")
print("Fitur aktif: Buka Aplikasi, Set Pengingat, Cek Waktu.")
print("Ketik 'keluar' untuk menutup program.\n")

# 4. Loop Percakapan
while True:
    try:
        user_input = input("Anda: ")
        if user_input.strip().lower() in ["exit", "keluar", "quit"]:
            print("Asisten: Sampai jumpa lagi!")
            scheduler.shutdown() 
            break
        
        if not user_input.strip():
            continue

        response = chat.send_message(user_input)
        print(f"\nAsisten: {response.text}\n")

    except KeyboardInterrupt:
        print("\nProgram dihentikan.")
        scheduler.shutdown()
        break
    except Exception as e:
        print(f"\n[Error]: {e}\n")