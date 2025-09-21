from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.image import Image, AsyncImage
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from picamera2 import Picamera2
import os, time, shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BILDER_DIR = os.path.join(SCRIPT_DIR, "bilder")
TEMP_FILE = os.path.join(SCRIPT_DIR, "temp.jpg")


# --------- Kamera Widget ---------
class CameraWidget(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (640, 480)}
        )
        self.picam2.configure(config)
        try:
            self.picam2.set_controls({"AwbMode": 0})
        except Exception:
            pass
        self.picam2.start()
        Clock.schedule_interval(self.update, 1/30)

    def update(self, dt):
        frame = self.picam2.capture_array()
        buf = frame.tobytes()
        from kivy.graphics.texture import Texture
        texture = self.texture
        if not texture or texture.width != frame.shape[1] or texture.height != frame.shape[0]:
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
            texture.flip_vertical()
        texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        self.texture = texture

    def capture(self, path):
        self.picam2.capture_file(path)


# --------- PhotoBooth Screen ---------
class PhotoBoothScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.countdown_seconds = 3
        self.countdown_remaining = 0
        self.countdown_event = None

        self.camera = CameraWidget(allow_stretch=True, keep_ratio=False)
        self.layout.add_widget(self.camera)

        # Countdown Label
        self.countdown_label = Label(text='', font_size=150,
                                     color=(1, 1, 1, 1),
                                     pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.layout.add_widget(self.countdown_label)

        self.btn_photo = Button(
            text="📸 Foto",
            font_size=32,
            size_hint=(0.25, 0.15),
            pos_hint={'x': 0.05, 'y': 0.05},
            background_color=(0, 0, 0, 0.5)
        )
        self.btn_photo.bind(on_release=self.start_countdown)
        self.layout.add_widget(self.btn_photo)

        self.btn_gallery = Button(
            text="🖼 Galerie",
            font_size=32,
            size_hint=(0.25, 0.15),
            pos_hint={'right': 0.95, 'y': 0.05},
            background_color=(0, 0, 0, 0.5)
        )
        self.btn_gallery.bind(on_release=self.go_to_gallery)
        self.layout.add_widget(self.btn_gallery)

        self.add_widget(self.layout)

    def go_to_gallery(self, *args):
        self.manager.current = "gallery"

    def start_countdown(self, instance):
        if self.countdown_event:
            return  # Countdown läuft schon
        self.countdown_remaining = self.countdown_seconds
        self.countdown_label.text = str(self.countdown_remaining)
        self.btn_photo.disabled = True
        self.btn_gallery.disabled = True
        self.countdown_event = Clock.schedule_interval(self._countdown_step, 1)

    def _countdown_step(self, dt):
        self.countdown_remaining -= 1
        if self.countdown_remaining > 0:
            self.countdown_label.text = str(self.countdown_remaining)
        else:
            Clock.unschedule(self.countdown_event)
            self.countdown_event = None
            self.countdown_label.text = ''
            self.take_photo()

    def take_photo(self):
        # Foto nur in TEMP_FILE speichern
        self.camera.capture(TEMP_FILE)
        image_view = self.manager.get_screen("imageview")
        image_view.set_image(TEMP_FILE, temp=True)
        self.manager.current = "imageview"
        self.btn_photo.disabled = False
        self.btn_gallery.disabled = False


# --------- ImageView Screen ---------
class ImageViewScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.image_widget = Image(allow_stretch=True, keep_ratio=False)
        self.layout.add_widget(self.image_widget)

        btn_save = Button(
            text="💾 Speichern",
            font_size=32,
            size_hint=(0.3, 0.15),
            pos_hint={'x': 0.05, 'y': 0.05},
            background_color=(0, 0, 0, 0.5)
        )
        btn_save.bind(on_release=self.save_photo)
        self.layout.add_widget(btn_save)

        btn_delete = Button(
            text="🗑 Löschen",
            font_size=32,
            size_hint=(0.3, 0.15),
            pos_hint={'right': 0.95, 'y': 0.05},
            background_color=(0, 0, 0, 0.5)
        )
        btn_delete.bind(on_release=self.delete_photo)
        self.layout.add_widget(btn_delete)

        self.add_widget(self.layout)

        self.current_path = None
        self.temp = False

    def set_image(self, path, temp=False):
        self.image_widget.source = path
        self.image_widget.reload()
        self.current_path = path
        self.temp = temp

    def save_photo(self, instance):
        if self.temp and os.path.exists(self.current_path):
            os.makedirs(BILDER_DIR, exist_ok=True)
            filename = os.path.join(
                BILDER_DIR,
                time.strftime("photo_%Y%m%d_%H%M%S.jpg")
            )
            shutil.move(self.current_path, filename)
        self.manager.current = "photo"

    def delete_photo(self, instance):
        if os.path.exists(self.current_path):
            os.remove(self.current_path)
        self.manager.current = "photo"


# --------- Gallery Screen ---------
class GalleryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()

        scroll = ScrollView(size_hint=(1, 0.9), pos_hint={'x': 0, 'y': 0})
        self.grid = GridLayout(cols=3, spacing=10, size_hint_y=None, padding=10)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)

        btn_back = Button(
            text="⬅ Zurück",
            font_size=28,
            size_hint=(0.2, 0.1),
            pos_hint={'x': 0.02, 'top': 0.98},
            background_color=(0, 0, 0, 0.5)
        )
        btn_back.bind(on_release=self.go_back)

        layout.add_widget(scroll)
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def go_back(self, *args):
        self.manager.current = "photo"

    def on_pre_enter(self, *args):
        self.load_images()

    def load_images(self):
        self.grid.clear_widgets()
        if os.path.exists(BILDER_DIR):
            for file in sorted(os.listdir(BILDER_DIR), reverse=True):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    img_path = os.path.join(BILDER_DIR, file)
                    thumb = AsyncImage(
                        source=img_path,
                        size_hint_y=None, height=200, allow_stretch=True
                    )
                    thumb.bind(on_touch_down=lambda img, touch, p=img_path:
                               self.open_image_if_clicked(img, touch, p))
                    self.grid.add_widget(thumb)

    def open_image_if_clicked(self, img, touch, path):
        if img.collide_point(*touch.pos):
            image_view = self.manager.get_screen("imageview")
            image_view.set_image(path, temp=False)
            self.manager.current = "imageview"


# --------- App ---------
class PhotoBoothApp(App):
    def build(self):
        Window.fullscreen = 'auto'
        sm = ScreenManager()
        sm.add_widget(PhotoBoothScreen(name="photo"))
        sm.add_widget(ImageViewScreen(name="imageview"))
        sm.add_widget(GalleryScreen(name="gallery"))
        return sm


if __name__ == '__main__':
    PhotoBoothApp().run()