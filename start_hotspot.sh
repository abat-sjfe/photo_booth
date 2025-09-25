#!/bin/bash
set -e

IFACE="wlan0"
SSID="Fotobox"
PASS="Fritz123"
IPADDR="192.168.4.1/24"
LEASE_RANGE="192.168.4.10,192.168.4.50,255.255.255.0,5m"

echo "[1/6] Stoppe alle aktiven WLAN-Verbindungen..."
ACTIVE_CONS=$(nmcli -t -f NAME,DEVICE connection show --active | grep ":${IFACE}" | cut -d: -f1 || true)
for con in $ACTIVE_CONS; do
    echo "   Stoppe $con und deaktiviere Autoconnect..."
    nmcli connection down "$con"
    nmcli connection modify "$con" connection.autoconnect no
done

echo "[2/6] Schalte WLAN aus/ein um Interface zu resetten..."
nmcli radio wifi off
sleep 2
nmcli radio wifi on

echo "[3/6] Erstelle Hotspot '$SSID'..."
nmcli connection delete "$SSID" >/dev/null 2>&1 || true
nmcli device set "$IFACE" managed yes
nmcli device wifi hotspot ifname "$IFACE" con-name "$SSID" ssid "$SSID" password "$PASS"

echo "[4/6] Setze feste IP und DHCP-Range..."
nmcli connection modify "$SSID" ipv4.addresses "$IPADDR" ipv4.method shared

sudo mkdir -p /etc/NetworkManager/dnsmasq-shared.d
echo "dhcp-range=$LEASE_RANGE" | sudo tee /etc/NetworkManager/dnsmasq-shared.d/$SSID.conf >/dev/null

echo "[5/6] Aktivieren des Hotspots..."
nmcli connection up "$SSID"

echo "[6/6] Hotspot läuft!"
echo "   SSID: $SSID"
echo "   Passwort: $PASS"
echo "   IP: ${IPADDR%/*}"
echo ""
echo "Mit einem Gerät ins WLAN '$SSID' einwählen und im Browser http://${IPADDR%/*}:8000 öffnen."