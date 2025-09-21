#!/bin/bash

# Photo Booth Starter Script
echo "Starte Photo Booth App..."

# Wechsle ins Photo Booth Verzeichnis
cd "/home/foto/dev/photo_booth"

# Prüfe ob Python installiert ist
if ! command -v python3 &> /dev/null; then
    echo "Python3 ist nicht installiert!"
    exit 1
fi

# Prüfe ob Kivy installiert ist
if ! python3 -c "import kivy" 2>/dev/null; then
    echo "Kivy ist nicht installiert. Installiere mit: pip install kivy"
    exit 1
fi

# Prüfe ob Picamera2 installiert ist
if ! python3 -c "import picamera2" 2>/dev/null; then
    echo "Picamera2 ist nicht installiert. Installiere mit: pip install picamera2"
    exit 1
fi

# Starte die App
echo "Alle Abhängigkeiten gefunden. Starte App..."
python3 main.py

echo "App beendet."