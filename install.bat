@chcp 949 >nul
@echo off
setlocal enabledelayedexpansion


:: 경로 설정
set VENV_DIR=%cd%\venv
set IMAGE_EXE=%cd%\dist\ImageShrinker.exe
set ICON_FILE=%cd%\icon\run.ico
set SHORTCUT_NAME=ImageShrinker.lnk
set DESKTOP=%USERPROFILE%\Desktop
set VBS=%TEMP%\create_shortcut.vbs

echo [1/6] Python 설치 확인 중...
where python >nul 2>&1
if errorlevel 1 (
    echo [오류] Python 명령을 찾을 수 없습니다. 설치 또는 PATH 설정을 확인하세요.
    pause
    exit /b 1
)

echo [2/6] 기존 가상환경 제거 중...
if exist "%VENV_DIR%" (
    rmdir /s /q "%VENV_DIR%"
)

echo [3/6] 가상환경 생성 중...
python -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo [오류] 가상환경 생성 실패
    pause
    exit /b 1
)

echo [4/6] 가상환경 활성화 및 패키지 설치 중...
call "%VENV_DIR%\Scripts\activate.bat"

:: pip 업그레이드 및 의존성 설치
python -m pip install --upgrade pip setuptools wheel
pip install "numpy<2.0.0" --force-reinstall --only-binary=:all: --no-input
pip install pyqt6==6.5.2 pyqt6-qt6==6.5.2 pyqt6-sip==13.5.2 --no-input
pip install opencv-python==4.9.0.80 pyyaml pyinstaller --no-input

echo [5/6] PyInstaller로 빌드 중...
pyinstaller --noconfirm --onefile --console ^
  --icon="%ICON_FILE%" ^
  --add-data "ui\\image_shrinker.ui;ui" ^
  --collect-all numpy ^
  --collect-all PyQt6 ^
  ImageShrinker.py

if not exist "%IMAGE_EXE%" (
    echo [오류] 빌드 실패: 실행 파일이 생성되지 않았습니다.
    pause
    exit /b 1
)

echo [6/6] 바탕화면에 바로가기 생성 중...
:: VBS 스크립트 생성
> "%VBS%" echo Set oWS = CreateObject("WScript.Shell")
>> "%VBS%" echo sLinkFile = "%DESKTOP%\%SHORTCUT_NAME%"
>> "%VBS%" echo Set oLink = oWS.CreateShortcut(sLinkFile)
>> "%VBS%" echo oLink.TargetPath = "%IMAGE_EXE%"
>> "%VBS%" echo oLink.WorkingDirectory = "%cd%"
>> "%VBS%" echo oLink.IconLocation = "%ICON_FILE%"
>> "%VBS%" echo oLink.Save

:: 바로가기 생성 실행
cscript //nologo "%VBS%" >nul
del "%VBS%"

echo.
echo 설치 및 빌드 완료. 바탕화면에서 ImageShrinker를 실행하세요.
pause
exit /b 0
