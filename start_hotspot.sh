#!/bin/bash
set -e

###############################################################################
# Raspberry Pi Hotspot mit NetworkManager (nmcli)
# Verbesserungen:
# - Kein Neustart des NetworkManager (hält Hotspot stabil)
# - Interface explizit managed setzen
# - Alte Verbindung vorher löschen
# - DHCP-Range über dnsmasq-shared-Verzeichnis setzen
###############################################################################

# ===== Parameter =====
IFACE="wlan0"       # ggf. anpassen (prüfen mit: ip link show)
SSID="Fotobox"
PASS="Fritz123"
IPADDR="192.168.4.1/24"
LEASE_RANGE="192.168.4.10,192.168.4.50,255.255.255.0,5m"

echo "[1/4] Prüfe ob NetworkManager installiert ist..."
if ! command -v nmcli >/dev/null 2>&1; then
    echo "⚠ NetworkManager ist nicht installiert. Installiere..."
    sudo apt update
    sudo apt install -y network-manager
fi

echo "[2/4] Erstelle Hotspot '$SSID'..."
# Vorher ggf. alte Verbindung löschen
nmcli connection delete "$SSID" >/dev/null 2>&1 || true

# Interface durch NM verwalten lassen
nmcli device set "$IFACE" managed yes

# Hotspot starten
nmcli device wifi hotspot ifname "$IFACE" con-name "$SSID" ssid "$SSID" password "$PASS"

echo "[3/4] Setze feste IP $IPADDR und DHCP-Range..."
nmcli connection modify "$SSID" ipv4.addresses "$IPADDR" ipv4.method shared

sudo mkdir -p /etc/NetworkManager/dnsmasq-shared.d
echo "dhcp-range=$LEASE_RANGE" | sudo tee /etc/NetworkManager/dnsmasq-shared.d/$SSID.conf >/dev/null

# Verbindung aktivieren (ohne Neustart von NetworkManager)
nmcli connection up "$SSID"

echo "[4/4] Hotspot läuft!"
echo ""
echo "✅ Hotspot '$SSID' gestartet!"
echo "   Passwort: $PASS"
echo "   IP: ${IPADDR%/*}"
echo "   DHCP-Lease: 5 Minuten"
echo ""
echo "Mit einem Gerät ins WLAN '$SSID' einwählen und im Browser http://${IPADDR%/*}:8000 öffnen."