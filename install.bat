@echo off
setlocal enabledelayedexpansion

:: Change to script directory (important for double-click execution)
cd /d "%~dp0"

:: Path settings
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
set VENV_DIR=%SCRIPT_DIR%\venv
set IMAGE_EXE=%SCRIPT_DIR%\dist\ImageShrinker.exe
set ICON_FILE=%SCRIPT_DIR%\icon\run.ico
set SHORTCUT_NAME=ImageShrinker.lnk
set VBS=%TEMP%\create_shortcut.vbs

:: Detect Desktop path (OneDrive or regular)
if exist "%USERPROFILE%\OneDrive\Desktop" (
    set DESKTOP=%USERPROFILE%\OneDrive\Desktop
) else (
    set DESKTOP=%USERPROFILE%\Desktop
)

echo Working directory: %SCRIPT_DIR%

echo [1/6] Checking Python installation...
where python >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found. Please install Python or check PATH settings.
    pause
    exit /b 1
)

echo [2/6] Removing existing virtual environment...
if exist "%VENV_DIR%" (
    rmdir /s /q "%VENV_DIR%"
)

echo [3/6] Creating virtual environment...
python -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo [Error] Failed to create virtual environment
    pause
    exit /b 1
)

echo [4/6] Activating virtual environment and installing packages...
call "%VENV_DIR%\Scripts\activate.bat"

:: Upgrade pip and install dependencies
python -m pip install --upgrade pip setuptools wheel
pip install "numpy<2.0.0" --force-reinstall --only-binary=:all: --no-input
pip install pyqt6==6.5.2 pyqt6-qt6==6.5.2 pyqt6-sip==13.5.2 --no-input
pip install opencv-python==4.9.0.80 pyyaml pyinstaller --no-input

echo [5/6] Building with PyInstaller...
pyinstaller --noconfirm --onefile --console ^
  --icon="%ICON_FILE%" ^
  --add-data "ui\\image_shrinker.ui;ui" ^
  --collect-all numpy ^
  --collect-all PyQt6 ^
  ImageShrinker.py

if not exist "%IMAGE_EXE%" (
    echo [Error] Build failed: Executable was not created.
    pause
    exit /b 1
)

echo [6/6] Creating desktop shortcut...
:: Create VBS script with proper quoting
(
echo Set oWS = CreateObject^("WScript.Shell"^)
echo sLinkFile = "%DESKTOP%\%SHORTCUT_NAME%"
echo Set oLink = oWS.CreateShortcut^(sLinkFile^)
echo oLink.TargetPath = "%IMAGE_EXE%"
echo oLink.WorkingDirectory = "%cd%"
echo oLink.IconLocation = "%ICON_FILE%"
echo oLink.Save
) > "%VBS%"

:: Execute shortcut creation
cscript //nologo "%VBS%"
if errorlevel 1 (
    echo [Warning] Could not create desktop shortcut. You can manually create one.
)
del "%VBS%" 2>nul

echo.
echo Installation and build complete. Run ImageShrinker from your desktop.
pause
exit /b 0
