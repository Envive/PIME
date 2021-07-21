
import envive_helper_ui as ui
import json
import os
import platform
import pyautogui
import subprocess
import sys
from datetime import datetime
# from image_matcher import ImageMatcher
from pynput import mouse, keyboard
from pynput.mouse import Controller
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView
from PyQt5.QtWebChannel import QWebChannel

is_retina = False

if platform.system() == "Darwin":
    is_retina = subprocess.call("system_profiler SPDisplaysDataType | grep 'retina'", shell=True)


class HiddenWindow(QDialog):

    def __init__(self, server):
        try:
            print('First window start')
            super().__init__()
            self.main_window = None
            self.create_new_window()

            self.thread = QThread()
            self.sub_server = server

            self.sub_server.moveToThread(self.thread)
            self.thread.started.connect(self.sub_server.run)
            print('connect server')
            self.thread.start()
            print('serve start')
        except Exception as e:
            print("ERROR:", e)

    def create_new_window(self):
        if self.main_window is None:
            self.main_window = QtWindow(self)
        # set second window as modal, because MainWindow is QDialog/QWidget.
        self.setModal(True)
        self.main_window.show()


class QtWindow(QDialog, ui.Ui_MainWindow):

    def __init__(self, *args, **kwargs):
        print('main window init')
        # super().__init__()
        super(QtWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        # self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # self.mouse_controller = QtMouseController(self)
        # self.keyborad_controller = QtKeyboardController(self)

        vbox = QVBoxLayout(self)
        self.webEngineView = QWebEngineView()
        # self.webEngineView.load(QUrl("http://localhost:8080/"))
        # self.webEngineView.load(QUrl("http://localhost:8080/#/dx/web-channel-demo?patientId=6839&patientVisitId=5395"))
        # self.webEngineView.load(QUrl("https://test7.envive.cn/"))
        self.webEngineView.load(QUrl("https://test7.envive.cn/#/dx/web-channel-demo?patientId=109&patientVisitId=3853"))
        vbox.addWidget(self.webEngineView)
        self.web_layout.addLayout(vbox)

        # self.channel = QWebChannel()
        # self.payload = QtData(self)
        # self.channel.registerObject("QtData", self.payload)
        # self.webEngineView.page().setWebChannel(self.channel)

        # self.mouse_detect_button.clicked.connect(self.show_mouse_position)
        # self.send_data_to_web_button.clicked.connect(self.send_data_to_web)

        # self.to_web_data_type.textChanged.connect(self.payload.set_data_type)
        # self.to_web_data_value.textChanged.connect(self.payload.set_data_value)

        # self.qi = QInputMethodEvent()

    def window_show(self):
        # self.raise_()
        self.show()

    def window_hide(self):
        self.hide()

    def window_resize(self, width, height):
        self.resize(width, height)
        print(f'width: {width}')
        print(f'height: {height}')

    def set_current_input(self, key):
        # position_x, position_y = self.mouse_controller.position
        # self.move(position_x, position_y)
        self.current_input += key
        # self.payload.set_data_value(self.current_input)
        print(self.current_input)
        print('self.qi')
        print(self.qi.__dict__)
        print('self.qi.preeditString()')
        print(self.qi.preeditString())
        print('self.qi.commitString()')
        print(self.qi.commitString())

    def show_mouse_position(self):
        position_x, position_y = self.mouse_controller.position
        self.mouse_position_x_label.setText(f'X: {position_x}')
        self.mouse_position_y_label.setText(f'Y: {position_y}')

    def capture_screen(self, position_x, position_y):
        print('Start Capture Screen.....')
        dirname = os.path.dirname(__file__)
        my_screenshot = pyautogui.screenshot()

        if is_retina:
            my_screenshot.thumbnail((round(my_screenshot.size[0] * 0.5), round(my_screenshot.size[1] * 0.5)))

        w, h = my_screenshot.size
        datetime_now = datetime.today().strftime('%Y%m%d-%H%M%S')
        my_screenshot_path = f'{dirname}/screenshots/CaptureScreen-{datetime_now}.png'
        my_screenshot.save(my_screenshot_path)
        print('Capture Screen Done')
        # image_matcher = ImageMatcher(f'{dirname}/source')
        # tags = image_matcher.match_image(position_x, position_y, my_screenshot_path)
        # print(tags)

    def capture_screen_temp(self, mouse_button):
        self.current_input = ''
        if mouse_button == 'right':
            self.payload.set_data_type('')
            self.window_hide()
        else:
            self.payload.set_data_type('cc')
            self.window_show()

    def send_data_to_web(self):
        js_code = 'CallJsByPyqt5()'
        self.webEngineView.page().runJavaScript(js_code)

class QtMouseController(QWidget):
    left_mouse_clicked = pyqtSignal(str)
    right_mouse_clicked = pyqtSignal(str)
    capture_screen_triggered = pyqtSignal(float, float)

    def __init__(self, main_window):
        super().__init__()
        self.window = main_window
        self.position_x = 0
        self.position_y = 0

        self.listener = mouse.Listener(on_click=self.on_mouse_click)
        self.listener.start()

        # self.left_mouse_clicked.connect(self.window.capture_sceen_temp)
        # self.right_mouse_clicked.connect(self.window.capture_sreen_temp)
        self.capture_screen_triggered.connect(self.window.capture_screen)

    @pyqtSlot(object, result=object)
    def get_mouse_position(self):
        return (self.position_x, self.position_y)

    def on_mouse_click(self, x, y, button, pressed):
        self.position_x = x
        self.position_y = y

        if button == mouse.Button.left:
            # print('{0} at {1}'.format('Pressed left' if pressed else 'Released', (x, y)))
            self.left_mouse_clicked.emit('left')
        elif button == mouse.Button.right:
            self.right_mouse_clicked.emit('right')
            # print('{0} at {1}'.format('Pressed right' if pressed else 'Released', (x, y)))
            # self.capture_screen_triggered.emit(x, y)

    position = pyqtProperty(object, fget=get_mouse_position)

class QtKeyboardController(QWidget):
    keyboard_pressed = pyqtSignal(str)

    def __init__(self, main_window):
        super().__init__()
        self.window = main_window

        self.listener = keyboard.Listener(on_press=self.on_keyboard_pressed)
        self.listener.start()

        self.keyboard_pressed.connect(self.window.set_current_input)

    def on_keyboard_pressed(self, key):
        try:
            print('keyboard press')
            self.keyboard_pressed.emit(key.char)
        except AttributeError:
            print('error')
            print('Key {0} pressed'.format(key))

class QtData(QWidget):
    valueChanged = pyqtSignal(str)
    window_resize = pyqtSignal(int, int)

    def __init__(self, main_window):
        super().__init__()
        self.window = main_window
        self.data_type = ''
        self.data_value = ''
        self.window_width, self.window_height = pyautogui.size()

        self.window_resize.connect(self.window.window_resize)

    @pyqtSlot(str, result=str)
    def get_pyqt_to_web_value(self):
        return json.dumps(
            {
                'type': self.data_type,
                'value': self.data_value,
                'window_width': self.window_width,
                'window_height': self.window_height
            }
        )

    def set_pyqt_to_web_value(self, category):
        self._category = category

    def set_data_type(self, data_type):
        # print(f'dataType: {data_type}')
        if self.data_type == data_type:
            return
        self.data_type = data_type
        self.valueChanged.emit(self.value)

    def set_data_value(self, data_value):
        # print(f'dataValue: {data_value}')
        if self.data_value == data_value:
            return
        self.data_value = data_value
        self.valueChanged.emit(self.value)

    @pyqtSlot(int, int)
    def set_window_size(self, width, height):
        self.window_resize.emit(int(width), int(height))

    value = pyqtProperty(str, fget=get_pyqt_to_web_value, fset=set_pyqt_to_web_value)

