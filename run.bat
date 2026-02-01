@echo off
chcp 65001 >nul
title f0rkn_d0wnl0ader

:: Refresh PATH for Deno
set "PATH=%PATH%;%USERPROFILE%\.deno\bin"

:: Add FFmpeg from WinGet packages (find dynamically)
for /d %%D in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*") do (
    for /d %%F in ("%%D\ffmpeg-*\bin") do (
        set "PATH=%PATH%;%%F"
    )
)

:: Run the application
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe main.py
) else (
    echo Kurulum yapilmamis! Once install.bat calistirin.
    pause
)
