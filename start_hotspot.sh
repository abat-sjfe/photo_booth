#!/bin/bash
set -e

###############################################################################
# Raspberry Pi Hotspot Script (NMCLI)
#
# Troubleshooting-Anleitung:
# 1️⃣ Prüfen, ob das WLAN-Interface im Access-Point-Modus funktioniert:
#     nmcli device wifi hotspot ifname wlan0 ssid TestAP password "12345678"
#     Falls Fehlermeldung "Device does not support AP mode" → Treiberproblem,
#     dann musst du hostapd + dnsmasq verwenden (siehe Option 2 unten).
#
# 2️⃣ Prüfen, ob NetworkManager das Interface verwaltet:
#     nmcli device status
#     Falls bei wlan0 "unmanaged" steht:
#        sudo nmcli device set wlan0 managed yes
#
# 3️⃣ Vor Hotspot-Start eventuell alle WLAN-Verbindungen trennen:
#     nmcli radio wifi off && sleep 2 && nmcli radio wifi on
#
# 4️⃣ Falls Hotspot sofort trennt:
#     - Security des AP: WPA2 wählen (WPA im Skript entspricht WPA2-PSK)
#     - Interface im 2.4GHz-Bereich betreiben (hw_mode=g, channel 1-11 mit hostapd)
#
# 5️⃣ Testen ob DHCP läuft:
#     ip addr show wlan0      → sollte 192.168.4.1 haben
#     sudo tail -f /var/log/syslog | grep dnsmasq   → DHCP-Anfragen sehen
#
# 6️⃣ Alternative: Stabile Lösung mit hostapd + dnsmasq
#     - hostapd: Hotspot-SSID + Passwort
#     - dnsmasq: IP-Zuweisung
#     Diese Variante läuft unabhängig vom NetworkManager und ist oft stabiler.
#
###############################################################################

# ===== Parameter =====
IFACE="wlan0"       # ggf. anpassen (prüfen mit: ip link show)
SSID="Fotobox"
PASS="Fritz123"
IPADDR="192.168.4.1/24"
LEASE_RANGE="192.168.4.10,192.168.4.50,255.255.255.0,5m"

echo "[1/4] Prüfe ob NetworkManager vorhanden ist..."
if ! command -v nmcli >/dev/null 2>&1; then
    echo "⚠ NetworkManager ist nicht installiert. Installiere..."
    sudo apt update
    sudo apt install -y network-manager
fi

echo "[2/4] Erstelle Hotspot '$SSID'..."
# Alte Verbindung löschen (ohne Fehler, falls nicht vorhanden)
nmcli connection delete "$SSID" >/dev/null 2>&1 || true

# Interface durch NM verwalten lassen
nmcli device set "$IFACE" managed yes

# Hotspot starten
nmcli device wifi hotspot ifname "$IFACE" con-name "$SSID" ssid "$SSID" password "$PASS"

echo "[3/4] Setze feste IP $IPADDR und DHCP-Range..."
nmcli connection modify "$SSID" ipv4.addresses "$IPADDR" ipv4.method shared

sudo mkdir -p /etc/NetworkManager/dnsmasq-shared.d
echo "dhcp-range=$LEASE_RANGE" | sudo tee /etc/NetworkManager/dnsmasq-shared.d/$SSID.conf >/dev/null

# Verbindung aktivieren (ohne NetworkManager-Neustart)
nmcli connection up "$SSID"

echo "[4/4] Hotspot läuft!"
echo ""
echo "✅ Hotspot '$SSID' gestartet!"
echo "   Passwort: $PASS"
echo "   IP: ${IPADDR%/*}"
echo "   DHCP-Lease: 5 Minuten"
echo ""
echo "Mit einem Gerät ins WLAN '$SSID' einwählen und im Browser http://${IPADDR%/*}:8000 öffnen."