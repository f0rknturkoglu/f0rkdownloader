@echo off
chcp 65001 >nul
title f0rkn_d0wnl0ader Kurulum

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║           f0rkn_d0wnl0ader - Kurulum Scripti                  ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

:: Check Python
echo [1/5] Python kontrol ediliyor...
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi!
    echo Python 3.10+ yukleyin: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python bulundu

:: Create virtual environment
echo.
echo [2/5] Sanal ortam olusturuluyor...
if not exist ".venv" (
    python -m venv .venv
    echo [OK] Sanal ortam olusturuldu
) else (
    echo [OK] Sanal ortam mevcut
)

:: Activate and install dependencies
echo.
echo [3/5] Bagimliliklar yukleniyor...
call .venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo [HATA] Bagimliliklar yuklenemedi!
    pause
    exit /b 1
)
echo [OK] Bagimliliklar yuklendi

:: Install FFmpeg
echo.
echo [4/5] FFmpeg kontrol ediliyor...
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo FFmpeg bulunamadi, yukleniyor...
    winget install --id=Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements >nul 2>&1
    if errorlevel 1 (
        echo [UYARI] FFmpeg otomatik yuklenemedi.
        echo Manuel olarak yukleyin: https://ffmpeg.org/download.html
    ) else (
        echo [OK] FFmpeg yuklendi
    )
) else (
    echo [OK] FFmpeg mevcut
)

:: Install Deno
echo.
echo [5/5] Deno kontrol ediliyor...
where deno >nul 2>&1
if errorlevel 1 (
    echo Deno bulunamadi, yukleniyor...
    winget install --id=DenoLand.Deno -e --accept-package-agreements --accept-source-agreements >nul 2>&1
    if errorlevel 1 (
        echo [UYARI] Deno otomatik yuklenemedi.
        echo Manuel olarak yukleyin: https://deno.land/
    ) else (
        echo [OK] Deno yuklendi
    )
) else (
    echo [OK] Deno mevcut
)

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                    Kurulum Tamamlandi!                        ║
echo ╠═══════════════════════════════════════════════════════════════╣
echo ║  Calistirmak icin: run.bat                                    ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.
pause
