# photo_booth.py
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from picamera2 import Picamera2
import os

TEMP_FILE = "temp.jpg"

class CameraWidget(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.picam2 = Picamera2()

        # Vorschau als RGB888 für korrekte Farben
        config = self.picam2.create_preview_configuration(
            main={"format": 'RGB888', "size": (1280, 720)}
        )
        self.picam2.configure(config)

        # Weißabgleich Auto
        try:
            self.picam2.set_controls({"AwbMode": 0})  # Auto White Balance
        except Exception:
            pass

        self.picam2.start()

        # Jede 1/30 Sekunde Vorschau aktualisieren
        Clock.schedule_interval(self.update, 1/30)

    def update(self, dt):
        # Direktes Livebild abrufen
        frame = self.picam2.capture_array()  # NumPy-Array (RGB888)

        buf = frame.tobytes()
        from kivy.graphics.texture import Texture
        texture = self.texture
        if not texture or texture.width != frame.shape[1] or texture.height != frame.shape[0]:
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
            texture.flip_vertical()
        texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        self.texture = texture

    def capture(self):
        self.picam2.capture_file(TEMP_FILE)


class PhotoBoothScreen(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Fester Hintergrund
        with self.canvas.before:
            Color(0.1, 0.1, 0.2, 1)  # Dunkelblauer Hintergrund
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update_bg, pos=self._update_bg)

        # Kamera-Preview in der Mitte (kleiner Bereich)
        self.camera = CameraWidget(
            allow_stretch=True, 
            keep_ratio=True,
            size_hint=(0.6, 0.7),  # 60% Breite, 70% Höhe
            pos_hint={'center_x': 0.5, 'center_y': 0.55}  # Zentriert, etwas nach oben
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

    def _update_bg(self, instance, value):
        """Hintergrund an Fenstergröße anpassen"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def take_photo(self, instance):
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