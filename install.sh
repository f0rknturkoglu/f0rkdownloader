#!/bin/bash

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           f0rkn_d0wnl0ader - Kurulum Scripti                  ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
echo "[1/5] Python kontrol ediliyor..."
if ! command -v python3 &> /dev/null; then
    echo "[HATA] Python3 bulunamadı!"
    echo "Python 3.10+ yükleyin"
    exit 1
fi
echo "[OK] Python bulundu: $(python3 --version)"

# Create virtual environment
echo ""
echo "[2/5] Sanal ortam oluşturuluyor..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "[OK] Sanal ortam oluşturuldu"
else
    echo "[OK] Sanal ortam mevcut"
fi

# Activate and install dependencies
echo ""
echo "[3/5] Bağımlılıklar yükleniyor..."
source .venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[HATA] Bağımlılıklar yüklenemedi!"
    exit 1
fi
echo "[OK] Bağımlılıklar yüklendi"

# Install FFmpeg
echo ""
echo "[4/5] FFmpeg kontrol ediliyor..."
if ! command -v ffmpeg &> /dev/null; then
    echo "FFmpeg bulunamadı, yükleniyor..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ffmpeg
        else
            echo "[UYARI] Homebrew bulunamadı. FFmpeg manuel yükleyin."
        fi
    else
        # Linux
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y ffmpeg
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y ffmpeg
        elif command -v pacman &> /dev/null; then
            sudo pacman -S ffmpeg
        else
            echo "[UYARI] Paket yöneticisi bulunamadı. FFmpeg manuel yükleyin."
        fi
    fi
else
    echo "[OK] FFmpeg mevcut"
fi

# Install Deno
echo ""
echo "[5/5] Deno kontrol ediliyor..."
if ! command -v deno &> /dev/null; then
    echo "Deno bulunamadı, yükleniyor..."
    curl -fsSL https://deno.land/install.sh | sh
    export DENO_INSTALL="$HOME/.deno"
    export PATH="$DENO_INSTALL/bin:$PATH"
    echo "[OK] Deno yüklendi"
else
    echo "[OK] Deno mevcut"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    Kurulum Tamamlandı!                        ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║  Çalıştırmak için: ./run.sh                                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
