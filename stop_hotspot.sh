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
sudo pkill -f hostapd || true
sudo pkill -f dnsmasq || true

echo "📴 Disabling hotspot services at boot..."
sudo systemctl disable hostapd || true
sudo systemctl disable dnsmasq || true

echo "♻️ Restoring network configuration..."
# Bring interface down and up to reset
sudo ip link set "$IFACE" down
sudo ip addr flush dev "$IFACE"
sudo ip link set "$IFACE" up

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

# Reset hostapd daemon config
sudo sed -i 's|DAEMON_CONF="/etc/hostapd/hostapd.conf"|#DAEMON_CONF=""|' /etc/default/hostapd || true

echo "📡 Re-enabling wpa_supplicant..."
sudo systemctl enable wpa_supplicant || true
sudo systemctl start wpa_supplicant || true

# Check if NetworkManager is available and re-enable it
if command -v nmcli >/dev/null 2>&1; then
    echo "🔄 Re-enabling NetworkManager..."
    sudo systemctl enable NetworkManager || true
    sudo systemctl start NetworkManager || true
    # Wait a moment for NetworkManager to initialize
    sleep 3
    echo "� NetworkManager status:"
    sudo systemctl status NetworkManager --no-pager -l || true
fi

echo "🔄 Restarting networking service..."
sudo systemctl restart networking || true

echo "✅ Client mode restored!"
echo ""
echo "📋 Next steps to connect to Wi-Fi:"
echo "1. Wait 10 seconds for services to fully start"
echo "2. Use: nmcli dev wifi list"
echo "3. Use: nmcli dev wifi connect 'SSID' password 'PASSWORD'"
echo "4. Or use the desktop Wi-Fi menu"
echo "5. If nothing works, reboot: sudo reboot"