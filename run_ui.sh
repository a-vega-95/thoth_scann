#!/usr/bin/env bash
# Thoth Scann - Launcher de la Interfaz Web
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "[AVISO] Entorno virtual .venv no encontrado. Intentando ejecutar con el Python del sistema..."
fi

echo "[INFO] Iniciando Thoth Scann UI..."
streamlit run app.py --server.port 8501 --server.headless false
