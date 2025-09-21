# image_view.py
import sys
import os
import shutil
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.core.window import Window

PICTURES_DIR = "pictures"

class ImageView(FloatLayout):
    def __init__(self, img_path, **kwargs):
        super().__init__(**kwargs)
        self.img_path = img_path

        # Bild als Vollhintergrund
        self.image = Image(source=img_path, allow_stretch=True, keep_ratio=False)
        self.add_widget(self.image)

        # Speichern-Button unten links
        btn_save = Button(
            text="💾 Speichern",
            font_size=32,
            size_hint=(0.3, 0.15),
            pos_hint={'x': 0.05, 'y': 0.05},
            background_color=(0, 0, 0, 0.5)
        )
        btn_save.bind(on_release=self.save_photo)
        self.add_widget(btn_save)

        # Löschen-Button unten rechts
        btn_delete = Button(
            text="🗑 Löschen",
            font_size=32,
            size_hint=(0.3, 0.15),
            pos_hint={'right': 0.95, 'y': 0.05},
            background_color=(0, 0, 0, 0.5)
        )
        btn_delete.bind(on_release=self.delete_photo)
        self.add_widget(btn_delete)

    def save_photo(self, instance):
        os.makedirs(PICTURES_DIR, exist_ok=True)
        filename = os.path.join(PICTURES_DIR, os.path.basename(self.img_path))
        shutil.move(self.img_path, filename)
        App.get_running_app().stop()

    def delete_photo(self, instance):
        if os.path.exists(self.img_path):
            os.remove(self.img_path)
        App.get_running_app().stop()


class ImageViewApp(App):
    def __init__(self, img_path, **kwargs):
        super().__init__(**kwargs)
        self.img_path = img_path

    def build(self):
        Window.fullscreen = 'auto'
        return ImageView(self.img_path)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 image_view.py <bilddatei>")
        sys.exit(1)
    img_path = sys.argv[1]
    ImageViewApp(img_path).run()