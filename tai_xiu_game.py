"""
Tai Xiu LAN Game, Bầu Cua, 777 Slots, Caro XO & LAN Word Chaining
- Stacked widget name input screen (no blocking dialogs to prevent freezes)
- LAN Word Chaining (Nối Chữ) - Multiplayer over LAN
- Points detail saved per game in tx_profile.json
- Trophy 🏆 button for leaderboard & personal points breakdown
"""
import sys, os, socket, random, threading, time, json
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QApplication, QDialog, QSpinBox, QListWidget,
    QComboBox, QMessageBox, QLineEdit, QStackedWidget, QProgressBar, QGridLayout, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QConicalGradient

from tx_network import GameHost, GameClient, discover_host

# ─── Sound System 🔊 ──────────────────────────────────────────────────
try:
    import winsound
    HAS_SOUND = True
except:
    HAS_SOUND = False

def play_sound_win():
    if HAS_SOUND:
        threading.Thread(target=lambda: [winsound.Beep(800, 100), winsound.Beep(1200, 150)], daemon=True).start()

def play_sound_lose():
    if HAS_SOUND:
        threading.Thread(target=lambda: winsound.Beep(350, 250), daemon=True).start()

def play_sound_click():
    if HAS_SOUND:
        threading.Thread(target=lambda: winsound.Beep(650, 50), daemon=True).start()


# ─── Xo So Music System 🎵 ───────────────────────────────────────────
HAS_MULTIMEDIA = False
try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PySide6.QtCore import QUrl
    HAS_MULTIMEDIA = True
except ImportError:
    pass

class XoSoMusicPlayer:
    def __init__(self):
        self.player = None
        self.audio_output = None
        if HAS_MULTIMEDIA:
            try:
                self.player = QMediaPlayer()
                self.audio_output = QAudioOutput()
                self.player.setAudioOutput(self.audio_output)
                self.audio_output.setVolume(0.8)  # 80% volume
                try:
                    self.player.setLoops(-1) # Loop infinitely
                except:
                    pass
                
                # Check for localized or absolute path
                abs_path = r"c:\Users\Tx\Desktop\vibecoder\ChestEMB\Xổ Số.mp3"
                if os.path.exists(abs_path):
                    self.player.setSource(QUrl.fromLocalFile(abs_path))
                else:
                    if getattr(sys, 'frozen', False):
                        mp3_path = os.path.join(sys._MEIPASS, "Xổ Số.mp3")
                    else:
                        mp3_path = os.path.join(os.path.dirname(__file__), "Xổ Số.mp3")
                    if os.path.exists(mp3_path):
                        self.player.setSource(QUrl.fromLocalFile(mp3_path))
            except Exception as e:
                print(f"Error initializing QMediaPlayer: {e}")

    def play(self):
        if self.player:
            try:
                from PySide6.QtMultimedia import QMediaPlayer
                if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    return
            except:
                pass
            try:
                self.player.setPosition(0)
                self.player.play()
            except Exception as e:
                print(f"Error playing music: {e}")

    def stop(self):
        if self.player:
            try:
                self.player.stop()
            except Exception as e:
                print(f"Error stopping music: {e}")

_xo_so_player = None

def play_xo_so_music():
    global _xo_so_player
    if _xo_so_player is None:
        _xo_so_player = XoSoMusicPlayer()
    _xo_so_player.play()

def stop_xo_so_music():
    global _xo_so_player
    if _xo_so_player:
        _xo_so_player.stop()


if getattr(sys, 'frozen', False):
    PROFILE_PATH = os.path.join(os.path.dirname(sys.executable), "tx_profile.json")
else:
    PROFILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tx_profile.json")

# ─── Profile Storage ──────────────────────────────────────────────────
def load_profile():
    today = datetime.now().strftime("%Y-%m-%d")
    default_profile = {
        "username": "",
        "points": 10000,
        "last_claim_date": today,
        "game_scores": {
            "taixiu": 0,
            "baucua": 0,
            "slots": 0,
            "caro": 0,
            "noichu": 0
        }
    }
    try:
        if os.path.exists(PROFILE_PATH):
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "game_scores" not in data:
                data["game_scores"] = default_profile["game_scores"]
            
            # Daily reset
            if data.get("last_claim_date") != today:
                data["points"] = 10000
                data["last_claim_date"] = today
                save_profile(data)
            return data
    except Exception as e:
        print(f"Error loading profile: {e}")
    save_profile(default_profile)
    return default_profile

def save_profile(data):
    try:
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving profile: {e}")


# ─── Name Input Screen ✍️ ──────────────────────────────────────────
class NameInputDialog(QDialog):
    def __init__(self, current_name="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Đăng Ký Biệt Danh")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(260, 160)
        self.setStyleSheet("""
            QDialog { background: #0c0018; border: 2px solid #ff00ff; border-radius: 8px; }
            QLabel { color: #ff00ff; font-family: 'Consolas'; font-size: 11px; font-weight: bold; }
            QLineEdit { background: #000; color: #00ffcc; border: 1.5px solid #00ffcc; border-radius: 4px; padding: 4px; font-size: 12px; }
            QPushButton { background: #220044; border: 1.5px solid #ff00ff; color: #ff00ff; font-weight: bold; border-radius: 4px; padding: 6px; }
            QPushButton:hover { background: #3c0066; color: #fff; }
        """)
        
        lay = QVBoxLayout(self)
        lay.setSpacing(10); lay.setContentsMargins(15,15,15,15)

        lbl = QLabel("✍️ NHẬP BIỆT DANH ĐỂ VÀO GAME:")
        lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl)

        self.le_name = QLineEdit(current_name)
        self.le_name.setPlaceholderText("Nhập tên của bạn...")
        self.le_name.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.le_name)

        btn_ok = QPushButton("🎮 VÀO TRÒ CHƠI")
        btn_ok.clicked.connect(self._accept)
        lay.addWidget(btn_ok)

        self.username = ""

    def _accept(self):
        name = self.le_name.text().strip()
        if len(name) < 2:
            QMessageBox.warning(self, "Lỗi", "Tên phải chứa ít nhất 2 ký tự!")
            return
        if name.upper() == "TX" or name.upper() == "ADMIN":
            self.username = "TX"
        else:
            self.username = name
        self.accept()


# ─── Leaderboard / Trophy Dialog 🏆 ──────────────────────────────────
class LeaderboardDialog(QDialog):
    def __init__(self, scores: dict, game_scores: dict, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.scores = scores
        self.game_scores_breakdown = {}
        if parent and parent.current_state:
            self.game_scores_breakdown = parent.current_state.get("game_scores", {})
            
        self.setWindowTitle("🏆 Bảng Vàng Danh Vọng")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(300, 400)
        self.setStyleSheet("""
            QDialog { background: #0a0014; border: 2px solid #ffcc00; border-radius: 8px; }
            QLabel { color: #ffcc00; font-family: 'Consolas'; font-size: 11px; }
            QPushButton { background: #1a0033; border: 1.5px solid #ffcc00; color: #ffcc00;
                font-weight: bold; font-size: 10px; padding: 4px; border-radius: 4px; }
            QPushButton:hover { background: #330055; color: #fff; }
            QComboBox { background: #0a0014; border: 1px solid #ffcc00; color: #ffcc00;
                font-size: 10px; padding: 2px; }
            QListWidget { background: #060010; border: 1px solid #2a1a00; color: #00ffcc;
                font-size: 10px; border-radius: 4px; }
            QListWidget::item:selected { background: #1a0033; }
        """)
        lay = QVBoxLayout(self)
        lay.setSpacing(6); lay.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("🏆  AI LÀ VUA LÌ ĐÒN  🏆")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 12px; font-weight: bold; color: #ffcc00;"
                            "background: #1a0a00; border: 1px solid #ffcc00;"
                            "border-radius: 4px; padding: 3px;")
        lay.addWidget(title)

        # Filter
        filter_lay = QHBoxLayout()
        filter_lay.addWidget(QLabel("Lọc theo:"))
        self.cb_filter = QComboBox()
        self.cb_filter.addItems([
            "🏅 Tổng Điểm",
            "🎲 Tài Xỉu LAN",
            "🦀 Bầu Cua Tôm Cá",
            "🎰 Vòng Quay 777",
            "⬜ Caro XO",
            "✍️ Nối Chữ LAN"
        ])
        self.cb_filter.currentIndexChanged.connect(self._update_leaderboard)
        filter_lay.addWidget(self.cb_filter, 1)
        lay.addLayout(filter_lay)

        # Leaderboard list
        self.score_list = QListWidget()
        self.score_list.setWordWrap(True)
        lay.addWidget(self.score_list, 1)

        # Personal breakdown
        lbl_detail = QLabel("📊 ĐIỂM CỦA BẠN THEO TỪNG GAME:")
        lbl_detail.setStyleSheet("color: #aaaaaa; font-size: 9px;")
        lay.addWidget(lbl_detail)

        self.detail_list = QListWidget()
        self.detail_list.setFixedHeight(82)
        self.game_names = {
            "taixiu": ("🎲", "Tài Xỉu LAN"),
            "baucua": ("🦀", "Bầu Cua"),
            "slots":  ("🎰", "Vòng Quay 777"),
            "caro":   ("⬜", "Caro XO"),
            "noichu": ("✍️", "Nối Chữ LAN"),
        }
        total_gs = 0
        for k, (ico, name) in self.game_names.items():
            val = game_scores.get(k, 0)
            total_gs += val
            color_txt = "+" if val >= 0 else ""
            item_text = f" {ico} {name:<14}: {color_txt}{val}"
            self.detail_list.addItem(item_text)
        # Total row
        total_item = f" 🏆 TỔNG TẤT CẢ GAME : {'+' if total_gs>=0 else ''}{total_gs}"
        self.detail_list.addItem(total_item)
        # Style the last (total) item
        last = self.detail_list.item(self.detail_list.count() - 1)
        if last:
            last.setForeground(__import__('PySide6.QtGui', fromlist=['QColor']).QColor("#ffcc00"))
        lay.addWidget(self.detail_list)

        # Buttons
        btn_lay = QHBoxLayout()
        is_admin = (parent and getattr(parent, "is_admin", False))
        if is_admin:
            self.btn_reset = QPushButton("🗑️ Reset Bảng")
            self.btn_reset.setStyleSheet("background: #440011; border-color: #ff3366; color: #ff3366;")
            self.btn_reset.clicked.connect(self._reset_leaderboard)
            btn_lay.addWidget(self.btn_reset)
        self.btn_close = QPushButton("✕ Đóng")
        self.btn_close.clicked.connect(self.close)
        btn_lay.addWidget(self.btn_close)
        lay.addLayout(btn_lay)

        self._update_leaderboard()

    def _update_leaderboard(self):
        self.score_list.clear()
        medals = ["🥇", "🥈", "🥉"]
        idx = self.cb_filter.currentIndex()
        keys = [None, "taixiu", "baucua", "slots", "caro", "noichu"]

        if idx == 0:
            # Total scores
            sorted_scores = sorted(self.scores.items(), key=lambda x: -x[1])
            for i, (name, pts) in enumerate(sorted_scores):
                medal = medals[i] if i < 3 else f" #{i+1}"
                sign = "+" if pts >= 0 else ""
                item = __import__('PySide6.QtWidgets', fromlist=['QListWidgetItem']).QListWidgetItem(
                    f" {medal}  {name}  →  {sign}{pts}đ"
                )
                if i == 0:
                    item.setForeground(__import__('PySide6.QtGui', fromlist=['QColor']).QColor("#ffcc00"))
                elif i == 1:
                    item.setForeground(__import__('PySide6.QtGui', fromlist=['QColor']).QColor("#cccccc"))
                elif i == 2:
                    item.setForeground(__import__('PySide6.QtGui', fromlist=['QColor']).QColor("#cc8844"))
                self.score_list.addItem(item)
        else:
            game_key = keys[idx]
            player_scores = []
            for name in self.scores:
                val = self.game_scores_breakdown.get(name, {}).get(game_key, 0)
                player_scores.append((name, val))
            sorted_scores = sorted(player_scores, key=lambda x: -x[1])
            for i, (name, pts) in enumerate(sorted_scores):
                medal = medals[i] if i < 3 else f" #{i+1}"
                sign = "+" if pts >= 0 else ""
                item = __import__('PySide6.QtWidgets', fromlist=['QListWidgetItem']).QListWidgetItem(
                    f" {medal}  {name}  →  {sign}{pts}đ"
                )
                if i == 0:
                    item.setForeground(__import__('PySide6.QtGui', fromlist=['QColor']).QColor("#ffcc00"))
                elif i == 1:
                    item.setForeground(__import__('PySide6.QtGui', fromlist=['QColor']).QColor("#cccccc"))
                elif i == 2:
                    item.setForeground(__import__('PySide6.QtGui', fromlist=['QColor']).QColor("#cc8844"))
                self.score_list.addItem(item)

    def _reset_leaderboard(self):
        reply = QMessageBox.question(
            self, "Xác nhận",
            "Bạn có chắc muốn Reset toàn bộ điểm số về 10,000 không?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.parent_window and self.parent_window.net:
                self.parent_window.net.admin_reset_scores()
                QMessageBox.information(self, "Thành công", "Đã reset toàn bộ điểm số!")
                self.close()


# ─── Dice Widget ─────────────────────────────────────────────────────
class DiceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(48, 48)
        self.value = 0
        self._anim = False
        self._anim_count = 0
        self._final = 1
        self._on_done = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def roll_animate(self, final_val, on_done=None):
        self._final = final_val
        self._on_done = on_done
        self._anim_count = 0
        self._anim = True
        self._timer.start(60)

    def _tick(self):
        self._anim_count += 1
        self.value = random.randint(1, 6)
        self.update()
        if self._anim_count >= 15:
            self._timer.stop()
            self.value = self._final
            self._anim = False
            self.update()
            if self._on_done:
                self._on_done()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg = QColor("#221133") if self._anim else QColor("#110522")
        p.setBrush(bg)
        p.setPen(QPen(QColor("#00ffcc"), 1.5))
        p.drawRoundedRect(2, 2, 44, 44, 8, 8)
        if not self.value:
            p.end(); return
        dots = {
            1: [(24,24)],
            2: [(13,13),(35,35)],
            3: [(13,13),(24,24),(35,35)],
            4: [(13,13),(35,13),(13,35),(35,35)],
            5: [(13,13),(35,13),(24,24),(13,35),(35,35)],
            6: [(13,13),(35,13),(13,24),(35,24),(13,35),(35,35)],
        }
        p.setBrush(QColor("#00ffcc"))
        p.setPen(Qt.NoPen)
        for x, y in dots.get(self.value, []):
            p.drawEllipse(x-4, y-4, 8, 8)
        p.end()


# ─── History Circle Widget ───────────────────────────────────────────
class HistoryCircle(QWidget):
    def __init__(self, result_type: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(18, 18)
        self.result_type = result_type

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self.result_type == "Tai":
            p.setBrush(QColor("#000000"))
            p.setPen(QPen(QColor("#ffffff"), 1.5))
        elif self.result_type == "Xiu":
            p.setBrush(QColor("#ffffff"))
            p.setPen(QPen(QColor("#aaaaaa"), 1))
        elif self.result_type == "Bao":
            p.setBrush(QColor("#ff00ff"))
            p.setPen(QPen(QColor("#ffffff"), 1))
        else:
            p.setBrush(QColor("#00ff41"))
            p.setPen(Qt.NoPen)
        p.drawEllipse(1, 1, 15, 15)
        p.end()


# ─── Admin Panel ─────────────────────────────────────────────────────
class AdminPanel(QDialog):
    def __init__(self, net, state: dict, parent=None):
        super().__init__(parent)
        self.net = net
        self.setWindowTitle("Admin Panel")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setFixedWidth(280)
        self.setStyleSheet("""
            QDialog { background: #0c0018; border: 2px solid #00ffcc; border-radius: 8px; }
            QLabel { color: #00ffcc; font-family: 'Consolas'; font-size: 11px; }
            QPushButton { background: #1a0230; border: 1px solid #00ffcc; color: #00ffcc;
                font-weight: bold; font-size: 10px; padding: 4px 8px; border-radius: 4px; }
            QPushButton:hover { background: #2f0454; }
            QSpinBox, QComboBox { background: #060010; border: 1px solid #00ffcc;
                color: #00ffcc; font-size: 10px; padding: 2px; }
        """)
        self._drag_pos = None
        lay = QVBoxLayout(self)
        lay.setSpacing(8); lay.setContentsMargins(12,12,12,12)

        title = QLabel("⚙️ THAO TÚNG TRẬN ĐẤU")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 12px; color: #ff00ff;")
        lay.addWidget(title)

        lay.addWidget(QLabel("Thiết lập xúc sắc tiếp theo:"))
        d_row = QHBoxLayout()
        self.d1 = QSpinBox(); self.d1.setRange(1,6); self.d1.setValue(4)
        self.d2 = QSpinBox(); self.d2.setRange(1,6); self.d2.setValue(5)
        self.d3 = QSpinBox(); self.d3.setRange(1,6); self.d3.setValue(6)
        for w in (self.d1, self.d2, self.d3):
            w.setFixedWidth(44)
            d_row.addWidget(w)
        lay.addLayout(d_row)

        btn_pub = QPushButton("📢 Lập tức công bố kết quả")
        btn_pub.clicked.connect(self._publish)
        lay.addWidget(btn_pub)

        lay.addWidget(QLabel("── Cộng/Trừ điểm người chơi ──"))
        sc_row = QHBoxLayout()
        self.cb_player = QComboBox()
        players = list(state.get("scores", {}).keys())
        self.cb_player.addItems(players)
        self.sp_pts = QSpinBox(); self.sp_pts.setRange(-9999,9999); self.sp_pts.setValue(500)
        btn_add = QPushButton("+ Điểm")
        btn_add.clicked.connect(self._add_score)
        sc_row.addWidget(self.cb_player, 1); sc_row.addWidget(self.sp_pts); sc_row.addWidget(btn_add)
        lay.addLayout(sc_row)

        lay.addWidget(QLabel("── Trình điều khiển ──"))
        btn_reset = QPushButton("🔄 Reset Vòng Mới")
        btn_reset.clicked.connect(self._reset)
        lay.addWidget(btn_reset)

        btn_close = QPushButton("✕ Đóng")
        btn_close.clicked.connect(self.close)
        lay.addWidget(btn_close)

    def mousePressEvent(self, event):
        child = self.childAt(event.pos())
        if child is None or child == self:
            if event.button() == Qt.LeftButton:
                try:
                    self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                except AttributeError:
                    self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            try:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
            except AttributeError:
                self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def update_players(self, players):
        current_sel = self.cb_player.currentText()
        self.cb_player.clear()
        self.cb_player.addItems(players)
        idx = self.cb_player.findText(current_sel)
        if idx >= 0:
            self.cb_player.setCurrentIndex(idx)

    def _publish(self):
        if self.net:
            dice = [self.d1.value(), self.d2.value(), self.d3.value()]
            self.net.admin_result(dice)

    def _add_score(self):
        if self.net:
            player = self.cb_player.currentText()
            pts = self.sp_pts.value()
            if player:
                self.net.admin_add_score(player, pts)

    def _reset(self):
        if self.net:
            self.net.admin_reset()


# ─── Bầu Cua Widget ───────────────────────────────────────────────────
class BauCuaWidget(QWidget):
    def __init__(self, parent_window, parent=None):
        super().__init__(parent)
        self.parent_window = parent_window
        self.symbols = {
            "Nai": "🦌", "Bầu": "🥒", "Gà": "🐓", "Cá": "🐟", "Cua": "🦀", "Tôm": "🍤"
        }
        self.active_bets = {k: 0 for k in self.symbols}
        self._roll_timer = QTimer(self)
        self._roll_timer.timeout.connect(self._tick_roll)
        self._roll_count = 0
        self._final_results = []
        
        self.setStyleSheet("""
            QLabel { color: #00ffcc; font-family: 'Consolas'; }
            QPushButton { background: #0c0018; border: 1.5px solid #00ffcc; color: #00ffcc;
                font-weight: bold; border-radius: 6px; font-size: 10px; padding: 4px; }
            QPushButton:hover { background: #23003a; }
        """)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4,4,4,4); lay.setSpacing(4)

        title = QLabel("🦀 BẦU CUA TÔM CÁ (LAN) 🦀")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 11px; color: #ff00ff; font-weight: bold;")
        lay.addWidget(title)

        roll_lay = QHBoxLayout(); roll_lay.setSpacing(6); roll_lay.addStretch()
        self.roll_labels = [QLabel("❓") for _ in range(3)]
        for lbl in self.roll_labels:
            lbl.setFixedSize(36, 36)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("background: #110022; border: 2px solid #00ffcc; border-radius: 6px; font-size: 20px;")
            roll_lay.addWidget(lbl)
        roll_lay.addStretch()
        lay.addLayout(roll_lay)

        grid_lay = QGridLayout()
        grid_lay.setSpacing(4)
        self.btns = {}
        row, col = 0, 0
        for name, emoji in self.symbols.items():
            btn = QPushButton(f"{emoji} {name}")
            btn.setFixedSize(85, 34)
            btn.clicked.connect(lambda _, n=name: self._click_bet(n))
            grid_lay.addWidget(btn, row, col)
            self.btns[name] = btn
            col += 1
            if col > 2:
                col = 0; row += 1
        lay.addLayout(grid_lay)

        bet_lay = QHBoxLayout()
        bet_lay.addWidget(QLabel("Đặt:"))
        self.sp_bet = QSpinBox()
        self.sp_bet.setRange(10, 999999999)
        self.sp_bet.setValue(100)
        self.sp_bet.setStyleSheet("background: #000; color: #00ffcc; border: 1px solid #00ffcc;")
        bet_lay.addWidget(self.sp_bet, 1)
        
        btn_all = QPushButton("Tất tay")
        btn_all.setFixedWidth(50)
        btn_all.clicked.connect(self._all_in)
        bet_lay.addWidget(btn_all)
        lay.addLayout(bet_lay)

        act_lay = QHBoxLayout()
        self.btn_play = QPushButton("🎲 LẮC 🎲")
        self.btn_play.setFixedHeight(28)
        self.btn_play.setStyleSheet("background: #220044; border-color: #ff00ff; color: #ff00ff;")
        self.btn_play.clicked.connect(self._play)
        
        self.btn_clear = QPushButton("🗑️ Xóa cược")
        self.btn_clear.setFixedHeight(28)
        self.btn_clear.setStyleSheet("background: #330011; border-color: #ff3366; color: #ff3366;")
        self.btn_clear.clicked.connect(self._clear_all_bets)
        
        act_lay.addWidget(self.btn_play, 2)
        act_lay.addWidget(self.btn_clear, 1)
        lay.addLayout(act_lay)

        self.lbl_info = QLabel("Click vào linh vật để đặt điểm cược!")
        self.lbl_info.setAlignment(Qt.AlignCenter)
        self.lbl_info.setStyleSheet("color: #888; font-size: 8px;")
        lay.addWidget(self.lbl_info)

    def _click_bet(self, name):
        bet_val = self.sp_bet.value()
        profile = load_profile()
        if profile["points"] < bet_val:
            QMessageBox.warning(self, "Lỗi", "Không đủ điểm!")
            return
        
        profile["points"] -= bet_val
        profile["game_scores"]["baucua"] = profile["game_scores"].get("baucua", 0) - bet_val
        save_profile(profile)
        
        self.active_bets[name] += bet_val
        self.parent_window.local_points = profile["points"]
        self.parent_window.lbl_my_score.setText(f"Điểm: {profile['points']}")
        
        emoji = self.symbols[name]
        self.btns[name].setText(f"{emoji} {name}\n{self.active_bets[name]}đ")
        self.btns[name].setStyleSheet("background: #330055; border: 1.5px solid #ff00ff; color: #ff00ff;")
        
        play_sound_click()
        
        if self.parent_window.net:
            self.parent_window.sync_points_to_server(profile["points"])

    def _clear_all_bets(self):
        total_refund = sum(self.active_bets.values())
        if total_refund == 0:
            return
        
        profile = load_profile()
        profile["points"] += total_refund
        profile["game_scores"]["baucua"] = profile["game_scores"].get("baucua", 0) + total_refund
        save_profile(profile)
        
        self.parent_window.local_points = profile["points"]
        self.parent_window.lbl_my_score.setText(f"Điểm: {profile['points']}")
        
        for k in self.symbols:
            self.active_bets[k] = 0
            emoji = self.symbols[k]
            self.btns[k].setText(f"{emoji} {k}")
            self.btns[k].setStyleSheet("")
        
        self.lbl_info.setText("Đã xóa và hoàn lại toàn bộ điểm cược!")
        self.lbl_info.setStyleSheet("color: #888; font-size: 8px;")
        
        if self.parent_window.net:
            self.parent_window.sync_points_to_server(profile["points"])

    def _all_in(self):
        self.sp_bet.setValue(max(10, self.parent_window.local_points))

    def _play(self):
        total_bet = sum(self.active_bets.values())
        if total_bet == 0:
            QMessageBox.warning(self, "Lỗi", "Vui lòng click đặt cược vào ít nhất một linh vật!")
            return

        self.btn_play.setEnabled(False)
        self.btn_clear.setEnabled(False)
        for k in self.btns:
            self.btns[k].setEnabled(False)

        play_xo_so_music()

        choices = list(self.symbols.keys())
        self._final_results = [random.choice(choices) for _ in range(3)]
        self._roll_count = 0
        self._roll_timer.start(100)

    def _tick_roll(self):
        self._roll_count += 1
        choices = list(self.symbols.keys())
        for i in range(3):
            random_name = random.choice(choices)
            self.roll_labels[i].setText(self.symbols[random_name])

        if self._roll_count >= 15:
            self._roll_timer.stop()
            stop_xo_so_music()

            for i in range(3):
                self.roll_labels[i].setText(self.symbols[self._final_results[i]])

            total_bet = sum(self.active_bets.values())
            total_winnings = 0
            details = []
            for name, bet_amt in self.active_bets.items():
                if bet_amt > 0:
                    match_cnt = self._final_results.count(name)
                    if match_cnt > 0:
                        win = bet_amt * (match_cnt + 1)
                        total_winnings += win
                        details.append(f"{self.symbols[name]}x{match_cnt}(+{win}đ)")
                    else:
                        details.append(f"{self.symbols[name]}(Trượt)")

            profile = load_profile()
            if total_winnings > 0:
                fee = int(total_winnings * 0.03)
                net_reward = total_winnings - fee
                profile["points"] += net_reward
                profile["game_scores"]["baucua"] = profile["game_scores"].get("baucua", 0) + (net_reward - total_bet)
                save_profile(profile)
                self.parent_window.local_points = profile["points"]
                self.parent_window.lbl_my_score.setText(f"Điểm: {profile['points']}")
                
                play_sound_win()
                self.lbl_info.setText(f"🎉 Kết quả: {', '.join(details)} | Nhận: +{net_reward}đ (phí {fee}đ)")
                self.lbl_info.setStyleSheet("color: #00ff99; font-size: 8px; font-weight: bold;")
            else:
                play_sound_lose()
                profile["game_scores"]["baucua"] = profile["game_scores"].get("baucua", 0) - total_bet
                save_profile(profile)
                self.lbl_info.setText(f"❌ Kết quả: {', '.join(details)} | Thất bại -{total_bet}đ")
                self.lbl_info.setStyleSheet("color: #ff3366; font-size: 8px; font-weight: bold;")

            for k in self.symbols:
                self.active_bets[k] = 0
                emoji = self.symbols[k]
                self.btns[k].setText(f"{emoji} {k}")
                self.btns[k].setStyleSheet("")

            if self.parent_window.net:
                self.parent_window.sync_points_to_server(profile["points"])

            self.btn_play.setEnabled(True)
            self.btn_clear.setEnabled(True)
            for k in self.btns:
                self.btns[k].setEnabled(True)


# ─── Slots 777 Widget ───────────────────────────────────────────────
class SlotsWidget(QWidget):
    def __init__(self, parent_window, parent=None):
        super().__init__(parent)
        self.parent_window = parent_window
        self.setStyleSheet("""
            QLabel { color: #ff00ff; font-family: 'Consolas'; font-weight: bold; }
            QPushButton { background: #330033; border: 1.5px solid #ff00ff; color: #ff00ff;
                font-weight: bold; border-radius: 6px; }
            QPushButton:hover { background: #550055; color: #fff; }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6,6,6,6); lay.setSpacing(6)

        title = QLabel("🎰 VÒNG QUAY 777 🎰")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 12px; color: #00ffcc;")
        lay.addWidget(title)

        self.wheel_row = QHBoxLayout(); self.wheel_row.setSpacing(8)
        self.wheels = [QLabel("7") for _ in range(3)]
        for w in self.wheels:
            w.setFixedSize(55, 55)
            w.setAlignment(Qt.AlignCenter)
            w.setStyleSheet("""
                background: #110022; border: 2px solid #ff00ff; border-radius: 8px;
                font-size: 24px; font-weight: bold; color: #ffff00;
            """)
            self.wheel_row.addWidget(w)
        lay.addLayout(self.wheel_row)

        bet_lay = QHBoxLayout()
        bet_lay.addWidget(QLabel("Cược:"))
        self.sp_bet = QSpinBox()
        self.sp_bet.setRange(10, 999999999)
        self.sp_bet.setValue(100)
        self.sp_bet.setStyleSheet("background: #000; color: #00ffcc; border: 1px solid #ff00ff; padding: 1px;")
        bet_lay.addWidget(self.sp_bet, 1)

        btn_all = QPushButton("Tất tay")
        btn_all.setFixedWidth(50)
        btn_all.clicked.connect(self._all_in)
        bet_lay.addWidget(btn_all)
        lay.addLayout(bet_lay)

        self.cb_skip_anim = QCheckBox("⚡ Bỏ qua hoạt ảnh")
        self.cb_skip_anim.setStyleSheet("color: #00ffcc; font-size: 10px; font-weight: bold;")
        lay.addWidget(self.cb_skip_anim)

        self.btn_spin = QPushButton("🎰 QUAY 🎰")
        self.btn_spin.setFixedHeight(30)
        self.btn_spin.clicked.connect(self._spin)
        lay.addWidget(self.btn_spin)

        self.lbl_info = QLabel("Quay 3 số giống nhau để thắng lớn!")
        self.lbl_info.setAlignment(Qt.AlignCenter)
        self.lbl_info.setStyleSheet("color: #aaa; font-size: 8px;")
        lay.addWidget(self.lbl_info)

        self.symbols = ["🍒", "🍋", "🍇", "💎", "7"]
        self._spin_timer = QTimer(self)
        self._spin_timer.timeout.connect(self._tick_spin)
        self._spin_count = 0

    def _all_in(self):
        self.sp_bet.setValue(max(10, self.parent_window.local_points))

    def _spin(self):
        profile = load_profile()
        bet_amt = self.sp_bet.value()
        if profile["points"] < bet_amt:
            QMessageBox.warning(self, "Lỗi", "Không đủ điểm!")
            return
        
        profile["points"] -= bet_amt
        profile["game_scores"]["slots"] = profile["game_scores"].get("slots", 0) - bet_amt
        save_profile(profile)
        self.parent_window.local_points = profile["points"]
        self.parent_window.lbl_my_score.setText(f"Điểm: {profile['points']}")

        if self.cb_skip_anim.isChecked():
            for w in self.wheels:
                w.setText(random.choice(self.symbols))
            self._calculate_win()
        else:
            self.btn_spin.setEnabled(False)
            self._spin_count = 0
            play_xo_so_music()
            self._spin_timer.start(80)

    def _tick_spin(self):
        self._spin_count += 1
        for w in self.wheels:
            w.setText(random.choice(self.symbols))
        if self._spin_count >= 12:
            self._spin_timer.stop()
            stop_xo_so_music()
            self._calculate_win()

    def _calculate_win(self):
        results = [w.text() for w in self.wheels]
        bet_amt = self.sp_bet.value()
        profile = load_profile()

        win_factor = 0
        if results[0] == results[1] == results[2]:
            win_factor = 15 if results[0] == "7" else 5
            self.lbl_info.setText(f"🔥 Thắng x{win_factor}! ({results[0]})")
        elif results[0] == results[1] or results[1] == results[2] or results[0] == results[2]:
            win_factor = 2
            self.lbl_info.setText("✨ Có đôi! Thắng x2!")
        else:
            self.lbl_info.setText("❌ Trượt rồi! Hãy thử lại.")

        if win_factor > 0:
            reward = bet_amt * win_factor
            fee = int(reward * 0.03)
            net_reward = reward - fee
            profile["points"] += net_reward
            profile["game_scores"]["slots"] = profile["game_scores"].get("slots", 0) + (net_reward - bet_amt)
            save_profile(profile)
            self.parent_window.local_points = profile["points"]
            self.parent_window.lbl_my_score.setText(f"Điểm: {profile['points']}")
            play_sound_win()
        else:
            play_sound_lose()
            profile["game_scores"]["slots"] = profile["game_scores"].get("slots", 0) - bet_amt
            save_profile(profile)

        self.btn_spin.setEnabled(True)
        if self.parent_window.net:
            self.parent_window.sync_points_to_server(profile["points"])


# ─── Caro XO Widget (Bot AI & Multiplayer LAN Matchmaking) ─────────────
class CaroXOWidget(QWidget):
    def __init__(self, parent_window, parent=None):
        super().__init__(parent)
        self.parent_window = parent_window
        self.grid_size = 8
        self.board = [["" for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.game_active = False
        self.suggested_cell = None
        
        # Matchmaking variables
        self.is_bot_game = True
        self.my_symbol = "X" # X goes first
        self.current_game_id = ""
        self.is_my_turn = False

        self.setStyleSheet("""
            QLabel { color: #00ffcc; font-family: 'Consolas'; }
            QPushButton { background: #080010; border: 1px solid #330066; color: #fff; font-size: 10px; font-weight: bold; }
            QPushButton:hover { background: #1a0033; }
            QCheckBox { color: #ff00ff; font-weight: bold; font-size: 9px; }
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(2,2,2,2); lay.setSpacing(2)

        title = QLabel("❌ CARO XO BATTLEGROUND ⭕")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 11px; color: #ff00ff; font-weight: bold;")
        lay.addWidget(title)

        # Config row: Bot/LAN checkbox
        config_lay = QHBoxLayout()
        self.cb_bot = QCheckBox("Chơi với nhà cái (Bot siêu khó)")
        self.cb_bot.setChecked(True)
        config_lay.addWidget(self.cb_bot)
        lay.addLayout(config_lay)

        bet_lay = QHBoxLayout()
        bet_lay.addWidget(QLabel("Cược:"))
        self.sp_bet = QSpinBox()
        self.sp_bet.setRange(10, 999999999)
        self.sp_bet.setValue(100)
        self.sp_bet.setStyleSheet("background: #000; color: #00ffcc; border: 1px solid #00ffcc;")
        bet_lay.addWidget(self.sp_bet, 1)

        btn_all = QPushButton("Tất tay")
        btn_all.setFixedWidth(50)
        btn_all.clicked.connect(self._all_in)
        bet_lay.addWidget(btn_all)
        lay.addLayout(bet_lay)

        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("🎮 Bắt Đầu")
        self.btn_start.clicked.connect(self._click_start)
        btn_row.addWidget(self.btn_start)

        self.btn_suggest = QPushButton("🧠 Gợi ý")
        self.btn_suggest.setStyleSheet("background: #120024; border: 1px solid #ff00ff; color: #ff00ff; font-size: 9px; padding: 2px 6px;")
        self.btn_suggest.clicked.connect(self._admin_suggest_move)
        self.btn_suggest.setVisible(False)
        btn_row.addWidget(self.btn_suggest)
        lay.addLayout(btn_row)

        self.board_widget = QWidget()
        self.grid_layout = QGridLayout(self.board_widget)
        self.grid_layout.setSpacing(1)
        self.grid_layout.setContentsMargins(0,0,0,0)
        self.buttons = []
        for r in range(self.grid_size):
            row_btns = []
            for c in range(self.grid_size):
                btn = QPushButton("")
                btn.setFixedSize(26, 26)
                btn.clicked.connect(lambda _, x=r, y=c: self._cell_clicked(x, y))
                self.grid_layout.addWidget(btn, r, c)
                row_btns.append(btn)
            self.buttons.append(row_btns)
        lay.addWidget(self.board_widget, 0, Qt.AlignCenter)

        self.lbl_info = QLabel("Chọn cược & Bắt Đầu. Thắng bot khó x2 điểm.")
        self.lbl_info.setAlignment(Qt.AlignCenter)
        self.lbl_info.setStyleSheet("color: #888; font-size: 8px;")
        lay.addWidget(self.lbl_info)

    def _all_in(self):
        self.sp_bet.setValue(max(10, self.parent_window.local_points))

    def _click_start(self):
        # 1. Local Bot Game
        self.is_bot_game = self.cb_bot.isChecked()
        if self.is_bot_game:
            bet_amt = self.sp_bet.value()
            profile = load_profile()
            if profile["points"] < bet_amt:
                QMessageBox.warning(self, "Lỗi", "Không đủ điểm!")
                return
            profile["points"] -= bet_amt
            profile["game_scores"]["caro"] = profile["game_scores"].get("caro", 0) - bet_amt
            save_profile(profile)
            self.parent_window.local_points = profile["points"]
            self.parent_window.lbl_my_score.setText(f"Điểm: {profile['points']}")

            self.board = [["" for _ in range(self.grid_size)] for _ in range(self.grid_size)]
            self.suggested_cell = None
            self._update_board_display()
            
            self.game_active = True
            self.my_symbol = "X"
            self.is_my_turn = True
            self.lbl_info.setText("Lượt đi của bạn (X).")
            self.btn_start.setText("🔄 Làm Lại")
            self.btn_suggest.setVisible(self.parent_window.profile["username"] == "TX")
            if self.parent_window.net:
                self.parent_window.sync_points_to_server(profile["points"])
        else:
            # 2. LAN Matchmaking Game
            if not self.parent_window.net:
                QMessageBox.warning(self, "Lỗi", "Không tìm thấy kết nối LAN!")
                return
            
            # If in active LAN game: Forfeit
            if self.current_game_id:
                reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc muốn đầu hàng/thoát trận đấu?", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    if self.parent_window.is_host:
                        self.parent_window.net.local_caro_forfeit(self.parent_window.profile["username"], self.current_game_id)
                    else:
                        self.parent_window.net.caro_forfeit(self.current_game_id)
                return

            # If in matchmaking queue: Leave queue
            if getattr(self, "is_queued", False):
                if self.parent_window.is_host:
                    self.parent_window.net.local_caro_leave(self.parent_window.profile["username"])
                else:
                    self.parent_window.net.caro_leave()
                return

            # Else: Join queue
            bet_amt = self.sp_bet.value()
            if self.parent_window.local_points < bet_amt:
                QMessageBox.warning(self, "Lỗi", "Không đủ điểm!")
                return

            self.lbl_info.setText("⏳ Đang tìm đối thủ LAN...")
            self.lbl_info.setStyleSheet("color: #ffff00; font-weight: bold;")
            
            if self.parent_window.is_host:
                self.parent_window.net.local_caro_join(self.parent_window.profile["username"], bet_amt)
            else:
                self.parent_window.net.caro_join(bet_amt)

    def _cell_clicked(self, r, c):
        if not self.game_active or self.board[r][c] != "":
            return

        if self.is_bot_game:
            if not self.is_my_turn: return
            self.board[r][c] = "X"
            self._update_board_display()
            self.suggested_cell = None

            if self._check_win_local("X"):
                self._end_local_game(True)
                return
            
            # Check draw
            if all(cell != "" for row in self.board for cell in row):
                self._end_local_game(draw=True)
                return

            self.is_my_turn = False
            self.lbl_info.setText("Nhà cái (AI) đang tính toán...")
            QTimer.singleShot(400, self._bot_ai_move)
        else:
            # LAN multiplayer game
            if not self.is_my_turn or not self.current_game_id: return
            
            # Send move to server
            if self.parent_window.is_host:
                self.parent_window.net.local_caro_move(self.parent_window.profile["username"], self.current_game_id, r, c)
            else:
                self.parent_window.net.caro_move(self.current_game_id, r, c)

    def _bot_ai_move(self):
        if not self.game_active:
            return
        
        best_score = -1
        best_move = None
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.board[r][c] == "":
                    # Block Player (X) and build own line (O)
                    score = self._evaluate_spot(r, c, "O") + self._evaluate_spot(r, c, "X") * 1.5
                    if score > best_score:
                        best_score = score
                        best_move = (r, c)

        if best_move:
            r, c = best_move
            self.board[r][c] = "O"
            self._update_board_display()
            
            if self._check_win_local("O"):
                self._end_local_game(False)
                return
            
            # Check draw
            if all(cell != "" for row in self.board for cell in row):
                self._end_local_game(draw=True)
                return
            
        self.is_my_turn = True
        self.lbl_info.setText("Lượt đi của bạn (X).")

    def _evaluate_spot(self, r, c, player):
        # We count the patterns of length 5 centered on (r, c)
        directions = [(1,0), (0,1), (1,1), (1,-1)]
        score = 0
        for dr, dc in directions:
            for i in range(5):
                win_cells = []
                valid = True
                for step in range(5):
                    idx = step - i
                    nr, nc = r + dr * idx, c + dc * idx
                    if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size:
                        win_cells.append(self.board[nr][nc])
                    else:
                        valid = False
                        break
                if not valid:
                    continue
                
                my_count = win_cells.count(player)
                opp_player = "X" if player == "O" else "O"
                opp_count = win_cells.count(opp_player)
                
                if opp_count > 0:
                    continue
                
                count = my_count + 1
                if count == 5:
                    score += 200000
                elif count == 4:
                    score += 20000
                elif count == 3:
                    score += 2000
                elif count == 2:
                    score += 200
                elif count == 1:
                    score += 20
        return score

    def _admin_suggest_move(self):
        if not self.game_active or not self.is_bot_game:
            return
        
        if self.suggested_cell:
            r, c = self.suggested_cell
            if self.board[r][c] == "":
                self._cell_clicked(r, c)
                return

        best_score = -1
        best_move = None
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.board[r][c] == "":
                    score = self._evaluate_spot(r, c, "X") * 1.8 + self._evaluate_spot(r, c, "O")
                    if score > best_score:
                        best_score = score
                        best_move = (r, c)
        
        if best_move:
            r, c = best_move
            self.suggested_cell = best_move
            self._update_board_display()
            self.buttons[r][c].setStyleSheet("background: #2a004d; border: 2px solid #ff00ff; color: #ff3366;")
            self.lbl_info.setText("💡 Gợi ý (Màu Tím). Ấn Gợi ý lần nữa để đi!")

    def _check_win_local(self, player):
        directions = [(1,0), (0,1), (1,1), (1,-1)]
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.board[r][c] != player:
                    continue
                for dr, dc in directions:
                    count = 1
                    for step in range(1, 5):
                        nr, nc = r + dr * step, c + dc * step
                        if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size and self.board[nr][nc] == player:
                            count += 1
                        else:
                            break
                    if count >= 5:
                        return True
        return False

    def _end_local_game(self, player_won=None, draw=False):
        self.game_active = False
        bet_amt = self.sp_bet.value()
        profile = load_profile()
        
        if draw:
            refund = int(bet_amt * 0.5)
            profile["points"] += refund
            profile["game_scores"]["caro"] = profile["game_scores"].get("caro", 0) - refund
            self.lbl_info.setText(f"🤝 HÒA! Bạn bị trừ 50% cược (-{refund}đ)")
            self.lbl_info.setStyleSheet("color: #ffaa00; font-size: 8px; font-weight: bold;")
        elif player_won:
            # Thắng nhà cái bot siêu khó được x2 điểm (payout = bet * 3 - phí)
            reward = bet_amt * 3
            fee = int(reward * 0.03)
            net_gain = reward - fee
            
            profile["points"] += net_gain
            profile["game_scores"]["caro"] = profile["game_scores"].get("caro", 0) + (net_gain - bet_amt)
            self.lbl_info.setText(f"🎉 THẮNG BOT! +{net_gain - bet_amt}đ (phí {fee}đ)")
            self.lbl_info.setStyleSheet("color: #00ff99; font-size: 8px; font-weight: bold;")
            play_sound_win()
        else:
            profile["game_scores"]["caro"] = profile["game_scores"].get("caro", 0) - bet_amt
            self.lbl_info.setText(f"💀 BẠN THUA! Mất -{bet_amt}đ")
            self.lbl_info.setStyleSheet("color: #ff3366; font-size: 8px; font-weight: bold;")
            play_sound_lose()
        
        save_profile(profile)
        self.parent_window.local_points = profile["points"]
        self.parent_window.lbl_my_score.setText(f"Điểm: {profile['points']}")

        if self.parent_window.net:
            self.parent_window.sync_points_to_server(profile["points"])
        self.btn_start.setText("🎮 Bắt Đầu")

    def _update_board_display(self):
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                val = self.board[r][c]
                self.buttons[r][c].setText(val)
                self.buttons[r][c].setEnabled(self.game_active and val == "")
                if val == "X":
                    self.buttons[r][c].setStyleSheet("color: #ff3366; font-size: 12px; font-weight: bold;")
                elif val == "O":
                    self.buttons[r][c].setStyleSheet("color: #00ffcc; font-size: 12px; font-weight: bold;")
                else:
                    self.buttons[r][c].setStyleSheet("")

    def apply_lan_state(self, games: dict, queue: list):
        # Look for our active game
        my_name = self.parent_window.profile["username"]
        my_game = None
        my_gid = ""
        for gid, g in games.items():
            if g["status"] == "playing" and (g["player_x"] == my_name or g["player_o"] == my_name):
                my_game = g
                my_gid = gid
                break
        
        if my_game:
            self.cb_bot.setEnabled(False)
            self.btn_start.setEnabled(True)
            self.is_queued = False
            self.game_active = True
            self.current_game_id = my_gid
            self.my_symbol = "X" if my_game["player_x"] == my_name else "O"
            self.board = my_game["board"]
            self.is_my_turn = (my_game["turn"] == my_name)
            
            opp_name = my_game["player_o"] if self.my_symbol == "X" else my_game["player_x"]
            bet_amt = my_game["bet_x"] if self.my_symbol == "X" else my_game["bet_o"]
            
            self._update_board_display()
            self.btn_start.setText("🏳️ Đầu Hàng")
            self.btn_start.setStyleSheet("background: #3c0000; border: 1.5px solid #ff3333; color: #ff3333; font-weight: bold;")
            
            # Highlight whose turn it is
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if self.board[r][c] == "" and self.is_my_turn:
                        self.buttons[r][c].setEnabled(True)
                    else:
                        self.buttons[r][c].setEnabled(False)
            
            if self.is_my_turn:
                self.lbl_info.setText(f"⚔️ Đối đầu {opp_name} ({self.my_symbol}) | Lượt Của BẠN!")
                self.lbl_info.setStyleSheet("color: #00ff99; font-weight: bold;")
            else:
                self.lbl_info.setText(f"⚔️ Đối đầu {opp_name} ({self.my_symbol}) | Lượt đối thủ...")
                self.lbl_info.setStyleSheet("color: #ff3366;")
        else:
            self.cb_bot.setEnabled(True)
            self.btn_start.setEnabled(True)
            self.current_game_id = ""
            
            # Check if we are in matchmaking queue
            is_queued = any(q["name"] == my_name for q in queue)
            self.is_queued = is_queued
            if is_queued:
                self.lbl_info.setText("⏳ Đang ghép đối thủ trên mạng LAN...")
                self.lbl_info.setStyleSheet("color: #ffff00; font-weight: bold;")
                self.game_active = False
                self.btn_start.setText("⏳ Đang tìm... (Hủy)")
                self.btn_start.setStyleSheet("background: #331a00; border: 1.5px solid #ffaa00; color: #ffaa00; font-weight: bold;")
                for r in range(self.grid_size):
                    for c in range(self.grid_size):
                        self.buttons[r][c].setEnabled(False)
            else:
                # Idle
                self.btn_start.setStyleSheet("")
                if not self.game_active:
                    self.lbl_info.setText("Chọn cược & Bắt Đầu. Thắng bot khó x2 điểm.")
                    self.lbl_info.setStyleSheet("color: #888;")
                    self.btn_start.setText("🎮 Bắt Đầu")
                    # Clear board
                    self.board = [["" for _ in range(self.grid_size)] for _ in range(self.grid_size)]
                    self._update_board_display()


# ─── LAN Nối Chữ Widget ───────────────────────────────────────────────
class LANNoiChuWidget(QWidget):
    def __init__(self, parent_window, parent=None):
        super().__init__(parent)
        self.parent_window = parent_window
        self.is_playing = False
        self.current_game_id = ""
        self.is_my_turn = False
        self.is_queued = False
        
        self.setStyleSheet("""
            QLabel { color: #00ffcc; font-family: 'Consolas'; }
            QPushButton { background: #0c0018; border: 1.5px solid #00ffcc; color: #00ffcc; font-weight: bold; border-radius: 4px; }
            QLineEdit { background: #000; color: #ffff00; border: 1px solid #ff00ff; border-radius: 4px; padding: 3px; }
            QListWidget { background: #060012; border: 1px solid #ff00ff; border-radius: 4px; color: #00ffcc; font-size: 10px; }
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(4,4,4,4); lay.setSpacing(4)

        title = QLabel("✍️ NỐI CHỮ LAN MULTIPLAYER ✍️")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 11px; color: #ff00ff; font-weight: bold;")
        lay.addWidget(title)

        self.lbl_curr_word = QLabel("SẴN SÀNG GHÉP TRẬN")
        self.lbl_curr_word.setAlignment(Qt.AlignCenter)
        self.lbl_curr_word.setStyleSheet("color: #00ffcc; font-size: 11px; font-weight: bold;")
        lay.addWidget(self.lbl_curr_word)

        bet_lay = QHBoxLayout()
        bet_lay.addWidget(QLabel("Cược:"))
        self.sp_bet = QSpinBox()
        self.sp_bet.setRange(10, 999999999)
        self.sp_bet.setValue(100)
        self.sp_bet.setStyleSheet("background: #000; color: #00ffcc; border: 1px solid #00ffcc;")
        bet_lay.addWidget(self.sp_bet, 1)
        
        btn_all = QPushButton("Tất tay")
        btn_all.setFixedWidth(50)
        btn_all.clicked.connect(self._all_in)
        bet_lay.addWidget(btn_all)
        lay.addLayout(bet_lay)

        self.btn_start = QPushButton("🎮 Tìm Trận đấu (LAN)")
        self.btn_start.setFixedHeight(24)
        self.btn_start.clicked.connect(self._click_start)
        lay.addWidget(self.btn_start)

        self.chat_list = QListWidget()
        self.chat_list.setWordWrap(True)
        lay.addWidget(self.chat_list)

        input_lay = QHBoxLayout()
        self.le_input = QLineEdit()
        self.le_input.setPlaceholderText("Gõ từ khi vào trận...")
        self.le_input.setEnabled(False)
        self.le_input.returnPressed.connect(self._send)
        self.btn_send = QPushButton("Gửi")
        self.btn_send.setFixedSize(50, 22)
        self.btn_send.setEnabled(False)
        self.btn_send.clicked.connect(self._send)
        input_lay.addWidget(self.le_input, 1)
        input_lay.addWidget(self.btn_send)
        lay.addLayout(input_lay)

        self.lbl_timer = QLabel("Thời gian: 15s/lượt")
        self.lbl_timer.setAlignment(Qt.AlignCenter)
        self.lbl_timer.setStyleSheet("color: #ff5555; font-size: 9px; font-weight: bold;")
        lay.addWidget(self.lbl_timer)

    def _all_in(self):
        self.sp_bet.setValue(max(10, self.parent_window.local_points))

    def _click_start(self):
        if not self.parent_window.net:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy kết nối LAN!")
            return

        if self.is_queued:
            # Leave queue
            if self.parent_window.is_host:
                self.parent_window.net.local_noichu_leave(self.parent_window.profile["username"])
            else:
                self.parent_window.net.noichu_leave()
            return

        if self.is_playing:
            # Forfeit / leave game
            reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc muốn đầu hàng/thoát trận đấu?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                if self.parent_window.is_host:
                    self.parent_window.net.local_noichu_forfeit(self.parent_window.profile["username"], self.current_game_id)
                else:
                    self.parent_window.net.noichu_forfeit(self.current_game_id)
            return

        bet_amt = self.sp_bet.value()
        if self.parent_window.local_points < bet_amt:
            QMessageBox.warning(self, "Lỗi", "Không đủ điểm!")
            return

        # Join queue
        if self.parent_window.is_host:
            self.parent_window.net.local_noichu_join(self.parent_window.profile["username"], bet_amt)
        else:
            self.parent_window.net.noichu_join(bet_amt)

    def _send(self):
        word = self.le_input.text().strip().lower()
        self.le_input.clear()
        if not word: return

        parts = word.split()
        if len(parts) != 2:
            self.chat_list.addItem("Hệ thống: Từ phải là từ ghép có 2 từ!")
            return

        if self.parent_window.is_host:
            self.parent_window.net.local_noichu(self.parent_window.profile["username"], self.current_game_id, word)
        elif self.parent_window.net:
            self.parent_window.net.submit_noichu(self.current_game_id, word)

    def apply_lan_state(self, games: dict, queue: list):
        my_name = self.parent_window.profile["username"]
        my_game = None
        my_gid = ""
        for gid, g in games.items():
            if g["status"] == "playing" and (g["player_a"] == my_name or g["player_b"] == my_name):
                my_game = g
                my_gid = gid
                break
                
        if my_game:
            self.is_playing = True
            self.current_game_id = my_gid
            self.is_queued = False
            self.sp_bet.setEnabled(False)
            
            opp_name = my_game["player_b"] if my_game["player_a"] == my_name else my_game["player_a"]
            self.is_my_turn = (my_game["turn"] == my_name)
            
            self.lbl_curr_word.setText(f"Từ hiện tại: {my_game['current_word'].upper()}")
            self.lbl_timer.setText(f"Thời gian: {my_game['time_left']}s")
            self.btn_start.setText("🏳️ Đầu Hàng")
            self.btn_start.setStyleSheet("background: #3c0000; border: 1.5px solid #ff3333; color: #ff3333; font-weight: bold;")
            
            if self.is_my_turn:
                self.lbl_curr_word.setStyleSheet("color: #00ff99; font-size: 11px; font-weight: bold;")
                self.le_input.setEnabled(True)
                self.btn_send.setEnabled(True)
                self.le_input.setPlaceholderText("Lượt BẠN! Gõ từ...")
            else:
                self.lbl_curr_word.setStyleSheet("color: #ff3366; font-size: 11px; font-weight: bold;")
                self.le_input.setEnabled(False)
                self.btn_send.setEnabled(False)
                self.le_input.setPlaceholderText("Đợi đối thủ...")
        else:
            self.is_playing = False
            self.current_game_id = ""
            self.sp_bet.setEnabled(True)
            self.le_input.setEnabled(False)
            self.btn_send.setEnabled(False)
            self.le_input.setPlaceholderText("Gõ từ khi vào trận...")
            
            is_queued = any(q["name"] == my_name for q in queue)
            self.is_queued = is_queued
            
            if is_queued:
                self.lbl_curr_word.setText("ĐANG GHÉP CẶP LAN...")
                self.lbl_curr_word.setStyleSheet("color: #ffff00; font-size: 11px; font-weight: bold;")
                self.lbl_timer.setText("Thời gian: -")
                self.btn_start.setText("⏳ Đang tìm... (Hủy)")
                self.btn_start.setStyleSheet("background: #331a00; border: 1.5px solid #ffaa00; color: #ffaa00; font-weight: bold;")
            else:
                self.lbl_curr_word.setText("SẴN SÀNG GHÉP TRẬN")
                self.lbl_curr_word.setStyleSheet("color: #00ffcc; font-size: 11px; font-weight: bold;")
                self.lbl_timer.setText("Thời gian: 15s/lượt")
                self.btn_start.setText("🎮 Tìm Trận đấu (LAN)")
                self.btn_start.setStyleSheet("background: #0c0018; border: 1.5px solid #00ffcc; color: #00ffcc; font-weight: bold;")


# ─── Main Game Window ─────────────────────────────────────────────────
class TaiXiuGameWindow(QMainWindow):
    _state_signal = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setFixedSize(300, 480)

        # Load profile and check username
        self.profile = load_profile()
        if not self.profile.get("username"):
            dlg = NameInputDialog(parent=self)
            if dlg.exec() == QDialog.Accepted:
                self.profile["username"] = dlg.username
                save_profile(self.profile)
            else:
                self.profile["username"] = f"Player_{random.randint(1000, 9999)}"
                save_profile(self.profile)

        self.local_points = self.profile["points"]
        self.main_app = parent

        self.is_host = False
        self.is_admin = (self.profile["username"] == "TX")
        self.net = None
        self.current_state: dict = {}
        
        self.selected_choice = ""
        self.my_bet: str = ""
        self._drag_pos = None

        self._state_signal.connect(self._apply_state)
        self._build_ui()

        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.tab_widget.setCurrentIndex(0)
        self._on_tab_changed(0)
        self._connect_network()

    def _on_tab_changed(self, index):
        if index in [0, 1, 2]:
            play_xo_so_music()
        else:
            stop_xo_so_music()

    def mousePressEvent(self, event):
        child = self.childAt(event.pos())
        if child is None or child.objectName() == "main_bg":
            if event.button() == Qt.LeftButton:
                try:
                    self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                except AttributeError:
                    self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            try:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
            except AttributeError:
                self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def _connect_network(self):
        self.lbl_status.setText("🔍 Đang quét mạng LAN...")
        QApplication.processEvents()

        def _do():
            result = discover_host(timeout=2.0)
            if result:
                host_ip, host_name = result
                if host_ip == self._my_local_ip():
                    self._become_host()
                else:
                    client = GameClient(host_ip, self.profile["username"], self.local_points, self.profile.get("game_scores", {}), on_state=self._on_state_received)
                    if client.connect():
                        self.net = client
                        self.is_host = False
                        self._state_signal.emit({"type": "CONNECTED", "host": host_name})
                    else:
                        self._become_host()
            else:
                self._become_host()

        threading.Thread(target=_do, daemon=True).start()

    def _become_host(self):
        host = GameHost(self.profile["username"], on_state_change=self._on_state_received)
        host.start()
        self.net = host
        self.is_host = True
        init_state = host.state.copy()
        self._state_signal.emit(init_state)

    @staticmethod
    def _my_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def _on_state_received(self, state: dict):
        self._state_signal.emit(state)

    def reset_host_network(self):
        self.lbl_status.setText("🔄 Đang reset & quét lại...")
        QApplication.processEvents()
        
        stop_xo_so_music()
        
        if self.net:
            try:
                if self.is_host:
                    self.net.stop()
                    time.sleep(0.3)
                else:
                    self.net.disconnect()
            except Exception as e:
                print(f"Error resetting net: {e}")
            self.net = None
            
        self.is_host = False
        self._connect_network()

    def sync_points_to_server(self, points):
        if self.is_host:
            self.net.state["scores"][self.profile["username"]] = points
            if "game_scores" not in self.net.state:
                self.net.state["game_scores"] = {}
            self.net.state["game_scores"][self.profile["username"]] = self.profile.get("game_scores", {})
            self.net.broadcast_state()
        elif self.net:
            self.net._send({"type": "JOIN", "name": self.profile["username"], "points": points, "game_scores": self.profile.get("game_scores", {})})

    # ── UI Construction ──────────────────────────────────────────
    def _build_ui(self):
        bg = QWidget(); bg.setObjectName("main_bg")
        self.setCentralWidget(bg)
        root = QVBoxLayout(bg)
        root.setContentsMargins(6,6,6,6); root.setSpacing(4)

        # Header Title Bar
        title_bar = QHBoxLayout()
        self.lbl_logo = QLabel("👑 AI LÀ VUA LÌ ĐÒN")
        self.lbl_logo.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffcc00;")
        title_bar.addWidget(self.lbl_logo)
        title_bar.addStretch()

        # Eye view count label
        self.lbl_viewers = QLabel("👁️ 1")
        self.lbl_viewers.setStyleSheet("color: #00ffcc; font-size: 10px; font-weight: bold; margin-right: 5px;")
        title_bar.addWidget(self.lbl_viewers)

        self.btn_leaderboard = QPushButton("🏆")
        self.btn_leaderboard.setFixedSize(22, 22)
        self.btn_leaderboard.setStyleSheet("background: transparent; border: none; font-size: 14px;")
        self.btn_leaderboard.clicked.connect(self._open_leaderboard)
        title_bar.addWidget(self.btn_leaderboard)

        self.btn_close_top = QPushButton("✕")
        self.btn_close_top.setFixedSize(16, 16)
        self.btn_close_top.setStyleSheet("background: transparent; color: #ff00ff; border: none; font-size: 11px;")
        self.btn_close_top.clicked.connect(self.close)
        title_bar.addWidget(self.btn_close_top)
        root.addLayout(title_bar)

        # User profile panel
        profile_lay = QHBoxLayout()
        profile_lay.addWidget(QLabel("Tên:"))
        self.le_username = QLineEdit(self.profile["username"])
        self.le_username.setFixedWidth(70)
        
        # Read-Only lock for username as requested
        if self.profile["username"]:
            self.le_username.setReadOnly(True)
            self.le_username.setEnabled(False)
            self.le_username.setStyleSheet("background: #111; color: #888; border: 1px solid #333; font-size: 10px; padding: 1px;")
        else:
            self.le_username.setStyleSheet("background: #000; color: #00ffcc; border: 1px solid #ff00ff; font-size: 10px; padding: 1px;")
            self.le_username.editingFinished.connect(self._change_username)
            
        profile_lay.addWidget(self.le_username)

        self.btn_reset_net = QPushButton("🔄 Reset Host")
        self.btn_reset_net.setFixedSize(65, 16)
        self.btn_reset_net.setStyleSheet("QPushButton { background: #110022; color: #ff9900; border: 1px solid #ff9900; border-radius: 2px; font-size: 8px; font-weight: bold; } QPushButton:hover { background: #330066; }")
        self.btn_reset_net.clicked.connect(self.reset_host_network)
        profile_lay.addWidget(self.btn_reset_net)

        self.lbl_my_score = QLabel(f"Điểm: {self.local_points}")
        self.lbl_my_score.setStyleSheet("color: #ffff00; font-weight: bold;")
        profile_lay.addWidget(self.lbl_my_score, 1, Qt.AlignRight)
        root.addLayout(profile_lay)

        # Stacked Widget
        self.tab_widget = QStackedWidget()
        
        # Page 0: Tài Xỉu
        self.tx_page = QWidget()
        self._build_tx_page()
        self.tab_widget.addWidget(self.tx_page)

        # Page 1: Bầu Cua
        self.bau_cua_page = BauCuaWidget(self)
        self.tab_widget.addWidget(self.bau_cua_page)

        # Page 2: Slots 777
        self.slots_page = SlotsWidget(self)
        self.tab_widget.addWidget(self.slots_page)

        # Page 3: Caro XO
        self.xo_page = QWidget() # Will build next
        self.xo_page = CaroXOWidget(self)
        self.tab_widget.addWidget(self.xo_page)

        # Page 4: Nối Chữ LAN
        self.noichu_page = LANNoiChuWidget(self)
        self.tab_widget.addWidget(self.noichu_page)

        # Tab bar buttons (Only icons as requested)
        tab_bar = QHBoxLayout()
        tab_bar.setSpacing(1)
        
        self.btn_tab_tx = QPushButton("🎲")
        self.btn_tab_tx.setToolTip("Tài Xỉu")
        self.btn_tab_tx.clicked.connect(lambda: self.tab_widget.setCurrentIndex(0))
        
        self.btn_tab_bc = QPushButton("🦀")
        self.btn_tab_bc.setToolTip("Bầu Cua")
        self.btn_tab_bc.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))

        self.btn_tab_slots = QPushButton("🎰")
        self.btn_tab_slots.setToolTip("Slots 777")
        self.btn_tab_slots.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))

        self.btn_tab_xo = QPushButton("⬜")
        self.btn_tab_xo.setToolTip("Caro XO")
        self.btn_tab_xo.clicked.connect(lambda: self.tab_widget.setCurrentIndex(3))

        self.btn_tab_nc = QPushButton("✍️")
        self.btn_tab_nc.setToolTip("Nối Chữ LAN")
        self.btn_tab_nc.clicked.connect(lambda: self.tab_widget.setCurrentIndex(4))

        for b in [self.btn_tab_tx, self.btn_tab_bc, self.btn_tab_slots, self.btn_tab_xo, self.btn_tab_nc]:
            b.setFixedSize(34, 24)
            b.setStyleSheet("font-size: 14px; background: #0a0a1a; border: 1px solid #2a2a4a; border-radius: 3px; color: #eee;")
            tab_bar.addWidget(b)
        root.addLayout(tab_bar)

        root.addWidget(self.tab_widget, 1)

    def _build_tx_page(self):
        lay = QVBoxLayout(self.tx_page)
        lay.setContentsMargins(0,0,0,0); lay.setSpacing(4)

        self.lbl_status = QLabel("Quét kết nối...")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color: #888; font-size: 8px;")
        lay.addWidget(self.lbl_status)

        self.timer_bar = QProgressBar()
        self.timer_bar.setRange(0, 30)
        self.timer_bar.setValue(30)
        self.timer_bar.setFixedHeight(10)
        lay.addWidget(self.timer_bar)

        self.lbl_round = QLabel("Kỳ 1 | Chờ cược")
        self.lbl_round.setAlignment(Qt.AlignCenter)
        self.lbl_round.setStyleSheet("color: #ff00ff; font-size: 9px; font-weight: bold;")
        lay.addWidget(self.lbl_round)

        dice_row = QHBoxLayout(); dice_row.addStretch()
        self.dices = [DiceWidget() for _ in range(3)]
        for d in self.dices: dice_row.addWidget(d)
        dice_row.addStretch()
        lay.addLayout(dice_row)

        self.lbl_result = QLabel("Đang chờ...")
        self.lbl_result.setAlignment(Qt.AlignCenter)
        self.lbl_result.setStyleSheet("color: #00ffcc; font-size: 14px; font-weight: bold;")
        lay.addWidget(self.lbl_result)

        history_lay = QHBoxLayout()
        history_lay.addWidget(QLabel("Lịch sử:"))
        self.history_scroll = QScrollArea()
        self.history_scroll.setFixedHeight(22)
        self.history_scroll.setWidgetResizable(True)
        self._history_container = QWidget()
        self._history_lay = QHBoxLayout(self._history_container)
        self._history_lay.setContentsMargins(2,2,2,2); self._history_lay.setSpacing(3)
        self.history_scroll.setWidget(self._history_container)
        history_lay.addWidget(self.history_scroll)
        lay.addLayout(history_lay)

        bet_amt_lay = QHBoxLayout()
        bet_amt_lay.addWidget(QLabel("Mức cược:"))
        self.sp_tx_bet = QSpinBox()
        self.sp_tx_bet.setRange(10, 999999999)
        self.sp_tx_bet.setValue(100)
        self.sp_tx_bet.setStyleSheet("background: #000; color: #00ffcc; border: 1px solid #00ffcc; padding: 1px;")
        bet_amt_lay.addWidget(self.sp_tx_bet, 1)
        lay.addLayout(bet_amt_lay)

        quick_bet_lay = QHBoxLayout()
        for amt in [100, 500, 1000]:
            btn = QPushButton(f"+{amt}")
            btn.clicked.connect(lambda _, a=amt: self.sp_tx_bet.setValue(self.sp_tx_bet.value() + a))
            quick_bet_lay.addWidget(btn)
        btn_all = QPushButton("Tất tay")
        btn_all.clicked.connect(lambda: self.sp_tx_bet.setValue(max(10, self.local_points)))
        quick_bet_lay.addWidget(btn_all)
        lay.addLayout(quick_bet_lay)

        choices_lay = QHBoxLayout()
        self.btn_tai = QPushButton("TÀI (Đen)\n[Tổng: 0đ]")
        self.btn_tai.setFixedHeight(32)
        self.btn_tai.setStyleSheet(self._choice_style("#ff007f"))
        self.btn_tai.clicked.connect(lambda: self._select_choice("Tai"))
        
        self.btn_xiu = QPushButton("XỈU (Trắng)\n[Tổng: 0đ]")
        self.btn_xiu.setFixedHeight(32)
        self.btn_xiu.setStyleSheet(self._choice_style("#00ccff"))
        self.btn_xiu.clicked.connect(lambda: self._select_choice("Xiu"))
        
        choices_lay.addWidget(self.btn_tai)
        choices_lay.addWidget(self.btn_xiu)
        lay.addLayout(choices_lay)

        choices_lay2 = QHBoxLayout()
        self.btn_chan = QPushButton("CHẴN\n[0đ]")
        self.btn_chan.setFixedHeight(26)
        self.btn_chan.setStyleSheet(self._choice_style("#00ff99"))
        self.btn_chan.clicked.connect(lambda: self._select_choice("Chan"))
        
        self.btn_le = QPushButton("LẺ\n[0đ]")
        self.btn_le.setFixedHeight(26)
        self.btn_le.setStyleSheet(self._choice_style("#ffaa00"))
        self.btn_le.clicked.connect(lambda: self._select_choice("Le"))
        
        self.btn_bao = QPushButton("BÃO\n[0đ]")
        self.btn_bao.setFixedHeight(26)
        self.btn_bao.setStyleSheet(self._choice_style("#ff00ff"))
        self.btn_bao.clicked.connect(lambda: self._select_choice("Bao"))
        
        choices_lay2.addWidget(self.btn_chan)
        choices_lay2.addWidget(self.btn_le)
        choices_lay2.addWidget(self.btn_bao)
        lay.addLayout(choices_lay2)

        # Confirm Bet Button as requested
        self.btn_confirm_bet = QPushButton("✓ XÁC NHẬN ĐẶT CƯỢC")
        self.btn_confirm_bet.setFixedHeight(26)
        self.btn_confirm_bet.setStyleSheet("""
            QPushButton { background: #004411; border: 2px solid #00ff55; color: #00ff55; font-weight: bold; font-size: 10px; border-radius: 4px; }
            QPushButton:hover { background: #006622; }
            QPushButton:disabled { background: #222; border-color: #444; color: #666; }
        """)
        self.btn_confirm_bet.clicked.connect(self._confirm_bet)
        lay.addWidget(self.btn_confirm_bet)

        self.lbl_my_bet = QLabel("Chưa đặt cược")
        self.lbl_my_bet.setAlignment(Qt.AlignCenter)
        self.lbl_my_bet.setStyleSheet("color: #888; font-size: 8px;")
        lay.addWidget(self.lbl_my_bet)

        self.score_scroll = QScrollArea()
        self.score_scroll.setFixedHeight(60)
        self._score_inner = QWidget()
        self._score_lay = QVBoxLayout(self._score_inner)
        self._score_lay.setContentsMargins(4,2,4,2); self._score_lay.setSpacing(2)
        self.score_scroll.setWidget(self._score_inner)
        self.score_scroll.setWidgetResizable(True)
        lay.addWidget(self.score_scroll)

        self.btn_admin = QPushButton("⚙️ Admin Control Tool")
        self.btn_admin.setVisible(False)
        self.btn_admin.clicked.connect(self._open_admin)
        lay.addWidget(self.btn_admin)

    def _choice_style(self, color, selected=False):
        bg_alpha = "77" if selected else "22"
        border_width = "3px" if selected else "1.5px"
        return f"""
            QPushButton {{ background: {color}{bg_alpha}; border: {border_width} solid {color}; color: #fff; font-weight: bold; font-size: 9px; }}
            QPushButton:hover {{ background: {color}44; }}
        """

    def _highlight_choice(self, choice):
        self.btn_tai.setStyleSheet(self._choice_style("#ff007f", selected=(choice=="Tai")))
        self.btn_xiu.setStyleSheet(self._choice_style("#00ccff", selected=(choice=="Xiu")))
        self.btn_chan.setStyleSheet(self._choice_style("#00ff99", selected=(choice=="Chan")))
        self.btn_le.setStyleSheet(self._choice_style("#ffaa00", selected=(choice=="Le")))
        self.btn_bao.setStyleSheet(self._choice_style("#ff00ff", selected=(choice=="Bao")))

    def _change_username(self):
        pass # Disallowed changing username once registered

    def _select_choice(self, choice):
        # Admin silent cheat double click detection
        if self.is_admin:
            now = time.time()
            prev_time, click_cnt = getattr(self, "_admin_click_tracker", {}).get(choice, (0.0, 0))
            if now - prev_time < 0.6:
                click_cnt += 1
            else:
                click_cnt = 1

            if not hasattr(self, "_admin_click_tracker"):
                self._admin_click_tracker = {}
            self._admin_click_tracker[choice] = (now, click_cnt)

            if click_cnt >= 2:
                # Reset click tracker to prevent multiple triggers
                self._admin_click_tracker[choice] = (0.0, 0)
                dice = self._generate_dice_for_choice(choice)
                if self.net:
                    self.net.admin_result(dice)
                return

        if not self.current_state.get("betting_open", True):
            return
        self.selected_choice = choice
        self._highlight_choice(choice)
        
        display_map = {"Tai": "Tài", "Xiu": "Xỉu", "Chan": "Chẵn", "Le": "Lẻ", "Bao": "Bão"}
        display = display_map.get(choice, choice)
        self.lbl_my_bet.setText(f"Lựa chọn: {display} (Chờ xác nhận...)")
        self.lbl_my_bet.setStyleSheet("color: #ffaa00; font-size: 8px; font-weight: bold;")

    def _confirm_bet(self):
        if not self.selected_choice:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn cửa cược trước!")
            return
        if not self.current_state.get("betting_open", True):
            QMessageBox.warning(self, "Lỗi", "Đã đóng cược!")
            return
        
        bet_amount = self.sp_tx_bet.value()
        if bet_amount > self.local_points:
            QMessageBox.warning(self, "Lỗi", "Không đủ điểm!")
            return

        self.my_bet = self.selected_choice
        
        # Deduct locally immediately
        self.local_points -= bet_amount
        self.profile["points"] = self.local_points
        self.profile["game_scores"]["taixiu"] = self.profile["game_scores"].get("taixiu", 0) - bet_amount
        save_profile(self.profile)
        self.lbl_my_score.setText(f"Điểm: {self.local_points}")
        
        display_map = {"Tai": "Tài", "Xiu": "Xỉu", "Chan": "Chẵn", "Le": "Lẻ", "Bao": "Bão"}
        display = display_map.get(self.my_bet, self.my_bet)
        self.lbl_my_bet.setText(f"✅ Đã xác nhận: {display} ({bet_amount} đ)")
        self.lbl_my_bet.setStyleSheet("color: #00ff55; font-size: 8px; font-weight: bold;")
        
        # Disable betting UI
        self.btn_confirm_bet.setEnabled(False)
        self.btn_tai.setEnabled(False)
        self.btn_xiu.setEnabled(False)
        self.btn_chan.setEnabled(False)
        self.btn_le.setEnabled(False)
        self.btn_bao.setEnabled(False)

        if self.is_host:
            self.net.local_bet(self.profile["username"], self.my_bet, bet_amount)
        else:
            self.net.bet(self.my_bet, bet_amount)

    def _generate_dice_for_choice(self, choice):
        while True:
            d1 = random.randint(1, 6)
            d2 = random.randint(1, 6)
            d3 = random.randint(1, 6)
            total = d1 + d2 + d3
            is_bao = (d1 == d2 == d3)
            if choice == "Bao":
                if is_bao: return [d1, d2, d3]
            elif choice == "Tai":
                if total >= 11 and total <= 17 and not is_bao: return [d1, d2, d3]
            elif choice == "Xiu":
                if total >= 4 and total <= 10 and not is_bao: return [d1, d2, d3]
            elif choice == "Chan":
                if total % 2 == 0 and not is_bao: return [d1, d2, d3]
            elif choice == "Le":
                if total % 2 != 0 and not is_bao: return [d1, d2, d3]


    def _open_admin(self):
        if not self.is_admin: return
        if hasattr(self, 'admin_dlg') and self.admin_dlg:
            try:
                self.admin_dlg.close()
                self.admin_dlg.deleteLater()
            except: pass
        self.admin_dlg = AdminPanel(self.net, self.current_state, self)
        self.admin_dlg.show()
        self.admin_dlg.move(self.x() + self.width() + 10, self.y())

    def _open_leaderboard(self):
        scores = self.current_state.get("scores", {self.profile["username"]: self.local_points})
        dlg = LeaderboardDialog(scores, self.profile["game_scores"], self)
        dlg.exec()

    @Slot(dict)
    def _apply_state(self, state: dict):
        if state.get("type") == "CONNECTED":
            host_name = state.get("host", "?")
            self.lbl_status.setText(f"Connected to LAN Host: {host_name}")
            return

        self.current_state = state
        host_name = state.get("host", "")
        rnd = state.get("round", 1)
        betting_open = state.get("betting_open", True)
        time_left = state.get("time_left", 30)
        dice = state.get("dice", [0,0,0])
        result = state.get("result", "")
        scores = state.get("scores", {})
        bets = state.get("bets", {})
        history = state.get("history", [])

        # Sync player counter label with eye icon 👁️
        players_list = state.get("players", [self.profile["username"]])
        self.lbl_viewers.setText(f"👁️ {len(players_list)}")

        # Sync LAN Word chain page elements
        nc_word = state.get("noichu_word", "học sinh")
        nc_time = state.get("noichu_time_left", 20)
        nc_chat = state.get("noichu_chat", [])

        # Sync profile score
        my_name = self.profile["username"]
        if my_name in scores:
            diff = scores[my_name] - self.local_points
            if diff != 0:
                self.local_points = scores[my_name]
                self.profile["points"] = self.local_points
                # Update specific game score details
                current_tab = self.tab_widget.currentIndex()
                if current_tab == 0:
                    self.profile["game_scores"]["taixiu"] = self.profile["game_scores"].get("taixiu", 0) + diff
                elif current_tab == 3:
                    self.profile["game_scores"]["caro"] = self.profile["game_scores"].get("caro", 0) + diff
                elif current_tab == 4:
                    self.profile["game_scores"]["noichu"] = self.profile["game_scores"].get("noichu", 0) + diff
                save_profile(self.profile)
                self.lbl_my_score.setText(f"Điểm: {self.local_points}")

        self.is_admin = (my_name == "TX")
        self.btn_admin.setVisible(self.is_admin)
        self.xo_page.btn_suggest.setVisible(self.is_admin)

        if hasattr(self, 'admin_dlg') and self.admin_dlg and self.admin_dlg.isVisible():
            self.admin_dlg.update_players(list(scores.keys()))

        if self.is_host:
            self.lbl_status.setText(f"Host Server Đang Chạy (LAN)")
        else:
            self.lbl_status.setText(f"Kết Nối Host: {host_name}")

        if hasattr(self, "main_app") and self.main_app:
            players_str = ", ".join(players_list)
            self.main_app.lbl_alt_tips.setText(f"Host: {host_name} | {len(players_list)} Online: {players_str}")
            self.main_app.lbl_alt_tips.setStyleSheet("color: #00ffcc; font-family: 'Consolas'; font-size: 8px; font-weight: bold;")

        self.timer_bar.setValue(time_left)
        self.timer_bar.setFormat(f"Thời gian: {time_left}s")

        self.lbl_round.setText(
            f"Kỳ {rnd} | {'🟢 Đang nhận cược' if betting_open else '🔴 Đã đóng cược'}"
        )

        # Real-time betting sums calculation
        total_tai = sum(b["amount"] for b in bets.values() if b["choice"] == "Tai")
        total_xiu = sum(b["amount"] for b in bets.values() if b["choice"] == "Xiu")
        total_chan = sum(b["amount"] for b in bets.values() if b["choice"] == "Chan")
        total_le = sum(b["amount"] for b in bets.values() if b["choice"] == "Le")
        total_bao = sum(b["amount"] for b in bets.values() if b["choice"] == "Bao")

        self.btn_tai.setText(f"TÀI (Đen)\n[Tổng: {total_tai}đ]")
        self.btn_xiu.setText(f"XỈU (Trắng)\n[Tổng: {total_xiu}đ]")
        self.btn_chan.setText(f"CHẴN\n[{total_chan}đ]")
        self.btn_le.setText(f"LẺ\n[{total_le}đ]")
        self.btn_bao.setText(f"BÃO\n[{total_bao}đ]")

        # Reset choices and enable betting UI on new round
        if betting_open:
            if not self.my_bet and not self.selected_choice:
                self.btn_confirm_bet.setEnabled(True)
                self.btn_tai.setEnabled(True)
                self.btn_xiu.setEnabled(True)
                self.btn_chan.setEnabled(True)
                self.btn_le.setEnabled(True)
                self.btn_bao.setEnabled(True)
                self.lbl_my_bet.setText("Chưa đặt cược")
                self.lbl_my_bet.setStyleSheet("color: #888; font-size: 8px;")
        else:
            self.btn_confirm_bet.setEnabled(False)
            self.btn_tai.setEnabled(False)
            self.btn_xiu.setEnabled(False)
            self.btn_chan.setEnabled(False)
            self.btn_le.setEnabled(False)
            self.btn_bao.setEnabled(False)

        # Dice roll result
        if result and dice and dice[0] != 0:
            total = sum(dice)
            prev_dice = [d.value for d in self.dices]
            if prev_dice != dice:
                play_xo_so_music()
                done_count = [0]
                def _done():
                    done_count[0] += 1
                    if done_count[0] == 3:
                        if self.tab_widget.currentIndex() not in [0, 1, 2]:
                            stop_xo_so_music()
                        if result == "Bao":
                            color = "#ff00ff"
                            display_text = "🔥 BÃO"
                        elif result == "Tai":
                            color = "#ff007f"
                            display_text = "🔴 TÀI"
                        else:
                            color = "#00ccff"
                            display_text = "🔵 XỈU"
                        self.lbl_result.setText(f"{display_text} ({total})")
                        self.lbl_result.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
                        self.my_bet = ""
                        self.selected_choice = ""
                for i, d in enumerate(self.dices):
                    d.roll_animate(dice[i] if i < len(dice) else 1, _done)
        elif not result:
            self.lbl_result.setText("Đang cược...")
            self.lbl_result.setStyleSheet("color: #00ffcc; font-size: 12px;")
            for d in self.dices:
                d.value = 0; d.update()

        self._refresh_history_ui(history)

        if my_name in bets:
            b_info = bets[my_name]
            display_map = {"Tai": "Tài", "Xiu": "Xỉu", "Chan": "Chẵn", "Le": "Lẻ", "Bao": "Bão"}
            bet_choice = display_map.get(b_info["choice"], b_info["choice"])
            self.lbl_my_bet.setText(f"✅ Đã cược: {bet_choice} ({b_info['amount']} đ)")
            self.lbl_my_bet.setStyleSheet("color: #00ff55; font-size: 8px; font-weight: bold;")
            
            # Disable confirm UI
            self.btn_confirm_bet.setEnabled(False)

        self._refresh_scores_ui(scores, bets)

        # Sync Caro Matchmaking tab
        caro_games = state.get("caro_games", {})
        caro_queue = state.get("caro_queue", [])
        self.xo_page.apply_lan_state(caro_games, caro_queue)

        # Sync LAN Word Chain
        noichu_games = state.get("noichu_games", {})
        noichu_queue = state.get("noichu_queue", [])
        self.noichu_page.apply_lan_state(noichu_games, noichu_queue)
        
        self.noichu_page.chat_list.clear()
        for chat in nc_chat:
            self.noichu_page.chat_list.addItem(chat)
        self.noichu_page.chat_list.scrollToBottom()

    def _refresh_history_ui(self, history):
        while self._history_lay.count():
            item = self._history_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for res in history[-12:]:
            circle = HistoryCircle(res)
            self._history_lay.addWidget(circle)
        self._history_lay.addStretch()

    def _refresh_scores_ui(self, scores, bets):
        while self._score_lay.count():
            item = self._score_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        sorted_players = sorted(scores.items(), key=lambda x: -x[1])
        for name, pts in sorted_players:
            row = QHBoxLayout()
            lbl_n = QLabel(name)
            
            # Show player's bet details in real-time next to their score
            lbl_p = QLabel()
            bet_info = bets.get(name)
            if bet_info:
                display_map = {"Tai": "Tài", "Xiu": "Xỉu", "Chan": "Chẵn", "Le": "Lẻ", "Bao": "Bão"}
                c = display_map.get(bet_info["choice"], bet_info["choice"])
                lbl_p.setText(f"{pts:+} (cược {c}: {bet_info['amount']}đ)")
            else:
                lbl_p.setText(f"{pts:+}")
                
            lbl_p.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            is_me = (name == self.profile["username"])
            lbl_n.setStyleSheet("color:#ff00ff;font-weight:bold;font-size:10px;" if is_me else "color:#aaa;font-size:10px;")
            lbl_p.setStyleSheet("color:#00ff99;font-weight:bold;font-size:10px;" if pts >= 10000 else "color:#ff5555;font-weight:bold;font-size:10px;")
            row.addWidget(lbl_n, 1); row.addWidget(lbl_p)
            c = QWidget()
            c.setLayout(row)
            if is_me:
                c.setStyleSheet("background: #220044; border-radius: 3px;")
            self._score_lay.addWidget(c)
        self._score_lay.addStretch()

    def closeEvent(self, event):
        stop_xo_so_music()
        if self.net:
            if self.is_host:
                self.net.stop()
            else:
                self.net.disconnect()
        if hasattr(self, "main_app") and self.main_app:
            self.main_app.lbl_alt_tips.setText("Lan Host: Offline")
            self.main_app.lbl_alt_tips.setStyleSheet("color: #ff3333; font-family: 'Consolas'; font-size: 8px; font-weight: bold; background: transparent;")
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = TaiXiuGameWindow()
    w.show()
    sys.exit(app.exec())
