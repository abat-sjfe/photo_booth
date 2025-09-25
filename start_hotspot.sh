#!/bin/bash
set -e

###############################################################################
# Raspberry Pi Hotspot Setup (STABIL: hostapd + dnsmasq ohne wpa_supplicant)
#
# Ablauf:
# 1. Installiert hostapd und dnsmasq
# 2. Schaltet wpa_supplicant für wlan0 aus (verhindert AP-Abbruch)
# 3. Schaltet WLAN-Powersave aus
# 4. Setzt Country Code (DE) in hostapd.conf
# 5. Nutzt statische IP via dhcpcd.conf
# 6. Aktiviert und startet Hotspot-Dienste
###############################################################################

# ===== Parameter =====
IFACE="wlan0"
SSID="Fotobox"
PASS="Fritz123"
STATIC_IP="192.168.4.1"
LEASE_RANGE="192.168.4.10,192.168.4.50,255.255.255.0,5m"
COUNTRY_CODE="DE"

echo "[1/8] Installiere benötigte Pakete..."
sudo apt update
sudo apt install -y hostapd dnsmasq

echo "[2/8] Stoppe und deaktiviere wpa_supplicant für $IFACE..."
sudo systemctl stop wpa_supplicant@$IFACE.service || true
sudo systemctl disable wpa_supplicant@$IFACE.service || true

echo "[3/8] Deaktiviere WLAN-Powersave..."
sudo iw dev $IFACE set power_save off
# Dauerhaft:
if ! grep -q "iw dev $IFACE set power_save off" /etc/rc.local; then
    sudo sed -i "/^exit 0/i iw dev $IFACE set power_save off" /etc/rc.local
fi

echo "[4/8] Setze statische IP für $IFACE..."
sudo sed -i "/^interface $IFACE/d" /etc/dhcpcd.conf
sudo bash -c "cat >> /etc/dhcpcd.conf" <<EOF
interface $IFACE
static ip_address=$STATIC_IP/24
nohook wpa_supplicant
EOF
sudo systemctl restart dhcpcd

echo "[5/8] Erstelle hostapd-Konfiguration..."
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

echo "[6/8] Erstelle dnsmasq-Konfiguration..."
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig 2>/dev/null || true
sudo bash -c "cat > /etc/dnsmasq.conf" <<EOF
interface=$IFACE
dhcp-range=$LEASE_RANGE
EOF

echo "[7/8] Aktivieren der Hotspot-Dienste..."
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

echo "[8/8] Starten der Hotspot-Dienste..."
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq

echo ""
echo "✅ Stabiler Hotspot gestartet!"
echo "   SSID: $SSID"
echo "   Passwort: $PASS"
echo "   IP: $STATIC_IP"
echo "   DHCP-Range: $LEASE_RANGE"
echo ""
echo "Mit einem Gerät ins WLAN '$SSID' verbinden und im Browser http://$STATIC_IP:8000 öffnen."