#!/bin/bash
set -e

###############################################################################
# Client Mode Restore Script
# Switches Raspberry Pi back to normal Wi-Fi client mode
# Re-enables wpa_supplicant and NetworkManager (if desired)
# Disables hostapd + dnsmasq
###############################################################################

# ===== Interface you want to restore =====
IFACE="wlan0"

echo "🛑 Stopping hotspot services..."
sudo systemctl stop hostapd || true
sudo systemctl stop dnsmasq || true

echo "📴 Disabling hotspot services at boot..."
sudo systemctl disable hostapd || true
sudo systemctl disable dnsmasq || true

echo "♻️ Restoring DHCP configuration..."
# Flush static IP
sudo ip addr flush dev "$IFACE"

# If dnsmasq config was replaced, restore original if backup exists
if [ -f /etc/dnsmasq.conf.orig ]; then
    echo "📂 Restoring original dnsmasq.conf..."
    sudo mv /etc/dnsmasq.conf.orig /etc/dnsmasq.conf
else
    echo "🗑️ Removing custom dnsmasq config..."
    sudo rm -f /etc/dnsmasq.conf
fi

# Remove hostapd config to avoid AP start in client mode
sudo rm -f /etc/hostapd/hostapd.conf

echo "📡 Re-enabling wpa_supplicant..."
sudo systemctl enable wpa_supplicant || true
sudo systemctl start wpa_supplicant || true

# Optional: Re-enable NetworkManager if installed
if systemctl list-units --type=service | grep -q NetworkManager; then
    echo "🔄 Re-enabling NetworkManager..."
    sudo systemctl enable NetworkManager
    sudo systemctl start NetworkManager
fi

echo "✅ Client mode restored!"
echo "You can now reconnect to your Wi-Fi network using 'nmcli', Raspberry Pi's desktop Wi-Fi menu, or 'raspi-config'."