# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI_labcams.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(727, 578)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.mdiArea = QtWidgets.QMdiArea(self.centralwidget)
        self.mdiArea.setObjectName("mdiArea")
        self.horizontalLayout.addWidget(self.mdiArea)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 727, 21))
        self.menubar.setObjectName("menubar")
        self.menuView = QtWidgets.QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionCascade = QtWidgets.QAction(MainWindow)
        self.actionCascade.setObjectName("actionCascade")
        self.actionTiled = QtWidgets.QAction(MainWindow)
        self.actionTiled.setObjectName("actionTiled")
        self.actionSubwindow = QtWidgets.QAction(MainWindow)
        self.actionSubwindow.setObjectName("actionSubwindow")
        self.actionTabbed = QtWidgets.QAction(MainWindow)
        self.actionTabbed.setObjectName("actionTabbed")
        self.menuView.addAction(self.actionCascade)
        self.menuView.addAction(self.actionTiled)
        self.menuView.addAction(self.actionTabbed)
        self.menuView.addAction(self.actionSubwindow)
        self.menubar.addAction(self.menuView.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "LabCams"))
        self.menuView.setTitle(_translate("MainWindow", "View"))
        self.actionCascade.setText(_translate("MainWindow", "Cascade View"))
        self.actionTiled.setText(_translate("MainWindow", "Tiled View"))
        self.actionSubwindow.setText(_translate("MainWindow", "Subwindow View"))
        self.actionTabbed.setText(_translate("MainWindow", "Tabbed View"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
