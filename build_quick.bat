@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

echo [1/5] Installing project dependencies...
if exist "requirements.txt" (
    "%PYTHON_EXE%" -m pip install -r requirements.txt || goto :fail
) else (
    echo requirements.txt not found, skipping dependency install.
)

echo [2/5] Checking PyInstaller...
"%PYTHON_EXE%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    "%PYTHON_EXE%" -m pip install pyinstaller || goto :fail
)

echo [3/5] Cleaning previous build output...
if exist "build\Tx6" rmdir /s /q "build\Tx6"
if exist "dist\Tx6.exe" del /f /q "dist\Tx6.exe"

echo [4/5] Building EXE...
if exist "Tx6.spec" (
    "%PYTHON_EXE%" -m PyInstaller --clean --noconfirm "Tx6.spec" || goto :fail
) else (
    "%PYTHON_EXE%" -m PyInstaller --clean --noconfirm --onefile --windowed --name Tx6 app.py || goto :fail
)

echo [5/5] Build finished.
if exist "dist\Tx6.exe" (
    for %%I in ("dist\Tx6.exe") do (
        echo EXE: %%~fI
        echo Size: %%~zI bytes
    )
    exit /b 0
)

echo Build completed but EXE not found in dist folder.
exit /b 1

:fail
echo Build failed.
exit /b 1
