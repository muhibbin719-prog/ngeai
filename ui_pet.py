import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QLineEdit
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap

class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 1. Membuat jendela transparan, selalu di atas (always on top), dan tanpa border
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 2. Layout utama (susunan atas-bawah)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 3. Label untuk menampilkan gambar karakter
        self.image_label = QLabel(self)
        
        # Mencoba memuat gambar karakter.png
        try:
            self.pixmap = QPixmap('karakter.png')
            # Ubah ukuran gambar jika terlalu besar (opsional)
            self.pixmap = self.pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
            self.image_label.setPixmap(self.pixmap)
        except Exception:
            # Jika gambar tidak ditemukan, tampilkan teks ini sebagai gantinya
            self.image_label.setText("(Gambar karakter.png tidak ditemukan)")
            self.image_label.setStyleSheet("color: white; background-color: rgba(0,0,0,150); padding: 20px; border-radius: 10px;")
            
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)

        # 4. Kolom input teks untuk mengetik perintah ke AI
        self.input_box = QLineEdit(self)
        self.input_box.setPlaceholderText("Ketik perintah di sini... lalu tekan Enter")
        self.input_box.setStyleSheet("""
            background-color: rgba(255, 255, 255, 200); 
            border-radius: 10px; 
            padding: 8px;
            font-size: 14px;
        """)
        # Menghubungkan tombol Enter dengan fungsi kirim pesan
        self.input_box.returnPressed.connect(self.kirim_pesan)
        layout.addWidget(self.input_box)

        # Variabel untuk menyimpan posisi mouse saat menggeser jendela
        self.oldPos = QPoint()

    def kirim_pesan(self):
        """Fungsi ini akan dijalankan saat Anda menekan Enter di kolom input."""
        pesan = self.input_box.text()
        print(f"Anda mengetik perintah: {pesan}")
        self.input_box.clear()
        # CATATAN: Di Fase selanjutnya, pesan ini akan kita lempar ke main.py (Otak AI)

    # =======================================================
    # FITUR DRAG AND DROP (AGAR KARAKTER BISA DIGESER MOUSE)
    # =======================================================
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec())