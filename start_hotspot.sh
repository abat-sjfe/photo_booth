#!/bin/bash
set -e

# ===== Parameter für Hotspot =====
IFACE="wlan0"
SSID="Fotobox"
PASS="Fritz123"
STATIC_IP="192.168.4.1"
LEASE_RANGE="192.168.4.10,192.168.4.50,255.255.255.0,5m"
COUNTRY_CODE="DE"

echo "🔹 Starte Hotspot-only Modus..."

# wpa_supplicant stoppen und deaktivieren
sudo systemctl stop wpa_supplicant || true
sudo systemctl disable wpa_supplicant || true

# Statische IP setzen
sudo sed -i "/^interface $IFACE/d" /etc/dhcpcd.conf
sudo bash -c "cat >> /etc/dhcpcd.conf" <<EOF
interface $IFACE
static ip_address=$STATIC_IP/24
nohook wpa_supplicant
EOF
sudo systemctl restart dhcpcd

# Hostapd-Konfiguration
sudo bash -c "cat > /etc/hostapd/hostapd.conf" <<EOF
country_code=$COUNTRY_CODE
interface=$IFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=6
wmm_enabled=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASS
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF
sudo sed -i "s|#DAEMON_CONF=\"\"|DAEMON_CONF=\"/etc/hostapd/hostapd.conf\"|" /etc/default/hostapd

# dnsmasq-Konfiguration
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig 2>/dev/null || true
sudo bash -c "cat > /etc/dnsmasq.conf" <<EOF
interface=$IFACE
dhcp-range=$LEASE_RANGE
EOF

# Dienste starten
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq

echo "✅ Hotspot gestartet!"
echo "   SSID: $SSID"
echo "   Passwort: $PASS"
echo "   IP: $STATIC_IP"