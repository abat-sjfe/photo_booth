# photo_booth.py
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
from picamera2 import Picamera2
import os

TEMP_FILE = "temp.jpg"

class CameraWidget(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.picam2 = Picamera2()

        # Vorschau-Konfiguration mit RGB888 -> richtige Farben
        config = self.picam2.create_preview_configuration(
            main={"format": 'RGB888', "size": (1280, 720)}
        )
        self.picam2.configure(config)

        # Auto White Balance auf "Auto" setzen (0)
        try:
            self.picam2.set_controls({"AwbMode": 0})
        except Exception as e:
            print("AWB Control nicht verfügbar:", e)

        self.picam2.start()

        # Update-Loop starten (30 FPS)
        Clock.schedule_interval(self.update, 1/30)

    def update(self, dt):
        frame = self.picam2.capture_array()  # schon im RGB-Format
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

        # Kamera-Vorschau im Hintergrund
        self.camera = CameraWidget(allow_stretch=True, keep_ratio=False)
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