import os
import sys
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# PyQt6 UI & Threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QCheckBox, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QPoint, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon

# Otomasi Keyboard
import pyautogui
pyautogui.PAUSE = 0.05

# Google GenAI SDK
from google import genai
from google.genai import types

# Penjadwalan & Notifikasi
from apscheduler.schedulers.background import BackgroundScheduler
from plyer import notification

# Audio Player, TTS, & Speech Recognition
import pygame
import edge_tts
import speech_recognition as sr

pygame.mixer.init()

# ==========================================
# 1. SISTEM MEMORI LOKAL (PERSISTENT MEMORY)
# ==========================================
HISTORY_FILE = "chat_history.json"
MAX_SAVED_HISTORY = 30

def load_local_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data[-MAX_SAVED_HISTORY:]
    except Exception as e:
        print(f"[Warning] Gagal membaca riwayat: {e}")
        return []

def save_single_message(role: str, text: str):
    if not text.strip():
        return
    history = load_local_history()
    history.append({"role": role, "text": text})
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Error] Gagal menyimpan chat: {e}")

# ==========================================
# 2. SETUP TOOLS SISTEM LAPTOP
# ==========================================
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

def tampilkan_popup(pesan: str):
    notification.notify(
        title="Asisten AI",
        message=pesan,
        app_name="Asisten Desktop",
        timeout=7
    )

def set_reminder(jam: int, menit: int, pesan: str) -> str:
    """Mengatur pengingat/alarm pada jam dan menit tertentu (format 24 jam)."""
    scheduler.add_job(tampilkan_popup, 'cron', hour=jam, minute=menit, args=[pesan])
    return f"Pengingat disetel untuk {jam:02d}:{menit:02d} dengan pesan: '{pesan}'"

def press_single_key(key: str) -> str:
    """Menekan satu tombol keyboard satuan (enter, space, esc, volumeup, volumedown, playpause, f5, dll)."""
    try:
        pyautogui.press(key.lower().strip())
        return f"Berhasil menekan tombol '{key}'."
    except Exception as e:
        return f"Gagal menekan tombol: {str(e)}"

def press_hotkey(keys: list[str]) -> str:
    """Menekan shortcut kombinasi tombol keyboard (misal: ['ctrl', 'c'], ['alt', 'tab'], ['win', 'd'])."""
    try:
        cleaned_keys = [k.lower().strip() for k in keys]
        pyautogui.hotkey(*cleaned_keys)
        return f"Berhasil menekan shortcut: {' + '.join(cleaned_keys)}."
    except Exception as e:
        return f"Gagal menekan shortcut: {str(e)}"

tools_list = [get_current_time, open_program, set_reminder, press_single_key, press_hotkey]

# ==========================================
# 3. KONFIGURASI AI MODEL
# ==========================================
system_instruction = (
    "Kamu adalah asisten AI desktop pribadi yang ramah, ringkas, dan santai. "
    "Kamu hidup di layar laptop pengguna dan memiliki ingatan percakapan masa lalu. "
    "Kamu bisa mengontrol laptop (buka aplikasi, setel pengingat jadwal, menekan tombol keyboard/shortcut). "
    "Jawablah dengan bahasa santai dan ringkas (1-3 kalimat) agar nyaman dibaca atau didengarkan."
)

config_ai = types.GenerateContentConfig(
    system_instruction=system_instruction,
    tools=tools_list,
    temperature=0.7,
)

# Muat riwayat awal
initial_history = []
for msg in load_local_history():
    initial_history.append(
        types.Content(
            role=msg["role"],
            parts=[types.Part.from_text(text=msg["text"])]
        )
    )

chat_session = client.chats.create(
    model="gemini-flash-lite-latest",
    config=config_ai,
    history=initial_history
)

# ==========================================
# 4. THREAD WORKERS (AI & VOICE)
# ==========================================
class AIWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, pesan_user, voice_enabled=True):
        super().__init__()
        self.pesan_user = pesan_user
        self.voice_enabled = voice_enabled

    def run(self):
        try:
            save_single_message("user", self.pesan_user)
            response = chat_session.send_message(self.pesan_user)
            teks_balasan = response.text.strip()

            if not teks_balasan:
                teks_balasan = "Siap, perintah sudah saya jalankan!"

            save_single_message("model", teks_balasan)

            # Jika Mode Suara Aktif, generate dan putar audio
            if self.voice_enabled:
                suara = "id-ID-GadisNeural"  # Pilihan lain: "id-ID-ArdiNeural"
                audio_file = "temp_voice.mp3"

                async def generate_speech():
                    communicate = edge_tts.Communicate(teks_balasan, suara)
                    await communicate.save(audio_file)

                asyncio.run(generate_speech())

                if os.path.exists(audio_file):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                        pygame.mixer.music.unload()
                    pygame.mixer.music.load(audio_file)
                    pygame.mixer.music.play()

            self.finished.emit(teks_balasan)

        except Exception as e:
            self.finished.emit(f"Kendala: {str(e)}")


class VoiceListenerThread(QThread):
    text_detected = pyqtSignal(str)
    status_signal = pyqtSignal(str)

    def __init__(self, continuous_mode=False):
        super().__init__()
        self.continuous_mode = continuous_mode
        self.is_running = True
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

    def run(self):
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
                while self.is_running:
                    self.status_signal.emit("Mendengarkan suara...")
                    try:
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                        self.status_signal.emit("Memproses suara...")
                        teks = self.recognizer.recognize_google(audio, language="id-ID")
                        if teks.strip():
                            self.text_detected.emit(teks)
                        if not self.continuous_mode:
                            break
                    except sr.WaitTimeoutError:
                        if not self.continuous_mode:
                            self.status_signal.emit("Tidak ada suara.")
                            break
                    except sr.UnknownValueError:
                        self.status_signal.emit("Suara kurang jelas...")
                    except Exception:
                        if not self.continuous_mode:
                            break
        except Exception as e:
            self.status_signal.emit(f"Error Mic: {str(e)}")

    def stop(self):
        self.is_running = False
        self.quit()

# ==========================================
# 5. ANTARMUKA DESKTOP (GUI)
# ==========================================
class DesktopPetApp(QWidget):
    def __init__(self):
        super().__init__()
        self.voice_thread = None
        self.initUI()
        self.initTray()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(290)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Balon Dialog
        self.bubble_label = QLabel("Halo! Saya siap membantu di desktop.", self)
        self.bubble_label.setWordWrap(True)
        self.bubble_label.setStyleSheet("""
            background-color: rgba(255, 255, 255, 240);
            color: #111;
            border: 2px solid #555;
            border-radius: 12px;
            padding: 10px;
            font-size: 12px;
            font-weight: 500;
        """)
        self.bubble_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.bubble_label)

        # Gambar Karakter
        self.image_label = QLabel(self)
        try:
            self.pixmap = QPixmap('karakter.png')
            self.pixmap = self.pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(self.pixmap)
        except Exception:
            self.image_label.setText("[Gambar karakter.png]")
            self.image_label.setStyleSheet("color: white; background-color: rgba(0,0,0,150); padding: 15px; border-radius: 10px;")
            
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)

        # Input Box & Tombol Mic
        input_layout = QHBoxLayout()
        self.input_box = QLineEdit(self)
        self.input_box.setPlaceholderText("Ketik / tekan mic...")
        self.input_box.setStyleSheet("""
            background-color: rgba(255, 255, 255, 220); 
            border: 1px solid #777;
            border-radius: 6px; 
            padding: 5px;
            font-size: 12px;
        """)
        self.input_box.returnPressed.connect(lambda: self.proses_input(self.input_box.text()))
        input_layout.addWidget(self.input_box)

        self.btn_mic = QPushButton("🎙️", self)
        self.btn_mic.setFixedSize(32, 32)
        self.btn_mic.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
        """)
        self.btn_mic.clicked.connect(self.toggle_single_listen)
        input_layout.addWidget(self.btn_mic)
        layout.addLayout(input_layout)

        # Opsi Mode Suara (Voice Toggle)
        self.chk_voice_mode = QCheckBox("🔊 Suara Aktif (Voice ON)", self)
        self.chk_voice_mode.setChecked(True)  # Default menyala
        self.chk_voice_mode.setStyleSheet("""
            QCheckBox {
                color: #111;
                background-color: rgba(255, 255, 255, 200);
                padding: 3px 6px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.chk_voice_mode)

        # Opsi Hands-Free (Mic Always-On)
        self.chk_always_mic = QCheckBox("🎙️ Mic Selalu Aktif (Hands-Free)", self)
        self.chk_always_mic.setStyleSheet("""
            QCheckBox {
                color: #111;
                background-color: rgba(255, 255, 255, 180);
                padding: 3px 6px;
                border-radius: 4px;
                font-size: 11px;
            }
        """)
        self.chk_always_mic.toggled.connect(self.toggle_always_mic)
        layout.addWidget(self.chk_always_mic)

        self.oldPos = QPoint()

    def initTray(self):
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists('karakter.png'):
            self.tray_icon.setIcon(QIcon('karakter.png'))
        tray_menu = QMenu()
        tray_menu.addAction("Tampilkan Karakter", self.show)
        tray_menu.addAction("Sembunyikan", self.hide)
        tray_menu.addAction("Hapus Riwayat Chat", self.reset_memory)
        tray_menu.addSeparator()
        tray_menu.addAction("Keluar Sepenuhnya", self.keluar_aplikasi)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def reset_memory(self):
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        self.bubble_label.setText("Riwayat obrolan berhasil dihapus!")

    def toggle_single_listen(self):
        if self.voice_thread and self.voice_thread.isRunning():
            self.voice_thread.stop()
            self.bubble_label.setText("Mic dinonaktifkan.")
            return

        self.voice_thread = VoiceListenerThread(continuous_mode=False)
        self.voice_thread.status_signal.connect(self.update_status_mic)
        self.voice_thread.text_detected.connect(self.proses_input)
        self.voice_thread.start()

    def toggle_always_mic(self, checked):
        if self.voice_thread and self.voice_thread.isRunning():
            self.voice_thread.stop()

        if checked:
            self.voice_thread = VoiceListenerThread(continuous_mode=True)
            self.voice_thread.status_signal.connect(self.update_status_mic)
            self.voice_thread.text_detected.connect(self.proses_input)
            self.voice_thread.start()
        else:
            self.bubble_label.setText("Mode Always-On mati.")

    def update_status_mic(self, status):
        self.bubble_label.setText(status)

    def proses_input(self, pesan):
        pesan = pesan.strip()
        if not pesan:
            return

        self.input_box.clear()
        self.bubble_label.setText(f'"{pesan}"\n(Sedang merespons...)')

        # Kirim status apakah mode suara aktif atau tidak
        voice_on = self.chk_voice_mode.isChecked()
        self.worker = AIWorker(pesan, voice_enabled=voice_on)
        self.worker.finished.connect(self.update_balasan)
        self.worker.start()

    def update_balasan(self, teks_balasan):
        self.bubble_label.setText(teks_balasan)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if not self.oldPos.isNull():
            delta = event.globalPosition().toPoint() - self.oldPos
            self.move(self.pos() + delta)
            self.oldPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = QPoint()

    def keluar_aplikasi(self):
        if self.voice_thread and self.voice_thread.isRunning():
            self.voice_thread.stop()
        scheduler.shutdown(wait=False)
        QApplication.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    pet = DesktopPetApp()
    pet.show()
    sys.exit(app.exec())