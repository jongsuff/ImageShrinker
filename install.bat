@echo off
setlocal enabledelayedexpansion

:: ȯ�溯�� �ʱ�ȭ (�ʿ� �ø� ����)
set PYTHONHOME=
set PYTHONPATH=
set PATH=%SystemRoot%\system32;%SystemRoot%;%SystemRoot%\System32\Wbem

:: ��� ����
set VENV_DIR=%cd%\venv
set IMAGE_EXE=%cd%\dist\ImageShrinker.exe
set ICON_FILE=%cd%\icon\run.ico
set SHORTCUT_NAME=ImageShrinker.lnk
set DESKTOP=%USERPROFILE%\Desktop
set VBS=%TEMP%\create_shortcut.vbs

echo [1/6] Python ��ġ Ȯ�� ��...
py -V >nul 2>&1
if errorlevel 1 (
    echo [����] Python(py) ����� ã�� �� �����ϴ�. Python ��ġ�� Ȯ���ϼ���.
    exit /b 1
)

echo [2/6] ���� ����ȯ�� ���� ��...
if exist "%VENV_DIR%" (
    rmdir /s /q "%VENV_DIR%"
)

echo [3/6] ����ȯ�� ���� ��...
py -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo [����] ����ȯ�� ���� ����
    exit /b 1
)

echo [4/6] ����ȯ�� Ȱ��ȭ �� ��Ű�� ��ġ ��...
call "%VENV_DIR%\Scripts\activate.bat"

:: pip ���׷��̵� �� ������ ��ġ (�ڵ� ��ġ �ɼ� ����)
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
pip install "numpy<2.0.0" --force-reinstall --only-binary=:all: --quiet --no-input
pip install pyqt6==6.5.2 pyqt6-qt6==6.5.2 pyqt6-sip==13.5.2 --quiet --no-input
pip install opencv-python==4.9.0.80 pyyaml pyinstaller --quiet --no-input

echo [5/6] PyInstaller�� ���� ��...
pyinstaller --noconfirm --onefile --console ^
  --icon="%ICON_FILE%" ^
  --add-data "ui\\image_shrinker.ui;ui" ^
  --collect-all numpy ^
  --collect-all PyQt6 ^
  ImageShrinker.py >nul 2>&1

if not exist "%IMAGE_EXE%" (
    echo [����] ���� ����: ���� ������ �������� �ʾҽ��ϴ�.
    exit /b 1
)

echo [6/6] ����ȭ�鿡 �ٷΰ��� ���� ��...
:: VBS ��ũ��Ʈ ����
> "%VBS%" echo Set oWS = CreateObject("WScript.Shell")
>> "%VBS%" echo sLinkFile = "%DESKTOP%\%SHORTCUT_NAME%"
>> "%VBS%" echo Set oLink = oWS.CreateShortcut(sLinkFile)
>> "%VBS%" echo oLink.TargetPath = "%IMAGE_EXE%"
>> "%VBS%" echo oLink.WorkingDirectory = "%cd%"
>> "%VBS%" echo oLink.IconLocation = "%ICON_FILE%"
>> "%VBS%" echo oLink.Save

:: �ٷΰ��� ���� ����
cscript //nologo "%VBS%" >nul
del "%VBS%"

echo ��ġ �� ���� �Ϸ�. ����ȭ�鿡�� ImageShrinker�� �����ϼ���.
exit /b 0
