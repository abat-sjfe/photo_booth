#!/bin/bash
IFACE="wlan0"  # ggf. anpassen!
SSID="Fotobox"
PASS="Fritz123"

nmcli device wifi hotspot ifname $IFACE con-name $SSID ssid $SSID password $PASS
nmcli connection modify $SSID ipv4.addresses 192.168.4.1/24 ipv4.method shared
nmcli connection up $SSID
echo "Hotspot '$SSID' gestartet auf $IFACE mit Passwort '$PASS'"
echo "IP-Adresse: 192.168.4.1"