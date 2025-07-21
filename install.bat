@echo off
setlocal

set PY_VER=3.10.11
set PY_DIR=%cd%\python
set VENV_DIR=%cd%\venv
set IMAGE_WS=%cd%\workspace
set IMAGE_EXE=%cd%\dist\ImageShrinker.exe
set ICON_FILE=%cd%\icon\run.ico
set SHORTCUT_NAME=ImageShrinker.lnk
set DESKTOP=%USERPROFILE%\Desktop

echo.
echo [1/6] Python 설치 확인 중...
if not exist "%PY_DIR%\python.exe" (
    echo [1/6] Python 설치 중...
    python-%PY_VER%-amd64.exe /quiet InstallAllUsers=0 TargetDir=%PY_DIR% PrependPath=0 Include_test=0
)

echo.
echo [2/6] 가상환경 생성 중...
"%PY_DIR%\python.exe" -m venv "%VENV_DIR%"

echo.
echo [3/6] 가상환경 활성화 및 라이브러리 설치 중...
call "%VENV_DIR%\Scripts\activate.bat"
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [4/6] PyInstaller로 빌드 중...
pyinstaller --onefile --icon="%ICON_FILE%" --console --add-data "ui/image_shrinker.ui;ui" ImageShrinker.py

echo.
echo [5/6] 환경 변수 설정...
setx IMAGESHRINKER_WS "%IMAGE_WS%" > nul

echo.
echo [6/6] 바탕화면에 바로가기 생성...
set VBS=%TEMP%\create_shortcut.vbs
> "%VBS%" echo Set oWS = CreateObject("WScript.Shell")
>> "%VBS%" echo sLinkFile = "%DESKTOP%\%SHORTCUT_NAME%"
>> "%VBS%" echo Set oLink = oWS.CreateShortcut(sLinkFile)
>> "%VBS%" echo oLink.TargetPath = "%IMAGE_EXE%"
>> "%VBS%" echo oLink.WorkingDirectory = "%cd%"
>> "%VBS%" echo oLink.IconLocation = "%ICON_FILE%"
>> "%VBS%" echo oLink.Save

cscript //nologo "%VBS%"
del "%VBS%"

echo.
echo 설치 및 빌드 완료! 바탕화면의 바로가기 아이콘으로 실행하세요.
pause
