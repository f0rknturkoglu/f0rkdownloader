#!/bin/bash

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           f0rkn_d0wnl0ader - Kurulum Scripti                  ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Find suitable Python version
PYTHON_CMD=""

for cmd in python3.12 python3.11 python3.10 python3; do
    if command -v $cmd &> /dev/null; then
        VERSION=$($cmd -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        major=$(echo $VERSION | cut -d. -f1)
        minor=$(echo $VERSION | cut -d. -f2)
        
        if [ "$major" -eq 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON_CMD=$cmd
            PY_VERSION=$VERSION
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "[HATA] Python 3.10+ bulunamadı!"
    echo "Mevcut python3 sürümünüz: $(python3 --version 2>&1)"
    echo "Lütfen Python 3.10 veya daha yeni bir sürüm yükleyin."
    exit 1
fi

echo "[OK] Uygun Python bulundu: $PYTHON_CMD ($PY_VERSION)"

# Create virtual environment
echo ""
echo "[2/5] Sanal ortam oluşturuluyor..."
if [ -d ".venv" ]; then
    echo "Eski sanal ortam temizleniyor..."
    rm -rf .venv
fi

$PYTHON_CMD -m venv .venv
if [ $? -ne 0 ]; then
    echo "[HATA] Sanal ortam oluşturulamadı!"
    exit 1
fi
echo "[OK] Sanal ortam oluşturuldu"

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
        if command -v brew &> /dev/null; then
            brew install ffmpeg
        else
            echo "[UYARI] Homebrew bulunamadı. FFmpeg manuel yükleyin."
        fi
    else
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y ffmpeg
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
