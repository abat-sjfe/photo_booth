#!/bin/bash
set -e

# ===== Parameter =====
IFACE="wlan0"       # ggf. anpassen falls dein WLAN Interface anders heißt (prüfen mit "ip link show")
SSID="Fotobox"
PASS="Fritz123"
IPADDR="192.168.4.1/24"
LEASE_RANGE="192.168.4.10,192.168.4.50,255.255.255.0,5m"

echo "[1/5] Prüfe ob NetworkManager vorhanden ist..."
if ! command -v nmcli >/dev/null 2>&1; then
    echo "⚠ NetworkManager ist nicht installiert. Installiere..."
    sudo apt update
    sudo apt install -y network-manager
fi

echo "[2/5] Erstelle Hotspot '$SSID'..."
nmcli connection delete "$SSID" >/dev/null 2>&1 || true
nmcli device wifi hotspot ifname "$IFACE" con-name "$SSID" ssid "$SSID" password "$PASS"

echo "[3/5] Setze feste IP $IPADDR..."
nmcli connection modify "$SSID" ipv4.addresses "$IPADDR" ipv4.method shared

echo "[4/5] Setze DHCP-Lease-Zeit auf 5 Minuten..."
sudo mkdir -p /etc/NetworkManager/dnsmasq-shared.d
echo "dhcp-range=$LEASE_RANGE" | sudo tee /etc/NetworkManager/dnsmasq-shared.d/$SSID.conf >/dev/null

echo "[5/5] Starte Hotspot..."
sudo systemctl restart NetworkManager
nmcli connection up "$SSID"

echo ""
echo "✅ Hotspot '$SSID' gestartet!"
echo "   Passwort: $PASS"
echo "   IP: ${IPADDR%/*}"
echo "   DHCP-Lease: 5 Minuten"
echo ""
echo "Mit einem Gerät ins WLAN '$SSID' einwählen und dann im Fotobox-QR-Code http://${IPADDR%/*}:8000 verwenden."