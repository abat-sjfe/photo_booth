#!/bin/bash
set -e

echo "[Hotspot] Installiere benötigte Pakete..."
sudo apt update
sudo apt install -y hostapd dnsmasq

echo "[Hotspot] Konfiguriere Hostapd..."
sudo bash -c 'cat > /etc/hostapd/hostapd.conf <<EOF
interface=wlan0
driver=nl80211
ssid=Fotobox
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=0
EOF'

sudo sed -i 's|#DAEMON_CONF=".*"|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd

echo "[Hotspot] Setze feste IP-Adresse für wlan0..."
grep -q "interface wlan0" /etc/dhcpcd.conf || sudo bash -c 'cat >> /etc/dhcpcd.conf <<EOF

interface wlan0
static ip_address=192.168.4.1/24
nohook wpa_supplicant
EOF'

echo "[Hotspot] Konfiguriere DNSmasq..."
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig || true
sudo bash -c 'cat > /etc/dnsmasq.conf <<EOF
interface=wlan0
dhcp-range=192.168.4.10,192.168.4.50,255.255.255.0,24h
EOF'

echo "[Hotspot] Aktivierte Dienste..."
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

echo "[Hotspot] Konfiguration abgeschlossen!"
echo "Du kannst nun mit ./start_hotspot.sh den Access Point starten."