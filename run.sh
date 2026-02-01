#!/bin/bash

# Add Deno to PATH if installed
export DENO_INSTALL="$HOME/.deno"
export PATH="$DENO_INSTALL/bin:$PATH"

# Run the application
if [ -f ".venv/bin/python" ]; then
    .venv/bin/python main.py
else
    echo "Kurulum yapılmamış! Önce ./install.sh çalıştırın."
fi
