#!/bin/bash
set -e

###############################################################################
# Raspberry Pi Hotspot Setup (hostapd + dnsmasq)
# Diese Variante ist sehr stabil und unabhängig vom NetworkManager.
#
# Ablauf:
# 1. Installiert notwendige Pakete
# 2. Konfiguriert statische IP für wlan0
# 3. Erstellt hostapd-Konfiguration (SSID & Passwort)
# 4. Erstellt dnsmasq-Konfiguration (DHCP)
# 5. Aktiviert und startet hostapd/dnsmasq
#
###############################################################################

# ===== Parameter =====
IFACE="wlan0"
SSID="Fotobox"
PASS="Fritz123"
STATIC_IP="192.168.4.1"
NETMASK="255.255.255.0"
LEASE_RANGE="192.168.4.10,192.168.4.50,255.255.255.0,5m"

echo "[1/6] Installiere benötigte Pakete..."
sudo apt update
sudo apt install -y hostapd dnsmasq

echo "[2/6] Konfiguriere statische IP für $IFACE..."
sudo bash -c "cat > /etc/dhcpcd.conf" <<EOF
interface $IFACE
static ip_address=$STATIC_IP/24
nohook wpa_supplicant
EOF
sudo systemctl restart dhcpcd

echo "[3/6] Erstelle hostapd-Konfiguration..."
sudo bash -c "cat > /etc/hostapd/hostapd.conf" <<EOF
interface=$IFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASS
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

sudo sed -i "s|#DAEMON_CONF=\"\"|DAEMON_CONF=\"/etc/hostapd/hostapd.conf\"|" /etc/default/hostapd

echo "[4/6] Erstelle dnsmasq-Konfiguration..."
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig || true
sudo bash -c "cat > /etc/dnsmasq.conf" <<EOF
interface=$IFACE
dhcp-range=$LEASE_RANGE
EOF

echo "[5/6] Dienste aktivieren..."
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

echo "[6/6] Dienste starten..."
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq

echo ""
echo "? Hostapd/Dnsmasq-Hotspot gestartet!"
echo "   SSID: $SSID"
echo "   Passwort: $PASS"
echo "   IP: $STATIC_IP"
echo "   DHCP-Range: $LEASE_RANGE"
echo ""
echo "Mit einem Gerät ins WLAN '$SSID' einwählen und im Browser http://$STATIC_IP:8000 öffnen."