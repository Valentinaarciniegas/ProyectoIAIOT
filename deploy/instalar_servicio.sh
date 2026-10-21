#!/usr/bin/env bash
# Instala la app como servicio systemd. Ejecutar con: sudo bash deploy/instalar_servicio.sh
set -euo pipefail
cd "$(dirname "$0")"

echo "==> 1/4 Deteniendo la app de prueba (python app.py) si estaba corriendo"
pkill -f 'venv/bin/python app.py' && sleep 2 || echo "   no estaba corriendo"

echo "==> 2/4 Copiando cocatrace.service a /etc/systemd/system/"
install -m 644 cocatrace.service /etc/systemd/system/cocatrace.service

echo "==> 3/4 Activando el servicio (arranca ahora y en cada reinicio)"
systemctl daemon-reload
systemctl enable --now cocatrace
sleep 3

echo "==> 4/4 Verificando"
systemctl --no-pager status cocatrace | head -n 5
curl -s http://127.0.0.1:5000/health; echo
echo "==> LISTO: servicio cocatrace instalado"
