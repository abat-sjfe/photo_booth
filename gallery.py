# gallery.py
import os
from kivy.app import App
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage
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
                    img = AsyncImage(source=img_path, size_hint_y=None, height=200)
                    self.add_widget(img)

class GalleryApp(App):
    def build(self):
        Window.fullscreen = 'auto'
        scroll = ScrollView()
        scroll.add_widget(Gallery())
        return scroll

if __name__ == '__main__':
    GalleryApp().run()