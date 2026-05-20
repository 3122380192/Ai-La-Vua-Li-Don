"""
Color & Layer Reader Module - TX Embroider Tool
Hỗ trợ đọc Layer từ vùng màn hình được chỉ định (Calibration)
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QScrollArea, QWidget, QGridLayout,
                                QFrame, QSizePolicy, QApplication)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QRect, QPoint
from PySide6.QtGui import QColor, QPixmap, QPainter, QFont, QPen, QBrush, QScreen
import time
import os
import json

try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

import sys
if getattr(sys, 'frozen', False):
    CONFIG_FILE = os.path.join(os.path.dirname(sys.executable), "color_config.json")
else:
    CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "color_config.json")

# ─────────────────────────────────────────────────
# Quản lý cấu hình (Lưu vùng đã chọn)
# ─────────────────────────────────────────────────
def save_config(rect_dict):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(rect_dict, f)
    except: pass

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except: pass
    return None

# ─────────────────────────────────────────────────
# Region Selector - Cửa sổ chọn vùng bằng chuột
# ─────────────────────────────────────────────────
class RegionSelector(QDialog):
    selected = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        
        # Lấy kích thước toàn màn hình
        self.screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(self.screen_geometry)
        
        self.begin = QPoint()
        self.end = QPoint()
        self.is_selecting = False

    def paintEvent(self, event):
        painter = QPainter(self)
        # Vẽ màn tối mờ
        painter.setBrush(QColor(0, 0, 0, 100))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())
        
        if not self.begin.isNull() and not self.end.isNull():
            # Vẽ vùng chọn trong suốt
            rect = QRect(self.begin, self.end).normalized()
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.drawRect(rect)
            
            # Vẽ viền vùng chọn
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor("#00ff41"), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)
            
            # Vẽ kích thước
            painter.setPen(QColor("#00ff41"))
            painter.drawText(rect.bottomRight() + QPoint(5, 20), f"{rect.width()}x{rect.height()}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.begin = event.pos()
            self.end = self.begin
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            rect = QRect(self.begin, self.end).normalized()
            if rect.width() > 5 and rect.height() > 5:
                res = {
                    "x": rect.x(),
                    "y": rect.y(),
                    "w": rect.width(),
                    "h": rect.height()
                }
                save_config(res)
                self.selected.emit(res)
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

# ─────────────────────────────────────────────────
# Tìm cửa sổ Color-Object List tự động
# ─────────────────────────────────────────────────
def find_color_object_window():
    if not HAS_WIN32: return None, None
    
    target_hwnd = [None]
    
    def enum_handler(hwnd, l):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "Color-Object List" in title:
                target_hwnd[0] = hwnd
    
    # Thử tìm cửa sổ Top-level trước
    win32gui.EnumWindows(enum_handler, None)
    
    # Nếu không thấy, thử tìm cửa sổ con của Ultimate Special Edition
    if target_hwnd[0] is None:
        def find_ultimate(hwnd, l):
            if "Ultimate" in win32gui.GetWindowText(hwnd):
                win32gui.EnumChildWindows(hwnd, enum_handler, None)
        win32gui.EnumWindows(find_ultimate, None)

    if target_hwnd[0]:
        rect = win32gui.GetWindowRect(target_hwnd[0])
        # rect = (left, top, right, bottom)
        return target_hwnd[0], (rect[0], rect[1], rect[2]-rect[0], rect[3]-rect[1])
    
    return None, None

# ─────────────────────────────────────────────────
# Worker Thread - Đọc màu từ vùng đã lưu hoặc tự động
# ─────────────────────────────────────────────────
class ColorReadWorker(QThread):
    finished = Signal(list, str)
    progress = Signal(str)

    def run(self):
        try:
            hwnd, rect = find_color_object_window()
            if not hwnd:
                config = load_config()
                if config:
                    rect = (config["x"], config["y"], config["w"], config["h"])
                    self.progress.emit("Sử dụng vùng căn chỉnh...")
                else:
                    self.finished.emit([], "Không thấy cửa sổ. Hãy dùng nút [Mục tiêu 🎯].")
                    return
            else:
                self.progress.emit("Đã thấy cửa sổ Color-Object List!")

            self.progress.emit("Đang phân tích...")
            # Giảm offset xuống 45 để tránh hụt Layer đầu tiên
            header_offset = 45 
            if rect[3] > header_offset:
                capture_rect = (rect[0], rect[1] + header_offset, rect[2], rect[3] - header_offset)
            else:
                capture_rect = rect

            image = capture_region(capture_rect)
            if image is None:
                self.finished.emit([], "Lỗi chụp ảnh.")
                return

            # LƯU ẢNH DEBUG ĐỂ KIỂM TRA (Sẽ hiện trong folder Desktop/EMBBBBB)
            try:
                image.save("debug_captured.png")
                print("Đã lưu ảnh debug_captured.png để kiểm tra vùng chụp.")
            except: pass

            colors = detect_color_swatches(image)
            self.finished.emit(colors, "")
        except Exception as e:
            self.finished.emit([], f"Lỗi: {str(e)}")

# ─────────────────────────────────────────────────
# Logic tìm kiếm & Xử lý (Dựa trên ảnh của user)
# ─────────────────────────────────────────────────
def capture_region(rect):
    if not HAS_PYAUTOGUI: return None
    x, y, w, h = rect
    return pyautogui.screenshot(region=(x, y, w, h))

def detect_color_swatches(image):
    if not HAS_PIL: return []
    img = image.convert("RGB")
    width, height = img.size
    
    detected = []
    y = 5
    # Cột lấy mẫu (tránh các con số ở giữa ô màu)
    # Trong ảnh, ô màu rộng khoảng 30px, ta lấy mẫu ở cột 25 hoặc 45 (phần gạch ngang)
    sample_x = 30
    if width > 60: 
        sample_x = 60 # Lấy mẫu ở phần gạch ngang màu bên phải ô số thì sạch hơn

    def get_average_color(px, py, size=5):
        """Lấy trung bình màu của một vùng nhỏ để tránh nhiễu"""
        r_total, g_total, b_total = 0, 0, 0
        count = 0
        for i in range(px, min(px + size, width)):
            for j in range(py, min(py + size, height)):
                r, g, b = img.getpixel((i, j))
                r_total += r
                g_total += g
                b_total += b
                count += 1
        if count == 0: return (0, 0, 0)
        return (r_total // count, g_total // count, b_total // count)

    def is_background(rgb):
        """Kiểm tra xem có phải màu nền xám/trắng của grid không"""
        r, g, b = rgb
        # Màu nền xám grid thường có r,g,b sàn sàn nhau và > 150
        diff = max(r, g, b) - min(r, g, b)
        if diff < 15 and r > 150: return True
        # Hoặc màu xám đậm của đường kẻ
        if diff < 10 and 100 < r < 140: return True
        return False

    row_height = 23 # Chiều cao trung bình 1 dòng
    
    while y < height - 15:
        # Lấy màu trung bình tại điểm quét
        color = get_average_color(sample_x, y, 5)
        
        if not is_background(color):
            # Tìm thấy một màu tiềm năng (không phải nền)
            r, g, b = color
            hex_val = f"#{r:02x}{g:02x}{b:02x}"
            
            # Kiểm tra xem đây là màu mới hay vẫn là màu cũ của cùng 1 ô
            is_new = True
            if detected:
                last = detected[-1]
                # Nếu màu giống và khoảng cách y quá gần -> cùng 1 layer
                if y - last['last_y'] < 18:
                    is_new = False
            
            if is_new:
                detected.append({
                    "rgb": (r, g, b),
                    "hex": hex_val,
                    "index": len(detected) + 1,
                    "last_y": y
                })
                # Nhảy qua 1 row_height để đến dòng tiếp theo
                y += row_height - 5
            else:
                y += 2
        else:
            # Vẫn là nền, đi tiếp
            y += 2
            
    return detected

# ─────────────────────────────────────────────────
# Dialog hiển thị kết quả
# ─────────────────────────────────────────────────
class ColorReaderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("🎨 Layer Reader")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setFixedSize(300, 450)
        self.setStyleSheet("background: #080018; border: 2px solid #00f3ff;")

        layout = QVBoxLayout(self)
        
        self.lbl_info = QLabel("NHẤN 🎯 ĐỂ CHỌN VÙNG LAYER")
        self.lbl_info.setStyleSheet("color: #ffff00; font-weight: bold; font-size: 11px;")
        self.lbl_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_info)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll)
        
        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.container)

        btn_row = QHBoxLayout()
        
        self.btn_calib = QPushButton("🎯 Mục tiêu")
        self.btn_calib.setToolTip("Quét chuột qua vùng danh sách Layer")
        self.btn_calib.clicked.connect(self.start_calibration)
        btn_row.addWidget(self.btn_calib)

        self.btn_read = QPushButton("🔍 Đọc Layer")
        self.btn_read.clicked.connect(self.run_read)
        btn_row.addWidget(self.btn_read)
        
        layout.addLayout(btn_row)
        
        self.setStyleSheet(self.styleSheet() + """
            QPushButton { 
                background: #110022; color: #00f3ff; border: 1px solid #00f3ff; 
                padding: 5px; font-weight: bold;
            }
            QPushButton:hover { background: #00f3ff; color: black; }
        """)

    def start_calibration(self):
        self.hide()
        # Đợi một chút để cửa sổ ẩn hẳn
        QTimer.singleShot(200, self._show_selector)

    def _show_selector(self):
        self.selector = RegionSelector()
        self.selector.selected.connect(self._on_calibrated)
        self.selector.show()

    def _on_calibrated(self, rect):
        self.show()
        self.lbl_info.setText("ĐÃ CĂN CHỈNH VÙNG")
        self.run_read()

    def run_read(self):
        self.btn_read.setEnabled(False)
        self.lbl_info.setText("Đang tập trung vào Layer...")
        
        self.worker = ColorReadWorker()
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_finished(self, colors, error):
        self.btn_read.setEnabled(True)
        if error:
            self.lbl_info.setText(error)
            return
            
        self.lbl_info.setText(f"TÌM THẤY {len(colors)} LAYERS")
        # Xóa cũ
        while self.list_layout.count():
            self.list_layout.takeAt(0).widget().deleteLater()
            
        for c in colors:
            row = QFrame()
            row.setFixedHeight(30)
            row.setStyleSheet("background: rgba(255,255,255,10); border: 1px solid #333;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(5,0,5,0)
            
            sw = QLabel()
            sw.setFixedSize(16, 16)
            pix = QPixmap(16, 16)
            pix.fill(QColor(*c['rgb']))
            sw.setPixmap(pix)
            
            txt = QLabel(f"Layer {c['index']} - {c['hex'].upper()}")
            txt.setStyleSheet("color: white; font-size: 10px;")
            
            rl.addWidget(sw)
            rl.addWidget(txt)
            self.list_layout.addWidget(row)
