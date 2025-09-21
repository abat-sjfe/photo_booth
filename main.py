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


# --------- Abgerundeter Button ---------
class RoundedButton(Button):
    def __init__(self, **kwargs):
        # Speichere die gewünschte Hintergrundfarbe
        self.custom_bg_color = kwargs.get('background_color', (0, 0, 0, 0.5))
        
        # Setze transparenten Standard-Hintergrund
        kwargs['background_color'] = (0, 0, 0, 0)  # Komplett transparent
        
        super().__init__(**kwargs)
        
        # Entferne Standard-Button-Hintergrund komplett
        self.background_normal = ''
        self.background_down = ''
        self.background_disabled_normal = ''
        
        # Erstelle abgerundeten Hintergrund
        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            self.bg_color = Color(*self.custom_bg_color)
            self.bg_rect = RoundedRectangle(
                size=self.size, 
                pos=self.pos, 
                radius=[15]  # Einheitlicher Radius
            )
            
        # Aktualisiere Größe und Position bei Änderungen
        self.bind(size=self._update_bg, pos=self._update_bg)
    
    def _update_bg(self, instance, value):
        """Hintergrund an Button-Größe anpassen"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


# --------- Kamera Widget ---------
class CameraWidget(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        print("Initialisiere Kamera...")
        self.picam2 = Picamera2()
        
        # Preview-Konfiguration
        preview_config = self.picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (640, 480)}
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
        
        # Live-Feed starten - robuster Event-Handler
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
            print(f"Kamera Update Fehler: {e}")

    def capture(self, path):
        self.picam2.capture_file(path)


# --------- PhotoBooth Screen ---------
class PhotoBoothScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.countdown_seconds = 5
        self.countdown_remaining = 0
        self.countdown_event = None

        self.camera = CameraWidget(allow_stretch=True, keep_ratio=False)
        self.layout.add_widget(self.camera)

        # Countdown Label
        self.countdown_label = Label(text='', font_size=150,
                                     color=(1, 1, 1, 1),
                                     pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.layout.add_widget(self.countdown_label)

        self.btn_photo = RoundedButton(
            text="Foto",
            font_size=32,
            size_hint=(0.25, 0.15),
            pos_hint={'right': 0.95, 'y': 0.05},
            background_color=(0, 0, 0, 0.5)
        )
        self.btn_photo.bind(on_release=self.start_countdown)
        self.layout.add_widget(self.btn_photo)

        self.btn_gallery = RoundedButton(
            text="Galerie",
            font_size=32,
            size_hint=(0.25, 0.15),
            pos_hint={'x': 0.05, 'top': 0.95},
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

        btn_save = RoundedButton(
            text="Speichern",
            font_size=32,
            size_hint=(0.3, 0.15),
            pos_hint={'x': 0.05, 'y': 0.05},
            background_color=(0, 0, 0, 0.5)
        )
        btn_save.bind(on_release=self.save_photo)
        self.layout.add_widget(btn_save)

        btn_delete = RoundedButton(
            text="Löschen",
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
        self.from_gallery = False

    def set_image(self, path, temp=False, from_gallery=False):
        self.image_widget.source = path
        self.image_widget.reload()
        self.current_path = path
        self.temp = temp
        self.from_gallery = from_gallery
        
        # Button-Text je nach Herkunft anpassen
        if from_gallery:
            # Aus Gallery: Zurück-Button statt Speichern
            self.layout.children[1].text = "Zurück"  # btn_save
            self.layout.children[0].text = "Löschen"  # btn_delete
        else:
            # Neues Foto: Speichern und Löschen
            self.layout.children[1].text = "Speichern"  # btn_save
            self.layout.children[0].text = "Löschen"   # btn_delete

    def save_photo(self, instance):
        if self.from_gallery:
            # Zurück zur Gallery
            self.manager.current = "gallery"
        else:
            # Foto speichern (nur bei neuen Fotos)
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
        
        # Zurück zur Herkunft: Gallery oder Kamera
        if self.from_gallery:
            self.manager.current = "gallery"
        else:
            self.manager.current = "photo"


# --------- Clickable Image Widget für Gallery ---------
class ClickableImage(AsyncImage):
    def __init__(self, image_path, gallery_screen, **kwargs):
        super().__init__(**kwargs)
        self.image_path = image_path
        self.gallery_screen = gallery_screen
        self.touch_start_pos = None

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Merke Position beim Touch-Start
            self.touch_start_pos = touch.pos
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and self.touch_start_pos:
            # Prüfe ob Touch nicht zu weit bewegt wurde (= kein Scroll)
            start_x, start_y = self.touch_start_pos
            end_x, end_y = touch.pos
            distance = ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5
            
            # Wenn Bewegung kleiner als 20 Pixel = Klick, nicht Scroll
            if distance < 20:
                self.gallery_screen.open_image(self.image_path)
            
            self.touch_start_pos = None
            return True
        return super().on_touch_up(touch)


# --------- Gallery Screen ---------
class GalleryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        
        # Hintergrundfarbe für die Gallery hinzufügen
        from kivy.graphics import Color, Rectangle
        with layout.canvas.before:
            Color(0.65, 0.55, 0.4, 1)  # Warmes Eichenholz-Hellbraun
            self.bg_rect = Rectangle(size=layout.size, pos=layout.pos)
            layout.bind(size=self._update_bg, pos=self._update_bg)

        scroll = ScrollView(size_hint=(1, 0.9), pos_hint={'x': 0, 'y': 0})
        self.grid = GridLayout(cols=3, spacing=10, size_hint_y=None, padding=10)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)

        btn_back = RoundedButton(
            text="Zurück",
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

    def _update_bg(self, instance, value):
        """Hintergrund an Layout-Größe anpassen"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def on_pre_enter(self, *args):
        self.load_images()

    def load_images(self):
        self.grid.clear_widgets()
        if os.path.exists(BILDER_DIR):
            for file in sorted(os.listdir(BILDER_DIR), reverse=True):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    img_path = os.path.join(BILDER_DIR, file)
                    # Erstelle ein benutzerdefiniertes Image-Widget mit besserer Touch-Behandlung
                    thumb = ClickableImage(
                        source=img_path,
                        size_hint_y=None, 
                        height=200, 
                        allow_stretch=True,
                        image_path=img_path,
                        gallery_screen=self
                    )
                    self.grid.add_widget(thumb)

    def open_image(self, path):
        """Öffnet ein Bild - wird nur bei tatsächlichen Klicks aufgerufen"""
        image_view = self.manager.get_screen("imageview")
        image_view.set_image(path, temp=False, from_gallery=True)
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