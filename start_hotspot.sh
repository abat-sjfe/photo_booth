#!/bin/bash
set -e
echo "[Hotspot] Starte WLAN Access Point 'Fotobox'..."
sudo systemctl start hostapd
sudo systemctl start dnsmasq
echo "[Hotspot] Fertig. Netzwerk 'Fotobox' läuft jetzt mit Passwort 'Fritz123' und 5-Minuten-Lease."