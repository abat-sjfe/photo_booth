# gallery.py
import os
import sys
from kivy.app import App
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.uix.image import Image as KivyImage
from PIL import Image

PICTURES_DIR = "pictures"
THUMB_DIR = ".thumbs"

THUMB_SIZE = (300, 200)  # Breite, Höhe in Pixel

def create_thumbnail(img_path):
    os.makedirs(THUMB_DIR, exist_ok=True)
    thumb_path = os.path.join(THUMB_DIR, os.path.basename(img_path))
    if not os.path.exists(thumb_path) or os.path.getmtime(thumb_path) < os.path.getmtime(img_path):
        try:
            img = Image.open(img_path)
            img.thumbnail(THUMB_SIZE)
            img.save(thumb_path)
        except Exception as e:
            print("Fehler beim Erstellen des Thumbnails:", e)
            return img_path
    return thumb_path

class GalleryGrid(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(cols=3, spacing=10, size_hint_y=None, padding=10, **kwargs)
        self.bind(minimum_height=self.setter('height'))

        if os.path.exists(PICTURES_DIR):
            for file in sorted(os.listdir(PICTURES_DIR)):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    img_path = os.path.join(PICTURES_DIR, file)
                    thumb_path = create_thumbnail(img_path)

                    # Button mit Thumbnail-Hintergrund
                    btn = Button(
                        size_hint_y=None,
                        height=THUMB_SIZE[1],
                        background_normal=thumb_path,
                        background_down=thumb_path
                    )
                    btn.img_path = img_path
                    btn.bind(on_release=self.open_image)
                    self.add_widget(btn)

    def open_image(self, instance):
        os.system(f"python3 image_view.py \"{instance.img_path}\"")

class GalleryScreen(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Scrollbare Grid-Galerie
        scroll = ScrollView(size_hint=(1, 1))
        grid = GalleryGrid()
        scroll.add_widget(grid)
        self.add_widget(scroll)

        # Zurück-Button oben links (Overlay)
        btn_back = Button(
            text="⬅ Zurück",
            font_size=28,
            size_hint=(0.2, 0.1),
            pos_hint={'x': 0.02, 'top': 0.98},
            background_color=(0, 0, 0, 0.5)
        )
        btn_back.bind(on_release=lambda x: os.system("python3 photo_booth.py"))
        self.add_widget(btn_back)

class GalleryApp(App):
    def build(self):
        Window.fullscreen = 'auto'
        return GalleryScreen()

if __name__ == '__main__':
    GalleryApp().run()