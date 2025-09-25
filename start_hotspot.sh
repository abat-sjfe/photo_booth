#!/bin/bash
set -e

IFACE="wlan0"
SSID="Fotobox"
PASS="Fritz123"
IPADDR="192.168.4.1/24"
LEASE_RANGE="192.168.4.10,192.168.4.50,255.255.255.0,5m"

echo "[1/5] Deaktiviere alle gespeicherten WLAN-Verbindungen auf $IFACE..."
for con in $(nmcli -t -f NAME,DEVICE connection show --active | grep "^.*:${IFACE}" | cut -d: -f1); do
    echo "   Stoppe Verbindung: $con"
    nmcli connection down "$con"
    nmcli connection modify "$con" connection.autoconnect no
done

echo "[2/5] Erstelle Hotspot '$SSID'..."
nmcli connection delete "$SSID" >/dev/null 2>&1 || true
nmcli device set "$IFACE" managed yes
nmcli device wifi hotspot ifname "$IFACE" con-name "$SSID" ssid "$SSID" password "$PASS"

echo "[3/5] Setze feste IP und DHCP-Range..."
nmcli connection modify "$SSID" ipv4.addresses "$IPADDR" ipv4.method shared
sudo mkdir -p /etc/NetworkManager/dnsmasq-shared.d
echo "dhcp-range=$LEASE_RANGE" | sudo tee /etc/NetworkManager/dnsmasq-shared.d/$SSID.conf >/dev/null

echo "[4/5] Aktiviere Hotspot..."
nmcli connection up "$SSID"

echo "[5/5] Hotspot läuft!"
echo "   SSID: $SSID"
echo "   Passwort: $PASS"
echo "   IP: ${IPADDR%/*}"