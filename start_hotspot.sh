#!/bin/bash
set -e

echo "[Hotspot] Starte WLAN Access Point 'Fotobox'..."
sudo systemctl start hostapd
sudo systemctl start dnsmasq
echo "[Hotspot] Fertig. Netzwerk 'Fotobox' läuft jetzt."