from kivy.app import App
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from picamera2 import Picamera2
import os, time, threading, socket, qrcode
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(SCRIPT_DIR, "uploads")

# ------------ Mini-Webserver ------------
def start_webserver():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.chdir(UPLOAD_DIR)
    handler = SimpleHTTPRequestHandler
    with TCPServer(("", 8000), handler) as httpd:
        print("Webserver läuft auf Port 8000")
        httpd.serve_forever()

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


# ------------ Kamera Widget ------------
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


# ------------ PhotoBooth Screen ------------
class PhotoBoothScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.countdown_seconds = 3
        self.countdown_remaining = 0
        self.countdown_event = None

        self.camera = CameraWidget(allow_stretch=True, keep_ratio=False)
        self.layout.add_widget(self.camera)

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

        # QR-Code erstellen
        ip_addr = get_ip()
        link = f"http://{ip_addr}:8000/{filename}"
        qr = qrcode.make(link)
        qr_path = os.path.join(UPLOAD_DIR, "qr.png")
        qr.save(qr_path)

        # In QRScreen übergeben
        qr_screen = self.manager.get_screen("qr")
        qr_screen.show_photo_and_qr(save_path, qr_path)

        self.manager.current = "qr"
        self.btn_photo.disabled = False


# ------------ QRScreen (Foto + QR) ------------
class QRScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()

        # Foto groß als Hintergrund
        self.photo_widget = Image(allow_stretch=True, keep_ratio=False,
                                  size_hint=(1,1), pos_hint={'x':0,'y':0})
        self.layout.add_widget(self.photo_widget)

        # QR-Code klein in der Ecke
        self.qr_widget = Image(size_hint=(0.25, 0.25),
                               pos_hint={'right': 0.98, 'y': 0.02})
        self.layout.add_widget(self.qr_widget)

        # Button Neues Foto
        self.btn_back = Button(
            text="📷 Neues Foto",
            font_size=24,
            size_hint=(0.3, 0.1),
            pos_hint={'center_x': 0.5, 'y': 0.05},
            background_color=(0, 0, 0, 0.5)
        )
        self.btn_back.bind(on_release=self.go_back)
        self.layout.add_widget(self.btn_back)

        self.add_widget(self.layout)

    def show_photo_and_qr(self, photo_path, qr_path):
        self.photo_widget.source = photo_path
        self.photo_widget.reload()
        self.qr_widget.source = qr_path
        self.qr_widget.reload()

    def go_back(self, *args):
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