@echo off
REM ===================================================
REM Usage: switch_to_tv_profile.bat <profile_name>
REM Example: switch_to_tv_profile.bat LivingRoomTV
REM ===================================================

if "%~1"=="" (
    echo Usage: %~nx0 ^<profile_name^>
    exit /b 1
)

set "PROFILE_NAME=%~1"
set "USERNAME=%USERNAME%"
set "PROFILE_PATH=C:\Users\%USERNAME%\AppData\Roaming\MonitorSwitcher\Profiles\%PROFILE_NAME%.xml"
set "EXE_PATH=D:\MonitorProfileSwitcher_v0700\MonitorSwitcher.exe"

echo Switching profile: %PROFILE_PATH%
"%EXE_PATH%" -load:"%PROFILE_PATH%"