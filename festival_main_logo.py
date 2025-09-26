from kivy.app import App
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.uix.button import Button
class RoundedButton(Button):
    def __init__(self, **kwargs):
        self.custom_bg_color = kwargs.get('background_color', (0, 0, 0, 0.5))
        kwargs['background_color'] = (0, 0, 0, 0)
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_disabled_normal = ''
        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            self.bg_color = Color(*self.custom_bg_color)
            self.bg_rect = RoundedRectangle(
                size=self.size,
                pos=self.pos,
                radius=[15]
            )
        self.bind(size=self._update_bg, pos=self._update_bg)
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from picamera2 import Picamera2
import os, time, threading, socket, qrcode, mimetypes
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(SCRIPT_DIR, "uploads")
COUNTER_FILE = os.path.join(SCRIPT_DIR, "photo_count.txt")


# ------------ Direktdownload HTTP Handler ------------
class DownloadHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/") and len(self.path) > 1:
            filename = self.path[1:]
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(file_path):
                self.send_response(200)
                ctype, _ = mimetypes.guess_type(file_path)
                self.send_header('Content-Type', ctype or 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.send_header('Content-Length', os.path.getsize(file_path))
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
        self.send_error(404, "File not found")


def start_webserver():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.chdir(UPLOAD_DIR)
    with TCPServer(("", 8000), DownloadHandler) as httpd:
        print("Webserver (Direktdownload) läuft auf Port 8000")
        httpd.serve_forever()


def get_ip():
    return "192.168.4.1"  # feste IP mit Fotobox-Hotspot


# ------------ Counter Funktionen ------------
def load_counter():
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, "r") as f:
                return int(f.read().strip())
        except:
            return 0
    else:
        return 0


def save_counter(value):
    with open(COUNTER_FILE, "w") as f:
        f.write(str(value))


# ------------ Kamera Widget ------------
class CameraWidget(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("Initialisiere Kamera...")
        self.picam2 = Picamera2()
        preview_config = self.picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (1024, 600)}
        )
        self.picam2.configure(preview_config)
        try:
            self.picam2.set_controls({"AwbMode": 0})
        except Exception as e:
            print(f"AWB Einstellung fehlgeschlagen: {e}")
        self.picam2.start()
        time.sleep(0.1)
        self.update_event = Clock.schedule_interval(self.update, 1/25.0)
        print("Kamera Live-Feed gestartet")

        # Overlay wird jetzt im PhotoBoothScreen hinzugefügt, nicht hier
        self.overlay_widget = None

    def update(self, dt):
        try:
            frame = self.picam2.capture_array()
            buf = frame.tobytes()
            from kivy.graphics.texture import Texture
            h, w = frame.shape[:2]
            if not self.texture or self.texture.width != w or self.texture.height != h:
                self.texture = Texture.create(size=(w, h), colorfmt='rgb')
                self.texture.flip_vertical()
            self.texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
            self.canvas.ask_update()
            # Overlay-Widget bleibt immer im Vordergrund und an richtiger Stelle
            if self.overlay_widget:
                # Größe und Position werden durch size_hint und pos_hint automatisch gesetzt
                pass
        except Exception as e:
            print(f"Kamera Update Fehler: {e}")

    def capture(self, path):
        # Normales Foto aufnehmen
        self.picam2.capture_file(path)
        # Overlay unten mittig einfügen
        overlay_path = os.path.join(os.path.dirname(__file__), "overlay.png")
        if os.path.exists(overlay_path):
            try:
                from PIL import Image as PILImage
                base = PILImage.open(path).convert("RGBA")
                overlay = PILImage.open(overlay_path).convert("RGBA")
                # Zielgröße: 20% Breite, 15% Höhe des Fotos
                ow = int(base.width * 0.2)
                oh = int(base.height * 0.15)
                overlay = overlay.resize((ow, oh), PILImage.LANCZOS)
                # Position: unten mittig (PIL zählt Y von oben!)
                x = int((base.width - ow) / 2)      # Horizontal zentriert
                y = base.height - oh - int(base.height * 0.05)  # Unten mit 5% Abstand
                base.paste(overlay, (x, y), overlay)
                base = base.convert("RGB")
                base.save(path)
            except Exception as e:
                print(f"Overlay konnte nicht eingefügt werden: {e}")


# ------------ PhotoBooth Screen ------------
class PhotoBoothScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.countdown_seconds = 5
        self.countdown_remaining = 0
        self.countdown_event = None
        self.photo_counter = load_counter()

        self.camera = CameraWidget(allow_stretch=True, keep_ratio=False)
        self.layout.add_widget(self.camera)

        # Overlay-Image für Preview - direkt im Screen positioniert
        overlay_path = os.path.join(os.path.dirname(__file__), "overlay.png")
        if os.path.exists(overlay_path):
            self.overlay_widget = Image(
                source=overlay_path,
                allow_stretch=True,
                keep_ratio=True,
                size_hint=(0.2, 0.15),
                pos_hint={'center_x': 0.5, 'y': 0.05}  # Unten mittig
            )
            self.layout.add_widget(self.overlay_widget)

        self.countdown_label = Label(text='', font_size=150,
                                     color=(1, 1, 1, 1),
                                     pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.layout.add_widget(self.countdown_label)

        # Counter oben
        self.counter_label = Label(text=f"Fotos gemacht: {self.photo_counter}",
                                   font_size=24,
                                   color=(1, 1, 1, 1),
                                   pos_hint={'right': 0.98, 'top': 0.98})
        self.layout.add_widget(self.counter_label)

        self.btn_photo = RoundedButton(
            text="Foto",
            font_size=32,
            size_hint=(0.25, 0.15),
            pos_hint={'x': 0.05, 'y': 0.05},
            background_color=(0, 0, 0, 0.5)
        )
        self.btn_photo.bind(on_release=self.start_countdown)
        self.layout.add_widget(self.btn_photo)

        self.add_widget(self.layout)

    def start_countdown(self, instance):
        if self.countdown_event:
            return
        self.countdown_remaining = self.countdown_seconds
        self.countdown_label.text = str(self.countdown_remaining)
        self.btn_photo.disabled = True
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
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = time.strftime("photo_%Y%m%d_%H%M%S.jpg")
        save_path = os.path.join(UPLOAD_DIR, filename)
        self.camera.capture(save_path)

        # Counter erhöhen
        self.photo_counter += 1
        save_counter(self.photo_counter)
        self.counter_label.text = f"Fotos gemacht: {self.photo_counter}"

        # QR-Code erstellen
        ip_addr = get_ip()
        link = f"http://{ip_addr}:8000/{filename}"
        qr = qrcode.make(link)
        qr_path = os.path.join(UPLOAD_DIR, "qr.png")
        qr.save(qr_path)

        qr_screen = self.manager.get_screen("qr")
        qr_screen.show_photo_and_qr(save_path, qr_path)

        self.manager.current = "qr"
        self.btn_photo.disabled = False


# ------------ QRScreen mit Auto-Return ------------
class QRScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()

        self.photo_widget = Image(allow_stretch=True, keep_ratio=False,
                                  size_hint=(1,1), pos_hint={'x':0,'y':0})
        self.layout.add_widget(self.photo_widget)

        self.qr_widget = Image(size_hint=(0.25, 0.25),
                               pos_hint={'right': 0.98, 'y': 0.02})
        self.layout.add_widget(self.qr_widget)

        self.label_info = Label(text="Scanne diesen Code zum Runterladen",
                                font_size=20,
                                color=(1,1,1,1),
                                pos_hint={'center_x':0.5, 'top':0.95})
        self.layout.add_widget(self.label_info)

        # Zurück-Button
        self.btn_back = RoundedButton(
            text="Zurück",
            font_size=32,
            size_hint=(0.25, 0.15),
            pos_hint={'x': 0.05, 'y': 0.05},
            background_color=(0, 0, 0, 0.5)
        )
        self.btn_back.bind(on_release=self.on_back_button)
        self.layout.add_widget(self.btn_back)

        self.add_widget(self.layout)

        self.current_photo = None
        self.current_qr = None
        self.auto_timer = None

    def show_photo_and_qr(self, photo_path, qr_path):
        self.photo_widget.source = photo_path
        self.photo_widget.reload()
        self.qr_widget.source = qr_path
        self.qr_widget.reload()
        self.current_photo = photo_path
        self.current_qr = qr_path

        # Starte automatischen Rücksprung nach 30 Sekunden
        if self.auto_timer:
            Clock.unschedule(self.auto_timer)
        self.auto_timer = Clock.schedule_once(self.go_back, 30)

    def on_back_button(self, instance):
        # Timer stoppen falls aktiv
        if self.auto_timer:
            Clock.unschedule(self.auto_timer)
            self.auto_timer = None
        self.go_back()

    def go_back(self, *args):
        # Foto und QR löschen
        for f in [self.current_photo, self.current_qr]:
            try:
                if f and os.path.exists(f):
                    os.remove(f)
            except:
                pass
        self.manager.current = "photo"


# ------------ App ------------
class PhotoBoothApp(App):
    def build(self):
        Window.fullscreen = 'auto'
        threading.Thread(target=start_webserver, daemon=True).start()

        sm = ScreenManager()
        sm.add_widget(PhotoBoothScreen(name="photo"))
        sm.add_widget(QRScreen(name="qr"))
        return sm


if __name__ == '__main__':
    PhotoBoothApp().run()