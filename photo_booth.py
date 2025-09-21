# photo_booth.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.clock import Clock
from picamera2 import Picamera2
import time
import os
from PIL import Image as PILImage

TEMP_FILE = "temp.jpg"

class CameraWidget(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration()
        self.picam2.configure(config)
        self.picam2.start()
        Clock.schedule_interval(self.update, 1/30)

    def update(self, dt):
        frame = self.picam2.capture_array()
        # Frame aus NumPy Array als Texture wandeln
        import cv2
        from kivy.graphics.texture import Texture
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        buf = frame.tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]))
        texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        self.texture = texture

    def capture(self):
        self.picam2.capture_file(TEMP_FILE)

class PhotoBooth(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.camera = CameraWidget()
        self.add_widget(self.camera)

        btn_box = BoxLayout(size_hint_y=0.2)
        btn_capture = Button(text="📸 Foto aufnehmen", font_size=32)
        btn_gallery = Button(text="🖼 Galerie", font_size=32)
        btn_capture.bind(on_release=self.take_photo)
        btn_gallery.bind(on_release=self.open_gallery)
        btn_box.add_widget(btn_capture)
        btn_box.add_widget(btn_gallery)
        self.add_widget(btn_box)

    def take_photo(self, instance):
        self.camera.capture()
        os.system(f"python3 image_view.py {TEMP_FILE}")

    def open_gallery(self, instance):
        os.system("python3 gallery.py")

class PhotoBoothApp(App):
    def build(self):
        self.title = "Fotobox"
        self.window_fullscreen()
        return PhotoBooth()

    def window_fullscreen(self):
        from kivy.core.window import Window
        Window.fullscreen = 'auto'

if __name__ == '__main__':
    PhotoBoothApp().run()