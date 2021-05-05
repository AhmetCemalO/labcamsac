import sys
from os import getcwd
from os import path
from os.path import join, dirname
import numpy as np
import cv2
import time
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox, QMdiSubWindow, QAction, QLineEdit
from PyQt5.QtCore import Qt, QTimer

from udp_socket import UDPSocket
from view.UI_pycams import Ui_PyCams
from view.UI_cam import Ui_Cam
from view.UI_cam_settings import Ui_Settings
from utils import display
from camera_handler import CameraHandler

class PyCamsWindow(QMainWindow):
    def __init__(self, preferences = None):
        self.preferences = preferences if preferences is not None else {}
        
        super().__init__()
        self.ui = Ui_PyCams()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(path.dirname(path.realpath(__file__)) + '/icon/pycams.png'))
        
        self.cam_widgets = []
        for cam in self.preferences.get('cams', []):
            if cam['driver'] in ['avt', 'pco']:
                self.setup_camera(cam)
        
        server_params = self.preferences.get('server_params', None)
        if server_params is not None:
            server = server_params.get('server', None)
            if server == "udp":
                self.server = UDPSocket('0.0.0.0', server_params.get('server_port', 9999))
                self._timer = QTimer(self)
                self._timer.timeout.connect(self.process_server_messages)
                self._timer.start(server_params.get('server_refresh_time', 100))
        
        self.ui.mdiArea.setActivationOrder(1)
        
        self.ui.menuView.triggered[QAction].connect(self.viewMenuActions)
        
        self.show()
    
    def set_save_path(self, save_path):
        if os.path.sep == '/': # Makes sure that the experiment name has the right slashes.
            save_path = save_path.replace('\\',os.path.sep)
        save_path = save_path.strip(' ')
        for cam_widget in self.cam_widgets:
            cam_widget.cam_handler.set_folder_path(save_path)
        
    def process_server_messages(self):
        try:
            msg,address = self.server.receive()
        except Exception:
            return
        action, *value = [i.lower() for i in msg.decode().split('=')]
        if action == 'ping':
            display('Server got PING.')
            self.server.send(b'pong',address)
            
        elif action == 'expname':
            self.set_save_path(value)
            self.server.send(b'ok=expname',address)
            
        elif action == 'trigger':
            for cam_widget in self.cam_widgets:
                if cam_widget.is_triggered:
                    cam_widget.start_cam()
            self.server.send(b'ok=trigger',address)
        
        elif action == 'quit':
            self.server.send(b'ok=bye',address)
            self.close()
            
        
    def setup_camera(self, cam_dict):
        if 'settings_file' in cam_dict.get('params', {}):
            cam_dict['params']['settings_file'] = join(dirname(getcwd()), 'configs', cam_dict['params']['settings_file'])
        writer_dict = {**self.preferences.get('recorder_params', {}), **cam_dict.get('recorder_params', {})}
        cam_handler = CameraHandler(cam_dict, writer_dict)
        if cam_handler.camera_connected:
            cam_handler.start()
            widget = CamWidget(cam_handler)
            self.cam_widgets.append(widget)
            self.setup_widget(cam_dict['description'], widget)
        
    def setup_widget(self, name, widget):
        """
        Adds the supplied widget with the supplied name in the main window
        Checks if widget is already existing but hidden

        :param name: Widget name in main window
        :type name: string
        :param widget: Widget
        :type widget: QWidget
        """
        active_subwindows = [e.objectName() for e in self.ui.mdiArea.subWindowList()]
        if name not in active_subwindows:
            subwindow = QMdiSubWindow(self.ui.mdiArea)
            subwindow.setWindowTitle(name)
            subwindow.setObjectName(name)
            subwindow.setWidget(widget)
            subwindow.resize(widget.minimumSize().width() + 40,widget.minimumSize().height() + 40)
            subwindow.show()
            subwindow.setProperty("center", True)
        else:
            widget.show()
    
    def viewMenuActions(self,q):
        """
        Handles the click event from the View menu.

        :param q:
        :type q: QAction
        """
        if q.text() == 'Subwindow View':
            self.ui.mdiArea.setViewMode(0)
        if q.text() == 'Tabbed View':
            self.ui.mdiArea.setViewMode(1)
        elif q.text() == 'Cascade View':
            self.ui.mdiArea.setViewMode(0)
            self.ui.mdiArea.cascadeSubWindows()
        elif q.text() == 'Tile View':
            self.ui.mdiArea.setViewMode(0)
            self.ui.mdiArea.tileSubWindows()
    
    def closeEvent(self, event):
        """
        Handles the click event from the top right X to close.
        Asks for confirmation before it does.
        """
        reply = QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
            self.close()
        else:
            event.ignore()

    def close(self):
        """
        Clean up non GUI objects
        """
        for cam_widget in self.cam_widgets:
            cam_widget.cam_handler.close()
        time.sleep(0.5)
        display("Pycams out, bye!")
        QApplication.quit()
        sys.exit()


def nparray_to_qimg(img):
    height, width, n_chan = img.shape
    dtype = img.dtype
    if dtype == np.uint16:
        img = cv2.convertScaleAbs(img) #starting from pyqt 5.13 (not available yet) we could use Format_Grayscale16 to not have to do this conversion
    format = QImage.Format_Grayscale8 if n_chan == 1 else QImage.Format_RGB888
    bytesPerLine = n_chan * width
    return QImage(img.data, width, height, bytesPerLine, format)
        
class CamWidget(QWidget):
    def __init__(self, cam_handler = None):
        super().__init__()
        self.ui = Ui_Cam()
        self.ui.setupUi(self)
        
        self.cam_handler = cam_handler
        
        self._init_trigger_checkbox()
        self.is_triggered = self.ui.trigger_checkBox.isChecked()
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(100)
        
        self.AR_policy = Qt.KeepAspectRatio
        
        self.ui.start_stop_pushButton.clicked.connect(self._start_stop)
        self.ui.record_checkBox.stateChanged.connect(self._record)
        self.ui.trigger_checkBox.stateChanged.connect(self._trigger)
        self.ui.keep_AR_checkBox.stateChanged.connect(self._pixmap_aspect_ratio)
        
        self.settings = CamSettingsWidget(self.cam_handler)
        self.ui.settings_pushButton.clicked.connect(self._toggle_settings)
    
    def _update(self):
        if self.cam_handler is not None:
            dest = self.cam_handler.get_filepath()
            self.ui.save_location_label.setText('Filepath: ' + dest)
            if self.cam_handler.is_running.is_set():
                self._update_img()
            if self.cam_handler.start_trigger.is_set() and not self.cam_handler.stop_trigger.is_set():
                self._set_stop_text()
            else:
                self._set_start_text()
        super().update()
        
    def _update_img(self):
        img = np.copy(self.cam_handler.get_image())
        if img is not None:
            pixmap = QPixmap(nparray_to_qimg(img))
            pixmap = pixmap.scaled(self.ui.img_label.width(), self.ui.img_label.height(), self.AR_policy, Qt.FastTransformation)
            self.ui.img_label.setPixmap(pixmap)
    
    def _pixmap_aspect_ratio(self, state):
        if state:
            self.AR_policy = Qt.KeepAspectRatio
        else:
            self.AR_policy = Qt.IgnoreAspectRatio
            
    def resizeEvent(self, event):
        pixmap = self.ui.img_label.pixmap()
        if pixmap is not None:
            self.ui.img_label.setMinimumSize(1,1)
            pixmap = pixmap.scaled(self.ui.img_label.width(), self.ui.img_label.height(), self.AR_policy, Qt.FastTransformation)
            self.ui.img_label.setPixmap(pixmap)

    def _start_stop(self):
        if self.ui.start_stop_pushButton.text() == "Start":
            self.start_cam()
        else:
            self.stop_cam()
    
    def start_cam(self):
        if self.cam_handler is not None:
            ret = self.cam_handler.start_acquisition()
            if ret:
                self._set_stop_text()
        else:
            print("Could not start cam, camera already running", flush=True)
            
    def stop_cam(self):
        self.cam_handler.stop_acquisition()
        self._set_start_text()
    
    def _set_start_text(self):
        self.ui.start_stop_pushButton.setText("Start")
        self.ui.record_checkBox.setEnabled(True)
        self.ui.trigger_checkBox.setEnabled(True)
        
    def _set_stop_text(self):
        self.ui.start_stop_pushButton.setText("Stop")
        self.ui.record_checkBox.setEnabled(False)
        self.ui.trigger_checkBox.setEnabled(False)
        
    def _record(self, state):
        if state:
            self.cam_handler.start_saving()
        else:
            self.cam_handler.stop_saving()

    def _init_trigger_checkbox(self):
        self.cam_handler.query_cam_params()
        while not self.cam_handler.cam_param_get_flag.is_set():
            time.sleep(0.01)
        params = self.cam_handler.get_cam_params()
        if params is not None:
            is_setting_available = 'triggered' in params
            if is_setting_available:
                self.ui.trigger_checkBox.setChecked(params['triggered'])
            else:
                self.ui.trigger_checkBox.setEnabled(False)
                
    def _trigger(self, state):
        self.is_triggered = state
        self.cam_handler.set_cam_param('triggered', state)
        
    def _toggle_settings(self):
        is_visible = self.settings.isVisible()
        self.settings.setVisible(not is_visible)
        if not is_visible:
            self.settings.init_fields()

class CamSettingsWidget(QWidget):
    def __init__(self, cam_handler = None):
        super().__init__()
        self.ui = Ui_Settings()
        self.ui.setupUi(self)
        
        self.cam_handler = cam_handler
        
        self.ui.apply_pushButton.clicked.connect(self._apply_settings)
        self.ui.autogain_checkBox.stateChanged.connect(self._autogain)
        self._autogain(self.ui.autogain_checkBox.isChecked())
        
        self.settings = {'frame_rate': self.ui.framerate_lineEdit,
                         'exposure': self.ui.exposure_lineEdit,
                         'gain': self.ui.gain_lineEdit,
                         'gain_auto' : self.ui.autogain_checkBox}
    
    def _autogain(self, state):
        self.ui.gain_lineEdit.setEnabled(not state)
            
    def _apply_settings(self):
        for setting in self.settings:
            val = self.settings[setting].text()
            if val.isdigit():
                self.cam_handler.set_cam_param(setting, int(val))
        self.cam_handler.set_cam_param('gain_auto', self.ui.autogain_checkBox.isChecked())
        
    def init_fields(self):
        self.cam_handler.query_cam_params()
        while not self.cam_handler.cam_param_get_flag.is_set():
            time.sleep(0.01)
        params = self.cam_handler.get_cam_params()
        if params is not None:
            for setting in self.settings:
                is_setting_available = setting in params
                self.settings[setting].setEnabled(is_setting_available)
                if isinstance(self.settings[setting], QLineEdit):
                    self.settings[setting].setText(str(params[setting]) if is_setting_available else "")
                
                
                
                