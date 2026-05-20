# -*- mode: python ; coding: utf-8 -*-
import os

a = Analysis(
    ['tai_xiu_game.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=[
        ('Xổ Số.mp3', '.'),
    ],
    hiddenimports=[
        # PySide6 core
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtNetwork',
        'shiboken6',
        # project module
        'tx_network',
        # stdlib
        'socket',
        'threading',
        'winsound',
        'json',
        'datetime',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'tkinter', 'flask', 'requests'],
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
    name='TaiXiuGame',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
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
    icon='app_icon.png',
)
