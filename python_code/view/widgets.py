from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import Qt

from view.UI_labcams import Ui_Labcams
from view.UI_cam import Ui_Cam

class LabcamsWindow(QMainWindow):
    def __init__(self, preferences = None):
        self.preferences = preferences
        
        super().__init__()
        self.ui = Ui_Labcams()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(path.dirname(path.realpath(__file__)) + '/icon/labcam.png'))
        
        self.cams = None
        for cam in self.preferences.get('cams', []):
            self.setup_camera(cam)

    def setup_camera(self, cam):
        
        
        
        
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
        # display('[Closing connection to the rig and cleaning up screen]')
        # self.expSetter.close()
        display("Labcams out, bye!")
        
def nparray_to_qimg(img):
    height, width, channel = img.shape
    bytesPerLine = channel * width
    return QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)
        
class CamWidget(QWidget):
    def __init__(self, camHandler):
        super().__init__()
        self.ui = Ui_Cam()
        self.ui.setupUi(self)
        
        self.camHandler = camHandler
        
        self.save_folder = None
        self.cam_is_running = False
        self.is_triggered = False
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(100)
        
        self.ui.save_location_pushButton.clicked.connect(self._get_save_location)
        self.ui.start_stop_pushButton.clicked.connect(self._start_stop)
        self.ui.record_checkBox.stateChanged.connect(self._record)
        self.ui.trigger_checkBox.stateChanged.connect(self._trigger)
        
    def _update(self):
        if self.cam_is_running:
            self.update_img()
        super().update()
        
    def _update_img(self):
        img = self.camHandler.img
        if img is not None:
            pixmap = QPixmap(nparray_to_qimg(img))
            pixmap = pixmap.scaled(self.ui.img_label.width, self.ui.img_label.height, Qt.KeepAspectRatio)
            self.ui.img_label.setPixmap(pixmap)

    def _get_save_location(self):
        self.save_folder, _ = QFileDialog.getExistingDirectory(self, 'Select folder', os.path.expanduser('~'), QFileDialog.ShowDirsOnly)
        self.ui.save_location_label.setText(self.save_folder)

    def _start_stop(self):
        if self.ui.start_stop_pushButton.text == "Start":
            self._start_cam()
        else:
            self._stop_cam()
    
    def _start_cam(self):
        if not self.camHandler.is_running.is_set():
            ret = self.camHandler.start_acquisition()
            if ret:
                self.cam_is_running = True
                self.ui.start_stop_pushButton.setText("Stop")
        else:
            print("Could not start cam, camera already running")
            
    def _stop_cam(self):
        self.camHandler.stop_acquisition()
        self.cam_is_running = False
        self.ui.start_stop_pushButton.setText("Start")
        
    def _record(self, state):
        if state:
            self.camHandler.start_saving()
        else:
            self.camHandler.stop_saving()
    
    def _trigger(self, state):
        self.is_triggered = state