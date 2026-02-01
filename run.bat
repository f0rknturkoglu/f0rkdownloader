@echo off
title f0rkn_d0wnl0ader

set "PATH=%PATH%;%USERPROFILE%\.deno\bin"

for /d %%D in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*") do (
    for /d %%F in ("%%D\ffmpeg-*\bin") do (
        set "PATH=%PATH%;%%F"
    )
)

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe main.py
) else (
    echo Kurulum yapilmamis! Once install.bat calistirin.
    pause
)
