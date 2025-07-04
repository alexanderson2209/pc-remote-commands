@echo off
REM Build script for server

set "EXE_NAME=pc-remote"

echo Cleaning old build...
rmdir /s /q build
rmdir /s /q dist
del /q %EXE_NAME%.spec

echo Building exe with PyInstaller...
pyinstaller --onefile --windowed --name %EXE_NAME% server.py

echo Copying config.yaml to dist folder...
copy config.yaml dist\

echo Done! Built dist\%EXE_NAME%.exe
pause
