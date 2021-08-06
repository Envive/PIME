
import json
import os
import platform
import pyautogui
import subprocess
import sys
from datetime import datetime
from envive_helper_python.image_matcher import ImageMatcher
from . import envive_helper_ui as ui
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

            self.tray_icon = SystemTrayIcon(QIcon(r'envive_helper_python/icon.png'), self)
            self.tray_icon.show()

            self.tray_icon.method_changed.connect(self.main_window.set_current_match_method)

            self.thread = QThread()
            self.sub_server = server

            self.sub_server.value_changed.connect(self.main_window.payload.set_data_value)
            self.sub_server.value_changed.connect(self.main_window.window_show)
            self.sub_server.user_input_terminated.connect(self.main_window.payload.clear_data_value)
            self.sub_server.user_input_terminated.connect(self.main_window.window_hide)
            # self.sub_server.value_changed.connect(self.main_window.window_control)

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
            # self.main_window.setAttribute(Qt.WA_ShowWithoutActivating)
        # set second window as modal, because MainWindow is QDialog/QWidget.
        self.setModal(True)
        self.main_window.show()


# class QtWindow(QDialog, ui.Ui_MainWindow):
class QtWindow(QMainWindow, ui.Ui_MainWindow):
    RADIO_BUTTON_DICT = {
        '主诉': 'cc',
        '现病史': 'hpi',
        '既往史': 'preExistingCondition',
        '过敏史': 'allergiesHistory',
        '查体': 'pe',
        '辅助检查': 'exam',
        '门诊初步诊断': 'assessment',
        '处理': 'disposition',
        '治疗': 'treament',
    }

    def __init__(self, *args, **kwargs):
        print('main window init')
        # super().__init__()
        super(QtWindow, self).__init__(*args, **kwargs)
        self.current_match_method = 'Data'

        self.setupUi(self)
        # self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.mouse_controller = QtMouseController(self)
        # self.keyborad_controller = QtKeyboardController(self)

        vbox = QVBoxLayout(self)
        self.webEngineView = QWebEngineView()
        # self.webEngineView.load(QUrl("http://localhost:8080/"))
        # self.webEngineView.load(QUrl("http://localhost:8080/#/dx/web-channel-demo?patientId=6839&patientVisitId=5395"))
        # self.webEngineView.load(QUrl("https://test7.envive.cn/"))

        self.webEngineView.load(QUrl("https://test7.envive.cn/#/dx/web-channel-demo?patientId=109&patientVisitId=3853"))
        vbox.addWidget(self.webEngineView)
        self.web_layout.addLayout(vbox)

        self.channel = QWebChannel()
        self.payload = QtData(self)
        self.channel.registerObject("QtData", self.payload)
        self.webEngineView.page().setWebChannel(self.channel)

        self.set_up_radio_ui(self)

        # # self.mouse_detect_button.clicked.connect(self.show_mouse_position)
        # # self.send_data_to_web_button.clicked.connect(self.send_data_to_web)

    def set_up_radio_ui(self, main_window):
        radio_button_text_list = list(self.RADIO_BUTTON_DICT.keys())
        # radio_button_list[0].setChecked(True)

        radio_button_layout = QHBoxLayout()

        self.radio_button_group = QButtonGroup()

        for index , radio_button_text in enumerate(radio_button_text_list):
            radio_button = QRadioButton(radio_button_text)
            if index == 0:
                radio_button.setChecked(True)
            radio_button_layout.addWidget(radio_button)
            self.radio_button_group.addButton(radio_button, index)
            radio_button.clicked.connect(self.radio_button_clicked)

        self.radio_layout.addLayout(radio_button_layout)

    def radio_button_clicked(self):
        print(self.radio_button_group.checkedId())
        checked_button_text = self.radio_button_group.checkedButton().text()
        data_type = self.RADIO_BUTTON_DICT.get(checked_button_text)
        self.payload.set_data_type(data_type)

    def window_control(self, input_string):
        if input_string:
            self.window_show()
        else:
            self.window_hide()

    def window_show(self):
        self.setGeometry(self.mouse_controller.position_x, self.mouse_controller.position_y, self.width(), self.height())
        self.raise_()
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
        
    def set_current_match_method(self, method):
        self.current_match_method = method
        if self.current_match_method == 'User':
            self.horizontalLayoutWidget.show()
            self.verticalLayoutWidget.setGeometry(QRect(0, 70, 1121, 631))
            self.resize(1118, 704)
        else: 
            self.verticalLayoutWidget.setGeometry(QRect(0, 0, 1121, 631))
            self.horizontalLayoutWidget.hide()
            self.resize(1118, 633)

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

        image_matcher = ImageMatcher(
            source_path=f'{dirname}\source',
            meta_path=f'{dirname}\source\meta.json'
        )

 
        if self.current_match_method == 'Image':
            tags = image_matcher.match_image(position_x, position_y, my_screenshot_path)
        else:
            tags = image_matcher.match_by_meta(position_x, position_y)
        print(tags)

        if tags:
            tag = tags[0]
            self.payload.set_data_type(tag)
            radio_index = list(self.RADIO_BUTTON_DICT.values()).index(tag)
            self.radio_button_group.buttons()[radio_index].setChecked(True)

    def capture_screen_temp(self, mouse_button):
        self.current_input = ''
        print(f'mouse_button press: {mouse_button}')
        if mouse_button == 'right':
            # self.payload.set_data_type('')
            # self.window_hide()
            self.window_show()
        else:
            # self.payload.set_data_type('cc')
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

        # self.left_mouse_clicked.connect(self.window.capture_screen_temp)
        # self.right_mouse_clicked.connect(self.window.capture_screen_temp)
        self.capture_screen_triggered.connect(self.window.capture_screen)

    @pyqtSlot(object, result=object)
    def get_mouse_position(self):
        return (self.position_x, self.position_y)

    def on_mouse_click(self, x, y, button, pressed):
        if pressed:
            if button == mouse.Button.left:
                self.position_x = x
                self.position_y = y
                print('{0} at {1}'.format('Pressed left' if pressed else 'Released', (x, y)))
                # self.left_mouse_clicked.emit('left')
            elif button == mouse.Button.right:
                self.right_mouse_clicked.emit('right')
                # print('{0} at {1}'.format('Pressed right' if pressed else 'Released', (x, y)))
                if self.window.current_match_method != 'User':
                    self.capture_screen_triggered.emit(self.position_x, self.position_y)

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
        self.data_type = 'CC'
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
        print(f'dataValue: {data_value}')
        if self.data_value == data_value:
            return
        self.data_value = data_value
        self.valueChanged.emit(self.value)

    def clear_data_value(self):
        print(f'dataValue clear')
        self.data_value = ''
        self.valueChanged.emit(self.value)

    @pyqtSlot(int, int)
    def set_window_size(self, width, height):
        self.window_resize.emit(int(width), int(height))

    value = pyqtProperty(str, fget=get_pyqt_to_web_value, fset=set_pyqt_to_web_value)


class SystemTrayIcon(QSystemTrayIcon):
    method_changed = pyqtSignal(str)

    def __init__(self, icon, parent=None):
        QSystemTrayIcon.__init__(self, icon, parent)
        menu = QMenu(parent)

        match_menu = menu.addMenu('Match method')
        match_group = QActionGroup(match_menu)
        methods = ['Data', 'Image', 'User']
        for method in methods:
            action = QAction(f'Match by {method}', match_menu, checkable=True, checked=method==methods[0])
            action.setData(method)
            match_menu.addAction(action)
            match_group.addAction(action)
        match_group.setExclusive(True)
        match_group.triggered.connect(self.image_method_changed)

        exitAction = menu.addAction('Exit', self.exit)

        # hideAction = menu.addAction("Hide", self.hide)
        # openAction = menu.addAction("open")
        self.setContextMenu(menu)

    def exit(self):
        QCoreApplication.exit()

    def image_method_changed(self, action):
        print(action.text())
        print(action.data())
        self.method_changed.emit(action.data())

    # def hide(self):
    #     self.window.main_window.hide()

