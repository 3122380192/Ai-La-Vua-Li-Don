"""
Auto Workflow Module - Integrates with TX Embroider GUI
Contains AutoWorkflow class and DSTSuffixDialog for automated operations
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PySide6.QtCore import Qt
import pyautogui
import pyperclip
import time
import os
from datetime import datetime
import keyboard
try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except:
    HAS_WIN32 = False
    print("Warning: pywin32 not installed, window focus features disabled")

class DSTSuffixDialog(QDialog):
    """Small dialog for editing screenshot filename for DST files"""
    def __init__(self, default_filename, parent=None):
        super().__init__(parent)
        self.default_filename = default_filename
        self.filename = ""
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("DST Screenshot Name")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setFixedSize(300, 120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Label
        lbl = QLabel(f"Edit screenshot filename:")
        lbl.setStyleSheet("color: white; font-size: 10px;")
        layout.addWidget(lbl)
        
        # Input with default filename
        self.input = QLineEdit()
        self.input.setText(self.default_filename)  # Pre-fill with default
        self.input.selectAll()  # Select all for easy editing
        self.input.setStyleSheet("""
            QLineEdit {
                background: #111;
                color: #00ff41;
                border: 1px solid #00ff41;
                border-radius: 4px;
                padding: 6px;
                font-size: 11px;
            }
        """)
        self.input.returnPressed.connect(self.accept)
        layout.addWidget(self.input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("Save")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: #00ff41;
                color: black;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background: #00dd33; }
        """)
        self.btn_save.clicked.connect(self.accept)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background: #333;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background: #555; }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)
        
        self.setStyleSheet("background: #000500; border: 2px solid #00ff41; border-radius: 8px;")
        
    def get_suffix(self):
        """Show dialog and return edited filename, or None if cancelled"""
        self.input.setFocus()
        self.input.selectAll()
        result = self.exec()
        if result == QDialog.Accepted:
            return self.input.text().strip()
        return None

class AutoWorkflow:
    """Automated workflow for TX Embroider operations"""
    
    def __init__(self, gui_ref, context):
        self.gui = gui_ref  # Reference to main GUI window (Only for calling safe methods like flash_status)
        self.context = context # Pre-fetched data (SAFE)
        self.start_time = time.time()
        
        # Target window title (can be partial match)
        self.embroidery_window_title = "Ultimate Special Edition"
        self.abort_flag = False  # Flag to abort workflow
        self.embroidery_hwnd = None  # Window handle for screenshot
        self.id_checkbox = "" # Will be populated from context
        self.folder_path = "" # Will be populated from context
        self.file_type = "TBF" # Default
        
    def update_status(self, message, color="#00ff41"):
        """Update GUI status label via Signal"""
        try:
            self.gui.flash_status(message, color)
            self.gui.status_signal.emit(message, color)
        except:
            print(f"[STATUS] {message}")
    
    def find_window_by_partial_title(self, partial_title):
        """Find window by partial title match"""
        if not HAS_WIN32:
            return None
            
        def enum_handler(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if partial_title.lower() in window_text.lower():
                    results.append((hwnd, window_text))
        
        results = []
        win32gui.EnumWindows(enum_handler, results)
        return results
    
    def activate_embroidery_window(self):
        """
        Find and activate the embroidery software window
        NO Ctrl+A - just activate and verify focus
        Saves window handle for screenshot
        """
        self.update_status("Find Win...", "#ffff00")
        
        if not HAS_WIN32:
            print("Win32 not available, assuming window is active")
            self.embroidery_hwnd = None
            time.sleep(0.2)  # Reduced from 0.5s
            return True
        
        # List of possible window titles to try
        possible_titles = [
            "Ultimate Special Edition",
            "[Ultimate Special Edition]",  # With brackets
            # Other possible variations
            "Ultimate Special",
            "[Ultimate Special",
            "Embroider",
            "Embroidery",
            "Design",
            "Wilcom",
            "Brother",
            "Tajima",
            "Pulse",
        ]
        
        # Try exact match for each title (fast path)
        for title in possible_titles:
            try:
                hwnd = win32gui.FindWindow(None, title)
                if hwnd:
                    print(f"Found exact match: {title}")
                    if win32gui.IsIconic(hwnd):
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.2)  # Reduced from 0.5s
                    self.update_status("Win Ready", "#00ff41")
                    self.embroidery_hwnd = hwnd  # Save handle
                    return True
            except:
                continue
        
        # Try partial match search - look for "Ultimate" or "Special" in window title
        self.update_status("Search...", "#ffff00")
        
        search_keywords = ["Ultimate", "Special", "Edition", "Embroid", "Design"]
        
        for keyword in search_keywords:
            results = self.find_window_by_partial_title(keyword)
            if results:
                # Filter out TX tool itself (it also has "Ultimate Special Edition" in name)
                for hwnd, title in results:
                    # Skip if it's our own TX tool window
                    if "TX Embroider" in title or "TX EMBROIDER" in title:
                        continue
                    
                    print(f"Found window by keyword '{keyword}': {title}")
                    try:
                        if win32gui.IsIconic(hwnd):
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.SetForegroundWindow(hwnd)
                        time.sleep(0.2)  # Reduced from 0.5s
                        self.update_status("Win Ready", "#00ff41")
                        self.embroidery_hwnd = hwnd  # Save handle
                        return True
                    except Exception as e:
                        print(f"Error activating window: {e}")
                        continue
        
        # Last resort: List all windows for debugging
        print("\n=== Available Windows ===")
        def list_handler(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:  # Only show windows with titles
                    print(f"  - {title}")
        
        win32gui.EnumWindows(list_handler, None)
        print("========================\n")
        
        self.update_status("NO WIN!", "#ff0000")
        print("ERROR: Could not find embroidery window")
        print("Please check the window title and update the script")
        self.embroidery_hwnd = None
        return False
    
    def capture_window_screenshot(self):
        """
        Capture screenshot of embroidery window only
        Returns PIL Image or None
        """
        if not HAS_WIN32 or not self.embroidery_hwnd:
            # Fallback to full screen
            print("No window handle, using full screen screenshot")
            return pyautogui.screenshot()
        
        try:
            # Get window rect
            rect = win32gui.GetWindowRect(self.embroidery_hwnd)
            x, y, x2, y2 = rect
            width = x2 - x
            height = y2 - y
            
            print(f"Window rect: {x}, {y}, {width}, {height}")
            
            # Screenshot the specific region
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            return screenshot
        except Exception as e:
            print(f"Error capturing window screenshot: {e}")
            # Fallback to full screen
            return pyautogui.screenshot()
    
    def find_and_click_button(self, button_text):
        """
        Find and click a button by text using image recognition
        This is a simplified version - in production, you might need OCR
        """
        self.update_status(f"Find {button_text[:8]}...", "#ffff00")
        
        try:
            # Try to locate button on screen
            # This requires a screenshot of the button saved as an image
            # For now, we'll use keyboard navigation or skip this
            
            # Alternative: Use Alt+O or specific shortcut if available
            # Or tab navigation
            
            print(f"Looking for button: {button_text}")
            # For "Close all color nodes", we might need specific coordinates
            # or a saved image of the button
            
            # Fallback: Just wait and assume user positioned correctly
            time.sleep(0.5)
            return True
            
        except Exception as e:
            print(f"Button search error: {e}")
            return False
    
    def check_abort(self):
        """Check if user pressed Ctrl+Q (or Q) to abort, or if abort_flag was set, or if 5s timeout reached"""
        if time.time() - self.start_time > 5.0:
            self.abort_flag = True
            self.update_status("TIMEOUT 5S", "#ff3333")
            print("[AUTO] Emergency Abort: Workflow exceeded 5 seconds limit")
            return True
        if keyboard.is_pressed('ctrl+q') or keyboard.is_pressed('q') or self.abort_flag:
            self.abort_flag = True
            self.update_status("CTRL+Q STOP", "#ff3333")
            print("[AUTO] Emergency Abort Triggered (Ctrl+Q or Abort Flag)")
            return True
        return False
        
    def process_dialog_background(self, keywords, filepath, timeout=3.0):
        """
        Wait for dialog to appear, hide it instantly, set filename directly, and save.
        All done in the background.
        """
        if not HAS_WIN32:
            time.sleep(0.5)
            return True
            
        start_time = time.time()
        dialog_hwnd = None
        
        # 1. Poll very fast for the dialog window
        while time.time() - start_time < timeout:
            if self.check_abort():
                return False
                
            def enum_windows_callback(hwnd, results):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if any(kw.lower() in title.lower() for kw in keywords):
                        if "TX Embroider" not in title and "TX EMBROIDER" not in title:
                            results.append(hwnd)
            
            results = []
            win32gui.EnumWindows(enum_windows_callback, results)
            
            if results:
                dialog_hwnd = results[0]
                break
            time.sleep(0.01) # 10ms poll for instant detection
            
        if not dialog_hwnd:
            print(f"[BACKGROUND] Dialog with keywords {keywords} not found in time.")
            return False
            
        # 2. Hide dialog window instantly
        win32gui.ShowWindow(dialog_hwnd, win32con.SW_HIDE)
        print(f"[BACKGROUND] Hid dialog: {win32gui.GetWindowText(dialog_hwnd)}")
        
        # 3. Find the Edit control inside dialog
        edit_hwnd = None
        def enum_child_callback(hwnd, results):
            class_name = win32gui.GetClassName(hwnd)
            if class_name == 'Edit':
                results.append(hwnd)
            return True
            
        child_edits = []
        win32gui.EnumChildWindows(dialog_hwnd, enum_child_callback, child_edits)
        if child_edits:
            edit_hwnd = child_edits[0]
            
        if not edit_hwnd:
            print("[BACKGROUND] Edit control not found, falling back to keystrokes")
            # Fallback if no Edit control found
            win32gui.ShowWindow(dialog_hwnd, win32con.SW_SHOW)
            pyperclip.copy(filepath)
            time.sleep(0.05)
            keyboard.send('ctrl+v')
            time.sleep(0.05)
            keyboard.send('enter')
            return True
            
        # 4. Set text via WM_SETTEXT directly (instant & background)
        win32gui.SendMessage(edit_hwnd, win32con.WM_SETTEXT, 0, filepath)
        time.sleep(0.05)
        
        # 5. Submit dialog via WM_COMMAND (IDOK is 1)
        win32gui.PostMessage(dialog_hwnd, win32con.WM_COMMAND, 1, 0)
        print(f"[BACKGROUND] Filled and submitted dialog for filepath: {filepath}")
        return True

    def check_and_confirm_overwrite_bg(self, timeout=0.8):
        """
        Poll for overwrite confirmation dialog in the background.
        If found, hide it instantly and press Enter (or Yes) to confirm.
        """
        if not HAS_WIN32:
            return False
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.check_abort():
                return False
                
            def find_confirm(hwnd, results):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if any(kw in title.lower() for kw in ["confirm", "xác nhận", "already exists", "replace"]):
                        if "TX Embroider" not in title and "TX EMBROIDER" not in title:
                            results.append(hwnd)
            
            results = []
            win32gui.EnumWindows(find_confirm, results)
            if results:
                confirm_hwnd = results[0]
                # Hide instantly
                win32gui.ShowWindow(confirm_hwnd, win32con.SW_HIDE)
                print(f"[BACKGROUND] Hid overwrite dialog: {win32gui.GetWindowText(confirm_hwnd)}")
                # Send IDYES (6) and IDOK (1) to confirm overwrite
                win32gui.PostMessage(confirm_hwnd, win32con.WM_COMMAND, 6, 0)
                win32gui.PostMessage(confirm_hwnd, win32con.WM_COMMAND, 1, 0)
                return True
            time.sleep(0.01)
        return False
    
    def step0_prepare_data(self):
        """
        Step 0: Prepare data from safe context
        """
        if self.check_abort():
            return False
        
        self.gui.progress_signal.emit(5)
        self.update_status("Preparing Data...", "#888")
        print("\n[AUTO STEP 0] Preparing data...")
        self.update_status("Prep Data", "#00ff41")
        
        # Use pre-fetched data from context
        self.id_checkbox = self.context.get('final_id', 'Unknown')
        print(f"Prepared ID: {self.id_checkbox}")
        
        self.folder_path = self.context.get('folder_path')
        if not self.folder_path:
            self.update_status("NO FOLDER", "#ff0000")
            return False
        print(f"Prepared Folder: {self.folder_path}")
        
        self.file_type = self.context.get('file_type', 'TBF')
        print(f"File Type: {self.file_type}")
        
        self.update_status("Data Ready", "#00ff41")
        return True
    
    def step1_save_as(self):
        """
        Step 1: Save As with FULL PATH and .EMB extension in background
        """
        if self.check_abort():
            return False
            
        self.gui.progress_signal.emit(45)
        self.update_status("Saving EMB File...", "#888")
        print("\n[AUTO STEP 1] Save As workflow...")
        self.update_status("Step 1/3", "#00ff41")
        
        # 1. Find and activate window
        if not self.activate_embroidery_window():
            self.update_status("NO WIN-1", "#ff0000")
            return False
        
        # 2. Gửi phím "--" trước khi lưu (Bỏ phím 0)
        self.update_status("Send --", "#ffff00")
        keyboard.send('-')
        time.sleep(0.05)
        keyboard.send('-')
        time.sleep(0.1)
        
        # 3. Open Save As dialog with Alt+F then A
        self.update_status("Alt+F -> A", "#ffff00")
        keyboard.send('alt+f')
        time.sleep(0.15)
        keyboard.send('a')
        
        # 4. Build FULL PATH with .EMB extension
        full_save_path = os.path.join(self.folder_path, f"{self.id_checkbox}.EMB")
        
        # 5. Process dialog instantly in background
        if not self.process_dialog_background(["Save As", "Lưu", "Save"], full_save_path, timeout=3.0):
            return False
            
        # 6. Check and handle overwrite dialog in background
        self.check_and_confirm_overwrite_bg()
            
        self.gui.progress_signal.emit(70)
        self.update_status("Step 1 ✓", "#00ff41")
        print("[AUTO STEP 1] Complete")
        return True
    
    def step2_export_machine(self):
        """
        Step 2: Export Machine File in background
        """
        if self.check_abort():
            return False
            
        self.gui.progress_signal.emit(75)
        self.update_status("Exporting Machine File...", "#888")
        print("\n[AUTO STEP 2] Export Machine File...")
        self.update_status("Step 2/3", "#00ff41")
        
        # 1. Find and activate window
        if not self.activate_embroidery_window():
            self.update_status("NO WIN-2", "#ff0000")
            return False
        
        # 2. Send Shift+E to open Export dialog
        self.update_status("Shift+E", "#ffff00")
        keyboard.send('shift+e')
        
        # 3. Build full export path
        extension = f".{self.file_type}" if self.file_type in ['DST', 'TBF'] else '.TBF'
        export_filename = f"{self.id_checkbox}{extension}"
        full_export_path = os.path.join(self.folder_path, export_filename)
        
        # 4. Process dialog instantly in background
        if not self.process_dialog_background(["Export", "Machine", "Xuất"], full_export_path, timeout=3.0):
            return False
            
        # 5. Check and handle overwrite dialog in background
        self.check_and_confirm_overwrite_bg()
            
        self.gui.progress_signal.emit(95)
        self.update_status("Step 2 ✓", "#00ff41")
        print(f"[AUTO STEP 2] Exported: {export_filename}")
        return True
    
    def step3_screenshot(self):
        """
        Step 3: Screenshot of embroidery window ONLY
        TBF & DST: Auto-save window screenshot
        """
        if self.check_abort():
            return False
            
        self.gui.progress_signal.emit(35)
        self.update_status("Capturing Window...", "#888")
        print("\n[AUTO STEP 3] Screenshot...")
        self.update_status("Step 3/3", "#00ff41")
        
        # 1. Activate window
        if not self.activate_embroidery_window():
            self.update_status("NO WIN-3", "#ff0000")
            return False
        
        time.sleep(0.2)  # Reduced from 0.3s
        
        # 2. Take screenshot of WINDOW ONLY (not full screen)
        self.update_status("Capture Win", "#ffff00")
        screenshot = self.capture_window_screenshot()
        
        # 3. Save screenshot
        self.update_status("Save PNG", "#ffff00")
        filename = f"{self.id_checkbox}.png"
        filepath = os.path.join(self.folder_path, filename)
        
        # Overwrite: Explicitly remove old file if it exists to ensure overwrite works
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Warning: could not delete old screenshot {filename}: {e}")
                
        screenshot.save(filepath)
        print(f"[AUTO STEP 3] Window screenshot saved: {filename}")
        
        self.gui.progress_signal.emit(40)
        self.update_status("Step 3 ✓", "#00ff41")
        return True
    
    def run(self):
        """
        Run full automated workflow
        OPTIMIZED: Faster, smoother execution
        Press Q to abort at any time
        """
        print("\n" + "="*50)
        print("AUTO WORKFLOW STARTING (Press Q to abort)")
        print("="*50)
        
        # Ensure folder exists
        if not self.gui.current_folder:
            self.update_status("Create Fldr", "#ffff00")
            print("Creating folder first...")
            self.gui.on_create_folder()
            time.sleep(0.3)
        
        # Step 0: Prepare data from TX tool
        if not self.step0_prepare_data():
            self.update_status("FAIL @ 0", "#ff0000")
            return False
        
        if self.abort_flag:
            return False
        time.sleep(0.2)
        
        # Step 3: Screenshot (NOW RUN FIRST)
        if not self.step3_screenshot():
            self.update_status("FAIL @ 3", "#ff0000")
            return False
        
        if self.abort_flag:
            return False
        time.sleep(0.2)
        
        # Step 1: Save As
        if not self.step1_save_as():
            self.update_status("FAIL @ 1", "#ff0000")
            return False
        
        if self.abort_flag:
            return False
        time.sleep(0.2)
        
        # Step 2: Export Machine File
        if not self.step2_export_machine():
            self.update_status("FAIL @ 2", "#ff0000")
            return False
        
        if self.abort_flag:
            print("Workflow aborted by user")
            return False
        
        print("\n" + "="*50)
        print("AUTO WORKFLOW COMPLETE!")
        print("="*50)
        
        self.gui.progress_signal.emit(100)
        self.update_status("ALL DONE! ✓", "#00ff41")
        
        # Emit Success Toast Signal to Main GUI Thread
        try:
            self.gui.show_success_toast_signal.emit("Lưu Thành công")
        except Exception as e:
            print(f"Error showing success toast: {e}")
            
        time.sleep(1.0)
        self.update_status("AUTO OK", "#00ff41")
        return True
