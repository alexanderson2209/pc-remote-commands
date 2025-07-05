@echo off
REM Build script for server

setlocal
set "EXE_NAME=pc-remote"
set "SWITCHER_URL=https://sourceforge.net/projects/monitorswitcher/files/MonitorProfileSwitcher_v0700.zip/download"
set "ZIP_NAME=profile_switcher.zip"
set "TARGET_DIR=3rd-party"
set "TARGET_EXE=%TARGET_DIR%\MonitorSwitcher.exe"
set "TEMP_UNZIP_DIR=tmp_unzip"

REM Create 3rd-party if it doesn't exist
if not exist "%TARGET_DIR%" (
    mkdir "%TARGET_DIR%"
)

REM Step 1: Check if MonitorSwitcher.exe exists
if exist "%TARGET_EXE%" (
    echo MonitorSwitcher.exe already exists. Skipping download.
) else (
    echo MonitorSwitcher.exe not found. Downloading and extracting...

    REM Download the zip
    powershell -Command "Invoke-WebRequest -Uri '%SWITCHER_URL%' -OutFile '%ZIP_NAME%' -Headers @{ 'User-Agent' = 'Wget' }"

    REM Unzip to temp folder
    mkdir "%TEMP_UNZIP_DIR%"
    powershell -Command "Expand-Archive -Path '%ZIP_NAME%' -DestinationPath '%TEMP_UNZIP_DIR%'"

    REM Find MonitorSwitcher.exe and copy to 3rd-party
    for /r "%TEMP_UNZIP_DIR%" %%F in (MonitorSwitcher.exe) do (
        echo Found: %%F
        copy "%%F" "%TARGET_EXE%"
        goto :copied
    )

    echo ERROR: MonitorSwitcher.exe not found in zip!
    exit /b 1

    :copied
    echo Copy successful.

    REM Clean up temp unzip and zip
    rmdir /s /q "%TEMP_UNZIP_DIR%"
    del "%ZIP_NAME%"
)

echo Cleaning old build...
rmdir /s /q build
rmdir /s /q dist
del /q "%EXE_NAME%.spec"

echo Building exe with PyInstaller...
pyinstaller --onefile --windowed --hidden-import=plyer.platforms.win.notification --icon="static\icon.ico" --add-data "static;static" --add-data "3rd-party;3rd-party" --name "%EXE_NAME%" server.py

echo Copying config.yaml to dist folder...
copy config.yaml dist\

echo Done! Built dist\%EXE_NAME%.exe
pause
