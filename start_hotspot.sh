#!/bin/bash
set -e

###############################################################################
# Final Stable Hotspot-Only Setup for Raspberry Pi
# Removes NetworkManager and wpa_supplicant interference
# Works with onboard Wi-Fi (brcmfmac) or compatible AP-mode USB dongles
###############################################################################

# ===== Settings =====
IFACE="wlan0"
SSID="Fotobox"
PASS="Fritz123"
STATIC_IP="192.168.4.1"
LEASE_RANGE="192.168.4.10,192.168.4.50,255.255.255.0,5m"
COUNTRY_CODE="DE"

echo "📦 Installing required packages..."
sudo apt update
sudo apt install -y hostapd dnsmasq

echo "🛑 Stopping and disabling NetworkManager (if installed)..."
if systemctl list-units --type=service | grep -q NetworkManager; then
    sudo systemctl stop NetworkManager
    sudo systemctl disable NetworkManager
fi

echo "🛑 Stopping and disabling wpa_supplicant..."
sudo systemctl stop wpa_supplicant || true
sudo systemctl disable wpa_supplicant || true

echo "🌐 Assigning static IP to $IFACE..."
sudo ip link set "$IFACE" down
sudo ip addr flush dev "$IFACE"
sudo ip addr add "$STATIC_IP/24" dev "$IFACE"
sudo ip link set "$IFACE" up

echo "📝 Creating hostapd configuration..."
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

echo "📝 Creating dnsmasq configuration..."
# backup old config
if [ -f /etc/dnsmasq.conf ]; then
    sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig 2>/dev/null || true
fi
sudo bash -c "cat > /etc/dnsmasq.conf" <<EOF
interface=$IFACE
dhcp-range=$LEASE_RANGE
EOF

echo "⚡ Enabling services..."
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

echo "🚀 Starting hotspot services..."
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq

echo ""
echo "✅ Hotspot-Only setup complete!"
echo "SSID: $SSID"
echo "Password: $PASS"
echo "IP Address: $STATIC_IP"
echo "DHCP Range: $LEASE_RANGE"
echo ""
echo "Hotspot will start automatically at boot and cannot switch to client mode ."