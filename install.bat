@echo off
setlocal enabledelayedexpansion

:: ȯ�溯�� �ʱ�ȭ
set PYTHONHOME=
set PYTHONPATH=
set PATH=%SystemRoot%\system32;%SystemRoot%;%SystemRoot%\System32\Wbem

:: ��� ����
set VENV_DIR=%cd%\venv
set IMAGE_EXE=%cd%\dist\ImageShrinker.exe
set ICON_FILE=%cd%\icon\run.ico
set SHORTCUT_NAME=ImageShrinker.lnk
set DESKTOP=%USERPROFILE%\Desktop

echo [1/6] Python ��ġ Ȯ�� ��...
py -V >nul 2>&1
if errorlevel 1 (
    echo [����] py ����� �������� �ʽ��ϴ�. Python�� ��ġ�Ǿ� �ִ��� Ȯ���ϼ���.
    pause
    exit /b
)

echo.
echo [2/6] ���� ����ȯ�� ���� ��...
if exist "%VENV_DIR%" (
    echo ���� ����ȯ���� �����մϴ�...
    rmdir /s /q "%VENV_DIR%"
)

echo.
echo [3/6] ����ȯ�� ���� ��...
py -m venv "%VENV_DIR%" || (
    echo [����] ����ȯ�� ���� ����
    pause
    exit /b
)

echo.
echo [4/6] ����ȯ�� Ȱ��ȭ �� ��Ű�� ��ġ ��...
call "%VENV_DIR%\Scripts\activate.bat"

:: pip ���׷��̵�
call python -m pip install --upgrade pip setuptools wheel

:: numpy �ٿ�׷��̵� (�ʼ�)
call pip install "numpy<2.0.0" --force-reinstall --only-binary=:all:

:: PyQt6 ���� ���� (DLL �浹 ����)
call pip install pyqt6==6.5.2 pyqt6-qt6==6.5.2 pyqt6-sip==13.5.2

:: �ʼ� ��Ű�� ��ġ
call pip install opencv-python==4.9.0.80 pyyaml pyinstaller

echo.
echo [5/6] PyInstaller�� ���� ��...
call pyinstaller --noconfirm --onefile --console ^
  --icon="%ICON_FILE%" ^
  --add-data "ui/image_shrinker.ui;ui" ^
  --collect-all numpy ^
  --collect-all PyQt6 ^
  ImageShrinker.py

if not exist "%IMAGE_EXE%" (
    echo [����] ���� ����: ���� ������ �������� �ʾҽ��ϴ�.
    pause
    exit /b
)

echo.
echo [6/6] ����ȭ�鿡 �ٷΰ��� ���� ��...
set VBS=%TEMP%\create_shortcut.vbs
> "%VBS%" echo Set oWS = CreateObject("WScript.Shell")
>> "%VBS%" echo sLinkFile = "%DESKTOP%\%SHORTCUT_NAME%"
>> "%VBS%" echo Set oLink = oWS.CreateShortcut(sLinkFile)
>> "%VBS%" echo oLink.TargetPath = "%IMAGE_EXE%"
>> "%VBS%" echo oLink.WorkingDirectory = "%cd%"
>> "%VBS%" echo oLink.IconLocation = "%ICON_FILE%"
>> "%VBS%" echo oLink.Save

cscript //nologo "%VBS%" >nul
del "%VBS%"

echo.
echo ��ġ �� ���� �Ϸ�! ����ȭ�鿡�� �����ϼ���.
pause
