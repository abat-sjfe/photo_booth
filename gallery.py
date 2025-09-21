# gallery.py
import os
import sys
from kivy.app import App
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.core.window import Window

PICTURES_DIR = "pictures"

class Gallery(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(cols=3, spacing=10, size_hint_y=None, **kwargs)
        self.bind(minimum_height=self.setter('height'))

        if os.path.exists(PICTURES_DIR):
            for file in sorted(os.listdir(PICTURES_DIR)):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    img_path = os.path.join(PICTURES_DIR, file)

                    # Jeder Button zeigt das Bild an
                    btn = Button(
                        size_hint_y=None,
                        height=200,
                        background_normal=img_path,
                        background_down=img_path
                    )
                    btn.img_path = img_path
                    btn.bind(on_release=self.open_image)
                    self.add_widget(btn)

    def open_image(self, instance):
        os.system(f"python3 image_view.py {instance.img_path}")

class GalleryApp(App):
    def build(self):
        Window.fullscreen = 'auto'
        scroll = ScrollView()
        scroll.add_widget(Gallery())
        return scroll

if __name__ == '__main__':
    GalleryApp().run()