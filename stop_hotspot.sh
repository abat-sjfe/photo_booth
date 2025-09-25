#!/bin/bash
set -e

IFACE="wlan0"

echo "🔹 Schalte Raspberry Pi in Client-Modus..."

# Hotspot-Dienste stoppen & deaktivieren
sudo systemctl stop hostapd || true
sudo systemctl stop dnsmasq || true
sudo systemctl disable hostapd || true
sudo systemctl disable dnsmasq || true

# wpa_supplicant für Client-WLAN aktivieren
sudo systemctl enable wpa_supplicant || true
sudo systemctl start wpa_supplicant || true

# DHCP-Einstellungen wiederherstellen
sudo sed -i "/^interface $IFACE/d" /etc/dhcpcd.conf
sudo systemctl restart dhcpcd

echo "✅ Client-Modus aktiv!"
echo "   Du kannst dich jetzt mit 'nmcli' oder 'raspi-config' ins WLAN verbinden."