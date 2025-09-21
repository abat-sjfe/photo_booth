# photo_booth.py
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
from picamera2 import Picamera2
import time
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BILDER_DIR = os.path.join(SCRIPT_DIR, "bilder")
TEMP_FILE = "temp.jpg"

class CameraWidget(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Kamera initialisieren
        self.picam2 = Picamera2()
        
        # Preview-Konfiguration mit 1024x600 Auflösung
        preview_config = self.picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (1024, 768)}
        )
        self.picam2.configure(preview_config)
        
        # Kamera-Einstellungen
        try:
            self.picam2.set_controls({"AwbMode": 0})  # Auto White Balance
        except Exception as e:
            print(f"AWB Einstellung fehlgeschlagen: {e}")
        
        # Kamera starten
        self.picam2.start()
        
        # Kurz warten bis Kamera bereit ist
        time.sleep(0.1)
        
        # Live-Feed starten - höhere Frequenz für flüssigere Darstellung
        self.update_event = Clock.schedule_interval(self.update, 1/25.0)  # 25 FPS
        
        print("Kamera Live-Feed gestartet")

    def update(self, dt):
        try:
            # Aktuelles Frame von der Kamera holen
            frame = self.picam2.capture_array()
            
            # Frame in Bytes umwandeln
            buf = frame.tobytes()
            
            # Texture erstellen oder wiederverwenden
            from kivy.graphics.texture import Texture
            h, w = frame.shape[:2]
            
            # Neue Texture erstellen falls nötig
            if not self.texture or self.texture.width != w or self.texture.height != h:
                self.texture = Texture.create(size=(w, h), colorfmt='rgb')
                self.texture.flip_vertical()
            
            # Frame in Texture laden und sofort anzeigen
            self.texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
            
            # Explizit das Widget zum Neuzeichnen zwingen
            self.canvas.ask_update()
            
        except Exception as e:
            print(f"Update Fehler: {e}")

    def capture(self):
        self.picam2.capture_file(TEMP_FILE)


class PhotoBoothScreen(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Kamera-Preview im Hintergrund - ohne Stretching
        self.camera = CameraWidget(
            allow_stretch=True, 
            keep_ratio=True  # Seitenverhältnis beibehalten - kein Stretching
        )
        self.add_widget(self.camera)

        # Foto-Button unten links
        btn_capture = Button(
            text="📸 Foto",
            font_size=32,
            size_hint=(0.25, 0.15),
            pos_hint={'x': 0.05, 'y': 0.05},
            background_color=(0, 0, 0, 0.5)
        )
        btn_capture.bind(on_release=self.take_photo)
        self.add_widget(btn_capture)

        # Galerie-Button unten rechts
        btn_gallery = Button(
            text="🖼 Galerie",
            font_size=32,
            size_hint=(0.25, 0.15),
            pos_hint={'right': 0.95, 'y': 0.05},
            background_color=(0, 0, 0, 0.5)
        )
        btn_gallery.bind(on_release=self.open_gallery)
        self.add_widget(btn_gallery)

    def take_photo(self, instance):
        # Foto aufnehmen und temp speichern
        if not os.path.exists(BILDER_DIR):
            os.makedirs(BILDER_DIR)
        self.camera.capture()
        os.system(f"python3 image_view.py {TEMP_FILE}")

    def open_gallery(self, instance):
        os.system("python3 gallery.py")


class PhotoBoothApp(App):
    def build(self):
        self.title = "Fotobox"
        Window.fullscreen = 'auto'
        return PhotoBoothScreen()


if __name__ == '__main__':
    PhotoBoothApp().run()