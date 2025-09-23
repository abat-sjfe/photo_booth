#!/bin/bash
SSID="Fotobox"
nmcli connection down $SSID
echo "Hotspot '$SSID' gestoppt."