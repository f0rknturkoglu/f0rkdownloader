@echo off
chcp 65001 >nul
title f0rkn_d0wnl0ader - Build

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║           f0rkn_d0wnl0ader - EXE Olusturucu                   ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

:: Activate venv
call .venv\Scripts\activate.bat

:: Install PyInstaller if not present
echo [1/3] PyInstaller kontrol ediliyor...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller yukleniyor...
    pip install pyinstaller
)
echo [OK] PyInstaller hazir

:: Build
echo.
echo [2/3] EXE olusturuluyor...
pyinstaller --onefile ^
    --name "f0rkn_d0wnl0ader" ^
    --console ^
    --add-data "src;src" ^
    --hidden-import "yt_dlp" ^
    --hidden-import "yt_dlp_ejs" ^
    --hidden-import "gallery_dl" ^
    --hidden-import "rich" ^
    --hidden-import "questionary" ^
    --hidden-import "pycryptodomex" ^
    --hidden-import "brotli" ^
    --collect-all "yt_dlp" ^
    --collect-all "gallery_dl" ^
    main.py

if errorlevel 1 (
    echo [HATA] Build basarisiz!
    pause
    exit /b 1
)

echo.
echo [3/3] Temizlik yapiliyor...
rd /s /q build 2>nul
del /q *.spec 2>nul

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                    Build Tamamlandi!                          ║
echo ╠═══════════════════════════════════════════════════════════════╣
echo ║  EXE dosyasi: dist\f0rkn_d0wnl0ader.exe                       ║
echo ║                                                               ║
echo ║  NOT: EXE calistirmak icin ayni dizinde olmali:               ║
echo ║  - ffmpeg.exe                                                 ║
echo ║  - deno.exe (veya PATH'te)                                    ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.
pause
