# image_view.py
import sys, os, shutil
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.core.window import Window

PICTURES_DIR = "pictures"

class ImageView(BoxLayout):
    def __init__(self, img_path, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.img_path = img_path
        self.image = Image(source=img_path, allow_stretch=True, keep_ratio=True)
        self.add_widget(self.image)

        btn_box = BoxLayout(size_hint_y=0.2)
        btn_save = Button(text="💾 Speichern", font_size=32)
        btn_delete = Button(text="🗑 Löschen", font_size=32)
        btn_save.bind(on_release=self.save_photo)
        btn_delete.bind(on_release=self.delete_photo)
        btn_box.add_widget(btn_save)
        btn_box.add_widget(btn_delete)
        self.add_widget(btn_box)

    def save_photo(self, instance):
        os.makedirs(PICTURES_DIR, exist_ok=True)
        filename = os.path.join(PICTURES_DIR, os.path.basename(self.img_path))
        shutil.move(self.img_path, filename)
        App.get_running_app().stop()

    def delete_photo(self, instance):
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