#!/bin/bash
set -e

# ================================
# Prüft, ob WLAN-Adapter AP-Modus kann
# ================================

# Standard-Interface
IFACE="${1:-wlan0}"

echo "🔍 Prüfe Access Point (AP) Unterstützung für Interface: $IFACE"

# Prüfen ob Interface existiert
if ! ip link show "$IFACE" >/dev/null 2>&1; then
    echo "❌ Interface $IFACE existiert nicht!"
    echo "   Bitte prüfen mit: ip link show"
    exit 1
fi

# Prüfen ob iw installiert ist
if ! command -v iw >/dev/null 2>&1; then
    echo "⚠ 'iw' ist nicht installiert. Installiere..."
    sudo apt update
    sudo apt install -y iw
fi

# Abfrage der unterstützten Modi
SUPPORTED_MODES=$(iw list 2>/dev/null | grep -A 15 "Supported interface modes" || true)

if [ -z "$SUPPORTED_MODES" ]; then
    echo "❌ Konnte keine Interface-Modes abfragen. Möglicherweise fehlen Treiber."
    exit 1
fi

# Suche nach "* AP"
if echo "$SUPPORTED_MODES" | grep -q "AP"; then
    echo "✅ Der Adapter $IFACE unterstützt Access Point Mode!"
    exit 0
else
    echo "❌ Der Adapter $IFACE unterstützt KEINEN Access Point Mode!"
    echo "   Du kannst mit diesem Adapter keinen WLAN-Hotspot starten."
    echo "   ➡ Lösung: USB-WLAN-Stick mit AP-Unterstützung verwenden."
    exit 1
fi