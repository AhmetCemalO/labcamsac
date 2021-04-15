import sys
from os import path
import numpy as np
import cv2
import time
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox, QMdiSubWindow, QFileDialog
from PyQt5.QtCore import Qt, QTimer

from view.UI_labcams import Ui_LabCams
from view.UI_cam import Ui_Cam
from utils import display
from camera_handler import CameraHandler

class LabcamsWindow(QMainWindow):
    def __init__(self, preferences = None):
        self.preferences = preferences if preferences is not None else {}
        
        super().__init__()
        self.ui = Ui_LabCams()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(path.dirname(path.realpath(__file__)) + '/icon/labcam.png'))
        
        self.cam_handles = []
        for cam in self.preferences.get('cams', []):
        
            if cam['driver'] in ['avt', 'pco']:
                self.setup_camera(cam)
                
        self.ui.mdiArea.setActivationOrder(1)

        self.show()
        
    def setup_camera(self, cam):
        #cam_dict, writer_dict
        cam_dict = cam
        writer_dict = {**self.preferences.get('recorder_params', {}), **cam_dict.get('recorder_params', {})}
        cam_handler = CameraHandler(cam_dict, writer_dict)
        if cam_handler.camera_connected:
            self.cam_handles.append(cam_handler)
            cam_handler.start()
            widget = CamWidget(cam_handler)
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
        display(q.text()+ " clicked")
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
            self.close()
            event.accept()
            print('Window closed')
            QApplication.quit()
            sys.exit()
        else:
            event.ignore()

    def close(self):
        """
        Clean up non GUI objects
        """
        for cam_handle in self.cam_handles:
            cam_handle.close()
        time.sleep(0.5)
        display("Labcams out, bye!")


def nparray_to_qimg(img):
    height, width, n_chan = img.shape
    dtype = img.dtype
    if dtype == np.uint16:
        img = cv2.convertScaleAbs(img) #starting from pyqt 5.13 (not available yet) we could use Format_Grayscale16 to not have to do this conversion
    format = QImage.Format_Grayscale8 if n_chan == 1 else QImage.Format_RGB888
    bytesPerLine = n_chan * width
    return QImage(img.data, width, height, bytesPerLine, format)
        
class CamWidget(QWidget):
    def __init__(self, camHandler = None):
        super().__init__()
        self.ui = Ui_Cam()
        self.ui.setupUi(self)
        
        self.camHandler = camHandler
        
        self.is_triggered = False
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(100)
        
        self.AR_policy = Qt.KeepAspectRatio
        
        self.ui.start_stop_pushButton.clicked.connect(self._start_stop)
        self.ui.record_checkBox.stateChanged.connect(self._record)
        self.ui.trigger_checkBox.stateChanged.connect(self._trigger)
        self.ui.keep_AR_checkBox.stateChanged.connect(self._pixmap_aspect_ratio)
        
    def _update(self):
        if self.camHandler is not None:
            dest = self.camHandler.get_save_folder()
            self.ui.save_location_label.setText(dest)
            if self.camHandler.is_running.is_set():
                self._update_img()
        super().update()
        
    def _update_img(self):
        img = np.copy(self.camHandler.get_image())
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
            self._start_cam()
        else:
            self._stop_cam()
    
    def _start_cam(self):
        if self.camHandler is not None:
            ret = self.camHandler.start_acquisition()
            if ret:
                self.ui.start_stop_pushButton.setText("Stop")
        else:
            print("Could not start cam, camera already running", flush=True)
            
    def _stop_cam(self):
        self.camHandler.stop_acquisition()
        self.ui.start_stop_pushButton.setText("Start")
        
    def _record(self, state):
        if state:
            self.camHandler.start_saving()
        else:
            self.camHandler.stop_saving()
    
    def _trigger(self, state):
        self.is_triggered = state