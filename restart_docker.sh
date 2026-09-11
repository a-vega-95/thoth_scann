#!/usr/bin/env bash
# Thoth Scann - Script para reconstruir y reiniciar el contenedor Docker
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "[INFO] Reconstruyendo y reiniciando el contenedor Docker para Thoth Scann..."

# Detectar si se requiere sudo para ejecutar Docker
DOCKER_CMD="docker"
if ! docker ps > /dev/null 2>&1; then
    echo "[AVISO] Se requiere elevación de permisos (sudo) para acceder al socket de Docker."
    DOCKER_CMD="sudo docker"
fi

# Detener contenedor existente si está corriendo
$DOCKER_CMD compose down || true

# Reconstruir la imagen asegurando que tome los últimos cambios sin usar caché obsoleta
$DOCKER_CMD compose build --no-cache

# Levantar el servicio forzando la recreación del contenedor
$DOCKER_CMD compose up -d --force-recreate

echo ""
echo "[OK] Contenedor reiniciado y ejecutándose con éxito."
echo "[INFO] Disponible en: http://localhost:8501"
echo "[INFO] Estado actual del contenedor:"
$DOCKER_CMD compose ps
