# -*- mode: python ; coding: utf-8 -*-
import os

# Use local files from the project directory
PATCH_PRINT_EXE = os.path.abspath('A-PatchPrint.exe')
PS_AUTO_EXE     = os.path.abspath('PS_Auto_GUI1.exe')

a = Analysis(
    ['app.py'],
    pathex=[os.path.abspath('.')],
    binaries=[
        (PATCH_PRINT_EXE, 'tools'),
        (PS_AUTO_EXE,     'tools'),
    ],
    datas=[
        ('app_icon.png', '.'),
        ('Xổ Số.mp3', '.'),
        # Bundle all project .py modules explicitly
        ('gui.py', '.'),
        ('tai_xiu_game.py', '.'),
        ('tx_network.py', '.'),
        ('security.py', '.'),
        ('logic.py', '.'),
        ('server.py', '.'),
        ('color_reader.py', '.'),
        ('auto_workflow.py', '.'),
        ('ui_components.py', '.'),
    ],
    hiddenimports=[
        # ── Flask / web ──────────────────────────────────────────────
        'flask',
        'flask.json',
        'flask.wrappers',
        'flask.cli',
        'werkzeug',
        'werkzeug.serving',
        'werkzeug.routing',
        'werkzeug.exceptions',
        'werkzeug.middleware.proxy_fix',
        # ── PySide6 core UI ─────────────────────────────────────────
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        # ── PySide6 Multimedia (needed for QMediaPlayer / sound) ─────
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        # ── PySide6 miscellaneous ────────────────────────────────────
        'PySide6.QtPrintSupport',
        'PySide6.QtSvg',
        'PySide6.QtOpenGL',
        'PySide6.QtOpenGLWidgets',
        'shiboken6',
        # ── networking / system ──────────────────────────────────────
        'socket',
        'threading',
        'requests',
        'requests.adapters',
        'urllib3',
        'certifi',
        # ── automation / GUI control ─────────────────────────────────
        'keyboard',
        'psutil',
        'pyautogui',
        'pyperclip',
        'pyscreeze',
        # ── image / media ────────────────────────────────────────────
        'PIL',
        'PIL.Image',
        'PIL.ImageFilter',
        'PIL.ImageEnhance',
        'PIL.ImageGrab',
        'cv2',
        # ── web scraping / download ──────────────────────────────────
        'bs4',
        'yt_dlp',
        'yt_dlp.extractor',
        # ── Windows-specific ─────────────────────────────────────────
        'win32gui',
        'win32con',
        'win32process',
        'win32api',
        'winreg',
        'winsound',
        'ctypes',
        'ctypes.wintypes',
        # ── stdlib extras ────────────────────────────────────────────
        'json',
        'hashlib',
        'datetime',
        'traceback',
        'importlib',
        'importlib.metadata',
        'pkg_resources',
        # ── project modules ──────────────────────────────────────────
        'tai_xiu_game',
        'tx_network',
        'gui',
        'logic',
        'security',
        'server',
        'color_reader',
        'auto_workflow',
        'ui_components',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
        'PyQt6', 'tkinter', 'matplotlib', 'scipy',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TXv3',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        # Do not UPX-compress PySide6 DLLs — causes crashes
        'Qt6Multimedia.dll',
        'Qt6MultimediaWidgets.dll',
        'Qt6Network.dll',
        'Qt6Core.dll',
        'Qt6Gui.dll',
        'Qt6Widgets.dll',
        'python310.dll',
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon='app_icon.png',
)
