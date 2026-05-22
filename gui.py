from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                QLabel, QPushButton, QFrame, QApplication, QCheckBox, QGridLayout, QDialog, QScrollArea, QSystemTrayIcon, QMenu, QLineEdit, QLayout, QProgressBar, QComboBox, QFileDialog)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QThread, QPropertyAnimation, QRect, QPoint, QByteArray, QEvent
from PySide6.QtGui import QColor, QPalette, QLinearGradient, QPainter, QPen, QPixmap, QImage, QAction, QConicalGradient, QBrush, QIcon, QFont
import os
import sys
import random
import string
import socket
import logic
import keyboard
import time
import math
from ui_components import HackerLabel, ScrollingLabel, FireworkParticle

import security
try:
    import win32gui
    import win32con
    import win32process
    import win32api
    HAS_WIN32 = True
except:
    HAS_WIN32 = False
    print("Warning: pywin32 not installed, window features disabled")

class TextUtilityDialog(QDialog):
    """Small sleek popup for text transformations"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cong cu van ban")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setStyleSheet("""
            QDialog { background: #020005; border: 2px solid #00ff41; color: #00ff41; }
            QLineEdit { background: #000; color: #00ff41; border: 1px solid #00ff41; padding: 5px; font-family: 'Consolas'; }
            QPushButton { background: #002200; color: #00ff41; border: 1px solid #00ff41; padding: 4px; border-radius: 3px; font-size: 10px; }
            QPushButton:hover { background: #004400; color: #00f3ff; border: 1px solid #00f3ff; }
            QLabel { color: #ff00ff; font-weight: bold; font-family: 'Consolas'; font-size: 11px; }
        """)
        
        layout = QVBoxLayout(self)
        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText("Nhap noi dung can xu ly...")
        layout.addWidget(self.input_text)
        
        btn_grid = QGridLayout()
        
        btns = [
            ("HOA/THUONG", self.toggle_case),
            ("SO LA MA", self.to_roman),
            ("SO THUONG", self.to_num),
            ("DAO CHU", self.reverse_text),
            ("XOA", self.clear_text),
            ("DONG", self.close)
        ]
        
        for i, (name, func) in enumerate(btns):
            btn = QPushButton(name)
            btn.clicked.connect(func)
            btn_grid.addWidget(btn, i // 3, i % 3)
            
        layout.addLayout(btn_grid)
        self.setFixedWidth(180)

    def toggle_case(self):
        t = self.input_text.text()
        self.input_text.setText(t.swapcase() if t else "")
        
    def reverse_text(self):
        t = self.input_text.text()
        self.input_text.setText(t[::-1] if t else "")

    def clear_text(self):
        self.input_text.clear()

    def to_roman(self):
        t = self.input_text.text()
        if t.isdigit():
            val = int(t)
            roman = {1000: 'M', 900: 'CM', 500: 'D', 400: 'CD', 100: 'C', 90: 'XC', 50: 'L', 40: 'XL', 10: 'X', 9: 'IX', 5: 'V', 4: 'IV', 1: 'I'}
            res = ""
            for v, r in roman.items():
                while val >= v:
                    res += r
                    val -= v
            self.input_text.setText(res)

    def to_num(self):
        t = self.input_text.text().upper()
        roman = {'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000}
        res = 0
        for i in range(len(t)):
            if i > 0 and roman[t[i]] > roman[t[i-1]]:
                res += roman[t[i]] - 2 * roman[t[i-1]]
            else:
                res += roman[t[i]]
        self.input_text.setText(str(res) if res > 0 else "")

class HackMenuDialog(QDialog):
    """Bảng menu phím tắt phong cách Hacker (Hack Menu)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bang phim tat")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QDialog { background: #020005; border: 2px solid #00ff41; color: #00ff41; }
            QLabel { color: #00ff41; font-family: 'Consolas'; font-size: 10px; }
            .header { color: #ff00ff; font-weight: bold; font-size: 12px; }
            .key { color: #00f3ff; font-weight: bold; }
        """)
        
        layout = QVBoxLayout(self)
        
        header = QLabel("--- [ HUONG DAN PHIM TAT ] ---")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #ff00ff; font-weight: bold; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(header)
        
        shortcuts = [
            ("INSERT", "PHIM TAT", "Bat/tat bang huong dan phim tat"),
            ("CTRL+H", "PHIM TAT", "Bat/tat bang huong dan (phim phu)"),
            ("ALT+V", "COPY PATH", "Sao chep duong dan thu muc don hien tai"),
            ("ALT+E", "MO THU MUC", "Mo nhanh thu muc dang xu ly"),
            ("ALT+C", "COPY MA", "Sao chep ma don"),
            ("ALT+B", "CHUP ANH", "Chup cua so theu"),
            ("ALT+I", "IMPORT IMG", "Tu dong dan 2.png roi 1.png vao Wilcom"),
            ("CTRL+B", "CHAY AUTO", "Chay quy trinh tu dong 3 buoc"),
            ("CTRL+SHIFT+B", "AUTO NHANH", "Chay auto nhanh bang phim phu"),
            ("CTRL+SHIFT+V", "COPY MIX", "Copy ID kem vi tri da tick"),
            ("CTRL+R", "RESET", "Dat lai du lieu hien tai"),
            ("CTRL+SPACE", "TU DONG", "Chay quy trinh 3 buoc"),
            ("CTRL+X", "DONG APP", "Tat nhanh Ultimate"),
            ("CTRL+ALT+E", "MO THU MUC", "Mo thu muc da tao (phim phu)"),
            ("CTRL+M", "XEM ANH", "Mo anh chup gan nhat"),
            ("Q", "DUNG", "Dung quy trinh khan cap")
        ]
        
        for key, func, desc in shortcuts:
            row = QHBoxLayout()
            lbl_key = QLabel(f"[{key}]")
            lbl_key.setFixedWidth(80)
            lbl_key.setStyleSheet("color: #00f3ff; font-weight: bold;")
            
            lbl_func = QLabel(f"{func}")
            lbl_func.setFixedWidth(80)
            lbl_func.setStyleSheet("color: #00ff41; font-weight: bold;")
            
            lbl_desc = QLabel(f"- {desc}")
            lbl_desc.setStyleSheet("color: #008800;")
            
            row.addWidget(lbl_key)
            row.addWidget(lbl_func)
            row.addWidget(lbl_desc)
            layout.addLayout(row)
        
        footer = QLabel("\nNhan INSERT hoac CTRL+H de dong bang huong dan")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #444; font-size: 8px;")
        layout.addWidget(footer)
        
        self.setFixedWidth(350)

class LicenseDialog(QDialog):
    """Dialog shown when access is denied"""
    def __init__(self, hwid, pc_name, reason="Machine Unauthorized", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(300, 200)
        self.setStyleSheet("""
            QDialog { background: #0c0c0e; border: 2px solid #ff4444; color: white; }
            QLabel { font-family: 'Consolas'; font-size: 10px; color: #aaa; }
            .header { color: #ff4444; font-weight: bold; font-size: 13px; }
            .hwid { color: #00ff41; font-weight: bold; font-size: 11px; background: #1a1a1a; padding: 5px; border-radius: 4px; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel("ACCESS DENIED")
        header.setProperty("class", "header")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        layout.addSpacing(10)
        
        msg = QLabel(reason)
        msg.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg)
        
        layout.addSpacing(15)
        
        lbl_info = QLabel("Please send this ID to provider:")
        layout.addWidget(lbl_info)
        
        self.lbl_hwid = QLabel(hwid)
        self.lbl_hwid.setProperty("class", "hwid")
        self.lbl_hwid.setAlignment(Qt.AlignCenter)
        self.lbl_hwid.setCursor(Qt.PointingHandCursor)
        self.lbl_hwid.mousePressEvent = lambda e: self.copy_hwid()
        layout.addWidget(self.lbl_hwid)
        
        layout.addSpacing(10)
        
        lbl_pc = QLabel(f"PC: {pc_name}")
        lbl_pc.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_pc)
        
        layout.addStretch()
        
        btn_close = QPushButton("CLOSE")
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet("background: #222; border: 1px solid #444; color: white; padding: 5px;")
        layout.addWidget(btn_close)

    def copy_hwid(self):
        QApplication.clipboard().setText(self.lbl_hwid.text())
        self.lbl_hwid.setText("COPIED!")
        QTimer.singleShot(1000, lambda: self.lbl_hwid.setText(security.get_hwid()))

class SuccessToast(QDialog):
    """Sleek auto-disappearing toast notification"""
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #051a05, stop:1 #003300);
                border: 2px solid #00ff41;
                border-radius: 8px;
            }
            QLabel {
                color: #ffffff;
                font-family: 'Segoe UI', 'Consolas', sans-serif;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        
        lbl = QLabel(message)
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)
        
        self.adjust_position()
        QTimer.singleShot(2500, self.close)
        
    def adjust_position(self):
        screen = QApplication.primaryScreen().geometry()
        self.setFixedSize(220, 42)
        x = (screen.width() - self.width()) // 2
        y = 40  # Top center of the screen
        self.move(x, y)

class InfoOverlay(QWidget):
    """Transparent overlay to show info on top of Ultimate app"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        
        common_style = """
            color: red; 
            font-family: 'Consolas', 'Courier New', monospace; 
            font-weight: bold; 
            font-size: 10px;
            background: rgba(0, 0, 0, 150);
            padding: 1px 6px;
            border-radius: 2px;
        """
        
        self.lbl_info = QLabel("TX READY")
        self.lbl_info.setStyleSheet("""
            color: #00ff41; 
            font-family: 'Consolas', 'Courier New', monospace; 
            font-weight: bold; 
            font-size: 11px;
            background: rgba(0, 5, 0, 180);
            padding: 2px 10px;
            border: 1px solid #00ff41;
            border-radius: 3px;
        """)
        self.lbl_info.setAlignment(Qt.AlignCenter)
        
        self.lbl_line1 = QLabel("TX READY")
        self.lbl_line1.setStyleSheet(common_style)
        self.lbl_line1.setAlignment(Qt.AlignCenter)
        
        self.lbl_line2 = QLabel("-")
        self.lbl_line2.setStyleSheet(common_style)
        self.lbl_line2.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.lbl_line1)
        layout.addWidget(self.lbl_line2)
        self.setFixedSize(550, 42)
        
    def update_info(self, id_val, name, size, f_type, dims):
        self.lbl_line1.setText(f"◆ MÃ: {id_val}  |  LOẠI: {f_type} ◆")
        detail = f"➤ TÊN: {name}  |  SIZE: {size}"
        if dims and dims != "-":
            detail += f"  ({dims})"
        self.lbl_line2.setText(detail)

class HelpTooltip(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.ToolTip)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QFrame {
                background: rgba(5, 10, 5, 240);
                border: 2px solid #00ff41;
                border-radius: 6px;
            }
            QLabel {
                color: #00ff41;
                font-family: 'Consolas', 'Segoe UI', monospace;
                font-size: 9px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)
        
        title = QLabel("=== BẢNG HƯỚNG DẪN ===")
        title.setStyleSheet("font-weight: bold; font-size: 10px; color: #00ff41; border-bottom: 1px solid rgba(0, 255, 65, 80); padding-bottom: 2px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        guide_text = (
            "⚡ <b>Auto Run:</b> Ctrl+Space<br>"
            "📁 <b>Thư mục:</b> Alt+E (Tạo/Mở)<br>"
            "📸 <b>Chụp ảnh:</b> Alt+B (Chụp cửa sổ thêu)<br>"
            "📋 <b>MIX:</b> Ctrl+Shift+V (Copy đ.dẫn PO)<br>"
            "↻ <b>Reset:</b> Ctrl+R (Đặt lại dữ liệu)<br>"
            "👁️ <b>HUD:</b> Click mắt để ẩn/hiện chỉ số<br>"
            "📌 <b>Ghim:</b> Ghim tool luôn nổi<br>"
            "⌨️ <b>Insert:</b> Ẩn/Hiện tool (khay hệ thống)<br>"
            "❌ <b>Ctrl+Alt+X:</b> Tắt khẩn cấp công cụ"
        )
        
        content = QLabel(guide_text)
        layout.addWidget(content)
        self.setFixedSize(220, 160)

class HelpButton(QPushButton):
    def __init__(self, parent_app, parent=None):
        super().__init__("❓", parent)
        self.parent_app = parent_app
        self.setFixedSize(12, 12)
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #00ff41;
                border: none;
                font-size: 8px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover { color: #ffffff; }
        """)
        self.tooltip = None
        
    def enterEvent(self, event):
        if not self.tooltip:
            self.tooltip = HelpTooltip(self.parent_app)
        # Position to the left of the button
        pos = self.mapToGlobal(QPoint(-225, -50))
        self.tooltip.move(pos)
        self.tooltip.show()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        if self.tooltip:
            self.tooltip.hide()
            self.tooltip.deleteLater()
            self.tooltip = None
        super().leaveEvent(event)

class SpinningDisc(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(50)
        self.is_playing = False
        
    def rotate(self):
        if self.is_playing:
            self.angle = (self.angle + 8) % 360
            self.update()
            
    def set_playing(self, playing):
        self.is_playing = playing
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        
        painter.translate(rect.center())
        painter.rotate(self.angle)
        
        # Draw vinyl background
        painter.setPen(QPen(QColor(0, 255, 65, 100), 1))
        painter.setBrush(QBrush(QColor(15, 15, 20)))
        painter.drawEllipse(-9, -9, 18, 18)
        
        # Draw groove
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(0, 255, 65, 40), 1))
        painter.drawEllipse(-6, -6, 12, 12)
        
        # Draw center label
        painter.setBrush(QBrush(QColor(0, 255, 65)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(-2, -2, 4, 4)
        
        painter.end()

class MusicVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 16)
        self.bars = [2, 2, 2, 2, 2]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(100)
        self.is_playing = False
        
    def animate(self):
        if self.is_playing:
            self.bars = [random.randint(2, 14) for _ in range(5)]
        else:
            self.bars = [2] * 5
        self.update()
        
    def set_playing(self, playing):
        self.is_playing = playing
        if not playing:
            self.bars = [2] * 5
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        num_bars = len(self.bars)
        bar_width = 4
        spacing = 2
        
        total_width = num_bars * bar_width + (num_bars - 1) * spacing
        start_x = (width - total_width) // 2
        
        for i in range(num_bars):
            x = start_x + i * (bar_width + spacing)
            bar_height = self.bars[i]
            y = height - bar_height
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(0, 255, 65)))
            painter.drawRoundedRect(x, y, bar_width, bar_height, 1, 1)
            
        painter.end()


try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PySide6.QtCore import QUrl
    HAS_MULTIMEDIA = True
except Exception as e:
    HAS_MULTIMEDIA = False
    print(f"QtMultimedia not available: {e}")


class YoutubeUrlExtractor(QThread):
    finished_url = Signal(str, str)  # (stream_url, title)
    error = Signal(str)

    def __init__(self, youtube_url):
        super().__init__()
        self.youtube_url = youtube_url

    def run(self):
        try:
            import yt_dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.youtube_url, download=False)
                stream_url = info.get('url')
                title = info.get('title', 'YouTube Video')
                if stream_url:
                    self.finished_url.emit(stream_url, title)
                else:
                    self.error.emit("No audio url found")
        except Exception as e:
            self.error.emit(str(e))


class MusicPlayerWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            MusicPlayerWidget {
                background: rgba(10, 10, 15, 180);
                border: 1px solid rgba(0, 255, 65, 80);
                border-radius: 6px;
            }
        """)
        self.setFixedHeight(30)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(5)
        
        # 1. Spinning Disc
        self.disc = SpinningDisc(self)
        layout.addWidget(self.disc)
        
        # 2. Controls: Play & Next
        control_lay = QHBoxLayout()
        control_lay.setSpacing(4)
        
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedSize(16, 16)
        self.btn_play.setStyleSheet("""
            QPushButton {
                background: #020502;
                border: 1px solid #00ff41;
                border-radius: 8px;
                color: #00ff41;
                font-size: 8px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover { background: #002200; }
        """)
        self.btn_play.clicked.connect(self.toggle_play)
        control_lay.addWidget(self.btn_play)
        
        self.btn_next = QPushButton("⏭")
        self.btn_next.setFixedSize(16, 16)
        self.btn_next.setStyleSheet("""
            QPushButton {
                background: #020502;
                border: 1px solid #00ff41;
                border-radius: 8px;
                color: #00ff41;
                font-size: 8px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover { background: #002200; }
        """)
        self.btn_next.clicked.connect(self.play_next)
        control_lay.addWidget(self.btn_next)
        
        layout.addLayout(control_lay)
        
        # Song label
        self.lbl_song = QLabel("Synth Lofi")
        self.lbl_song.setStyleSheet("color: #00ff41; font-size: 8px; font-weight: bold; font-family: 'Consolas';")
        self.lbl_song.setFixedWidth(120)
        self.lbl_song.setToolTip("Tên bài hát")
        layout.addWidget(self.lbl_song)
        
        # 3. Visualizer
        self.visualizer = MusicVisualizer(self)
        layout.addWidget(self.visualizer)
        
        self.is_playing = False
        self.playlist = []
        self.current_index = -1
        self.extractor = None
        
        if HAS_MULTIMEDIA:
            self.player = QMediaPlayer(self)
            self.audio_output = QAudioOutput(self)
            self.player.setAudioOutput(self.audio_output)
            self.audio_output.setVolume(0.3)
            self.player.mediaStatusChanged.connect(self._status_changed)
        else:
            self.player = None

        # Load playlist immediately
        self.reload_playlist()
        
    def reload_playlist(self):
        self.playlist = []
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        music_dir = os.path.join(app_dir, "Music")
        if not os.path.exists(music_dir):
            os.makedirs(music_dir)
            # Create default youtube_links.txt template
            txt_path = os.path.join(music_dir, "youtube_links.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("# Dán link nhạc Youtube tại đây (mỗi dòng 1 link)\n")
                f.write("https://www.youtube.com/watch?v=dQw4w9WgXcQ\n")
        
        import glob
        # Scan local files
        for ext in ("*.mp3", "*.wav", "*.m4a"):
            for fpath in glob.glob(os.path.join(music_dir, ext)):
                self.playlist.append({"type": "local", "path": fpath, "title": os.path.basename(fpath)})
        
        # Scan YouTube links
        txt_path = os.path.join(music_dir, "youtube_links.txt")
        if os.path.exists(txt_path):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            self.playlist.append({"type": "youtube", "path": line, "title": "Youtube Link"})
            except Exception as e:
                print(f"Error loading youtube links: {e}")

        # If playlist is empty, add a default fallback local / remote stream
        if not self.playlist:
            self.playlist.append({
                "type": "remote", 
                "path": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", 
                "title": "Synth Lofi"
            })
            
    def toggle_play(self):
        if not self.playlist:
            self.reload_playlist()
            
        if self.current_index == -1 and self.playlist:
            self.current_index = 0
            self._load_current_track()
            self.is_playing = True
        else:
            self.is_playing = not self.is_playing
            
        self.disc.set_playing(self.is_playing)
        self.visualizer.set_playing(self.is_playing)
        
        if self.is_playing:
            self.btn_play.setText("⏸")
            if self.player:
                self.player.play()
        else:
            self.btn_play.setText("▶")
            if self.player:
                self.player.pause()

    def play_next(self):
        if not self.playlist:
            self.reload_playlist()
        if not self.playlist:
            return
            
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self._load_current_track()
        
        self.is_playing = True
        self.disc.set_playing(True)
        self.visualizer.set_playing(True)
        self.btn_play.setText("⏸")

    def _load_current_track(self):
        if not self.player:
            return
            
        self.player.stop()
        if self.extractor:
            self.extractor.terminate()
            self.extractor = None
            
        track = self.playlist[self.current_index]
        self.lbl_song.setText(track["title"][:20])
        self.lbl_song.setToolTip(track["title"])
        
        if track["type"] == "local":
            self.player.setSource(QUrl.fromLocalFile(track["path"]))
            self.player.play()
        elif track["type"] == "remote":
            self.player.setSource(QUrl(track["path"]))
            self.player.play()
        elif track["type"] == "youtube":
            self.lbl_song.setText("⏳ Loading Youtube...")
            self.extractor = YoutubeUrlExtractor(track["path"])
            self.extractor.finished_url.connect(self._play_youtube_stream)
            self.extractor.error.connect(self._handle_extractor_error)
            self.extractor.start()
            
    def _play_youtube_stream(self, stream_url, title):
        if self.player:
            self.lbl_song.setText(title[:20])
            self.lbl_song.setToolTip(title)
            # Update title in our playlist cache
            self.playlist[self.current_index]["title"] = title
            self.player.setSource(QUrl(stream_url))
            if self.is_playing:
                self.player.play()
                
    def _handle_extractor_error(self, err):
        self.lbl_song.setText("❌ Error loading YT")
        QTimer.singleShot(2500, self.play_next)
        
    def _status_changed(self, status):
        try:
            from PySide6.QtMultimedia import QMediaPlayer
            if status == QMediaPlayer.EndOfMedia:
                self.play_next()
        except:
            pass

class MiniApp(QMainWindow):
    # Define Signal for Thread-Safe Updates
    update_status_signal = Signal(str, str)
    status_signal = Signal(str, str) 
    progress_signal = Signal(int)
    show_success_toast_signal = Signal(str)
    hotkey_triggered_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(165, 222)
        
        self.current_data = {}
        self.current_folder = None
        self._drag_pos = None
        self.last_copied = ""  # Store for screenshot naming
        self.last_screenshot_path = None # Track for Ctrl+M preview
        self.last_detected_export_hwnd = None
        
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        self._config_path = os.path.join(app_dir, 'tx_config.json')
        self._save_folder = self._load_save_folder()
        
        # Folder button click tracking for double-click detection
        self._folder_clicks = 0
        self._folder_click_timer = QTimer()
        self._folder_click_timer.setSingleShot(True)
        self._folder_click_timer.timeout.connect(self._handle_folder_single_click)
        
        # State flags
        self.is_expanded = True
        self.is_pinned = True
        self.auto_trigger_enabled = False  # Auto-trigger when data arrives (DEFAULT OFF)
        
        # Docking state
        self.is_docked = False
        self.target_window_hwnd = None
        self.dock_offset_x = -170  # X offset from target window (negative = left of right edge)
        self.dock_offset_y = 10    # Y offset from target window top
        self.dock_search_attempts = 0  # Counter for reconnection attempts
        
        # Checkbox references
        self.chk_groups = {} 
        
        # Fireworks
        self.fireworks = []
        
        # RGB Border Animation
        self.border_hue = 0
        self.border_angle = 0  
        self.border_timer = QTimer()
        self.border_timer.timeout.connect(self.update_border)
        self.border_timer.start(30)  # Update every 30ms for smooth animation

        # Docking timer
        self.dock_timer = QTimer()
        self.dock_timer.timeout.connect(self.update_dock_position)
        
        # FPS Counter State
        self.fps_start_time = time.time()
        self.fps_frame_count = 0
        self.current_fps = 0
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps)
        self.fps_timer.start(1000) # Update FPS label every second
        
        # Screenshot Timer (for single/double click detection)
        self.screenshot_clicks = 0
        self.screenshot_timer = QTimer()
        self.screenshot_timer.setSingleShot(True)
        self.screenshot_timer.timeout.connect(self.handle_screenshot_single)
        
        self.setup_ui()
        self.setup_tray_icon()
        self.setup_hotkeys()

        # Server status polling (green/red indicator button)
        self.server_status_timer = QTimer(self)
        self.server_status_timer.timeout.connect(self._cap_nhat_nut_server)
        self.server_status_timer.start(1500)
        self._cap_nhat_nut_server()
        
        # Info Overlay Setup
        self.overlay_enabled = True
        self.info_overlay = InfoOverlay()
        if self.is_pinned:
             self.info_overlay.show()
        
        self.overlay_timer = QTimer()
        self.overlay_timer.timeout.connect(self.update_overlay_position)
        self.overlay_timer.start(50) # Very fast sync for "glued" feel
        
        # Connect Signal to Slot
        self.update_status_signal.connect(self._flash_status_safe)
        self.status_signal.connect(self._update_status_strip)
        self.progress_signal.connect(self.set_progress)
        self.show_success_toast_signal.connect(self.show_success_toast)
        self.hotkey_triggered_signal.connect(self._handle_hotkey_on_main_thread)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    
    def update_fps(self):
        """Calculate FPS for the hack-menu feel"""
        now = time.time()
        dt = now - self.fps_start_time
        if dt > 0:
            self.current_fps = int(self.fps_frame_count / dt)
            if hasattr(self, 'lbl_fps'):
                # Simulate high-fps "flicker" common in hack menus
                flicker = random.randint(-2, 2)
                self.lbl_fps.setText(f"FPS: {self.current_fps + flicker}")
        
        self.fps_start_time = now
        self.fps_frame_count = 0

    @Slot(int)
    def set_progress(self, value):
        if hasattr(self, 'prog_bar'):
            self.prog_bar.setValue(value)
            self.prog_bar.setVisible(value > 0 and value <= 100)
            self.prog_bar.repaint()  # Force immediate UI redraw
            if value >= 100:
                self.lbl_status_strip.setText("Hoan tat")
                QTimer.singleShot(3000, lambda: self.prog_bar.setVisible(False))

    @Slot(str, str)
    def _update_status_strip(self, text, color="#f6de95"):
        if hasattr(self, 'lbl_status_strip'):
            self.lbl_status_strip.setText(text)
            self.lbl_status_strip.setStyleSheet(f"color: {color}; font-size: 9px; font-weight: 700;")

    def update_border(self):
        """Update RGB border color and rotation + Fireworks + Frame Counter"""
        self.fps_frame_count += 1
        self.border_hue = (self.border_hue + 3) % 360
        self.border_angle = (self.border_angle + 2) % 360  # Rotation angle
        
        # Spawn Fireworks (Low chance)
        if random.random() < 0.05: 
             cx = random.randint(20, 140)
             cy = random.randint(20, 140)
             color = QColor.fromHsv(random.randint(0, 360), 255, 255)
             for _ in range(15): # Particles
                 self.fireworks.append(FireworkParticle(cx, cy, color))
                 
        # Update Fireworks
        self.fireworks = [p for p in self.fireworks if p.update()]
        
        self.update()  # Trigger repaint
    
    def paintEvent(self, event):
        """Custom paint for black-glass overlay panel with rotating rainbow border"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        panel_rect = rect.adjusted(3, 3, -3, -3)

        gradient = QLinearGradient(0, 0, 0, rect.height())
        gradient.setColorAt(0.0, QColor(8, 8, 12, 245))
        gradient.setColorAt(1.0, QColor(4, 4, 6, 250))
        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
        painter.drawRoundedRect(panel_rect, 10, 10)

        # Paint purple grid background
        painter.setPen(QPen(QColor(80, 20, 100, 35), 1, Qt.DashLine))
        grid_size = 12
        for x in range(panel_rect.left(), panel_rect.right(), grid_size):
            painter.drawLine(x, panel_rect.top(), x, panel_rect.bottom())
        for y in range(panel_rect.top(), panel_rect.bottom(), grid_size):
            painter.drawLine(panel_rect.left(), y, panel_rect.right(), y)

        # Paint rotating rainbow border
        conical = QConicalGradient(panel_rect.center().x(), panel_rect.center().y(), self.border_angle)
        for i in range(13):
            hue = (self.border_hue + i * 30) % 360
            conical.setColorAt(i / 12.0, QColor.fromHsv(hue, 255, 255))
        
        pen_border = QPen(QBrush(conical), 3)
        painter.setPen(pen_border)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(panel_rect, 10, 10)

        # Keep subtle particle effects
        painter.setPen(Qt.NoPen)
        for p in self.fireworks:
            alpha = int(p.life * 255)
            color = p.color
            color.setAlpha(alpha)
            painter.setBrush(color)
            painter.drawEllipse(p.x, p.y, 2, 2)
            
        painter.end()

    def setup_ui(self):
        self.container = QWidget()
        self.container.setObjectName("Container")
        self.container.setStyleSheet("""
            #Container {
                background-color: rgba(8, 8, 10, 230);
                border: none;
                border-radius: 8px;
            }
            QLabel {
                color: #ffffff;
                font-family: 'Consolas', 'Segoe UI', sans-serif;
                font-size: 9px;
                background: transparent;
            }
        """)
        self.setCentralWidget(self.container)

        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2)

        # 1. Title Bar
        title_bar = QHBoxLayout()
        title_bar.setSpacing(1)
        
        self.lbl_chu_chay = ScrollingLabel("AI LÀ VUA LÌ ĐÒN ⚡ BEYOND ALL BORDERS ⚡")
        self.lbl_chu_chay.setStyleSheet("color: #00ff41; font-family: 'Consolas'; font-weight: bold; font-size: 8px; background: transparent;")
        self.lbl_chu_chay.setFixedHeight(12)
        title_bar.addWidget(self.lbl_chu_chay, 1)

        self.btn_dock_title = QPushButton("🔗")
        self.btn_dock_title.setFixedSize(12, 12)
        self.btn_dock_title.setStyleSheet("background: transparent; color: #777; font-size: 8px; font-weight: bold; border: none; padding: 0;")
        self.btn_dock_title.clicked.connect(self.on_toggle_dock)
        self.btn_dock_title.setToolTip("Dock to Ultimate Window")
        title_bar.addWidget(self.btn_dock_title)

        self.btn_overlay_title = QPushButton("👁️")
        self.btn_overlay_title.setFixedSize(12, 12)
        self.btn_overlay_title.setStyleSheet("background: transparent; color: #00ff41; font-size: 8px; font-weight: bold; border: none; padding: 0;")
        self.btn_overlay_title.clicked.connect(self.on_toggle_overlay)
        self.btn_overlay_title.setToolTip("Toggle HUD Overlay")
        title_bar.addWidget(self.btn_overlay_title)

        self.btn_pin_title = QPushButton("📌")
        self.btn_pin_title.setFixedSize(12, 12)
        self.btn_pin_title.setStyleSheet("background: transparent; color: #ff3333; font-size: 8px; font-weight: bold; border: none; padding: 0;")
        self.btn_pin_title.clicked.connect(self.on_toggle_pin)
        self.btn_pin_title.setToolTip("Toggle Always on Top")
        title_bar.addWidget(self.btn_pin_title)

        self.btn_min = QPushButton("-")
        self.btn_min.setFixedSize(12, 12)
        self.btn_min.setStyleSheet("background: transparent; color: #00ff41; font-size: 10px; font-weight: bold; border: none; padding: 0;")
        self.btn_min.clicked.connect(self.on_minimize_to_tray)
        self.btn_min.setToolTip("Minimize to Tray")
        title_bar.addWidget(self.btn_min)

        self.btn_close = QPushButton("X")
        self.btn_close.setFixedSize(12, 12)
        self.btn_close.setStyleSheet("background: transparent; color: #00ff41; font-size: 8px; font-weight: bold; border: none; padding: 0;")
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setToolTip("Close App")
        title_bar.addWidget(self.btn_close)

        # Help Button
        self.btn_help = HelpButton(self)
        title_bar.addWidget(self.btn_help)

        self.lbl_server_status = QLabel()
        self.lbl_server_status.setFixedSize(8, 8)
        self.lbl_server_status.setStyleSheet("background-color: #ff3333; border-radius: 4px;")
        self.lbl_server_status.setToolTip("Server Connection Status")
        title_bar.addWidget(self.lbl_server_status)

        main_layout.addLayout(title_bar)

        # 2. Order ID
        self.lbl_id = ScrollingLabel("WAITING DATA...")
        self.lbl_id.setStyleSheet("color: #ffffff; font-family: 'Consolas', 'Segoe UI'; font-weight: bold; font-size: 13px; background: transparent;")
        self.lbl_id.setFixedHeight(18)
        main_layout.addWidget(self.lbl_id)

        # 3. Product / Mode
        self.btn_mode = QPushButton("WAITING...")
        self.btn_mode.setStyleSheet("background: transparent; border: none; color: #00f3ff; font-family: 'Segoe UI', 'Bahnschrift'; font-size: 9px; font-weight: bold; text-align: left; padding: 0;")
        self.btn_mode.setFixedHeight(14)
        self.btn_mode.clicked.connect(lambda: self.copy_data("mode"))
        main_layout.addWidget(self.btn_mode)

        # 4. Badge (DST | Size)
        self.btn_badge = QPushButton("DST | 2x2 inches")
        self.btn_badge.setFixedHeight(20)
        self.btn_badge.setStyleSheet("""
            background: #440000;
            color: #ff003c;
            border: 1px solid #ff003c;
            border-radius: 6px;
            font-weight: bold;
            font-size: 10px;
            padding: 2px;
        """)
        self.btn_badge.clicked.connect(lambda: self.copy_data("badge"))
        main_layout.addWidget(self.btn_badge)

        # 5. Position Indicators (Dynamic Layout)
        self.positions_container = QWidget()
        self.positions_container.setFixedHeight(18)
        self.positions_layout = QHBoxLayout(self.positions_container)
        self.positions_layout.setContentsMargins(0, 0, 0, 0)
        self.positions_layout.setSpacing(4)

        # Create QCheckBoxes and add to horizontal layout
        self.chk_groups = {}
        self.all_keys = [
            '1','3','4','5','6','8','9','V','T',
            'I','O','P','B','G','H','S','E','C','D','F','L','R'
        ]

        checkbox_style = """
            QCheckBox {
                color: #00f3ff;
                font-family: 'Consolas';
                font-size: 9px;
                font-weight: bold;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 8px;
                height: 8px;
                border: 1px solid #00f3ff;
                background: transparent;
            }
            QCheckBox::indicator:checked {
                background: #00f3ff;
            }
        """

        for k in self.all_keys:
            chk = QCheckBox(k)
            chk.setStyleSheet(checkbox_style)
            chk.setVisible(False)
            chk.clicked.connect(lambda checked, key=k: self.on_checkbox_clicked(key))
            self.chk_groups[k] = chk
            self.positions_layout.addWidget(chk)

        self.positions_layout.addStretch()
        main_layout.addWidget(self.positions_container)

        # 6. Alt Text tips
        self.lbl_alt_tips = QLabel("C:ID | V:Folder | S:Shot")
        self.lbl_alt_tips.setStyleSheet("color: #00ff41; font-family: 'Consolas'; font-size: 8px; font-weight: bold; background: transparent;")
        self.lbl_alt_tips.setFixedHeight(10)
        main_layout.addWidget(self.lbl_alt_tips)

        # Real Neon Progress Bar
        self.prog_bar = QProgressBar()
        self.prog_bar.setFixedHeight(12)  # Increased from 8 to 12 for text readability
        self.prog_bar.setTextVisible(True)
        self.prog_bar.setAlignment(Qt.AlignCenter)
        self.prog_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #00ff41;
                border-radius: 3px;
                background: #020502;
                color: #ffffff; /* White text for contrast on both dark background and green chunk */
                font-family: 'Consolas', sans-serif;
                font-size: 9px;
                font-weight: bold;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #00ff41;
            }
        """)
        self.prog_bar.setVisible(False)
        main_layout.addWidget(self.prog_bar)

        # 7. Button Grid (4x2)
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(3)
        grid.setContentsMargins(0, 0, 0, 0)

        # Auto Button
        self.btn_auto = QPushButton("⚡")
        self.btn_auto.setFixedSize(36, 28)
        self.btn_auto.setStyleSheet("QPushButton { background: #020502; border: 1px solid #00ff41; border-radius: 4px; color: #ff9900; font-size: 14px; font-weight: bold; } QPushButton:hover { background: #002200; }")
        self.btn_auto.clicked.connect(self.on_auto_click)
        self.btn_auto.setToolTip("Auto run (Ctrl+Space)")

        # Folder Button
        self.btn_folder = QPushButton("📁")
        self.btn_folder.setFixedSize(36, 28)
        self.btn_folder.setStyleSheet("QPushButton { background: #020502; border: 1px solid #00ff41; border-radius: 4px; color: #ffcc00; font-size: 12px; font-weight: bold; } QPushButton:hover { background: #002200; }")
        self.btn_folder.clicked.connect(self.on_create_folder)
        self.btn_folder.setToolTip("Open folder (Alt+E)")

        # Screenshot Button
        self.btn_ss = QPushButton("📸")
        self.btn_ss.setFixedSize(36, 28)
        self.btn_ss.setStyleSheet("QPushButton { background: #020502; border: 1px solid #00ff41; border-radius: 4px; color: #cc66ff; font-size: 12px; font-weight: bold; } QPushButton:hover { background: #002200; }")
        self.btn_ss.clicked.connect(self.on_screenshot_click)
        self.btn_ss.setToolTip("Take screenshot (Alt+B)")

        # Copy Mix Button
        self.btn_mix = QPushButton("📋\nMIX")
        self.btn_mix.setFixedSize(36, 28)
        self.btn_mix.setStyleSheet("QPushButton { background: #020502; border: 1px solid #d4af37; border-radius: 4px; color: #d4af37; font-size: 8px; font-weight: bold; text-align: center; } QPushButton:hover { background: #1a1a00; }")
        self.btn_mix.clicked.connect(lambda: self.copy_data("mix"))
        self.btn_mix.setToolTip("Copy đường dẫn PO (Ctrl+Shift+V)")

        # Reset Button (compact)
        self.btn_reset = QPushButton("↻")
        self.btn_reset.setFixedSize(24, 24)
        self.btn_reset.setStyleSheet("QPushButton { background: #020502; border: 1px solid #00ff41; border-radius: 4px; color: #ff6600; font-size: 13px; font-weight: bold; } QPushButton:hover { background: #002200; }")
        self.btn_reset.clicked.connect(self.on_reset)
        self.btn_reset.setToolTip("Reset data (Ctrl+R)")

        # Combobox for launching tools (compact)
        self.cb_tools = QComboBox()
        self.cb_tools.setFixedSize(70, 24)
        self.cb_tools.setStyleSheet("""
            QComboBox {
                background: #020502;
                border: 1px solid #00ff41;
                border-radius: 4px;
                color: #00ff41;
                font-family: 'Segoe UI', 'Consolas', sans-serif;
                font-size: 7px;
                font-weight: bold;
                padding: 1px 12px 1px 4px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 10px;
                border-left: 1px solid #00ff41;
            }
            QComboBox::down-arrow {
                image: none;
                border: 2px solid transparent;
                border-top-color: #00ff41;
                margin-top: 2px;
            }
            QComboBox QAbstractItemView {
                background: #020502;
                border: 1px solid #00ff41;
                color: #00ff41;
                selection-background-color: #00ff41;
                selection-color: #020502;
                font-size: 8px;
            }
        """)
        self.cb_tools.addItems(["Chọn Tool...", "In (PS Auto)", "Thêu (PatchPrint)", "🎲 Game Tài Xỉu"])

        # Run button next to combobox
        self.btn_run_tool = QPushButton("▶")
        self.btn_run_tool.setFixedSize(20, 24)
        self.btn_run_tool.setStyleSheet("QPushButton { background: #020502; border: 1px solid #00ff41; border-radius: 4px; color: #00ff41; font-size: 10px; font-weight: bold; } QPushButton:hover { background: #003300; color: #ffffff; }")
        self.btn_run_tool.clicked.connect(self.on_run_tool)
        self.btn_run_tool.setToolTip("Chạy tool đã chọn")

        # QHBoxLayout for the bottom row
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(2)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.addWidget(self.btn_reset)
        row2_layout.addWidget(self.cb_tools)
        row2_layout.addWidget(self.btn_run_tool)
        
        # Paste 2 images into Wilcom Button
        self.btn_paste_wilcom = QPushButton("📥")
        self.btn_paste_wilcom.setFixedSize(24, 24)
        self.btn_paste_wilcom.setStyleSheet("QPushButton { background: #020502; border: 1px solid #00ff41; border-radius: 4px; color: #00e5ff; font-size: 11px; font-weight: bold; } QPushButton:hover { background: #002233; color: #ffffff; }")
        self.btn_paste_wilcom.clicked.connect(self.on_paste_wilcom_clicked)
        self.btn_paste_wilcom.setToolTip("Auto dán 2 ảnh (2.png -> 1.png) vào Wilcom (Alt+I)")
        row2_layout.addWidget(self.btn_paste_wilcom)
        row2_layout.addStretch()
        
        row2_widget = QWidget()
        row2_widget.setLayout(row2_layout)

        # Add to grid
        grid.addWidget(self.btn_auto, 0, 0)
        grid.addWidget(self.btn_folder, 0, 1)
        grid.addWidget(self.btn_ss, 0, 2)
        grid.addWidget(self.btn_mix, 0, 3)
        grid.addWidget(row2_widget, 1, 0, 1, 4)

        main_layout.addWidget(grid_widget)

        # 8. Music Player
        self.music_player = MusicPlayerWidget(self)
        main_layout.addWidget(self.music_player)

        # Create dummy references so existing functions don't fail
        self.lbl_fps = QLabel()
        self.lbl_status_strip = QLabel()
        self.lbl_goi_y = QLabel()

        # Update hover helps
        self._dang_ky_goi_y_hover(
            self.btn_min,
            self.btn_close,
            self.btn_auto,
            self.btn_folder,
            self.btn_ss,
            self.btn_mix,
        )

        self.setup_hotkeys()

    def _dang_ky_goi_y_hover(self, *widgets):
        for widget in widgets:
            if widget:
                widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        if hasattr(self, "lbl_goi_y") and isinstance(watched, QPushButton):
            if event.type() == QEvent.Enter:
                tip = watched.toolTip().strip()
                if tip:
                    self.lbl_goi_y.setText(f"Goi y: {tip}")
            elif event.type() == QEvent.Leave:
                self.lbl_goi_y.setText("Re chuot vao nut de xem chuc nang")
        return super().eventFilter(watched, event)

    def _server_dang_ket_noi(self):
        """Quick TCP probe to Flask server port."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.35)
        try:
            s.connect(("127.0.0.1", 5000))
            return True
        except OSError:
            return False
        finally:
            try:
                s.close()
            except OSError:
                pass

    def _cap_nhat_nut_server(self):
        if not hasattr(self, "lbl_server_status"):
            return

        self.lbl_server_status.setStyleSheet("background-color: #ffff00; border-radius: 4px;")
        QApplication.processEvents()

        if self._server_dang_ket_noi():
            self.lbl_server_status.setStyleSheet("background-color: #00ff41; border-radius: 4px;")
        else:
            self.lbl_server_status.setStyleSheet("background-color: #ff3333; border-radius: 4px;")

    def toggle_section(self, container, header_btn):
        is_visible = container.isVisible()
        container.setVisible(not is_visible)
        text = header_btn.text().strip()
        if text.startswith((">", "▼", "∨")):
            text = text[1:].strip()

        if is_visible:
            header_btn.setText(f"> {text}")
        else:
            header_btn.setText(f"▼ {text}")
        
        # Adjust window height based on content
        QTimer.singleShot(10, self.adjust_window_size)

    def adjust_window_size(self):
        pass
    
    def setup_tray_icon(self):
        """Setup system tray icon for minimize to tray"""
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create icon from emoji/text
        icon_pixmap = QPixmap(64, 64)
        icon_pixmap.fill(Qt.transparent)
        
        painter = QPainter(icon_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background circle
        painter.setBrush(QColor("#080018"))  # Dark purple
        painter.setPen(QPen(QColor("#00ff41"), 3))  # Neon green border
        painter.drawEllipse(4, 4, 56, 56)
        
        # Draw "TX" text
        painter.setPen(QColor("#00ff41"))
        font = QFont("Consolas", 24, QFont.Bold)
        painter.setFont(font)
        painter.drawText(icon_pixmap.rect(), Qt.AlignCenter, "TX")
        
        painter.end()
        
        self.tray_icon.setIcon(QIcon(icon_pixmap))
        self.tray_icon.setToolTip("Bang dieu khien theu TX")
        
        # Create context menu
        tray_menu = QMenu()
        
        show_action = QAction("Hien cua so", self)
        show_action.triggered.connect(self.show_from_tray)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("Thoat", self)
        exit_action.triggered.connect(self.close)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # Double-click to restore
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        # Show tray icon immediately and keep it visible
        self.tray_icon.show()
    
    def on_tray_icon_activated(self, reason):
        """Handle tray icon activation (click/double-click)"""
        if reason == QSystemTrayIcon.DoubleClick or reason == QSystemTrayIcon.Trigger:
            self.show_from_tray()
    
    def show_from_tray(self):
        """Show window from system tray"""
        self.showNormal()
        self.activateWindow()
        self.raise_()
    
    def on_minimize_to_tray(self):
        """Minimize window to system tray"""
        self.hide()
        
    def on_instance_requested(self):
        """Called when a new instance is started"""
        self.on_reset() # Reset all data
        self.show_from_tray() # Show and activate window
        self.flash_status("INST RESET", "#00ffff")

    def changeEvent(self, event):
        """Handle window state changes (minimize, etc.)"""
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized():
                # If minimized via OS taskbar button
                self.on_minimize_to_tray()
                return
        super().changeEvent(event)

    def _handle_hotkey_on_main_thread(self, action):
        try:
            if action == 'alt+v':
                self.hotkey_copy_path()
            elif action == 'alt+e':
                self.hotkey_open_folder()
            elif action == 'alt+c':
                self.hotkey_copy_name()
            elif action == 'alt+b':
                self.on_screenshot_v4()
            elif action == 'ctrl+b':
                self.hotkey_run_auto()
            elif action == 'ctrl+shift+b':
                self.hotkey_run_auto_fast()
            elif action == 'ctrl+shift+v':
                self.hotkey_copy_mix()
            elif action == 'ctrl+r':
                self.hotkey_reset_data()
            elif action == 'ctrl+space':
                self.on_auto_click()
            elif action == 'ctrl+x':
                self.on_close_ultimate_app()
            elif action == 'ctrl+alt+e':
                self.hotkey_open_folder()
            elif action == 'ctrl+m':
                self.hotkey_open_last_screenshot()
            elif action == 'ctrl+alt+x':
                self.exit_all_apps()
            elif action == 'ctrl+h':
                self.hotkey_show_hack_menu()
            elif action == 'ctrl+q':
                self.emergency_stop()
            elif action == 'insert':
                self.hotkey_toggle_visibility()
            elif action == 'alt+i':
                self.on_paste_wilcom_clicked()
        except Exception as e:
            print(f"Error handling hotkey {action} on main thread: {e}")

    def safe_trigger_event(self, event):
        """Handle key event safely on main thread and filter out keypad 0"""
        if event.name == 'insert' and not event.is_keypad:
            self.hotkey_triggered_signal.emit('insert')

    def setup_hotkeys(self):
        """Setup global hotkeys for the application"""
        # Prevent duplicate registration
        if hasattr(self, '_hotkeys_registered'):
            print("Hotkeys already registered, skipping...")
            return
            
        try:
            keyboard.add_hotkey('alt+v', lambda: self.hotkey_triggered_signal.emit('alt+v'))
            keyboard.add_hotkey('alt+e', lambda: self.hotkey_triggered_signal.emit('alt+e'))
            keyboard.add_hotkey('alt+c', lambda: self.hotkey_triggered_signal.emit('alt+c'))
            keyboard.add_hotkey('alt+b', lambda: self.hotkey_triggered_signal.emit('alt+b'))
            keyboard.add_hotkey('ctrl+b', lambda: self.hotkey_triggered_signal.emit('ctrl+b'))
            keyboard.add_hotkey('ctrl+shift+b', lambda: self.hotkey_triggered_signal.emit('ctrl+shift+b'))
            keyboard.add_hotkey('ctrl+shift+v', lambda: self.hotkey_triggered_signal.emit('ctrl+shift+v'))
            keyboard.add_hotkey('ctrl+r', lambda: self.hotkey_triggered_signal.emit('ctrl+r'))
            keyboard.add_hotkey('ctrl+space', lambda: self.hotkey_triggered_signal.emit('ctrl+space'))
            keyboard.add_hotkey('ctrl+x', lambda: self.hotkey_triggered_signal.emit('ctrl+x'))
            keyboard.add_hotkey('ctrl+alt+e', lambda: self.hotkey_triggered_signal.emit('ctrl+alt+e'))
            keyboard.add_hotkey('ctrl+m', lambda: self.hotkey_triggered_signal.emit('ctrl+m'))
            keyboard.add_hotkey('ctrl+alt+x', lambda: self.hotkey_triggered_signal.emit('ctrl+alt+x'))
            keyboard.add_hotkey('ctrl+h', lambda: self.hotkey_triggered_signal.emit('ctrl+h'))
            keyboard.add_hotkey('ctrl+q', lambda: self.hotkey_triggered_signal.emit('ctrl+q'))
            keyboard.add_hotkey('alt+i', lambda: self.hotkey_triggered_signal.emit('alt+i'))
            
            # Use on_press_key for 'insert' key to hook events with event argument to filter out Numpad 0
            keyboard.on_press_key('insert', self.safe_trigger_event)
            
            self._hotkeys_registered = True
            print("Hotkeys registered safely with main-thread marshalling. Insert key NumPad 0 filter active.")
        except Exception as e:
            print(f"Hotkey registration error: {e}")

    def emergency_stop(self):
        """Emergency stop of automated workflow (Ctrl+Q)"""
        if hasattr(self, 'current_workflow') and self.current_workflow:
            self.current_workflow.abort_flag = True
        self.flash_status("STOPPED", "#ff3333")
        print("[GUI] Emergency stop triggered via Ctrl+Q")

    def _ensure_current_folder_for_hotkey(self):
        """Ensure current order folder exists for hotkey actions."""
        if self.current_folder and os.path.exists(self.current_folder):
            return self.current_folder

        oid = self.current_data.get('order_id', 'Unknown')
        if not oid or oid == 'Unknown':
            return None

        path, _ = logic.create_order_folder(self._save_folder, oid)
        if path:
            self.current_folder = path
            self.btn_folder.setStyleSheet("QPushButton { background: #153126; border: 1px solid #00ff41; border-radius: 4px; color: #00ff41; font-size: 16px; font-weight: bold; } QPushButton:hover { background: #002200; }")
        return path

    def hotkey_copy_path(self):
        target_folder = self._ensure_current_folder_for_hotkey()
        if target_folder:
            logic.copy_to_clipboard(target_folder)
            self.flash_status("PATH")
        else:
            self.flash_status("Chua co thu muc", "#ffc172")
    
    def hotkey_copy_name(self):
        self.copy_data("id")

    def hotkey_run_auto(self):
        """Run auto workflow (Ctrl+B)."""
        self.on_auto_click()

    def hotkey_run_auto_fast(self):
        """Run auto workflow using alternate key (Ctrl+Shift+B)."""
        self.on_auto_click()

    def hotkey_copy_mix(self):
        """Copy mixed ID with checked positions (Ctrl+Shift+V)."""
        self.copy_data("mix")

    def hotkey_reset_data(self):
        """Quick reset current data (Ctrl+R)."""
        self.on_reset()
        self.flash_status("RESET", "#b7c2ca")

    def hotkey_open_folder(self):
        """Open current folder in Explorer (Alt+E / Ctrl+Alt+E)."""
        target_folder = self._ensure_current_folder_for_hotkey()
        if target_folder and os.path.exists(target_folder):
            os.startfile(target_folder)
            self.flash_status("Mo thu muc", "#58d7a1")
        else:
            self.flash_status("Chua co thu muc", "#ffc172")

    def hotkey_open_last_screenshot(self):
        """Open last captured screenshot (Ctrl+M)"""
        if self.last_screenshot_path and os.path.exists(self.last_screenshot_path):
            os.startfile(self.last_screenshot_path)
            self.flash_status("Mo anh chup", "#58d7a1")
        else:
            self.flash_status("Chua co anh chup", "#ffc172")
            
    def hotkey_toggle_shortcut_panel(self):
        """Toggle shortcuts panel (Insert)."""
        self.hotkey_show_hack_menu()

    def hotkey_toggle_visibility(self):
        """Toggle visibility of the main tool window (Insert)"""
        if self.isVisible():
            self.on_minimize_to_tray()
        else:
            self.show_from_tray()

    def hotkey_show_hack_menu(self):
        """Show/Hide Hack Menu (Ctrl+H)"""
        if hasattr(self, '_hack_menu_win') and self._hack_menu_win and self._hack_menu_win.isVisible():
            self._hack_menu_win.close()
            self._hack_menu_win = None
            return
            
        self._hack_menu_win = HackMenuDialog(self)
        # Position at center of screen or near main window
        if self.isVisible():
            self._hack_menu_win.move(self.x() - 100, self.y() - 50)
        self._hack_menu_win.show()
    
    def on_checkbox_clicked(self, selected_key):
        """Exclusive checkbox selection - only one can be checked"""
        # Uncheck all others when one is checked
        for key, chk in self.chk_groups.items():
            if key != selected_key and chk.isVisible():
                chk.setChecked(False)

    def copy_data(self, field):
        text = "-"
        base_id = self.current_data.get('order_id', '')
        
        if field == "id":
             # Just ID
             text = base_id
                     
        elif field == "mix":
             target_folder = self._ensure_current_folder_for_hotkey()
             if target_folder:
                 text = target_folder
             else:
                 text = "-"
        
        elif field == "mode":
             text = self.current_data.get('mode', '')
        elif field == "badge":
            text = self.current_data.get('size', '')
            
        if text and text != "-" and text != "Unknown":
            logic.copy_to_clipboard(text)
            self.last_copied = text  # Store for screenshot naming
            self.flash_status(f"COPIED") 

    def copy_file_to_clipboard(self, file_path):
        """Copy a file path as CF_HDROP to the Windows clipboard."""
        import ctypes
        import ctypes.wintypes
        import win32clipboard
        import win32con
        import struct

        try:
            file_path = os.path.abspath(file_path)
            # Encode as null-terminated UTF-16-LE, with double null at end
            file_bytes = (file_path + '\x00\x00').encode('utf-16-le')

            # DROPFILES struct: cbSize(4), pt.x(4), pt.y(4), fNC(4), fWide(4) = 20 bytes
            # pFiles offset = 20 (right after the struct)
            dropfiles_header = struct.pack('IIIII',
                20,   # cbSize = sizeof(DROPFILES)
                0,    # pt.x
                0,    # pt.y  
                0,    # fNC
                1,    # fWide = TRUE (Unicode)
            )
            clipboard_data = dropfiles_header + file_bytes

            # Allocate global memory
            hGlobal = ctypes.windll.kernel32.GlobalAlloc(
                win32con.GMEM_MOVEABLE | win32con.GMEM_ZEROINIT,
                len(clipboard_data)
            )
            if not hGlobal:
                raise RuntimeError('GlobalAlloc failed')

            pGlobal = ctypes.windll.kernel32.GlobalLock(hGlobal)
            if not pGlobal:
                ctypes.windll.kernel32.GlobalFree(hGlobal)
                raise RuntimeError('GlobalLock failed')

            ctypes.memmove(pGlobal, clipboard_data, len(clipboard_data))
            ctypes.windll.kernel32.GlobalUnlock(hGlobal)

            win32clipboard.OpenClipboard(0)
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_HDROP, hGlobal)
            finally:
                win32clipboard.CloseClipboard()

            print(f"[PASTE] Clipboard set: {file_path}")
            return True
        except Exception as e:
            print(f"[PASTE] copy_file_to_clipboard error: {e}")
            return False

    def focus_wilcom_window(self):
        """Find and force-foreground the Ultimate Special Edition window."""
        import ctypes
        import win32process
        import win32con

        search_keywords = ["Ultimate Special", "[Ultimate", "Embroid", "Wilcom", "Design", "Tajima", "Pulse"]

        hwnd = None

        # Use EnumWindows for a reliable partial-title search
        def enum_handler(h, _):
            nonlocal hwnd
            if hwnd:
                return  # Already found
            if not win32gui.IsWindowVisible(h):
                return
            title = win32gui.GetWindowText(h)
            if not title:
                return
            if any(kw in title for kw in search_keywords):
                # Skip our own app
                if 'TX Embroider' in title or 'TX EMBROIDER' in title:
                    return
                hwnd = h

        win32gui.EnumWindows(enum_handler, None)

        if not hwnd:
            print('[PASTE] Wilcom window not found')
            return False

        try:
            # Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.15)

            # Force focus using the foreground lock bypass trick:
            # Attach our thread's input state to the target window's thread
            fg_hwnd = win32gui.GetForegroundWindow()
            fg_tid, _ = win32process.GetWindowThreadProcessId(fg_hwnd)
            tgt_tid, _ = win32process.GetWindowThreadProcessId(hwnd)

            if fg_tid != tgt_tid:
                ctypes.windll.user32.AttachThreadInput(fg_tid, tgt_tid, True)

            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            win32gui.BringWindowToTop(hwnd)
            win32gui.SetForegroundWindow(hwnd)

            if fg_tid != tgt_tid:
                ctypes.windll.user32.AttachThreadInput(fg_tid, tgt_tid, False)

            time.sleep(0.25)  # Let the window receive focus
            title = win32gui.GetWindowText(hwnd)
            print(f'[PASTE] Focused: {title}')
            return True
        except Exception as e:
            print(f'[PASTE] focus_wilcom_window error: {e}')
            return False

    def on_paste_wilcom_clicked(self):
        """Worker thread: paste 2.png then 1.png into Ultimate Special Edition."""
        import threading
        import win32con
        import win32api

        def paste_one_image(img_path, label):
            """Copy file to clipboard and send Ctrl+V to the Wilcom window."""
            self.status_signal.emit(f"Dan {label}...", "#00ffff")

            if not self.copy_file_to_clipboard(img_path):
                self.status_signal.emit(f"Loi copy {label}", "#ff3333")
                return False

            # Re-focus every paste to make sure we have the window
            if not self.focus_wilcom_window():
                self.status_signal.emit("Mat focus Wilcom", "#ff3333")
                return False

            time.sleep(0.1)
            # Send Ctrl+V using pyautogui (window is now foreground)
            pyautogui.hotkey('ctrl', 'v')
            return True

        def run_paste_workflow():
            try:
                desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')

                # Resolve paths (case-insensitive fallback)
                def resolve(name):
                    p = os.path.join(desktop_path, name)
                    if os.path.exists(p):
                        return p
                    p2 = os.path.join(desktop_path, name.upper())
                    return p2 if os.path.exists(p2) else None

                img2 = resolve('2.png')
                img1 = resolve('1.png')

                if not img2 and not img1:
                    self.status_signal.emit('Thieu 1.png & 2.png', '#ff3333')
                    return

                self.status_signal.emit('Tim Wilcom...', '#ffff00')

                # Initial focus
                if not self.focus_wilcom_window():
                    self.status_signal.emit('Khong thay Wilcom', '#ff3333')
                    return

                pasted = False

                if img2:
                    ok = paste_one_image(img2, '2.png')
                    if ok:
                        pasted = True
                        time.sleep(0.8)  # Wait for Wilcom to load image

                if img1:
                    ok = paste_one_image(img1, '1.png')
                    if ok:
                        pasted = True
                        time.sleep(0.5)

                if pasted:
                    self.status_signal.emit('Dan xong!', '#00ff41')
                    self.show_success_toast_signal.emit('Dan anh vao Wilcom thanh cong!')
                else:
                    self.status_signal.emit('Khong dan duoc', '#ff3333')

            except Exception as e:
                print(f'[PASTE] Workflow error: {e}')
                self.status_signal.emit('Loi dan anh', '#ff3333')

        threading.Thread(target=run_paste_workflow, daemon=True).start() 

    def flash_status(self, text, color="#00ff41"):
        # Emit signal to update UI from Main Thread
        self.update_status_signal.emit(text, color)

    @Slot(str, str)
    def _flash_status_safe(self, text, color):
        # Actual UI Update (Must run on Main Thread)
        orig = getattr(self.lbl_id, 'original_text', 'WAITING...')
        self.lbl_id.scroll_timer.stop()
        self.lbl_id.setText(f"[{text}]")
        self.lbl_id.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
        QTimer.singleShot(800, lambda: self._reset_id_label(orig))
    
    def _reset_id_label(self, text):
        self.lbl_id.original_text = text
        self.lbl_id.setText(text)
        self.lbl_id.setStyleSheet("color: #f3fcff; font-size: 13px; font-weight: bold;")
        self.lbl_id.scroll_timer.start(150)
    
    def on_screenshot_click(self):
        """Handle screenshot button clicks - single or double"""
        self.screenshot_clicks += 1
        
        if self.screenshot_clicks == 1:
            # Start timer for double-click detection
            self.screenshot_timer.start(300)  # 300ms window
        elif self.screenshot_clicks == 2:
            # Double click detected
            self.screenshot_timer.stop()
            self.screenshot_clicks = 0
            self.handle_screenshot_region()
    
    def handle_screenshot_single(self):
        """Single click - capture focused window"""
        self.screenshot_clicks = 0
        self.on_screenshot_v4()  # Use existing window capture
    
    def handle_screenshot_region(self):
        """Double click - region selection"""
        if not self.current_folder:
            print("No folder created yet")
            return
        
        # Use pyautogui region selector
        import pyautogui
        try:
            # Hide window temporarily
            self.hide()
            time.sleep(0.5)
            
            # For now, capture full screen and user capture
            screenshot = pyautogui.screenshot()
            
            # Generate filename using last copied data
            name_base = getattr(self, 'last_copied', self.current_data.get('order_id', 'screenshot'))
            name_base = name_base.replace('/', '-').replace('\\', '-')[:50]
            
            timestamp = time.strftime("%H%M%S")
            filename = f"REGION_{name_base}_{timestamp}.png"
            filepath = os.path.join(self.current_folder, filename)
            
            screenshot.save(filepath)
            print(f"Region screenshot saved: {filepath}")
            
            self.show()
        except Exception as e:
            print(f"Region screenshot error: {e}")
            self.show()
    


    def on_reset(self):
        """Reset all data and checkboxes"""
        self.current_data = {}
        self.lbl_id.original_text = "WAITING DATA..."
        self.lbl_id.setText("WAITING DATA...")
        self.btn_mode.setText("WAITING...")
        self.btn_badge.setText("DST | 2x2 inches")
        self.btn_badge.setStyleSheet("""
            background: #440000;
            color: #ff003c;
            border: 1px solid #ff003c;
            border-radius: 6px;
            font-weight: bold;
            font-size: 10px;
            padding: 2px;
        """)
        
        # Hide all checkboxes
        for chk in self.chk_groups.values():
            chk.setChecked(False)
            chk.setVisible(False)
        
        # Reset folder
        self.current_folder = None
        self.btn_folder.setStyleSheet("QPushButton { background: #020502; border: 1px solid #00ff41; border-radius: 4px; color: #ffcc00; font-size: 12px; font-weight: bold; } QPushButton:hover { background: #002200; }")

    def on_reload_db(self):
        count = logic.reload_dimensions_db()
        self.flash_status(f"DB:{count}", "#00ffff")

    def _load_save_folder(self):
        """Load saved folder path from config, default to Desktop"""
        import json
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                folder = cfg.get('save_folder', desktop)
                if os.path.isdir(folder):
                    return folder
        except Exception:
            pass
        return desktop

    def _save_save_folder(self, folder):
        """Persist the save folder path to config"""
        import json
        try:
            cfg = {}
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
            cfg['save_folder'] = folder
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Config save error: {e}")

    def _handle_folder_single_click(self):
        """Single-click: open/create folder as before"""
        self._folder_clicks = 0
        self._do_open_or_create_folder()

    def _launch_exe_silent(self, exe_path):
        """Launch an EXE without showing a black console window, keeping GUI visible"""
        import subprocess
        subprocess.Popen(
            [exe_path],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def on_run_tool(self):
        """Run the currently selected tool in the combobox (no black window)"""
        index = self.cb_tools.currentIndex()
        if index == 0:
            self.flash_status("Chon tool truoc!", "#ffcc00")
            return

        tool_name = self.cb_tools.itemText(index)
        script_dir = os.path.dirname(os.path.abspath(__file__))

        def get_exe(exe_name, fallback_dirs):
            import sys
            # 1. Same folder as this script (ChestEMB/)
            local = os.path.join(script_dir, exe_name)
            if os.path.exists(local):
                return local
            # 2. PyInstaller bundle
            if getattr(sys, 'frozen', False):
                bundled = os.path.join(sys._MEIPASS, 'tools', exe_name)
                if os.path.exists(bundled):
                    return bundled
            # 3. Fallback directories
            for d in fallback_dirs:
                p = os.path.join(d, exe_name)
                if os.path.exists(p):
                    return p
            return None

        if tool_name == "In (PS Auto)":
            exe = get_exe('PS_Auto_GUI1.exe', [
                r'C:\Users\Tx\Desktop\vibecoder\ChestEMB',
                r'C:\Users\Tx\Desktop\vibecoder\in\dist',
                r'C:\Users\Tx\Desktop\vibecoder\in',
            ])
            if exe:
                self._launch_exe_silent(exe)
                self.flash_status("Launch PS Auto", "#00ff41")
            else:
                self.flash_status("Khong tim thay exe", "#ff3333")

        elif tool_name == "Thêu (PatchPrint)":
            exe = get_exe('A-PatchPrint.exe', [
                r'C:\Users\Tx\Desktop\vibecoder\ChestEMB',
                r'C:\Users\Tx\Desktop\vibecoder\thêu\A-PatchPrint',
            ])
            if exe:
                self._launch_exe_silent(exe)
                self.flash_status("Launch PatchPrint", "#00ff41")
            else:
                self.flash_status("Khong tim thay exe", "#ff3333")
        elif tool_name == "🎲 Game Tài Xỉu":
            self.on_open_mini_game()
            return

    def on_open_mini_game(self):
        """Open the Tài Xỉu LAN mini-game window (prompts for name once if not set yet)"""
        try:
            from PySide6.QtWidgets import QDialog
            from tai_xiu_game import TaiXiuGameWindow, NameInputDialog, load_profile, save_profile
            
            profile = load_profile()
            current_name = profile.get("username", "").strip()
            
            # Show name dialog ONLY if username is empty
            if not current_name:
                dlg = NameInputDialog(current_name, self)
                if dlg.exec() == QDialog.Accepted:
                    profile["username"] = dlg.username
                    save_profile(profile)
                else:
                    return # User cancelled, do not open the game window
            
            # Check and open game window safely (Only allow one instance)
            still_open = False
            if hasattr(self, '_game_window') and self._game_window is not None:
                try:
                    if self._game_window.isVisible():
                        still_open = True
                except RuntimeError:
                    self._game_window = None
            
            if still_open:
                try:
                    self._game_window.close()
                    self._game_window.deleteLater()
                except:
                    pass
                self._game_window = None
                self.flash_status("Dong game", "#ff3333")
                return
            else:
                self._game_window = None
            
            # Create a fresh single instance
            self._game_window = TaiXiuGameWindow(parent=self)
            self._game_window.show()
            self._game_window.raise_()
            self._game_window.activateWindow()
        except Exception as e:
            import traceback
            err_detail = traceback.format_exc()
            print(f"Mini game error: {e}\n{err_detail}")
            # In EXE mode write to log and show dialog so error is visible
            if getattr(__import__('sys'), 'frozen', False):
                try:
                    import os as _os
                    log_path = _os.path.join(_os.path.dirname(__import__('sys').executable), 'game_error.log')
                    with open(log_path, 'a', encoding='utf-8') as _f:
                        _f.write(f'\n--- Mini Game Error ---\n{err_detail}\n')
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.critical(self, 'Game Error', f'Lỗi mở game:\n{e}\n\nXem chi tiết tại: game_error.log')
                except Exception:
                    pass
            self.flash_status("Loi mo game", "#ff3333")

    def on_tool_selected(self, index):
        """Legacy: kept for backward compatibility — combo selection no longer auto-launches"""
        pass

    def exit_all_apps(self):
        """Emergency exit: terminates all related tools and python processes, then exits"""
        print("Ctrl+Alt+X pressed: Terminating all tools...")
        import subprocess
        import sys
        
        # Kill specific compiled executable names if running
        subprocess.run("taskkill /f /im PS_Auto_GUI.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run("taskkill /f /im A-PatchPrint.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Kill python.exe which handles scripts (app.py, main.py, autoluuEMB.py, gui.py)
        # Note: this will also kill the current process since it runs via python.
        subprocess.run("taskkill /f /im python.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Fallback exit
        sys.exit(0)

    def on_open_color_reader(self):
        try:
            from color_reader import ColorReaderDialog
            if not hasattr(self, 'color_dialog') or not self.color_dialog:
                self.color_dialog = ColorReaderDialog(self)
            self.color_dialog.show()
            self.color_dialog.raise_()
            self.color_dialog.activateWindow()
            self.flash_status("Layer Reader", "#ff99ff")
        except Exception as e:
            print(f"Error opening color reader: {e}")
            self.flash_status("ERR COLORREADER", "#ff3333")

    def on_toggle_overlay(self):
        self.overlay_enabled = not getattr(self, 'overlay_enabled', True)
        if not self.overlay_enabled:
            if self.info_overlay.isVisible():
                self.info_overlay.hide()
            self.flash_status("HUD: OFF", "#ff3333")
            if hasattr(self, 'btn_overlay_title'):
                self.btn_overlay_title.setStyleSheet("background: transparent; color: #777; font-size: 8px; font-weight: bold; border: none; padding: 0;")
                self.btn_overlay_title.setToolTip("Enable HUD Overlay")
        else:
            self.flash_status("HUD: ON", "#00ff41")
            if hasattr(self, 'btn_overlay_title'):
                self.btn_overlay_title.setStyleSheet("background: transparent; color: #00ff41; font-size: 8px; font-weight: bold; border: none; padding: 0;")
                self.btn_overlay_title.setToolTip("Disable HUD Overlay")

    def on_toggle_pin(self):
        flags = self.windowFlags()
        if self.is_pinned:
            flags &= ~Qt.WindowStaysOnTopHint
            self.is_pinned = False
            if hasattr(self, 'btn_pin') and self.btn_pin:
                self.btn_pin.setStyleSheet("QPushButton { background: #020502; border: 1px solid #00ff41; border-radius: 4px; color: #ff3333; font-size: 12px; font-weight: bold; } QPushButton:hover { background: #002200; }")
            if hasattr(self, 'btn_pin_title'):
                self.btn_pin_title.setStyleSheet("background: transparent; color: #777; font-size: 8px; font-weight: bold; border: none; padding: 0;")
            if hasattr(self, 'btn_pin') and self.btn_pin:
                self.btn_pin.setToolTip("Pin Always on Top (OFF)")
        else:
            flags |= Qt.WindowStaysOnTopHint
            self.is_pinned = True
            if hasattr(self, 'btn_pin') and self.btn_pin:
                self.btn_pin.setStyleSheet("QPushButton { background: #153126; border: 1px solid #00ff41; border-radius: 4px; color: #ff3333; font-size: 12px; font-weight: bold; } QPushButton:hover { background: #002200; }")
            if hasattr(self, 'btn_pin_title'):
                self.btn_pin_title.setStyleSheet("background: transparent; color: #ff3333; font-size: 8px; font-weight: bold; border: none; padding: 0;")
            if hasattr(self, 'btn_pin') and self.btn_pin:
                self.btn_pin.setToolTip("Pin Always on Top (ON)")
            
        self.setWindowFlags(flags)
        self.show()
    
    def on_toggle_pin_corner(self):
        self.on_toggle_pin()

    # on_toggle_expand removed per user request for list style UI

    @Slot(dict)
    def update_data(self, data):
        self.current_data = logic.parse_details(data)
        
        oid = self.current_data.get('order_id', 'Unknown')
        f_type = self.current_data.get('file_type', 'UNK')
        size = self.current_data.get('size', '-')
        mode = self.current_data.get('mode', '-')
        positions = self.current_data.get('positions', [])

        # Update ID label with scrolling
        self.lbl_id.original_text = oid
        self.lbl_id.setText(oid)
        self.lbl_id.scroll_pos = 0  # Reset scroll position
        
        self.btn_mode.setText(mode if mode else "-")
        if "DST" in f_type:
             bg_col = "#440000" 
             txt_col = "#ff003c"
             border_col = "#ff003c"
        elif "TBF" in f_type:
             bg_col = "#002200" 
             txt_col = "#00ff41"
             border_col = "#00ff41"
             
        # Add Dims if available
        dims = self.current_data.get('dims', '')
        badge_text = f"{f_type} | {size}"
        if dims:
            badge_text += f" | {dims}"
            
        self.btn_badge.setText(badge_text)
        
        # Checkbox Logic: Only show (Visible) but DO NOT CHECK (Values=False)
        for chk in self.chk_groups.values():
            chk.setChecked(False) # All Unchecked by default
            chk.setVisible(False)
            
        # Show detected
        visible_keys = []
        for pos in positions:
            if pos in self.chk_groups:
                self.chk_groups[pos].setVisible(True)
                visible_keys.append(pos)
        
        # Auto-check if only 1 checkbox is visible
        if len(visible_keys) == 1:
            self.chk_groups[visible_keys[0]].setChecked(True)
            print(f"[AUTO-CHECK] Only one option '{visible_keys[0]}' - auto-checked")
                
        # Badge Colors
        if "DST" in f_type:
            self.btn_badge.setStyleSheet("""
                background: #440000;
                color: #ff003c;
                border: 1px solid #ff003c;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10px;
                padding: 2px;
            """)
        elif "TBF" in f_type:
            self.btn_badge.setStyleSheet("""
                background: #002200;
                color: #00ff41;
                border: 1px solid #00ff41;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10px;
                padding: 2px;
            """)
        else:
            self.btn_badge.setStyleSheet("""
                background: #111111;
                color: #cccccc;
                border: 1px solid #cccccc;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10px;
                padding: 2px;
            """)
        
        self.current_folder = None 
        self.btn_folder.setStyleSheet("QPushButton { background: #020502; border: 1px solid #00ff41; border-radius: 4px; color: #ffcc00; font-size: 12px; font-weight: bold; } QPushButton:hover { background: #002200; }")
        
        # Auto-Create Folder when new data arrives (if valid order ID)
        if oid and oid != 'Unknown':
            path, created = logic.create_order_folder(self._save_folder, oid)
            if path:
                self.current_folder = path
                status = "CREATED" if created else "READY"
                print(f"[AUTO-FOLDER] {status}: {path}")
                self.btn_folder.setStyleSheet("QPushButton { background: #153126; border: 1px solid #00ff41; border-radius: 4px; color: #00ff41; font-size: 12px; font-weight: bold; } QPushButton:hover { background: #002200; }")
        
        # Update Overlay Info
        self.info_overlay.update_info(oid, mode, size, f_type, dims)
        
        # Auto-Trigger: Run workflow immediately if enabled and data is valid
        if self.auto_trigger_enabled and oid and oid != 'Unknown':
            print(f"[AUTO-TRIGGER] New data detected: {oid} - Triggering workflow...")
            # Small delay to ensure UI updates complete
            QTimer.singleShot(100, self.on_auto_click)
        
        # If in collapsed mode, we might want to temporarily expand or flash?
        # For now, stay in current mode.

    def on_create_folder(self):
        """Handle folder button click — single=open/create, double=change save path"""
        self._folder_clicks += 1
        if self._folder_clicks == 1:
            self._folder_click_timer.start(350)
        elif self._folder_clicks >= 2:
            self._folder_click_timer.stop()
            self._folder_clicks = 0
            self._change_save_folder()

    def _change_save_folder(self):
        """Let user pick a new default save folder (persisted)"""
        new_folder = QFileDialog.getExistingDirectory(
            self, "Chọn thư mục lưu mặc định", self._save_folder
        )
        if new_folder:
            self._save_folder = new_folder
            self._save_save_folder(new_folder)
            self.flash_status("Da doi thu muc luu", "#00ffcc")
            print(f"[SAVE FOLDER] Changed to: {new_folder}")

    def _do_open_or_create_folder(self):
        """Single-click logic: open existing folder or create new one"""
        # If we already have a path tracked, OPEN it
        if self.current_folder and os.path.exists(self.current_folder):
             logic.open_folder(self.current_folder)
             self.flash_status("OPENING...")
             return None

        # Otherwise CREATE/FIND it
        oid = self.current_data.get('order_id')
        if not oid: return None
        
        path, created = logic.create_order_folder(self._save_folder, oid)
        
        if path:
            self.current_folder = path
            self.flash_status("Da san sang thu muc", "#58d7a1")
            self.btn_folder.setStyleSheet("QPushButton { background: #153126; border: 1px solid #00ff41; border-radius: 4px; color: #00ff41; font-size: 12px; font-weight: bold; } QPushButton:hover { background: #002200; }")
            return path
        return None

    def on_screenshot_v4(self):
        """Screenshot của cửa sổ Ultimate Special Edition ONLY"""
        # If folder not known, try to create it first
        oid = self.current_data.get('order_id', 'Unknown')
        
        target_folder = self.current_folder
        
        if not target_folder and oid != 'Unknown':
             # Try auto-create
             desktop = os.path.join(os.path.expanduser("~"), "Desktop")
             path, _ = logic.create_order_folder(desktop, oid)
             if path:
                 self.current_folder = path
                 target_folder = path
        
        # Screenshot cửa sổ embroidery ONLY
        try:
            from auto_workflow import AutoWorkflow
            # Create temp workflow just to use window capture function
            temp_workflow = AutoWorkflow(self, {})
            
            # Find and activate window
            if not temp_workflow.activate_embroidery_window():
                self.flash_status("Khong thay cua so", "#ff7d86")
                return
            
            # Capture window screenshot
            screenshot = temp_workflow.capture_window_screenshot()
            
            # Generate filename (OVERWRITE MODE - No timestamp)
            screenshot_name = self.last_copied if self.last_copied else oid
            screenshot_name = screenshot_name.replace('/', '-').replace('\\', '-')[:50]
            
            filename = f"{screenshot_name}.png"
            
            if target_folder:
                filepath = os.path.join(target_folder, filename)
            else:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                filepath = os.path.join(desktop, filename)
            
            screenshot.save(filepath)
            self.last_screenshot_path = filepath # Save for Ctrl+M preview
            print(f"Window screenshot saved (OVERWRITTEN): {filepath}")
            self.flash_status("Da chup anh", color="#ffffff")
        except Exception as e:
            print(f"Screenshot error: {e}")
            self.flash_status("Loi chup anh", "#ff7d86")

    def on_open_image(self):
        url = self.current_data.get('image_url')
        if not url: return

        # Try to download and show in ImageViewer
        try:
            import urllib.request
            self.flash_status("LOADING...")
            QApplication.processEvents() 
            
            # Simple sync download (fast enough for small images, ideally thread)
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = response.read()
                
            # ImageViewer class is missing in provided snippets, assumed handled or not needed for this refactor
            # Since I didn't see ImageViewer in the file outline or content I read, I will omit the viewer part 
            # or assume it was imported but I missed it. 
            # Checking imports... logic doesn't have it. 
            # I will just fallback to browser logic as safety.
            logic.open_image_url(url)
            self.flash_status("VIEWING")
            
        except Exception as e:
            print(f"Image load error: {e}")
            self.flash_status("ERR IMG", "#ff0000")
            logic.open_image_url(url)
        
    def on_auto_click(self):
        """Run automated 3-step workflow"""
        try:
            from auto_workflow import AutoWorkflow
            
            oid = self.current_data.get('order_id', 'Unknown')
            if not oid or oid == 'Unknown':
                self.flash_status("Chua co du lieu", "#ffc172")
                return
            
            # PRE-FETCH DATA ON MAIN THREAD
            # Collect all data needed by the worker thread here
            # to avoid the worker thread accessing widgets (like checkboxes)
            
            # 1. Generate ID with Checkboxes logic
            base_id = oid
            checked = []
            for k in self.all_keys:
                if k in self.chk_groups and self.chk_groups[k].isChecked():
                    checked.append(k)
            
            final_id = base_id
            if checked:
                 checkbox_str = "_".join(checked)
                 final_id = f"{base_id}_({checkbox_str})"

            # 2. Pack Context
            context = {
                'order_id': oid,
                'final_id': final_id,
                'folder_path': self.current_folder,
                'file_type': self.current_data.get('file_type', 'TBF')
            }

            self.flash_status("Dang chay tu dong...", "#58d7a1")
            
            # Create workflow with SAFE context
            # Pass 'self' only for signal emission, NOT for reading widgets
            self.current_workflow = AutoWorkflow(self, context)
            
            import threading
            def run_async():
                time.sleep(0.3)  # Minimal delay for window switching
                self.current_workflow.run()
            
            thread = threading.Thread(target=run_async, daemon=True)
            thread.start()
            
            # Workflow started: We can assume it finishes. 
            # (Checkbox locking removed per user request)
            
        except Exception as e:
            print(f"Auto workflow error: {e}")
            self.flash_status("Loi tu dong", "#ff7d86")
    
    @Slot(str)
    def show_success_toast(self, message):
        toast = SuccessToast(message, self)
        toast.show()
        # Also show OS system notification (tray message)
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.showMessage("TX Embroider Tool", message, QSystemTrayIcon.Information, 2500)

    def lock_checkboxes(self):
        """Black out/Lock checkboxes after auto-run"""
        for cb in self.chk_groups.values():
            cb.setEnabled(False)
            cb.setStyleSheet("QCheckBox { color: #222; font-size: 10px; font-weight: bold; }")
            
    def unlock_checkboxes(self):
        """Restore checkboxes for new data"""
        for cb in self.chk_groups.values():
            cb.setEnabled(True)
            cb.setStyleSheet("QCheckBox { color: #00f3ff; font-size: 10px; font-weight: bold; }")

    def check_export_window(self):
        if not HAS_WIN32:
            return
        
        # Look for window matching the title
        def enum_handler(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                title_lower = title.lower()
                if "export curent" in title_lower or "export current" in title_lower or "export multi-decoration" in title_lower:
                    results.append(hwnd)
        
        results = []
        try:
            win32gui.EnumWindows(enum_handler, results)
        except Exception:
            pass
            
        if results:
            found_hwnd = results[0]
            if getattr(self, 'last_detected_export_hwnd', None) != found_hwnd:
                self.last_detected_export_hwnd = found_hwnd
                target_folder = self._ensure_current_folder_for_hotkey()
                if target_folder:
                    logic.copy_to_clipboard(target_folder)
                    self.flash_status("AUTO COPY PO", "#00ffcc")
                    print(f"[AUTO-COPY] Export window detected ({win32gui.GetWindowText(found_hwnd)}), copied PO path: {target_folder}")
        else:
            self.last_detected_export_hwnd = None

    def update_overlay_position(self):
        """Sync info overlay with Ultimate window position - ONLY when Active"""
        if not HAS_WIN32: return
        
        # Detect active export window to auto-copy PO folder
        self.check_export_window()
        
        if not getattr(self, 'overlay_enabled', True):
            if self.info_overlay.isVisible():
                self.info_overlay.hide()
            return
        
        target_hwnd = self.find_ultimate_window()
        foreground_hwnd = win32gui.GetForegroundWindow()
        
        # ONLY show if Ultimate is active OR we are active OR tool is active
        # CRITICAL: If Main window is hidden (in tray), only check Ultimate
        our_hwnd = int(self.winId()) if self.isVisible() else 0
        overlay_hwnd = int(self.info_overlay.winId())
        
        is_target_active = (foreground_hwnd == target_hwnd or 
                           (our_hwnd and foreground_hwnd == our_hwnd) or 
                           foreground_hwnd == overlay_hwnd)

        # If docked, we show even if Main App is hidden!
        if not target_hwnd or not is_target_active or (not self.isVisible() and not self.is_docked):
            if self.info_overlay.isVisible(): 
                self.info_overlay.hide()
            return
            
        if not self.info_overlay.isVisible():
            self.info_overlay.show()
            
        try:
            rect = win32gui.GetWindowRect(target_hwnd)
            target_x, target_y, target_x2, target_y2 = rect
            
            # Use smaller fixed width for the overlay to fit narrow windows too
            width = target_x2 - target_x
            overlay_width = 600 # Reduced from 800 for better fit
            self.info_overlay.setFixedWidth(overlay_width)
            
            # Center horizontally
            new_x = target_x + (width - overlay_width) // 2
            # Position for 2-line overlay (42px height)
            new_y = target_y2 - 50 
            
            self.info_overlay.move(new_x, new_y)
        except:
            pass

    def on_close_ultimate_app(self):
        """Tìm và đóng ứng dụng Ultimate Special Edition"""
        hwnd = self.find_ultimate_window()
        if hwnd:
            try:
                # Gửi tin nhắn đóng cửa sổ (tương đương Alt+F4)
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                self.flash_status("CLOSED APP", "#ff4444")
                print(f"Closed Ultimate app window: {hwnd}")
            except Exception as e:
                print(f"Error closing app: {e}")
                self.flash_status("CLOSE ERR", "#ff0000")
        else:
            self.flash_status("NO APP", "#ff8800")
            print("Ultimate app window not found for closing")

    def find_ultimate_window(self):
        """Find Ultimate Special Edition window using win32gui"""
        if not HAS_WIN32:
            print("Win32 not available, docking disabled")
            return None
        
        # List of possible window titles to search for
        possible_titles = [
            "Ultimate Special Edition",
            "[Ultimate Special Edition]",
            "Ultimate Special",
            "[Ultimate Special",
        ]
        
        # Try exact match first (fast path)
        for title in possible_titles:
            try:
                hwnd = win32gui.FindWindow(None, title)
                if hwnd and win32gui.IsWindowVisible(hwnd):
                    print(f"Found Ultimate window: {title}")
                    return hwnd
            except:
                continue
        
        # Try partial match search
        def enum_handler(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if "Ultimate" in window_text and "Special" in window_text:
                    # Skip our own window
                    if "TX" not in window_text and "Embroider" not in window_text:
                        results.append(hwnd)
        
        results = []
        try:
            win32gui.EnumWindows(enum_handler, results)
            if results:
                return results[0]
        except:
            pass
        
        return None
    
    def update_dock_position(self):
        """Update position to follow target window (called by timer)"""
        if not self.is_docked or not HAS_WIN32:
            return
        
        # Check if we have a valid window handle
        if not self.target_window_hwnd:
            # Try to find the window
            self.dock_search_attempts += 1
            if self.dock_search_attempts % 10 == 0:  # Every ~1 second
                hwnd = self.find_ultimate_window()
                if hwnd:
                    self.target_window_hwnd = hwnd
                    print("Reconnected to Ultimate window")
                    self.dock_search_attempts = 0
            return
        
        try:
            # Check if window still exists and is visible
            if not win32gui.IsWindow(self.target_window_hwnd):
                print("Target window closed")
                self.target_window_hwnd = None
                return
            
            if win32gui.IsIconic(self.target_window_hwnd):
                # Window is minimized, don't update position
                return
            
            if not win32gui.IsWindowVisible(self.target_window_hwnd):
                # Window is hidden
                return
            
            # Get target window position
            rect = win32gui.GetWindowRect(self.target_window_hwnd)
            target_x, target_y, target_x2, target_y2 = rect
            target_width = target_x2 - target_x
            
            # Calculate new position for MiniApp
            # Position at top-right corner with offset
            new_x = target_x2 + self.dock_offset_x
            new_y = target_y + self.dock_offset_y
            
            # Move to new position
            self.move(new_x, new_y)
            
        except Exception as e:
            print(f"Dock position update error: {e}")
            self.target_window_hwnd = None
    
    def on_toggle_dock(self):
        """Toggle docking to Ultimate Special Edition window"""
        if not HAS_WIN32:
            self.flash_status("Thieu win32", "#ff7d86")
            return
        
        self.is_docked = not self.is_docked
        
        if self.is_docked:
            # Enable docking
            hwnd = self.find_ultimate_window()
            if not hwnd:
                self.flash_status("Khong thay Ultimate", "#ff7d86")
                self.is_docked = False
                return
            
            self.target_window_hwnd = hwnd
            self.dock_search_attempts = 0
            
            # Update button appearance (Neon Glow)
            if hasattr(self, 'btn_dock') and self.btn_dock:
                self.btn_dock.setStyleSheet("QPushButton { background: #153126; border: 1px solid #00ff41; border-radius: 4px; color: #0099ff; font-size: 12px; font-weight: bold; } QPushButton:hover { background: #002200; }")
            if hasattr(self, 'btn_dock_title'):
                self.btn_dock_title.setStyleSheet("background: transparent; color: #00f3ff; font-size: 8px; font-weight: bold; border: none; padding: 0;")
            if hasattr(self, 'btn_dock') and self.btn_dock:
                self.btn_dock.setToolTip("Dock to Embroidery Window (ON)")
            
            # Start timer (100ms = 10 updates per second)
            self.dock_timer.start(100)
            
            # Immediately move to docked position
            self.update_dock_position()
            
            self.flash_status("Da bam vi tri", "#58d7a1")
            print("Docking enabled")
        else:
            # Disable docking
            self.dock_timer.stop()
            self.target_window_hwnd = None
            
            # Update button appearance
            if hasattr(self, 'btn_dock') and self.btn_dock:
                self.btn_dock.setStyleSheet("QPushButton { background: #020502; border: 1px solid #00ff41; border-radius: 4px; color: #0099ff; font-size: 12px; font-weight: bold; } QPushButton:hover { background: #002200; }")
            if hasattr(self, 'btn_dock_title'):
                self.btn_dock_title.setStyleSheet("background: transparent; color: #777; font-size: 8px; font-weight: bold; border: none; padding: 0;")
            if hasattr(self, 'btn_dock') and self.btn_dock:
                self.btn_dock.setToolTip("Dock to Embroidery Window (OFF)")
            
            self.flash_status("Da bo bam vi tri", "#b7c2ca")
            print("Docking disabled")
    
    def closeEvent(self, event):
        keyboard.unhook_all()
        self.dock_timer.stop()
        if hasattr(self, 'server_status_timer'):
            self.server_status_timer.stop()
        self.tray_icon.hide()  # Hide tray icon on exit
        event.accept()
        # Forcibly exit the process to terminate all background threads/Flask server/QLocalServer
        os._exit(0)
